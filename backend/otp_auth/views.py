import logging

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.serializers import UserSerializer
from users.services import issue_auth_cookies

from .serializers import RequestOTPSerializer, VerifyOTPSerializer
from .services import OTPInvalidOrExpired, OTPRateLimitExceeded, generate_otp, verify_otp
from .tasks import send_otp_email

logger = logging.getLogger(__name__)


class RequestOTPView(APIView):
    """
    Requests a one-time passcode for email sign-in/sign-up.

    Request Body:
        - email (str): The address to send the code to.
        - purpose (str, optional): "login" or "signup" — only changes email copy.

    Responses:
        200: OTP email queued.
        429: Too many OTP requests for this email in the current window.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("At RequestOTPView 1")
        serializer = RequestOTPSerializer(data=request.data)
        print("At RequestOTPView 2")
        serializer.is_valid(raise_exception=True)
        print("At RequestOTPView 3")
        email = serializer.validated_data["email"].lower()
        print("At RequestOTPView 4")
        purpose = request.data.get("purpose", "login")

        try:
            code = generate_otp(email)
        except OTPRateLimitExceeded:
            logger.warning(f"OTP rate limit hit for {email} (purpose={purpose})")
            return Response(
                {"error": "Too many OTP requests. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            send_otp_email.delay(email, code, purpose)
            print("At RequestOTPView 5")
        except Exception:
            # Broker unreachable or similar — the OTP row already exists,
            # but nothing will ever deliver it, so tell the caller plainly
            # instead of a bare 500.
            logger.exception(f"Failed to enqueue OTP email task for {email} (purpose={purpose})")
            return Response(
                {"error": "Could not send the verification email right now. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        logger.info(f"OTP requested for {email} (purpose={purpose})")
        return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """
    Verifies a one-time passcode and logs the user in, creating their
    account on first verification.

    Request Body:
        - email (str)
        - code (str): The 6-digit code.

    Responses:
        200: Verified. JWT cookies set.
        400: Invalid, expired, or already-used code.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        code = serializer.validated_data["code"]

        try:
            verify_otp(email, code)
        except OTPInvalidOrExpired:
            logger.warning(f"Invalid/expired OTP verify attempt for {email}")
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user, created = User.objects.get_or_create(email=email)

            message = "User login successfully"
            if created:
                message = "User created successfully"
                logger.info(f"New user created via email OTP: {email}")

            response = Response({
                "user": UserSerializer(user).data,
                "message": message,
            }, status=status.HTTP_200_OK)
            return issue_auth_cookies(response, user)
