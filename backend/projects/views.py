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
        
    