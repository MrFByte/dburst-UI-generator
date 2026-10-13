from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse

from .conftest import fetch_csrf
from .oauth_helpers import REDIRECT_URIS, callback, json_response, start_oauth


@pytest.fixture(autouse=True)
def client_ids(settings):
    settings.GOOGLE_CLIENT_ID = "google-client"
    settings.GITHUB_CLIENT_ID = "github-client"


@pytest.mark.django_db
@pytest.mark.parametrize("provider", ["google", "github"])
def test_start_returns_url_with_state_and_pkce(csrf_client, provider):
    token = fetch_csrf(csrf_client)
    res = csrf_client.post(
        reverse("oauth-start"),
        {"provider": provider, "redirect_uri": REDIRECT_URIS[provider]},
        format="json", HTTP_X_CSRFTOKEN=token,
    )
    assert res.status_code == 200
    url = res.data["authorization_url"]
    assert "state=" in url and "code_challenge=" in url and "code_challenge_method=S256" in url

    cookie = res.cookies[settings.AUTH_OAUTH_COOKIE]
    assert cookie["httponly"] is True
    assert cookie["secure"] is True
    assert cookie["path"] == settings.AUTH_REFRESH_COOKIE_PATH
    assert int(cookie["max-age"]) == settings.OAUTH_STATE_MAX_AGE
    # The PKCE verifier stays server-side (inside the signed cookie only).
    assert "code_verifier" not in url


@pytest.mark.django_db
def test_start_rejects_unknown_provider(csrf_client):
    token = fetch_csrf(csrf_client)
    res = csrf_client.post(
        reverse("oauth-start"), {"provider": "evil", "redirect_uri": "x"},
        format="json", HTTP_X_CSRFTOKEN=token,
    )
    assert res.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize("redirect_uri", [
    "https://evil.com/auth/google/callback",
    "http://localhost:5173/auth/google/callback/../../steal",
    "http://localhost:5173/auth/github/callback",  # other provider's URI
])
def test_start_rejects_non_whitelisted_redirect(csrf_client, redirect_uri):
    token = fetch_csrf(csrf_client)
    res = csrf_client.post(
        reverse("oauth-start"), {"provider": "google", "redirect_uri": redirect_uri},
        format="json", HTTP_X_CSRFTOKEN=token,
    )
    assert res.status_code == 400
    assert settings.AUTH_OAUTH_COOKIE not in res.cookies


@pytest.mark.django_db
def test_callback_without_state_fails(csrf_client):
    token, _, _ = start_oauth(csrf_client, "google")
    assert callback(csrf_client, "google", token).status_code == 400


@pytest.mark.django_db
def test_callback_with_wrong_state_fails(csrf_client):
    token, _, _ = start_oauth(csrf_client, "google")
    assert callback(csrf_client, "google", token, state="forged").status_code == 400


@pytest.mark.django_db
def test_callback_from_another_browser_fails(csrf_client, api_client):
    """State is bound to the browser that started the flow (its cookie)."""
    _, state, _ = start_oauth(csrf_client, "google")
    token = fetch_csrf(api_client)
    assert callback(api_client, "google", token, state=state).status_code == 400


@pytest.mark.django_db
def test_state_for_one_provider_rejected_by_other(csrf_client):
    token, state, _ = start_oauth(csrf_client, "google")
    assert callback(csrf_client, "github", token, state=state).status_code == 400


@pytest.mark.django_db
@patch("users.views.requests.post", return_value=json_response({"error": "invalid_grant"}, 400))
def test_state_is_single_use(mock_post, csrf_client):
    token, state, _ = start_oauth(csrf_client, "google")
    cookie = csrf_client.cookies[settings.AUTH_OAUTH_COOKIE].value

    first = callback(csrf_client, "google", token, state=state)
    assert first.status_code == 400  # provider rejected the code, state still consumed
    assert mock_post.called
    assert first.cookies[settings.AUTH_OAUTH_COOKIE].value == ""

    csrf_client.cookies[settings.AUTH_OAUTH_COOKIE] = cookie  # replay the cookie
    assert callback(csrf_client, "google", token, state=state).status_code == 400
