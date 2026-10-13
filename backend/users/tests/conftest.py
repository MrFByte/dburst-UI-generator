import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def csrf_client():
    """A client that enforces CSRF like a real browser request would."""
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        name="Test User",
        password="testpass123"
    )


def fetch_csrf(client):
    """GETs the CSRF endpoint and returns the token to send as X-CSRFToken."""
    res = client.get(reverse("csrf-token"))
    assert res.status_code == 200
    return res.cookies["csrftoken"].value


def login_with_cookies(client, user):
    """Puts a real JWT pair in `client`'s cookie jar. Returns the RefreshToken."""
    refresh = RefreshToken.for_user(user)
    client.cookies[settings.AUTH_ACCESS_COOKIE] = str(refresh.access_token)
    client.cookies[settings.AUTH_REFRESH_COOKIE] = str(refresh)
    return refresh
