import logging
import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.middleware.csrf import get_token
from google.oauth2.id_token import verify_oauth2_token
from google.auth.transport import requests as google_requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.throttling import ScopedRateThrottle

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from config.authentication import CSRFProtectedMixin
from . import oauth
from .models import User, AuthProvider
from .serializers import UserProfileUpdateSerializer, UserSerializer
from .services import (
    clear_auth_cookies,
    issue_auth_cookies,
    revoke_access_token,
    set_auth_cookies,
)

logger = logging.getLogger(__name__)

AUTH_FAILED = "Authentication failed. Please try again."


class OAuthLoginError(Exception):
    """Provider rejected the login or returned an unusable identity."""


def _clear_oauth_cookie(response):
    response.delete_cookie(
        settings.AUTH_OAUTH_COOKIE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.COOKIE_SAMESITE,
    )
    return response


def resolve_oauth_user(provider, provider_id, email, defaults):
    """Finds or creates the user for a provider identity.

    An existing (provider, provider_id) link always wins. Otherwise the caller
    must pass a provider-verified email, which is then linked to the matching
    account or used to create one.
    """
    provider_id = str(provider_id)
    with transaction.atomic():
        link = (
            AuthProvider.objects.select_related("user")
            .filter(provider=provider, provider_id=provider_id)
            .first()
        )
        if link:
            return link.user, False

        user = User.objects.filter(email__iexact=email).first()
        created = user is None
        if created:
            user = User.objects.create_user(email=email.lower(), **defaults)
        AuthProvider.objects.create(user=user, provider=provider, provider_id=provider_id)
        return user, created


