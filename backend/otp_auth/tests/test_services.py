import pytest
from django.utils import timezone

from otp_auth.models import OTP
from otp_auth.services import (
    OTPInvalidOrExpired,
    OTPRateLimitExceeded,
    generate_otp,
    verify_otp,
)


@pytest.mark.django_db
def test_generate_otp_creates_hashed_record():
    code = generate_otp("new@example.com")

    assert len(code) == 6
    assert code.isdigit()

    otp = OTP.objects.get(email="new@example.com")
    assert otp.code_hash != code
    assert otp.check_code(code)


@pytest.mark.django_db
def test_verify_otp_accepts_correct_code():
    code = generate_otp("good@example.com")
    verify_otp("good@example.com", code)

    otp = OTP.objects.get(email="good@example.com")
    assert otp.is_used


@pytest.mark.django_db
def test_verify_otp_rejects_wrong_code():
    generate_otp("wrong@example.com")

    with pytest.raises(OTPInvalidOrExpired):
        verify_otp("wrong@example.com", "000000")


@pytest.mark.django_db
def test_verify_otp_rejects_reused_code():
    code = generate_otp("reuse@example.com")
    verify_otp("reuse@example.com", code)

    with pytest.raises(OTPInvalidOrExpired):
        verify_otp("reuse@example.com", code)


@pytest.mark.django_db
def test_verify_otp_rejects_expired_code():
    code = generate_otp("expired@example.com")
    otp = OTP.objects.get(email="expired@example.com")
    otp.expires_at = timezone.now() - timezone.timedelta(seconds=1)
    otp.save(update_fields=["expires_at"])

    with pytest.raises(OTPInvalidOrExpired):
        verify_otp("expired@example.com", code)


@pytest.mark.django_db
def test_verify_otp_locks_out_after_max_attempts(settings):
    settings.OTP_MAX_VERIFY_ATTEMPTS = 3
    code = generate_otp("lockout@example.com")

    for _ in range(3):
        with pytest.raises(OTPInvalidOrExpired):
            verify_otp("lockout@example.com", "000000")

    # Even the correct code is now rejected — the OTP is locked out.
    with pytest.raises(OTPInvalidOrExpired):
        verify_otp("lockout@example.com", code)


@pytest.mark.django_db
def test_generate_otp_enforces_rate_limit(settings):
    settings.OTP_MAX_REQUESTS_PER_WINDOW = 3
    email = "ratelimited@example.com"

    for _ in range(3):
        generate_otp(email)

    with pytest.raises(OTPRateLimitExceeded):
        generate_otp(email)


@pytest.mark.django_db
def test_generate_otp_rate_limit_is_per_email(settings):
    settings.OTP_MAX_REQUESTS_PER_WINDOW = 1

    generate_otp("a@example.com")
    # Should not raise — a different email has its own budget.
    generate_otp("b@example.com")
