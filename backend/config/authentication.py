from django.conf import settings
from django.core.cache import cache
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


REVOKED_ACCESS_CACHE_PREFIX = "revoked_access_jti:"


def enforce_csrf(request):
    """Runs Django's CSRF check (Origin/Referer + X-CSRFToken vs csrftoken cookie).

    DRF views are csrf_exempt, so anything authenticated by a cookie must call
    this itself — same approach as DRF's SessionAuthentication. Safe methods
    pass through untouched.
    """
    def dummy_get_response(request):  # pragma: no cover - never called
        return None

    check = CSRFCheck(dummy_get_response)
    # populates request.META['CSRF_COOKIE'], which process_view reads
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")


def is_access_token_revoked(jti):
    return bool(jti) and cache.get(f"{REVOKED_ACCESS_CACHE_PREFIX}{jti}") is not None


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticates from the httpOnly access-token cookie only.

    There is deliberately no Authorization-header fallback: the frontend never
    sees a token, and a bearer path would bypass the CSRF check below.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_ACCESS_COOKIE)
        if not raw_token:
            return None

        try:
            # AUTH_TOKEN_CLASSES is AccessToken only, so this also rejects a
            # refresh token (token_type mismatch) placed in the access cookie.
            validated_token = self.get_validated_token(raw_token)
            if is_access_token_revoked(validated_token.get("jti")):
                raise InvalidToken()
            user = self.get_user(validated_token)
        except (InvalidToken, TokenError, exceptions.AuthenticationFailed):
            # Never echo simplejwt's reason (expired vs bad signature vs
            # unknown user) back to the client.
            raise exceptions.AuthenticationFailed("Invalid or expired session.", code="token_not_valid")

        enforce_csrf(request)
        return user, validated_token

    def authenticate_header(self, request):
        # Keeps DRF answering 401 (not 403) for unauthenticated requests,
        # without advertising a Bearer scheme we don't accept.
        return 'Cookie realm="api"'


class CSRFProtectedMixin:
    """For AllowAny auth endpoints: enforce CSRF even without a session, so a
    cross-site page can't log the victim into an attacker's account (login CSRF)."""

    def initial(self, request, *args, **kwargs):
        enforce_csrf(request)
        super().initial(request, *args, **kwargs)
