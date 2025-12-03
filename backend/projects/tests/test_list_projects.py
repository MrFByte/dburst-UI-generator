import pytest
from django.urls import reverse
from projects.models import Project
from projects.serializers import ProjectSerializer


@pytest.fixture
def list_url():
    return reverse("recent-projects") 


@pytest.mark.django_db
def test_recent_projects_requires_auth(api_client, list_url):
    """Unauthenticated users should get 401."""
    response = api_client.get(list_url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_recent_projects_returns_only_user_projects(api_client, user, list_url):
    """Ensure only the user's recent projects are returned."""

    p1 = Project.objects.create(user=user, title="P1")
    p2 = Project.objects.create(user=user, title="P2")
    p3 = Project.objects.create(user=user, title="P3")
    p4 = Project.objects.create(user=user, title="P4")

    other_user = user.__class__.objects.create_user(
        email="other@example.com", password="pass123"
    )
    Project.objects.create(user=other_user, title="Other")

    api_client.force_authenticate(user=user)
    response = api_client.get(list_url)

    assert response.status_code == 200
    assert len(response.data) == 3

    expected = list(
        Project.objects.filter(user=user).order_by("-updated_at")[:3]
        .values_list("title", flat=True)
    )
    returned = [proj["title"] for proj in response.data]

    assert returned == expected