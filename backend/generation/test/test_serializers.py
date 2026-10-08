import pytest
import uuid
from generation.serializers import (
    GenerationSerializer,
    GenerateRequestSerializer
)
from generation.models import Generations
from projects.models import Project


@pytest.mark.django_db
def test_generation_serializer_output(user):
    """Ensure GenerationSerializer returns all expected fields."""

    project = Project.objects.create(
        user=user,
        title="Test Project",
        description="Desc"
    )

    generation = Generations.objects.create(
        project=project,
        prompt="Generate UI",
        schema={"type": "Root"},
        code_bundle_url="https://cdn.example.com/bundle.js",
        llm_provider="groq",
        token_usage=123,
        status=Generations.Status.SUCCESS,
    )

    serializer = GenerationSerializer(generation)
    data = serializer.data

    assert data["id"] == str(generation.id)
    assert data["prompt"] == "Generate UI"
    assert data["schema"] == {"type": "Root"}
    assert data["code_bundle_url"] == "https://cdn.example.com/bundle.js"
    assert data["llm_provider"] == "groq"
    assert data["token_usage"] == 123
    assert data["status"] == Generations.Status.SUCCESS

    # Project is nested
    assert data["project"]["title"] == "Test Project"
    assert data["project"]["description"] == "Desc"
    assert "created_at" in data


def test_generate_request_serializer_valid():
    """Valid payload should pass validation."""

    payload = {
        "project_id": str(uuid.uuid4()),
        "prompt": "Create dashboard UI",
        "ui_model": "groq:openai/gpt-oss-20b",
    }

    serializer = GenerateRequestSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors

    assert serializer.validated_data["prompt"] == "Create dashboard UI"
    assert serializer.validated_data["ui_model"] == "groq:openai/gpt-oss-20b"


def test_generate_request_serializer_no_project_id():
    """project_id is optional and nullable."""

    payload = {
        "prompt": "Create component",
        "ui_model": "gemini:models/gemini-3.8-flash",
        "project_id": None,
    }

    serializer = GenerateRequestSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["project_id"] is None


def test_generate_request_serializer_missing_prompt():
    """prompt is required and cannot be missing."""

    payload = {"ui_model": "groq:openai/gpt-oss-20b"}

    serializer = GenerateRequestSerializer(data=payload)

    assert not serializer.is_valid()
    assert "prompt" in serializer.errors
    assert serializer.errors["prompt"][0].code == "required"


def test_generate_request_serializer_invalid_model():
    """Model must be a valid, currently-configured model id."""

    payload = {
        "prompt": "generate UI",
        "ui_model": "invalid_model"
    }

    serializer = GenerateRequestSerializer(data=payload)

    assert not serializer.is_valid()
    assert "ui_model" in serializer.errors
    assert "is not a valid choice" in serializer.errors["ui_model"][0]


def test_generate_request_serializer_invalid_uuid():
    """project_id must be a valid UUID when provided."""

    payload = {
        "project_id": "not-a-uuid",
        "prompt": "Test UI",
        "ui_model": "groq:openai/gpt-oss-20b",
    }

    serializer = GenerateRequestSerializer(data=payload)

    assert not serializer.is_valid()
    assert "project_id" in serializer.errors


def test_generate_request_serializer_defaults_ui_model():
    """ui_model is optional and falls back to settings.DEFAULT_UI_MODEL."""
    from generation.llm_models import DEFAULT_UI_MODEL

    payload = {"prompt": "Create dashboard UI"}

    serializer = GenerateRequestSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["ui_model"] == DEFAULT_UI_MODEL
