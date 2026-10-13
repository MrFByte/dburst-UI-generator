from unittest.mock import patch

import pytest
from django.conf import settings
from requests.exceptions import RequestException

from users.models import AuthProvider, User

from .oauth_helpers import REDIRECT_URIS, callback, json_response, start_oauth

GOOGLE_USER = {
    "email": "newuser@example.com",
    "name": "New User",
    "picture": "http://new.com/pic.jpg",
    "sub": "google999",
    "email_verified": True,
}


@pytest.fixture(autouse=True)
def client_id(settings):
    settings.GOOGLE_CLIENT_ID = "google-client"
    settings.GOOGLE_CLIENT_SECRET = "google-secret"


def run(client, verify_return=None, verify_side_effect=None, post_return=None, post_side_effect=None):
    token, state, _ = start_oauth(client, "google")
    with patch("users.views.requests.post") as mock_post, \
            patch("users.views.verify_oauth2_token") as mock_verify:
        mock_post.return_value = post_return or json_response({"id_token": "idtok"})
        if post_side_effect:
            mock_post.side_effect = post_side_effect
        mock_verify.return_value = verify_return
        if verify_side_effect:
            mock_verify.side_effect = verify_side_effect
        res = callback(client, "google", token, code="valid", state=state)
    return res, mock_post, mock_verify


@pytest.mark.django_db
def test_google_creates_user_and_sets_cookies(csrf_client):
    res, mock_post, mock_verify = run(csrf_client, verify_return=GOOGLE_USER)

    assert res.status_code == 200
    assert res.data["message"] == "User created successfully"
    user = User.objects.get(email="newuser@example.com")
    assert user.name == "New User"
    assert AuthProvider.objects.get(user=user).provider_id == "google999"
    assert res.cookies[settings.AUTH_ACCESS_COOKIE]["httponly"] is True

    sent = mock_post.call_args.kwargs["data"]
    # redirect_uri comes from the server-side state, PKCE verifier is sent.
    assert sent["redirect_uri"] == REDIRECT_URIS["google"]
    assert sent["code_verifier"]
    assert mock_verify.call_args.kwargs["audience"] == "google-client"


@pytest.mark.django_db
def test_google_logs_in_existing_user_by_verified_email(csrf_client):
    user = User.objects.create_user(email="NewUser@example.com")
    res, _, _ = run(csrf_client, verify_return=GOOGLE_USER)

    assert res.status_code == 200
    assert res.data["message"] == "User login successfully"
    assert res.data["user"]["id"] == str(user.id)
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_google_unverified_email_rejected(csrf_client):
    res, _, _ = run(csrf_client, verify_return={**GOOGLE_USER, "email_verified": False})
    assert res.status_code == 400
    assert not User.objects.exists()


@pytest.mark.django_db
def test_google_invalid_code(csrf_client):
    res, _, _ = run(csrf_client, post_return=json_response({"error": "invalid_grant"}, 400))
    assert res.status_code == 400


@pytest.mark.django_db
def test_google_network_error(csrf_client):
    res, _, _ = run(csrf_client, post_side_effect=RequestException("down"))
    assert res.status_code == 503


@pytest.mark.django_db
def test_google_invalid_id_token(csrf_client):
    res, _, _ = run(csrf_client, verify_side_effect=ValueError("Token has wrong audience"))
    assert res.status_code == 400
    assert "audience" not in res.data["error"]
