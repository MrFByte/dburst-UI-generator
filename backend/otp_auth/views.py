from config.api_errors import error_response
import logging

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from config.authentication import CSRFProtectedMixin
from users.models import User
from users.serializers import UserSerializer
from users.services import issue_auth_cookies

from .serializers import RequestOTPSerializer, VerifyOTPSerializer
from .services import OTPInvalidOrExpired, OTPRateLimitExceeded, generate_otp, verify_otp
from .tasks import send_otp_email

logger = logging.getLogger(__name__)


class RequestOTPView(CSRFProtectedMixin, APIView):
    """
    Requests a one-time passcode for email sign-in/sign-up.

    Request Body:
        - email (str): The address to send the code to.
        - purpose (str, optional): "login" or "signup" — only changes email copy.

    Responses:
        200: OTP email sent.
        429: Too many OTP requests for this email in the current window, or
             too many requests from this client.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        purpose = request.data.get("purpose", "login")

        try:
            code = generate_otp(email)
        except OTPRateLimitExceeded:
            logger.warning(f"OTP rate limit hit for {email} (purpose={purpose})")
            return error_response("Too many OTP requests. Please try again later.", "otp_rate_limited", 429)

        try:
            send_otp_email(email, code, purpose)
        except Exception:
            # The OTP row already exists, but delivery failed — tell the
            # caller plainly instead of a bare 500.
            logger.exception(f"Failed to send OTP email for {email} (purpose={purpose})")
            return error_response("Could not send the verification email right now. Please try again.", "email_unavailable", 503)

        logger.info(f"OTP requested for {email} (purpose={purpose})")
        return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)


class VerifyOTPView(CSRFProtectedMixin, APIView):
    """
    Verifies a one-time passcode and logs the user in, creating their
    account on first verification.

    Request Body:
        - email (str)
        - code (str): The 6-digit code.

    Responses:
        200: Verified. JWT cookies set.
        400: Invalid, expired, or already-used code.
        429: Too many attempts from this client.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        code = serializer.validated_data["code"]

        try:
            verify_otp(email, code)
        except OTPInvalidOrExpired:
            logger.warning(f"Invalid/expired OTP verify attempt for {email}")
            return error_response("Invalid or expired OTP.", "otp_invalid", 400)

        with transaction.atomic():
            # iexact: OAuth-created accounts may store the provider's casing.
            user = User.objects.filter(email__iexact=email).first()
            created = user is None
            if created:
                user = User.objects.create_user(email=email)

            if not user.is_active:
                return error_response("Invalid or expired OTP.", "otp_invalid", 400)

            message = "User login successfully"
            if created:
                message = "User created successfully"
                logger.info(f"New user created via email OTP: {email}")

            response = Response({
                "user": UserSerializer(user).data,
                "message": message,
            }, status=status.HTTP_200_OK)
            return issue_auth_cookies(response, user)
