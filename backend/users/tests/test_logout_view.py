import pytest
from django.urls import reverse
from .conftest import api_client


@pytest.fixture
def url():
    return reverse("logout")

@pytest.mark.django_db
def test_logout(api_client, url, user):
    api_client.force_authenticate(user=user)

    api_client.cookies["refresh"] = "123"
    api_client.cookies["access"] = "456"

    res = api_client.post(url)

    assert res.status_code == 200
    assert res.data["message"] == "Logout successful"

    refresh = res.cookies.get("refresh")
    access = res.cookies.get("access")

    assert refresh.value == ""   
    assert access.value == ""

    assert refresh["max-age"] == 0