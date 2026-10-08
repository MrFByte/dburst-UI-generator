from unittest.mock import patch

import pytest
from django.urls import reverse

from otp_auth.models import OTP
from otp_auth.services import generate_otp
from users.models import User


@pytest.fixture
def request_url():
    return reverse("otp-request")


@pytest.fixture
def verify_url():
    return reverse("otp-verify")


@pytest.mark.django_db
@patch("otp_auth.views.send_otp_email.delay")
def test_request_otp_sends_email_and_creates_record(mock_delay, api_client, request_url):
    response = api_client.post(request_url, data={"email": "user@example.com"})

    assert response.status_code == 200
    assert OTP.objects.filter(email="user@example.com").exists()
    mock_delay.assert_called_once()
    assert mock_delay.call_args.args[0] == "user@example.com"
    assert mock_delay.call_args.args[2] == "login"


@pytest.mark.django_db
@patch("otp_auth.views.send_otp_email.delay")
def test_request_otp_passes_signup_purpose(mock_delay, api_client, request_url):
    response = api_client.post(
        request_url, data={"email": "newbie@example.com", "purpose": "signup"}
    )

    assert response.status_code == 200
    assert mock_delay.call_args.args[2] == "signup"


@pytest.mark.django_db
@patch("otp_auth.views.send_otp_email.delay", side_effect=ConnectionError("broker down"))
def test_request_otp_returns_503_when_dispatch_fails(mock_delay, api_client, request_url):
    response = api_client.post(request_url, data={"email": "unlucky@example.com"})

    assert response.status_code == 503
    assert "error" in response.data


@pytest.mark.django_db
def test_request_otp_rejects_invalid_email(api_client, request_url):
    response = api_client.post(request_url, data={"email": "not-an-email"})
    assert response.status_code == 400


@pytest.mark.django_db
@patch("otp_auth.views.send_otp_email.delay")
def test_request_otp_rate_limited(mock_delay, api_client, request_url, settings):
    settings.OTP_MAX_REQUESTS_PER_WINDOW = 2
    email = "spammer@example.com"

    api_client.post(request_url, data={"email": email})
    api_client.post(request_url, data={"email": email})
    response = api_client.post(request_url, data={"email": email})

    assert response.status_code == 429
    assert "error" in response.data


@pytest.mark.django_db
def test_verify_otp_logs_in_existing_user(api_client, verify_url):
    user = User.objects.create_user(email="existing@example.com", name="Existing")
    code = generate_otp("existing@example.com")

    response = api_client.post(verify_url, data={"email": "existing@example.com", "code": code})

    assert response.status_code == 200
    assert response.data["message"] == "User login successfully"
    assert response.data["user"]["id"] == str(user.id)
    assert "refresh" in response.cookies
    assert "access" in response.cookies


@pytest.mark.django_db
def test_verify_otp_creates_new_user(api_client, verify_url):
    code = generate_otp("brandnew@example.com")

    response = api_client.post(verify_url, data={"email": "brandnew@example.com", "code": code})

    assert response.status_code == 200
    assert response.data["message"] == "User created successfully"
    assert User.objects.filter(email="brandnew@example.com").exists()


@pytest.mark.django_db
def test_verify_otp_rejects_wrong_code(api_client, verify_url):
    generate_otp("badcode@example.com")

    response = api_client.post(verify_url, data={"email": "badcode@example.com", "code": "000000"})

    assert response.status_code == 400
    assert response.data["error"] == "Invalid or expired OTP."


@pytest.mark.django_db
def test_verify_otp_rejects_malformed_code(api_client, verify_url):
    response = api_client.post(verify_url, data={"email": "x@example.com", "code": "abc"})
    assert response.status_code == 400
