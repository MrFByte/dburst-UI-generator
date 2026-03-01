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
    """
    Generate a UI schema and React component code based on a user prompt.

    This endpoint accepts a natural-language prompt, sends it to the configured LLM
    provider (Groq, Gemini, or OpenAI), validates the returned UI schema, generates
    React code, stores the generation record, and optionally caches the output.

    If `project_id` is not provided, a new project will be automatically created
    for the authenticated user with a default name (e.g., "Untitled Project 1").
    If provided, the `project_id` must belong to the requesting user.

    Permissions:
        - IsAuthenticated: Only logged-in users may generate UI code.

    Request Body (JSON):
        {
            "prompt": "Describe the UI you want to generate...",
            "llm_provider": "groq" | "gemini" | "openai"    # optional, defaults to 'groq'
            "project_id": "<uuid>"                          # optional
        }

    Success Response (201 Created):
        {
            "project_id": "<uuid>",
            "project_title": "Generated Title",
            "generation_id": "<uuid>",
            "schema": { ...validated UI schema... },
            "code": "<React component source code>",
            "meta": {
                "provider": "groq",
                "model": "groq/llama-3-70b",
                "usage": {
                    "total_tokens": 1234,
                    ...
                }
            }
        }

    Error Responses:
        400 Bad Request:
            - Invalid schema returned by the LLM.
            - Invalid request format.

            {
                "error": "Schema validation failed: missing field 'type'."
            }

        404 Not Found:
            - Provided project_id does not exist or does not belong to the user.

            {
                "error": "Project not found."
            }

        500 Internal Server Error:
            - Unexpected LLM failure, code generation failure, Redis error, etc.
            {
                "error": "Unhandled error message..."
            }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prompt = serializer.validated_data["prompt"]
        
        ui_model = serializer.validated_data.get("ui_model", "ui_llama_3_3")
        project_id = serializer.validated_data.get("project_id")

        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=request.user)
            except Project.DoesNotExist:
                return Response({"error": "Project not found."}, status=404)
        else:
            project = None
    
        try:
            llm_client = LLMClient(ui_model=ui_model)
            
            logger.info(f"Starting two-stage generation for user: {request.user.id}")
            result = llm_client.generate_ui(prompt)
            
            project_name = result["project_name"]
            project_description = result["project_description"]
            design_plan = result["design_plan"]
            
            schema = result["schema"]
            
            try:
                schema = SchemaValidator.validate(schema)
            except ValueError as e:
                logger.error(f"Schema validation failed: {e}")
                return Response(
                    {"error": f"Schema validation failed: {str(e)}"}, 
                    status=400
                )
            
            if not project:
                project = Project.objects.create(
                    user=request.user,
                    title=project_name,
                    description=project_description,
                )
                logger.info(f"Created project: {project.id} - {project.title}")


            code_generator = ReactCodeGenerator(schema)
            print(code_generator)
            react_code = code_generator.generate()

            planning_usage = result["usage"].get("planning_tokens", {})
            generation_usage = result["usage"].get("generation_tokens", {})
            total_tokens = (
                planning_usage.get("total_tokens", 0) + 
                generation_usage.get("total_tokens", 0)
            )
            
            # Generate brief AI response for chat history
            page_type = design_plan.get("intent", "page")
            sections_count = len(design_plan.get("design_plan", {}).get("sections", []))
            ai_response = f"Created {page_type} with {sections_count} sections using {design_plan.get('theme', {}).get('style', 'modern')} design"[:200]

            generation = Generations.objects.create(
                project=project,
                prompt=prompt,
                ai_response=ai_response,
                schema=schema,
                llm_provider=result["models"]["ui_generation"],
                token_usage=total_tokens,
                status=Generations.Status.SUCCESS,
                metadata={
                    "design_plan": design_plan,
                    "planning_model": result["models"]["planning"],
                    "ui_model": result["models"]["ui_generation"],
                    "planning_tokens": planning_usage,
                    "generation_tokens": generation_usage,
                    "theme": design_plan.get("theme", {}),
                    "layout_plan": design_plan.get("layout_plan", {})
                }
            )
            logger.info(f"Created generation: {generation.id}")

            try:
                GenerationCache.store_generation(
                    str(generation.id),
                    schema,
                    react_code,
                    {
                        "design_plan": design_plan,
                        "usage": result["usage"],
                        "models": result["models"]
                    }
                )
            except Exception as redis_err:
                logger.warning(f"Redis caching failed: {redis_err}")

            return Response(
                {
                    "success": True,
                    "project_id": str(project.id),
                    "project_title": project.title,
                    "project_description": project.description,
                    "generation_id": str(generation.id),
                    "schema": schema,
                    "code": react_code,
                    "design_plan": {
                        "concept": design_plan.get("concept", ""),
                        "theme": design_plan.get("theme", {}),
                        "layout_plan": design_plan.get("layout_plan", {}),
                        "image_suggestions": design_plan.get("image_suggestions", []),
                        "design_system": design_plan.get("design_system", {})
                    },
                    "meta": {
                        "models": {
                            "ui_generation": result["models"]["ui_generation"]
                        },
                        "usage": {
                            "planning": planning_usage,
                            "generation": generation_usage,
                            "total_tokens": total_tokens
                        },
                    },
                },
                status=201,
            )

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return Response({"error": str(e)}, status=400)
        
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return Response({"error": str(e)}, status=500)


class GenerationDetailView(APIView):
    """
    Retrieve details for a specific UI generation record.

    Permissions:
        - IsAuthenticated: Only the owner of the project may view the generation.

    Path Parameters:
        - generation_id (UUID): The ID of the generation to retrieve.

    Response (200 OK):
        {
            "id": "<uuid>",
            "project": { ...project fields... },
            "prompt": "original prompt",
            "schema": { ... },
            "code_bundle_url": "https://...",
            "llm_provider": "groq",
            "token_usage": 1234,
            "status": "SUCCESS",
            "created_at": "2025-01-01T12:00:00Z"
        }

    Error Responses:
        404 Not Found:
            Returned if the generation does not exist or does not belong to the user.

            {
                "error": "Not found"
            }
    """
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
