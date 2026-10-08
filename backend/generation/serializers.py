from rest_framework import serializers
from .models import Generations
from .llm_models import DEFAULT_UI_MODEL, is_valid_model_id
from projects.serializers import ProjectSerializer


class GenerationSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Generations
        fields = [
            "id",
            "project",
            "prompt",
            "schema",
            "code_bundle_url",
            "llm_provider",
            "token_usage",
            "status",
            "created_at",
        ]


class GenerateRequestSerializer(serializers.Serializer):
    """
    Request serializer for UI generation

    Fields:
        prompt: User's UI generation prompt (required)
        ui_model: Composite "provider:model" id (optional), e.g.
            "groq:openai/gpt-oss-20b" or "gemini:models/gemini-3.8-flash".
            Valid ids come from GET /generation/models/ — see llm_models.py.
            Default: settings.DEFAULT_UI_MODEL
    """
    prompt = serializers.CharField(
        required=True,
        max_length=2000,
        help_text="Description of the UI to generate"
    )
    ui_model = serializers.CharField(
        required=False,
        default=DEFAULT_UI_MODEL,
        help_text="Composite 'provider:model' id — see GET /generation/models/ for valid values."
    )
    project_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional project ID to attach generation to"
    )

    def validate_prompt(self, value):
        """Ensure prompt is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Prompt cannot be empty")
        return value.strip()

    def validate_ui_model(self, value):
        if not is_valid_model_id(value):
            raise serializers.ValidationError(f"'{value}' is not a valid choice.")
        return value