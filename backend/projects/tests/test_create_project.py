import pytest
from django.urls import reverse
from projects.models import Project
from projects.serializers import ProjectSerializer


@pytest.fixture
def create_url():
    return reverse("create-project") 


@pytest.mark.django_db
def test_create_project_requires_auth(api_client, create_url):
    response = api_client.post(create_url, data={})
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_project_success(api_client, user, create_url):
    """Authenticated users should be able to create a project."""
    api_client.force_authenticate(user=user)

    payload = {
        "title": "New Project",
        "description": "A sample project",
        "is_public": True
    }

    response = api_client.post(create_url, data=payload)

    assert response.status_code == 201

    project = Project.objects.get(title="New Project")

    assert project.user == user
    assert project.description == "A sample project"
    assert project.is_public is True

    serialized = ProjectSerializer(project).data
    
    for key in ["id", "title", "description", "is_public"]:
        assert response.data[key] == serialized[key]
    

@pytest.mark.django_db
def test_project_auto_timestamps(api_client, user, create_url):
    api_client.force_authenticate(user=user)

    response = api_client.post(create_url, data={"title": "TS Test"})

    assert response.status_code == 201
    assert response.data["created_at"] is not None
    assert response.data["updated_at"] is not None