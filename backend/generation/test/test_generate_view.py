import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from projects.models import Project
from generation.models import Generations


@pytest.fixture
def url():
    return "/api/v1/generation/generate/"


@pytest.mark.django_db
@patch("generation.views.GenerationCache.store_generation")
@patch("generation.views.ReactCodeGenerator")
@patch("generation.views.SchemaValidator.validate")
@patch("generation.views.LLMClient")
def test_generate_success(
    mock_llm,
    mock_validator,
    mock_codegen,
    mock_cache,
    api_client,
    user,
    url
):
    api_client.force_authenticate(user=user)

    mock_llm_instance = MagicMock()
    mock_llm_instance.generate_ui.return_value = {
        "project_name": "My UI",
        "project_description": "Test Project Description",
        "design_plan": {"concept": "Test concept", "theme": {}},
        "title": "My UI",
        "schema": {"type": "Root"},
        "metadata": {"framework": "react"},
        "usage": {
            "planning_tokens": {"total_tokens": 50},
            "generation_tokens": {"total_tokens": 73}
        },
        "models": {
            "planning": "plan_moonshot",
            "ui_generation": "groq"
        }
    }
    mock_llm.return_value = mock_llm_instance

    mock_validator.return_value = {"type": "Root"}

    mock_codegen_instance = MagicMock()
    mock_codegen_instance.generate.return_value = "<UI />"
    mock_codegen.return_value = mock_codegen_instance

    response = api_client.post(url, {
        "prompt": "Make a UI",
        "llm_provider": "groq"
    })

    assert response.status_code == 201
    assert response.data["project_title"] == "My UI"
    assert response.data["schema"] == {"type": "Root"}
    assert response.data["code"] == "<UI />"
    assert response.data["meta"]["usage"]["total_tokens"] == 123

    gen = Generations.objects.first()
    assert gen is not None
    assert gen.status == "success"

    mock_cache.assert_called_once()


@pytest.mark.django_db
@patch("generation.views.SchemaValidator.validate", side_effect=ValueError("bad schema"))
@patch("generation.views.LLMClient")
def test_generate_schema_validation_error(mock_llm, mock_validator, api_client, user, url):

    api_client.force_authenticate(user=user)

    mock_llm_instance = MagicMock()
    mock_llm_instance.generate_ui.return_value = {
        "project_name": "Bad UI",
        "project_description": "Bad Description",
        "design_plan": {},
        "title": "Bad UI",
        "schema": {"type": "Evil"},
        "metadata": {},
        "usage": {
            "planning_tokens": {},
            "generation_tokens": {}
        },
        "models": {
            "planning": "plan_moonshot",
            "ui_generation": "groq"
        }
    }
    mock_llm.return_value = mock_llm_instance

    res = api_client.post(url, {"prompt": "bad", "llm_provider": "groq"})

    assert res.status_code == 400
    assert "Schema validation failed" in res.data["error"]


@pytest.mark.django_db
@patch("generation.views.LLMClient.generate_ui", side_effect=Exception("LLM down"))
def test_generate_llm_failure(mock_generate_ui, api_client, user, url):
    api_client.force_authenticate(user=user)

    res = api_client.post(url, {"prompt": "hello", "llm_provider": "groq"})

    assert res.status_code == 500
    assert "LLM down" in res.data["error"]


@pytest.mark.django_db
def test_generate_invalid_project(api_client, user, url):
    api_client.force_authenticate(user=user)

    res = api_client.post(url, {
        "prompt": "hi",
        "llm_provider": "groq",
        "project_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    })

    assert res.status_code == 404
    assert res.data["error"] == "Project not found."