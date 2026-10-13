from unittest.mock import patch

import pytest

from otp_auth.tasks import send_otp_email


@pytest.fixture
def resend_key(settings):
    settings.RESEND_API_KEY = "re_test"
    settings.RESEND_DEFAULT_EMAIL = "noreply@example.com"


@patch("otp_auth.tasks.resend.Emails.send", return_value={"id": "email_123"})
def test_send_otp_email_sends_branded_email(mock_send, resend_key):
    send_otp_email("someone@example.com", "123456", "login")

    params = mock_send.call_args.args[0]
    assert params["to"] == ["someone@example.com"]
    assert "123456" in params["subject"]
    assert "123456" in params["html"]


@patch("otp_auth.tasks.resend.Emails.send", side_effect=Exception("resend down"))
def test_send_otp_email_raises_on_provider_failure(mock_send, resend_key):
    with pytest.raises(Exception):
        send_otp_email("someone@example.com", "123456", "login")


def test_send_otp_email_requires_api_key(settings):
    settings.RESEND_API_KEY = None
    with pytest.raises(ValueError):
        send_otp_email("someone@example.com", "123456", "login")
