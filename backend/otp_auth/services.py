import secrets

from django.conf import settings
from django.utils import timezone

from .models import OTP


class OTPRateLimitExceeded(Exception):
    """Too many OTP requests for this email within the rate-limit window."""


class OTPInvalidOrExpired(Exception):
    """The supplied code is wrong, expired, already used, or locked out."""


def generate_otp(email: str) -> str:
    """Creates and stores a new OTP for `email`, enforcing the per-window rate limit.

    Returns the raw (unhashed) code to be emailed to the user.
    """
    window_start = timezone.now() - timezone.timedelta(hours=settings.OTP_RATE_LIMIT_WINDOW_HOURS)
    recent_count = OTP.objects.filter(email=email, created_at__gte=window_start).count()
    if recent_count >= settings.OTP_MAX_REQUESTS_PER_WINDOW:
        raise OTPRateLimitExceeded()

    code = f"{secrets.randbelow(10 ** settings.OTP_LENGTH):0{settings.OTP_LENGTH}d}"
    OTP.create_for_email(email, code)
    return code


def verify_otp(email: str, code: str) -> None:
    """Verifies `code` against the most recent OTP for `email`, marking it used on success.

    Raises OTPInvalidOrExpired if the code is wrong, expired, already used, or
    the OTP has been locked out after too many failed attempts.
    """
    otp = OTP.objects.filter(email=email, is_used=False).order_by("-created_at").first()

    if not otp or otp.is_expired() or otp.is_locked():
        raise OTPInvalidOrExpired()

    if not otp.check_code(code):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        raise OTPInvalidOrExpired()

    otp.is_used = True
    otp.save(update_fields=["is_used"])
