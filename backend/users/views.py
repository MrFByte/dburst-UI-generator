import logging
import requests
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


class GoogleAuthView(APIView):
    """
    Authenticates or registers a user using Google OAuth `auth-code` flow.

    Frontend sends a short-lived Google OAuth code → backend exchanges it
    → validates the identity → creates/returns a User + JWT token pair.

    Request Body:
        - code (str): Google OAuth code, required.

    Responses:
        200: Google account authenticated, JWT returned.
        400: Invalid or missing data.
        500: Internal authentication error.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "Missing OAuth code"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_url = "https://oauth2.googleapis.com/token"
            payload = {
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": "postmessage",
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

            with transaction.atomic():
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
                    max_age=86400,  # 1 day
                )
                response.set_cookie(
                    key='access',
                    value=str(refresh.access_token),
                    httponly=True,
                    secure=True, 
                    samesite='None',
                    max_age=1800,  # 30 minutes
                )
                response.set_cookie('ua', request.META.get('HTTP_USER_AGENT', ''))
                response.set_cookie('ip', request.META.get('REMOTE_ADDR', ''))
                
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


