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
    project_id = serializers.UUIDField(required=False, allow_null=True)
    prompt = serializers.CharField()
    llm_provider = serializers.ChoiceField(choices=["groq", "gemini", "openai"])
