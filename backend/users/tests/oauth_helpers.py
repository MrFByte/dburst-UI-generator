from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse

from django.urls import reverse

from .conftest import fetch_csrf

REDIRECT_URIS = {
    "google": "http://localhost:5173/auth/google/callback",
    "github": "http://localhost:5173/auth/github/callback",
}


def start_oauth(client, provider):
    """Runs oauth/start/ and returns (csrf_token, state, authorization params)."""
    token = fetch_csrf(client)
    res = client.post(
        reverse("oauth-start"),
        {"provider": provider, "redirect_uri": REDIRECT_URIS[provider]},
        format="json", HTTP_X_CSRFTOKEN=token,
    )
    assert res.status_code == 200, res.data
    params = {k: v[0] for k, v in parse_qs(urlparse(res.data["authorization_url"]).query).items()}
    return token, params["state"], params


def callback(client, provider, token, code="code", state=None):
    payload = {"code": code}
    if state is not None:
        payload["state"] = state
    return client.post(
        reverse(f"{provider}-auth"), payload, format="json", HTTP_X_CSRFTOKEN=token
    )


def json_response(data, status_code=200):
    mock = MagicMock()
    mock.json.return_value = data
    mock.status_code = status_code
    mock.ok = status_code < 400
    mock.raise_for_status.return_value = None
    return mock
