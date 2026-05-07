import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock
from users.models import User, AuthProvider
from users.serializers import UserSerializer
from .conftest import api_client, user
from requests.exceptions import RequestException


VALID_REDIRECT_URI = "http://localhost:5173/auth/google/callback"


@pytest.fixture
def url():
    return reverse("google-auth")


def post(api_client, url, data):
    """Helper: always include a valid redirect_uri unless explicitly overridden."""
    payload = {"redirect_uri": VALID_REDIRECT_URI, **data}
    return api_client.post(url, data=payload)


@pytest.mark.django_db
def test_missing_code_returns_400(api_client, url):
    response = post(api_client, url, {})
    assert response.status_code == 400
    assert response.data["error"] == "Missing OAuth code"


@pytest.mark.django_db
def test_missing_redirect_uri_returns_400(api_client, url):
    response = api_client.post(url, data={"code": "abc"})
    assert response.status_code == 400
    assert response.data["error"] == "Missing redirect_uri"


@pytest.mark.django_db
def test_invalid_redirect_uri_returns_400(api_client, url):
    response = api_client.post(url, data={"code": "abc", "redirect_uri": "https://evil.com/steal"})
    assert response.status_code == 400
    assert response.data["error"] == "Invalid redirect_uri"


def mock_google_token_response(id_token="mock-id-token"):
    mock = MagicMock()
    mock.json.return_value = {"id_token": id_token}
    mock.raise_for_status.return_value = None
    return mock


@pytest.mark.django_db
@patch("users.views.requests.post")
def test_google_no_id_token_returns_400(mock_post, api_client, url):
    mock_post.return_value = mock_google_token_response(id_token=None)
    response = post(api_client, url, {"code": "abc"})
    assert response.status_code == 400
    assert response.data["error"] == "Unable to authenticate with Google"


@pytest.mark.django_db
@patch("users.views.verify_oauth2_token")
@patch("users.views.requests.post")
@patch("users.views.RefreshToken")
def test_google_auth_existing_user(mock_refresh, mock_post, mock_verify, api_client, url):
    mock_post.return_value = mock_google_token_response()
    mock_verify.return_value = {
        "email": "test@example.com",
        "name": "John Doe",
        "picture": "http://img.com/a.jpg",
        "sub": "google123",
        "email_verified": True,
    }

    user = User.objects.create_user(email="test@example.com", password="pass123", name="Existing User")

    mock_refresh_obj = MagicMock()
    mock_refresh_obj.__str__.return_value = "refresh-token"
    mock_refresh_obj.access_token.__str__.return_value = "access-token"
    mock_refresh.for_user.return_value = mock_refresh_obj

    response = post(api_client, url, {"code": "valid"})

    assert response.status_code == 200
    assert response.data["message"] == "User login successfully"
    assert response.data["user"] == UserSerializer(user).data
    assert response.cookies["refresh"].value == "refresh-token"
    assert response.cookies["access"].value == "access-token"
    # ua and ip cookies should NOT be present anymore
    assert "ua" not in response.cookies
    assert "ip" not in response.cookies


@pytest.mark.django_db
@patch("users.views.verify_oauth2_token")
@patch("users.views.requests.post")
@patch("users.views.RefreshToken")
def test_google_auth_creates_user(mock_refresh, mock_post, mock_verify, api_client, url):
    mock_post.return_value = mock_google_token_response()
    mock_verify.return_value = {
        "email": "newuser@example.com",
        "name": "New User",
        "picture": "http://new.com/pic.jpg",
        "sub": "google999",
        "email_verified": True,
    }

    mock_refresh_obj = MagicMock()
    mock_refresh_obj.__str__.return_value = "refresh-token"
    mock_refresh_obj.access_token.__str__.return_value = "access-token"
    mock_refresh.for_user.return_value = mock_refresh_obj

    response = post(api_client, url, {"code": "valid"})

    assert response.status_code == 200
    assert response.data["message"] == "User created successfully"

    user = User.objects.get(email="newuser@example.com")
    assert user.name == "New User"
    assert user.avatar_url == "http://new.com/pic.jpg"

    provider = AuthProvider.objects.get(user=user)
    assert provider.provider == "google"
    assert provider.provider_id == "google999"


@pytest.mark.django_db
@patch("users.views.verify_oauth2_token")
@patch("users.views.requests.post")
def test_google_unverified_email_returns_400(mock_post, mock_verify, api_client, url):
    mock_post.return_value = mock_google_token_response()
    mock_verify.return_value = {
        "email": "unverified@example.com",
        "sub": "googleXYZ",
        "email_verified": False,
    }
    response = post(api_client, url, {"code": "valid"})
    assert response.status_code == 400
    assert response.data["error"] == "Google email not verified"


@pytest.mark.django_db
@patch("users.views.requests.post", side_effect=RequestException("network fail"))
def test_google_network_error(mock_post, api_client, url):
    response = post(api_client, url, {"code": "abcd"})
    assert response.status_code == 503
    assert "Google authentication service unreachable" in response.data["error"]


@pytest.mark.django_db
@patch("users.views.verify_oauth2_token", side_effect=ValueError("invalid token"))
@patch("users.views.requests.post")
def test_google_invalid_token(mock_post, mock_verify, api_client, url):
    mock_post.return_value = mock_google_token_response()
    response = post(api_client, url, {"code": "valid"})
    assert response.status_code == 400
    assert response.data["error"] == "Invalid Google token provided"


@pytest.mark.django_db
@patch("users.views.requests.post")
@patch("users.views.verify_oauth2_token", side_effect=Exception("random error"))
def test_google_auth_unexpected_error(mock_verify, mock_post, api_client, url):
    mock_post.return_value = mock_google_token_response()
    response = post(api_client, url, {"code": "valid"})
    assert response.status_code == 500
    assert response.data["error"] == "Authentication failed"
