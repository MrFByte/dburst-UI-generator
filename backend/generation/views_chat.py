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
from rest_framework.decorators import api_view, permission_classes

from rest_framework_simplejwt.tokens import RefreshToken

from .llm import LLMClient
from .llm_chat import LLMChat
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

# ... (keep existing GenerateView and GenerationDetailView code)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_chat_history(request, generation_id):
    """
    Get chat history for a generation (all prompts and AI responses)
    
    Returns the initial prompt + ai_response as first message,
    then any future refinement messages (not implemented yet, but ready for future)
    """
    try:
        generation = Generations.objects.get(
            id=generation_id,
            project__user=request.user
        )
        
        # For now, just return the initial generation as chat history
        # In future, you can add a ChatMessage model if needed
        chat_history = {
            'messages': [
                {
                    'role': 'user',
                    'content': generation.prompt,
                    'created_at': generation.created_at.isoformat()
                },
                {
                    'role': 'assistant',
                    'content': generation.ai_response or 'UI generated successfully',
                    'created_at': generation.created_at.isoformat()
                }
            ]
        }
        
        return Response(chat_history)
        
    except Generations.DoesNotExist:
        return Response(
            {'error': 'Generation not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refine_ui(request):
    """
    Refine UI based on user chat message
    
    Request body:
    {
        "generation_id": "uuid",
        "message": "Change the header color to blue"
    }
    
    Response:
    {
        "schema": {...updated schema...},
        "code": "...updated code...",
        "ai_response": "Changed header background to blue"
    }
    """
    generation_id = request.data.get('generation_id')
    user_message = request.data.get('message')
    
    if not generation_id or not user_message:
        return Response(
            {'error': 'generation_id and message are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        generation = Generations.objects.get(
            id=generation_id,
            project__user=request.user
        )
        
        # Initialize LLMChat with the same model used for generation
        chat_client = LLMChat(ui_model=generation.llm_provider)
        
        # Build conversation history (for now, just the initial prompt)
        conversation_history = [
            {'role': 'user', 'content': generation.prompt},
            {'role': 'assistant', 'content': generation.ai_response or 'UI generated'}
        ]
        
        # Refine the UI
        refinement_result = chat_client.refine_ui(
            current_schema=generation.schema,
            user_request=user_message,
            conversation_history=conversation_history
        )
        
        # Update generation with new schema and AI response
        generation.schema = refinement_result['schema']
        generation.ai_response = refinement_result['ai_response']
        generation.save()
        
        # Regenerate code from updated schema
        from .codegen import ReactCodeGenerator
        code_generator = ReactCodeGenerator(refinement_result['schema'])
        react_code = code_generator.generate()
        
        # Update usage
        usage = refinement_result.get('usage', {})
        generation.token_usage += usage.get('total_tokens', 0)
        generation.save()
        
        return Response({
            'schema': refinement_result['schema'],
            'code': react_code,
            'ai_response': refinement_result['ai_response']
        }, status=status.HTTP_200_OK)
        
    except Generations.DoesNotExist:
        return Response(
            {'error': 'Generation not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"UI refinement failed: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
