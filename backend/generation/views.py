import logging
import requests
import json
from django.db import transaction
from django.conf import settings
from google.oauth2.id_token import verify_oauth2_token
from google.auth.transport import requests as google_requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from rest_framework_simplejwt.tokens import RefreshToken

from .llm import LLMClient
from .codegen import ReactCodeGenerator
from .schema_validator import SchemaValidator
from .models import Generations
from .cache import GenerationCache
from django_redis import get_redis_connection
from projects.models import Project
from .serializers import (
    GenerationSerializer,
    GenerateRequestSerializer,
)

logger = logging.getLogger(__name__)

# Create your views here.


class GenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prompt = serializer.validated_data["prompt"]
        provider = serializer.validated_data.get("llm_provider", "groq")
        project_id = serializer.validated_data.get("project_id")

        # Resolve or create project
        if not project_id:
            count = Project.objects.filter(user=request.user).count() + 1
            project = Project.objects.create(
                user=request.user,
                title=f"Untitled Project {count}",
                description="",
            )
        else:
            try:
                project = Project.objects.get(id=project_id, user=request.user)
            except Project.DoesNotExist:
                return Response({"error": "Project not found."}, status=404)

        try:
            # Call LLM with appropriate provider
            llm_client = LLMClient(provider=provider)
            llm_result = llm_client.call(prompt)
            
            schema = llm_result["schema"]
            
            # Validate schema
            try:
                schema = SchemaValidator.validate(schema)
            except ValueError as e:
                return Response({"error": f"Schema validation failed: {str(e)}"}, status=400)
            
            title = llm_result.get("title", "Generated UI")
            meta = llm_result.get("usage", {})

            # Update project title if needed
            if project.title.startswith("Untitled Project"):
                project.title = title
                project.save()

            # Generate code
            code_generator = ReactCodeGenerator(schema, component_name="GeneratedUI")
            react_code = code_generator.generate()

            # Save to database
            generation = Generations.objects.create(
                project=project,
                prompt=prompt,
                schema=schema,
                llm_provider=provider,
                token_usage=meta.get("total_tokens", 0),
                status=Generations.Status.SUCCESS,
            )

            # Cache generation
            try:
                GenerationCache.store_generation(
                    str(generation.id),
                    schema,
                    react_code,
                    meta
                )
            except Exception as redis_err:
                logger.warning(f"Redis caching failed: {redis_err}")

            return Response(
                {
                    "project_id": str(project.id),
                    "generation_id": str(generation.id),
                    "schema": schema,
                    "code": react_code,
                    "meta": {
                        "provider": provider,
                        "model": llm_result.get("provider"),
                        "usage": meta,
                    },
                },
                status=201,
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return Response({"error": str(e)}, status=500)


class GenerationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, generation_id):
        try:
            generation = Generations.objects.get(
                id=generation_id,
                project__user=request.user
            )
        except Generations.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(GenerationSerializer(generation).data)
