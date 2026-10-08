import pytest
from django.urls import reverse

from generation.llm_models import DEFAULT_UI_MODEL


@pytest.mark.django_db
def test_available_models_requires_auth(api_client):
    url = reverse("available-models")
    res = api_client.get(url)
    assert res.status_code == 401


@pytest.mark.django_db
def test_available_models_lists_both_providers(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse("available-models")

    res = api_client.get(url)

    assert res.status_code == 200
    assert res.data["default"] == DEFAULT_UI_MODEL

    providers = {m["provider"] for m in res.data["models"]}
    assert providers == {"groq", "gemini"}

    ids = {m["id"] for m in res.data["models"]}
    assert DEFAULT_UI_MODEL in ids
