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
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        return (
            Project.objects
            .filter(user=self.request.user)
            .order_by('-updated_at')[:3]
        )
    
    
class CreateProject(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    