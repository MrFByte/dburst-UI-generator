import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_otp_email(email, code, purpose="login"):
    """Sends an OTP email synchronously. Caller is responsible for turning a raised
    exception into an HTTP error response.
    """
    subject = f"Your DBurst verification code: {code}"

    if purpose == "signup":
        message = f"""Hello,

Welcome to DBurst!

To complete your signup, please use this verification code:

{code}

This code expires in {settings.OTP_TTL_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Best regards,
DBurst Team
"""
    else:
        message = f"""Hello,

To sign in to your DBurst account, please use this verification code:

{code}

This code expires in {settings.OTP_TTL_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Best regards,
DBurst Team
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"OTP email sent to {email} (purpose={purpose})")
    except Exception as exc:
        logger.error(f"OTP email send failed for {email} (purpose={purpose}): {exc}")
        raise
