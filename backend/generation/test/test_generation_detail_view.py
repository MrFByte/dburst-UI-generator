import pytest
from rest_framework.test import APIClient
from users.models import User
from projects.models import Project
from generation.models import Generations


@pytest.fixture
def url():
    return "/api/v1/generation/details/"


@pytest.mark.django_db
def test_generation_detail_success(api_client, url, user):
    api_client.force_authenticate(user=user)

    project = Project.objects.create(user=user, title="Proj", description="")
    gen = Generations.objects.create(
        project=project,
        prompt="hi",
        schema={"type": "Root"},
        llm_provider="groq",
        token_usage=10,
        status="success"
    )

    response = api_client.get(f"{url}{gen.id}/")

    assert response.status_code == 200
    assert response.data["id"] == str(gen.id)
    assert response.data["project"]["id"] == str(project.id)
    assert response.data["schema"] == {"type": "Root"}


@pytest.mark.django_db
def test_generation_detail_not_owner(api_client, url):
    owner = User.objects.create_user(email="owner@example.com", password="x")
    thief = User.objects.create_user(email="thief@example.com", password="y")

    project = Project.objects.create(user=owner, title="Secret", description="")
    gen = Generations.objects.create(
        project=project,
        prompt="secret",
        schema={"type": "Root"},
        llm_provider="groq",
    )

    api_client.force_authenticate(user=thief)

    res = api_client.get(f"{url}{gen.id}/")
    assert res.status_code == 404
    assert res.data["error"] == "Not found"
