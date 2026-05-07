import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from users.models import User, AuthProvider
from users.serializers import UserSerializer
from .conftest import api_client, user


VALID_REDIRECT_URI = "http://localhost:5173/auth/github/callback"


@pytest.fixture
def url():
    return reverse("github-auth")


def post(api_client, url, data):
    """Helper: always include a valid redirect_uri unless explicitly overridden."""
    payload = {"redirect_uri": VALID_REDIRECT_URI, **data}
    return api_client.post(url, data=payload)


@pytest.mark.django_db
def test_github_missing_code(api_client, url):
    res = post(api_client, url, {})
    assert res.status_code == 400
    assert res.data["error"] == "Missing OAuth code"


@pytest.mark.django_db
def test_github_missing_redirect_uri(api_client, url):
    res = api_client.post(url, data={"code": "abc"})
    assert res.status_code == 400
    assert res.data["error"] == "Missing redirect_uri"


@pytest.mark.django_db
def test_github_invalid_redirect_uri(api_client, url):
    res = api_client.post(url, data={"code": "abc", "redirect_uri": "https://evil.com/steal"})
    assert res.status_code == 400
    assert res.data["error"] == "Invalid redirect_uri"


def mock_token_response(access_token="access123"):
    mock = MagicMock()
    mock.json.return_value = {"access_token": access_token}
    mock.raise_for_status.return_value = None
    return mock


def mock_user_response(email="test@example.com", github_id=111, login="ghuser"):
    mock = MagicMock()
    mock.json.return_value = {
        "id": github_id,
        "email": email,
        "name": "GitHub User",
        "login": login,
        "avatar_url": "http://avatar.com/a.png",
    }
    mock.raise_for_status.return_value = None
    return mock


@pytest.mark.django_db
@patch("users.views.requests.post")
def test_github_no_access_token(mock_post, api_client, url):
    mock_post.return_value = mock_token_response(access_token=None)
    res = post(api_client, url, {"code": "123"})
    assert res.status_code == 400
    assert res.data["error"] == "Unable to authenticate with GitHub"


@pytest.mark.django_db
@patch("users.views.requests.get")
@patch("users.views.requests.post")
@patch("users.views.RefreshToken")
def test_github_existing_user(mock_refresh, mock_post, mock_get, api_client, url):
    mock_post.return_value = mock_token_response()
    mock_get.return_value = mock_user_response(email="test@example.com", github_id=222)

    user = User.objects.create_user(email="test@example.com", password="pass123")

    mock_refresh_obj = MagicMock()
    mock_refresh_obj.__str__.return_value = "refresh-token"
    mock_refresh_obj.access_token.__str__.return_value = "access-token"
    mock_refresh.for_user.return_value = mock_refresh_obj

    res = post(api_client, url, {"code": "123"})

    assert res.status_code == 200
    assert res.data["message"] == "User login successfully"
    assert res.data["user"] == UserSerializer(user).data
    assert res.cookies["refresh"].value == "refresh-token"
    assert res.cookies["access"].value == "access-token"
    # ua and ip cookies should NOT be present anymore
    assert "ua" not in res.cookies
    assert "ip" not in res.cookies


@pytest.mark.django_db
@patch("users.views.requests.get")
@patch("users.views.requests.post")
@patch("users.views.RefreshToken")
def test_github_creates_user(mock_refresh, mock_post, mock_get, api_client, url):
    mock_post.return_value = mock_token_response()
    mock_get.return_value = mock_user_response(email="new@example.com", github_id=333)

    mock_refresh_obj = MagicMock()
    mock_refresh_obj.__str__.return_value = "refresh-token"
    mock_refresh_obj.access_token.__str__.return_value = "access-token"
    mock_refresh.for_user.return_value = mock_refresh_obj

    res = post(api_client, url, {"code": "xyz"})

    assert res.status_code == 200
    assert res.data["message"] == "User created successfully"

    user = User.objects.get(email="new@example.com")
    provider = AuthProvider.objects.get(user=user)
    assert provider.provider == "github"
    assert provider.provider_id == "333"


@pytest.mark.django_db
@patch("users.views.requests.get")
@patch("users.views.requests.post")
@patch("users.views.RefreshToken")
def test_github_email_fallback(mock_refresh, mock_post, mock_get, api_client, url):
    mock_user = MagicMock()
    mock_user.json.return_value = {"id": 500, "email": None, "login": "abc"}
    mock_user.raise_for_status.return_value = None

    mock_email = MagicMock()
    mock_email.json.return_value = [{"email": "primary@example.com", "primary": True}]
    mock_email.raise_for_status.return_value = None

    mock_get.side_effect = [mock_user, mock_email]
    mock_post.return_value = mock_token_response()

    mock_refresh_obj = MagicMock()
    mock_refresh_obj.__str__.return_value = "refresh-token"
    mock_refresh_obj.access_token.__str__.return_value = "access-token"
    mock_refresh.for_user.return_value = mock_refresh_obj

    res = post(api_client, url, {"code": "xyz"})

    assert res.status_code == 200
    user = User.objects.get(email="primary@example.com")
    assert user is not None


@pytest.mark.django_db
@patch("users.views.requests.post", side_effect=Exception("fail"))
def test_github_unexpected_error(mock_post, api_client, url):
    res = post(api_client, url, {"code": "123"})
    assert res.status_code == 500
    assert res.data["error"] == "GitHub authentication failed"