class OAuthCallbackView(CSRFProtectedMixin, APIView):
    """Shared POST handler for the provider callbacks.

    Request Body:
        - code (str): Provider authorization code.
        - state (str): The state the provider echoed back. Must match the
          dburst_oauth cookie set by OAuthStartView in this same browser.

    Responses:
        200: Authenticated. JWT cookies set.
        400: Missing/invalid code or state, or provider rejected the login.
        503: Provider unreachable.
    """
    provider = None
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def fetch_identity(self, code, redirect_uri, code_verifier):
        """Returns (provider_id, verified_email, defaults). Raises OAuthLoginError."""
        raise NotImplementedError

    def post(self, request):
        code = request.data.get("code")
        state = request.data.get("state")
        if not code or not state:
            return _clear_oauth_cookie(
                Response({"error": AUTH_FAILED}, status=status.HTTP_400_BAD_REQUEST)
            )

        try:
            redirect_uri, code_verifier = oauth.consume(
                self.provider, state, request.COOKIES.get(settings.AUTH_OAUTH_COOKIE)
            )
        except oauth.OAuthStateError:
            logger.warning(f"{self.provider} auth: state check failed")
            return _clear_oauth_cookie(
                Response({"error": AUTH_FAILED}, status=status.HTTP_400_BAD_REQUEST)
            )

        try:
            provider_id, email, defaults = self.fetch_identity(code, redirect_uri, code_verifier)
            user, created = resolve_oauth_user(self.provider, provider_id, email, defaults)
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.provider} auth: provider unreachable: {e}")
            return _clear_oauth_cookie(Response(
                {"error": "Authentication service unreachable. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            ))
        except (OAuthLoginError, ValueError, KeyError) as e:
            logger.warning(f"{self.provider} auth rejected: {e}")
            return _clear_oauth_cookie(
                Response({"error": AUTH_FAILED}, status=status.HTTP_400_BAD_REQUEST)
            )

        if not user.is_active:
            return _clear_oauth_cookie(
                Response({"error": AUTH_FAILED}, status=status.HTTP_400_BAD_REQUEST)
            )

        if created:
            logger.info(f"New user created via {self.provider}: {user.id}")
        response = Response({
            "user": UserSerializer(user).data,
            "message": "User created successfully" if created else "User login successfully",
        }, status=status.HTTP_200_OK)
        return _clear_oauth_cookie(issue_auth_cookies(response, user))


class OAuthStartView(CSRFProtectedMixin, APIView):
    """
    Begins a Google/GitHub login: issues the state + PKCE challenge and returns
    the provider URL to send the browser to.

    Request Body:
        - provider (str): "google" or "github".
        - redirect_uri (str): Must be in that provider's server-side whitelist.

    Responses:
        200: {"authorization_url": "..."}; dburst_oauth cookie set.
        400: Unknown provider, non-whitelisted redirect_uri, or provider not configured.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        provider = request.data.get("provider")
        redirect_uri = request.data.get("redirect_uri")

        if provider not in oauth.PROVIDERS:
            return Response({"error": "Unsupported provider"}, status=status.HTTP_400_BAD_REQUEST)
        if redirect_uri not in oauth.allowed_redirect_uris(provider):
            logger.warning(f"{provider} auth: rejected redirect_uri={redirect_uri!r}")
            return Response({"error": "Invalid redirect_uri"}, status=status.HTTP_400_BAD_REQUEST)
        if not getattr(settings, oauth.PROVIDERS[provider]["client_id_setting"]):
            return Response({"error": "Provider not configured"}, status=status.HTTP_400_BAD_REQUEST)

        authorization_url, cookie_value = oauth.begin(provider, redirect_uri)
        response = Response({"authorization_url": authorization_url}, status=status.HTTP_200_OK)
        response.set_cookie(
            settings.AUTH_OAUTH_COOKIE,
            cookie_value,
            max_age=settings.OAUTH_STATE_MAX_AGE,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path=settings.AUTH_REFRESH_COOKIE_PATH,
        )
        return response


class GoogleAuthView(OAuthCallbackView):
    """Completes Google login (see OAuthCallbackView)."""
    provider = "google"

    def fetch_identity(self, code, redirect_uri, code_verifier):
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
            },
            timeout=10,
        )
        if token_response.status_code >= 500:
            token_response.raise_for_status()
        id_token = token_response.json().get("id_token") if token_response.ok else None
        if not id_token:
            raise OAuthLoginError("token exchange returned no id_token")

        google_user = verify_oauth2_token(
            id_token, google_requests.Request(), audience=settings.GOOGLE_CLIENT_ID
        )
        if not google_user.get("email_verified"):
            raise OAuthLoginError("Google email not verified")

        return google_user["sub"], google_user["email"], {
            "name": google_user.get("name", ""),
            "avatar_url": google_user.get("picture", ""),
        }


class GithubAuthView(OAuthCallbackView):
    """Completes GitHub login (see OAuthCallbackView).

    Only the account's primary *verified* email is trusted for linking — the
    public profile email is user-editable and unverified.
    """
    provider = "github"

    def fetch_identity(self, code, redirect_uri, code_verifier):
        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        token_res.raise_for_status()
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise OAuthLoginError("token exchange returned no access_token")

        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}
        user_res = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        user_res.raise_for_status()
        gh_user = user_res.json()

        email_res = requests.get("https://api.github.com/user/emails", headers=headers, timeout=10)
        email_res.raise_for_status()
        email = next(
            (e["email"] for e in email_res.json() if e.get("primary") and e.get("verified")),
            None,
        )
        if not email:
            raise OAuthLoginError("GitHub account has no verified primary email")

        return gh_user["id"], email, {
            "name": gh_user.get("name") or gh_user.get("login") or "",
            "avatar_url": gh_user.get("avatar_url", ""),
        }


class CSRFTokenView(APIView):
    """
    Issues the readable csrftoken cookie the frontend echoes back in
    X-CSRFToken on unsafe requests.

    Responses:
        200: Cookie set.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # CsrfViewMiddleware writes the cookie on the way out once a token
        # has been requested.
        get_token(request)
        return Response({"detail": "CSRF cookie set"})


class ProfileView(APIView):
    """
    The current user's profile.

    GET is the frontend's session check. PATCH updates the editable fields
    (`name`, `avatar_url`); everything else in the body is ignored. PATCH is
    CSRF-checked by CookieJWTAuthentication like every unsafe request.

    Request Body (PATCH):
        - name (str, optional): 1-120 chars, no control characters or < >.
        - avatar_url (str|null, optional): absolute http(s) URL, max 2048
          chars, no credentials, public host. Blank or null clears it. Never
          fetched server-side.

    Responses:
        200: {"user": {...}}
        400: Field errors, e.g. {"avatar_url": ["Enter a valid http(s) URL."]}
        401: User is not authenticated.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "profile"

    def get_throttles(self):
        # GET runs on every page load; only writes are rate limited.
        if self.request.method == "PATCH":
            return [ScopedRateThrottle()]
        return []

    def get(self, request):
        user = request.user
        return Response({"user": UserSerializer(user).data})

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserSerializer(user).data})


class TokenRefreshView(CSRFProtectedMixin, APIView):
    """
    Rotates the access/refresh cookie pair from the refresh cookie.

    The presented refresh token is blacklisted (BLACKLIST_AFTER_ROTATION), so
    each one works once.

    Responses:
        200: New cookies set. Body contains no tokens.
        401: Refresh cookie missing, invalid, expired, blacklisted, or the user
             is inactive. Auth cookies are cleared.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token_refresh"

    def post(self, request):
        refresh_str = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if not refresh_str:
            return clear_auth_cookies(Response(
                {"detail": "Invalid or expired session."}, status=status.HTTP_401_UNAUTHORIZED
            ))

        serializer = TokenRefreshSerializer(data={"refresh": refresh_str})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, AuthenticationFailed, ValidationError, ObjectDoesNotExist) as e:
            logger.info(f"Token refresh rejected: {type(e).__name__}")
            return clear_auth_cookies(Response(
                {"detail": "Invalid or expired session."}, status=status.HTTP_401_UNAUTHORIZED
            ))

        data = serializer.validated_data
        response = Response({"detail": "Session refreshed"}, status=status.HTTP_200_OK)
        return set_auth_cookies(response, data["access"], data.get("refresh", refresh_str))


class LogoutView(CSRFProtectedMixin, APIView):
    """
    Logs the user out: blacklists the refresh token, revokes the current access
    token, and clears the auth cookies.

    Works without a valid access token (it may have just expired), so it reads
    the cookies directly instead of requiring authentication.

    Responses:
        200: Logout successful.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_str = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if refresh_str:
            try:
                RefreshToken(refresh_str).blacklist()
            except TokenError:
                pass  # already blacklisted / expired — nothing left to revoke

        access_str = request.COOKIES.get(settings.AUTH_ACCESS_COOKIE)
        if access_str:
            try:
                revoke_access_token(AccessToken(access_str))
            except TokenError:
                pass

        response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        return clear_auth_cookies(response)


def blacklist_all_refresh_tokens(user):
    """Blacklists every outstanding refresh token of `user`. Returns how many."""
    outstanding = OutstandingToken.objects.filter(user=user).exclude(
        id__in=BlacklistedToken.objects.filter(token__user=user).values("token_id")
    )
    count = 0
    for token in outstanding:
        _, created = BlacklistedToken.objects.get_or_create(token=token)
        count += int(created)
    return count
