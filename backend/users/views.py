import logging
import requests
import json
from django.db import transaction
from django.conf import settings
from google.oauth2.id_token import verify_oauth2_token
from google.auth.transport import requests as google_requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, AuthProvider
from .serializers import UserSerializer

logger = logging.getLogger(__name__)
REFRESH_TOKEN_EXPIRY = settings.REFRESH_TOKEN_EXPIRY
ACCESS_TOKEN_EXPIRY = settings.ACCESS_TOKEN_EXPIRY


class GoogleAuthView(APIView):
    """
    Authenticates or registers a user using Google OAuth authorization-code flow.

    Frontend sends a short-lived Google OAuth code + the redirect_uri it used
    → backend validates redirect_uri against a whitelist, exchanges the code
    for tokens, verifies the ID token, and returns a user + JWT cookie pair.

    Request Body:
        - code (str): Google OAuth authorization code.
        - redirect_uri (str): The exact redirect URI used in the auth request.

    Responses:
        200: Authenticated. JWT cookies set.
        400: Invalid or missing data.
        503: Google is unreachable.
        500: Internal error.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("Working auth 1")
        code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri")

        print("Working auth 2")
        if not code:
            print("Working auth 3")
            return Response({"error": "Missing OAuth code"}, status=status.HTTP_400_BAD_REQUEST)
        if not redirect_uri:
            print("Working auth 4")
            return Response({"error": "Missing redirect_uri"}, status=status.HTTP_400_BAD_REQUEST)

        # Server-side whitelist — never trust a redirect_uri from the client blindly
        allowed_uris = getattr(settings, "GOOGLE_ALLOWED_REDIRECT_URIS", [])
        if redirect_uri not in allowed_uris:
            print("Working auth 5")
            logger.warning(f"Google auth: rejected redirect_uri={redirect_uri!r}")
            return Response({"error": "Invalid redirect_uri"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            print("Working auth 6")
            token_url = "https://oauth2.googleapis.com/token"
            payload = {
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }

            token_response = requests.post(token_url, data=payload, timeout=10)
            token_response.raise_for_status()

            token_data = token_response.json()
            id_token = token_data.get("id_token")
            if not id_token:
                logger.warning("Google token exchange did not return id_token")
                return Response({"error": "Unable to authenticate with Google"}, status=status.HTTP_400_BAD_REQUEST)

            google_user = verify_oauth2_token(id_token, google_requests.Request())
            email = google_user["email"]

            if not google_user.get("email_verified"):
                print("Working auth 7")
                return Response({"error": "Google email not verified"}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                print("Working auth 8")
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "name": google_user.get("name", ""),
                        "avatar_url": google_user.get("picture", ""),
                    },
                )

                AuthProvider.objects.get_or_create(
                    user=user,
                    provider=AuthProvider.Choices.GOOGLE,
                    provider_id=google_user["sub"],
                )

                message = "User login successfully"
                if created:
                    message = "User created successfully"
                    logger.info(f"New user created via Google: {email}")

                refresh = RefreshToken.for_user(user)
                response = Response({
                    "user": UserSerializer(user).data,
                    "message": message,
                }, status=status.HTTP_200_OK)

                response.set_cookie(
                    key='refresh',
                    value=str(refresh),
                    httponly=True,
                    secure=True,
                    samesite='None',
                    max_age=REFRESH_TOKEN_EXPIRY,
                )
                response.set_cookie(
                    key='access',
                    value=str(refresh.access_token),
                    httponly=True,
                    secure=True,
                    samesite='None',
                    max_age=ACCESS_TOKEN_EXPIRY,
                )
                return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during Google token exchange: {e}")
            return Response({"error": "Google authentication service unreachable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except ValueError as e:
            logger.warning(f"Invalid Google ID token: {e}")
            return Response({"error": "Invalid Google token provided"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Unexpected Google Auth error: {e}")
            return Response({"error": "Authentication failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GithubAuthView(APIView):
    """
    Authenticates/Registers a user using GitHub OAuth authorization-code flow.

    Frontend sends GitHub OAuth `code` + `redirect_uri` → backend validates
    redirect_uri against a whitelist, exchanges code for access token, fetches
    GitHub user profile, and returns JWT cookies.

    Request Body:
        - code (str): GitHub OAuth authorization code.
        - redirect_uri (str): The exact redirect URI used in the auth request.

    Responses:
        200: Authenticated. JWT cookies set.
        400: Invalid or missing data.
        500: Internal error.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri")

        if not code:
            return Response({"error": "Missing OAuth code"}, status=status.HTTP_400_BAD_REQUEST)
        if not redirect_uri:
            return Response({"error": "Missing redirect_uri"}, status=status.HTTP_400_BAD_REQUEST)

        # Server-side whitelist — never trust a redirect_uri from the client blindly
        allowed_uris = getattr(settings, "GITHUB_ALLOWED_REDIRECT_URIS", [])
        if redirect_uri not in allowed_uris:
            logger.warning(f"GitHub auth: rejected redirect_uri={redirect_uri!r}")
            return Response({"error": "Invalid redirect_uri"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_url = "https://github.com/login/oauth/access_token"
            payload = {
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            }

            headers = {"Accept": "application/json"}
            token_res = requests.post(token_url, data=payload, headers=headers, timeout=10)
            token_res.raise_for_status()

            token_data = token_res.json()
            access_token = token_data.get("access_token")

            if not access_token:
                return Response({"error": "Unable to authenticate with GitHub"}, status=400)

            user_res = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            user_res.raise_for_status()
            gh_user = user_res.json()

            email = gh_user.get("email")
            if not email:
                email_res = requests.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10
                )
                email_res.raise_for_status()
                email_list = email_res.json()
                primary_email = next((e["email"] for e in email_list if e["primary"]), None)
                email = primary_email or email_list[0]["email"]

            github_id = gh_user["id"]

            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "name": gh_user.get("name") or gh_user.get("login"),
                        "avatar_url": gh_user.get("avatar_url", "")
                    }
                )

                AuthProvider.objects.get_or_create(
                    user=user,
                    provider=AuthProvider.Choices.GITHUB,
                    provider_id=github_id
                )

                message = "User created successfully" if created else "User login successfully"
                if created:
                    logger.info(f"New user created via GitHub: {email}")

                refresh = RefreshToken.for_user(user)
                response = Response({
                    "user": UserSerializer(user).data,
                    "message": message,
                }, status=200)

                response.set_cookie(
                    key='refresh',
                    value=str(refresh),
                    httponly=True,
                    secure=True,
                    samesite='None',
                    max_age=REFRESH_TOKEN_EXPIRY,
                )
                response.set_cookie(
                    key='access',
                    value=str(refresh.access_token),
                    httponly=True,
                    secure=True,
                    samesite='None',
                    max_age=ACCESS_TOKEN_EXPIRY,
                )
                return response

        except Exception as e:
            logger.exception(f"GitHub OAuth error: {e}")
            return Response({"error": "GitHub authentication failed"}, status=500)
        

class GetProfileView(APIView):
    """
    Returns the current user's profile.
    
    Request Body:
        - None

    Responses:
        200: User profile returned.
        401: User is not authenticated.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({"user": UserSerializer(user).data})


class TokenRefreshView(APIView):
    """
    Refreshes the access token.
    
    Request Body:
        - None

    Responses:
        200: New access token returned.
        401: Refresh token is not found.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh = request.COOKIES.get("refresh")
        if not refresh:
            return Response({"error": "Refresh token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            token = RefreshToken(refresh)
            response = Response({"access": str(token.access_token)}, status=status.HTTP_200_OK)
            response.set_cookie(
                key='access',
                value=str(token.access_token),
                httponly=True,
                secure=True, 
                samesite='None',
                max_age=ACCESS_TOKEN_EXPIRY,
            )
            return response
        except Exception as e:
            logger.exception(f"Unexpected token refresh error: {e}")
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    Logout the user.
    
    Request Body:
        - None

    Responses:
        200: Logout successful.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh")
        response.delete_cookie("access")
        return response
    
