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
        "llm_provider": "groq",
    }

    serializer = GenerateRequestSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors

    assert serializer.validated_data["prompt"] == "Create dashboard UI"
    assert serializer.validated_data["llm_provider"] == "groq"


def test_generate_request_serializer_no_project_id():
    """project_id is optional and nullable."""

    payload = {
        "prompt": "Create component",
        "llm_provider": "gemini",
        "project_id": None,
    }

    serializer = GenerateRequestSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["project_id"] is None


def test_generate_request_serializer_missing_prompt():
    """prompt is required and cannot be missing."""

    payload = {"llm_provider": "groq"}

    serializer = GenerateRequestSerializer(data=payload)

    assert not serializer.is_valid()
    assert "prompt" in serializer.errors
    assert serializer.errors["prompt"][0].code == "required"


def test_generate_request_serializer_invalid_provider():
    """Provider must be one of groq/gemini/openai."""

    payload = {
        "prompt": "generate UI",
        "llm_provider": "anthropic"
    }

    serializer = GenerateRequestSerializer(data=payload)

    assert not serializer.is_valid()
    assert "llm_provider" in serializer.errors
    assert "is not a valid choice" in serializer.errors["llm_provider"][0]


def test_generate_request_serializer_invalid_uuid():
    """project_id must be a valid UUID when provided."""

    payload = {
        "project_id": "not-a-uuid",
        "prompt": "Test UI",
        "llm_provider": "openai",
    }

    serializer = GenerateRequestSerializer(data=payload)

    assert not serializer.is_valid()
    assert "project_id" in serializer.errors
