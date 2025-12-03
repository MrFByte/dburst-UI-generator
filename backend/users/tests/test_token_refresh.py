import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse
from .conftest import api_client


@pytest.fixture
def url():
    return reverse("token-refresh")


def test_refresh_no_cookie(api_client, url):
    res = api_client.post(url)
    assert res.status_code == 401
    assert res.data["error"] == "Refresh token not found"

@patch("users.views.RefreshToken", side_effect=Exception("bad token"))
def test_refresh_invalid_token(mock_rt, api_client, url):
    api_client.cookies["refresh"] = "invalid"

    res = api_client.post(url)

    assert res.status_code == 401
    assert res.data["error"] == "Invalid refresh token"

@patch("users.views.RefreshToken")
def test_refresh_success(mock_rt, api_client, url):
    api_client.cookies["refresh"] = "good-refresh"

    mock_obj = MagicMock()
    mock_obj.access_token.__str__.return_value = "new-access"
    mock_rt.return_value = mock_obj

    res = api_client.post(url)

    assert res.status_code == 200
    assert res.data["access"] == "new-access"
    assert res.cookies["access"].value == "new-access"
    