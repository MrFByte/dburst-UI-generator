import logging
import requests
import json
from django.db import transaction
from django.conf import settings
from google.oauth2.id_token import verify_oauth2_token
from google.auth.transport import requests as google_requests

from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Project
from .serializers import ProjectSerializer


logger = logging.getLogger(__name__)

# Create your views here.


class ListRecentProjects(ListAPIView):
    """
    Retrieve the three most recently updated projects belonging to the authenticated user.

    Permissions:
        - IsAuthenticated: Only logged-in users can access this endpoint.

    Description:
        This endpoint returns a list of the user's latest three projects,
        ordered by the `updated_at` timestamp in descending order.
        No request body is required.

    Query Parameters:
        - None

    Responses:
        200 OK:
            A list of project objects:
            [
                {
                    "id": 1,
                    "title": "My Project",
                    "description": "Project description",
                    "is_public": false,
                    "created_at": "2025-01-10T12:34:56Z",
                    "updated_at": "2025-01-11T09:30:00Z"
                },
                ...
            ]

        401 Unauthorized:
            Returned if the user is not authenticated.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        return (
            Project.objects
            .filter(user=self.request.user)
            .order_by('-updated_at')[:3]
        )
    
    
class CreateProject(CreateAPIView):
    """
    Create a new project for the authenticated user.

    Permissions:
        - IsAuthenticated: Only logged-in users can create a project.

    Request Body (JSON):
        {
            "title": "Project Title",
            "description": "Optional description",
        }

    Responses:
        201 Created:
            {
                "id": 3,
                "title": "Project Title",
                "description": "Optional description",
                "is_public": true,
                "created_at": "...",
                "updated_at": "..."
            }

        400 Bad Request:
            Returned when required fields are missing or invalid.

        401 Unauthorized:
            Returned if the user is not authenticated.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProjectPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48


class ListAllProjects(ListAPIView):
    """
    Retrieve all projects belonging to the authenticated user with pagination.

    Permissions:
        - IsAuthenticated: Only logged-in users can access this endpoint.

    Description:
        This endpoint returns a paginated list of the user's all projects,
        ordered by the `updated_at` timestamp in descending order.
        Default page size is 12 projects per page.

    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Number of items per page (default: 12, max: 48)

    Responses:
        200 OK:
            {
                "count": 25,
                "next": "http://example.com/api/v1/projects/all-projects/?page=2",
                "previous": null,
                "results": [
                    {
                        "id": 1,
                        "title": "My Project",
                        "description": "Project description",
                        "is_public": false,
                        "created_at": "2025-01-10T12:34:56Z",
                        "updated_at": "2025-01-11T09:30:00Z"
                    },
                    ...
                ]
            }

        401 Unauthorized:
            Returned if the user is not authenticated.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    pagination_class = ProjectPagination
    
    def get_queryset(self):
        return (
            Project.objects
            .filter(user=self.request.user)
            .order_by('-updated_at')
        )


class GetProjectDetail(APIView):
    """
    Retrieve a project by its ID with its latest generation data.

    Permissions:
        - IsAuthenticated: Only logged-in users can access this endpoint.

    Description:
        This endpoint returns a project by its ID along with its latest generation
        (if available) to load in the UI generator.

    Path Parameters:
        - project_id (UUID): The ID of the project.

    Responses:
        200 OK:
            {
                "project": {
                    "id": 1,
                    "title": "My Project",
                    "description": "Project description",
                    "is_public": false,
                    "created_at": "2025-01-10T12:34:56Z",
                    "updated_at": "2025-01-11T09:30:00Z"
                },
                "latest_generation": {
                    "id": "...",
                    "schema": {...},
                    "code": "...",
                    "metadata": {...},
                    ...
                }
            }

        404 Not Found:
            Returned if the project does not exist or does not belong to the user.

        401 Unauthorized:
            Returned if the user is not authenticated.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the latest generation for this project
        latest_generation = project.generations.filter(status='success').order_by('-created_at').first()
        
        response_data = {
            "project": ProjectSerializer(project).data
        }
        
        if latest_generation:
            from generation.serializers import GenerationSerializer
            from generation.codegen import ReactCodeGenerator
            
            # Generate code from schema
            try:
                code_generator = ReactCodeGenerator(latest_generation.schema)
                react_code = code_generator.generate()
            except Exception as e:
                logger.error(f"Error generating code: {e}")
                react_code = ""
            
            gen_data = GenerationSerializer(latest_generation).data
            gen_data["code"] = react_code
            
            response_data["latest_generation"] = gen_data
        
        return Response(response_data)

        
class ProjectPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48


class ListAllProjects(ListAPIView):
    """
    Retrieve all projects belonging to the authenticated user with pagination.

    Permissions:
        - IsAuthenticated: Only logged-in users can access this endpoint.

    Description:
        This endpoint returns a paginated list of the user's all projects,
        ordered by the `updated_at` timestamp in descending order.
        Default page size is 12 projects per page.

    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Number of items per page (default: 12, max: 48)

    Responses:
        200 OK:
            {
                "count": 25,
                "next": "http://example.com/api/v1/projects/all-projects/?page=2",
                "previous": null,
                "results": [
                    {
                        "id": 1,
                        "title": "My Project",
                        "description": "Project description",
                        "is_public": false,
                        "created_at": "2025-01-10T12:34:56Z",
                        "updated_at": "2025-01-11T09:30:00Z"
                    },
                    ...
                ]
            }

        401 Unauthorized:
            Returned if the user is not authenticated.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    pagination_class = ProjectPagination
    
    def get_queryset(self):
        return (
            Project.objects
            .filter(user=self.request.user)
            .order_by('-updated_at')
        )


class GetProjectDetail(APIView):
    """
    Retrieve a project by its ID with its latest generation data.

    Permissions:
        - IsAuthenticated: Only logged-in users can access this endpoint.

    Description:
        This endpoint returns a project by its ID along with its latest generation
        (if available) to load in the UI generator.

    Path Parameters:
        - project_id (UUID): The ID of the project.

    Responses:
        200 OK:
            {
                "project": {
                    "id": 1,
                    "title": "My Project",
                    "description": "Project description",
                    "is_public": false,
                    "created_at": "2025-01-10T12:34:56Z",
                    "updated_at": "2025-01-11T09:30:00Z"
                },
                "latest_generation": {
                    "id": "...",
                    "schema": {...},
                    "code": "...",
                    "metadata": {...},
                    ...
                }
            }

        404 Not Found:
            Returned if the project does not exist or does not belong to the user.

        401 Unauthorized:
            Returned if the user is not authenticated.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the latest generation for this project
        latest_generation = project.generations.filter(status='success').order_by('-created_at').first()
        
        response_data = {
            "project": ProjectSerializer(project).data
        }
        
        if latest_generation:
            from generation.serializers import GenerationSerializer
            from generation.codegen import ReactCodeGenerator
            
            # Generate code from schema
            try:
                code_generator = ReactCodeGenerator(latest_generation.schema)
                react_code = code_generator.generate()
            except Exception as e:
                logger.error(f"Error generating code: {e}")
                react_code = ""
            
            gen_data = GenerationSerializer(latest_generation).data
            gen_data["code"] = react_code
            
            response_data["latest_generation"] = gen_data
        
        return Response(response_data)
