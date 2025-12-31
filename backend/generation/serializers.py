from rest_framework import serializers
from .models import Generations
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
        ui_model: UI generation model selection (optional)
            Options: ui_llama_3_3, ui_llama_3_1, ui_gemini_2_0, ui_gemini_2_5, ui_gpt_oss_120b
            Default: ui_llama_3_3
    """
    prompt = serializers.CharField(
        required=True,
        max_length=2000,
        help_text="Description of the UI to generate"
    )
    ui_model = serializers.ChoiceField(
        required=False,
        choices=[
            "ui_llama_3_3",
            "ui_llama_3_1", 
            "ui_gemini_2_0",
            "ui_gemini_2_5",
            "ui_gpt_oss_120b"
        ],
        default="ui_llama_3_3",
        help_text="Model for UI generation (planning always uses plan_moonshot)"
    )
    
    def validate_prompt(self, value):
        """Ensure prompt is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Prompt cannot be empty")
        return value.strip()