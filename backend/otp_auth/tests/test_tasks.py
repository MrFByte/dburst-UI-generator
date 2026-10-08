from smtplib import SMTPException
from unittest.mock import patch

import pytest
from django.core import mail
from django.template import TemplateDoesNotExist

from otp_auth.tasks import send_otp_email


@pytest.fixture(autouse=True)
def locmem_email(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []


@pytest.mark.django_db
def test_send_otp_email_delivers_branded_email():
    result = send_otp_email.apply(args=("someone@example.com", "123456", "login"))
    result.get()

    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == ["someone@example.com"]
    assert "123456" in sent.subject
    assert len(sent.alternatives) == 1
    assert sent.alternatives[0][1] == "text/html"
    assert "123456" in sent.alternatives[0][0]
    # The DBurst logo is embedded as an inline attachment.
    assert len(sent.attachments) == 1


@pytest.mark.django_db
@patch("otp_auth.tasks.render_to_string", side_effect=TemplateDoesNotExist("missing"))
def test_send_otp_email_skips_cleanly_on_template_error(mock_render):
    # A broken template is a programming error, not a transient failure —
    # the task should log it and return without raising or sending mail.
    result = send_otp_email.apply(args=("someone@example.com", "123456", "login"))
    result.get()

    assert mail.outbox == []


@pytest.mark.django_db
@patch("otp_auth.tasks.EmailMultiAlternatives.send", side_effect=SMTPException("boom"))
def test_send_otp_email_contains_exhausted_retries(mock_send, monkeypatch):
    # Regression guard: self.retry() must be called WITHOUT exc=, otherwise
    # Celery re-raises that original exception on exhaustion instead of
    # MaxRetriesExceededError, which would skip our except clause and let
    # the failure escape the task entirely instead of being logged.
    monkeypatch.setattr(send_otp_email, "max_retries", 2)
    monkeypatch.setattr(send_otp_email, "default_retry_delay", 0)

    result = send_otp_email.apply(args=("someone@example.com", "123456", "login"))
    result.get()  # must not raise

    assert mock_send.call_count == 3  # 1 initial attempt + 2 retries
    assert mail.outbox == []
