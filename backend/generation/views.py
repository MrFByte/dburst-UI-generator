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

from .llm import call_groq_model
from .codegen import schema_to_react_component
from .models import Generations
from django_redis import get_redis_connection
from projects.models import Project
from .serializers import (
    GenerationSerializer,
    GenerateRequestSerializer,
)

logger = logging.getLogger(__name__)

# Create your views here.


class GenerateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prompt = serializer.validated_data["prompt"]
        provider = serializer.validated_data["llm_provider"]

        project_id = serializer.validated_data.get("project_id")

        # 1. Resolve or auto-create project
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

        # 2. Call LLM through adapter
        try:
            llm_result = call_groq_model(prompt)
        except Exception as e:
            logger.error("LLM error: %s", e)
            return Response({"error": str(e)}, status=500)

        schema = llm_result["schema"]
        title = llm_result["title"] or "Generated UI"
        meta = llm_result["meta"]

        # 3. Replace Untitled with LLM generated title
        if project.title.startswith("Untitled Project"):
            project.title = title
            project.save()

        # 4. Generate code from schema
        react_code = schema_to_react_component(
            schema,
            component_name="GeneratedUI"
        )

        # 5. Save generation in DB
        generation = Generations.objects.create(
            project=project,
            prompt=prompt,
            schema=schema,
            llm_provider=provider,
            code_bundle_url="",  # will fill during export phase
            token_usage=meta["usage"].get("total_tokens", 0),
            status=Generations.Status.SUCCESS,
        )

        # 6. Redis caching
        try:
            r = get_redis_connection("default")
            key = f"generation:{generation.id}"
            r.set(f"{key}:schema", json.dumps(schema))
            r.set(f"{key}:code", react_code)
            r.set(f"{key}:meta", json.dumps(meta))
        except Exception as redis_err:
            logger.warning("Redis unavailable: %s", redis_err)

        # 7. Response (PHASE 2 REQUIREMENT)
        return Response(
            {
                "project_id": str(project.id),
                "generation_id": str(generation.id),
                "schema": schema,
                "code": react_code,
                "meta": meta,
            },
            status=201,
        )


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
