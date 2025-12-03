
import pytest
from django.urls import reverse
from .conftest import api_client,user
from users.serializers import UserSerializer


@pytest.fixture
def profile_url():
    return reverse("user-profile") 


def test_get_profile_authenticated(api_client, user, profile_url):
    """Ensure authenticated users can access profile"""
    api_client.force_authenticate(user=user)

    response = api_client.get(profile_url)

    assert response.status_code == 200
    assert response.data["user"] == UserSerializer(user).data


def test_get_profile_unauthenticated(api_client, profile_url):
    """Ensure unauthenticated users get 401"""
    response = api_client.get(profile_url)

    assert response.status_code == 401