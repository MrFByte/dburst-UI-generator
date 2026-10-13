from unittest.mock import patch

import pytest
from django.conf import settings

from users.models import AuthProvider, User

from .oauth_helpers import REDIRECT_URIS, callback, json_response, start_oauth


@pytest.fixture(autouse=True)
def client_id(settings):
    settings.GITHUB_CLIENT_ID = "github-client"
    settings.GITHUB_CLIENT_SECRET = "github-secret"


def run(client, emails, gh_user=None, token_data=None):
    token, state, _ = start_oauth(client, "github")
    gh_user = gh_user or {"id": 333, "email": "public@example.com", "name": "GH", "login": "gh"}
    with patch("users.views.requests.post") as mock_post, \
            patch("users.views.requests.get") as mock_get:
        mock_post.return_value = json_response(token_data or {"access_token": "gho_x"})
        mock_get.side_effect = [json_response(gh_user), json_response(emails)]
        res = callback(client, "github", token, code="xyz", state=state)
    return res, mock_post


@pytest.mark.django_db
def test_github_creates_user_from_verified_primary_email(csrf_client):
    res, mock_post = run(csrf_client, [
        {"email": "other@example.com", "primary": False, "verified": True},
        {"email": "primary@example.com", "primary": True, "verified": True},
    ])
    assert res.status_code == 200
    assert res.data["message"] == "User created successfully"
    user = User.objects.get(email="primary@example.com")
    assert AuthProvider.objects.get(user=user).provider_id == "333"
    assert res.cookies[settings.AUTH_REFRESH_COOKIE]["httponly"] is True

    sent = mock_post.call_args.kwargs["data"]
    assert sent["redirect_uri"] == REDIRECT_URIS["github"]
    assert sent["code_verifier"]


@pytest.mark.django_db
def test_github_unverified_email_cannot_take_over_account(csrf_client):
    """Regression: an attacker adds the victim's address (unverified) to GitHub."""
    victim = User.objects.create_user(email="victim@example.com")
    res, _ = run(
        csrf_client,
        [{"email": "victim@example.com", "primary": True, "verified": False}],
        gh_user={"id": 666, "email": "victim@example.com", "login": "attacker"},
    )
    assert res.status_code == 400
    assert settings.AUTH_ACCESS_COOKIE not in res.cookies or res.cookies[settings.AUTH_ACCESS_COOKIE].value == ""
    assert not AuthProvider.objects.filter(user=victim).exists()


@pytest.mark.django_db
def test_github_public_profile_email_is_not_trusted(csrf_client):
    """Profile email says victim, but only a different verified email exists."""
    victim = User.objects.create_user(email="victim@example.com")
    res, _ = run(
        csrf_client,
        [{"email": "attacker@example.com", "primary": True, "verified": True}],
        gh_user={"id": 667, "email": "victim@example.com", "login": "attacker"},
    )
    assert res.status_code == 200
    assert res.data["user"]["email"] == "attacker@example.com"
    assert not AuthProvider.objects.filter(user=victim).exists()


@pytest.mark.django_db
def test_github_existing_link_wins(csrf_client):
    user = User.objects.create_user(email="old@example.com")
    AuthProvider.objects.create(user=user, provider="github", provider_id="333")
    res, _ = run(csrf_client, [{"email": "changed@example.com", "primary": True, "verified": True}])
    assert res.status_code == 200
    assert res.data["user"]["id"] == str(user.id)
    assert res.data["message"] == "User login successfully"


@pytest.mark.django_db
def test_github_no_access_token(csrf_client):
    token, state, _ = start_oauth(csrf_client, "github")
    with patch("users.views.requests.post", return_value=json_response({"error": "bad_verification_code"})):
        res = callback(csrf_client, "github", token, state=state)
    assert res.status_code == 400
