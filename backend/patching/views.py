import logging
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction

from generation.models import Generations
from generation.cache import GenerationCache
from .models import Patch
from .serializers import (
    PatchSerializer,
    ApplyPatchRequestSerializer,
    GetSchemaResponseSerializer,
    PatchListResponseSerializer,
)

logger = logging.getLogger(__name__)


class StorePatchView(APIView):
    """
    Store and apply a JSON Patch to a generation's schema.
    
    POST /api/v1/patching/<generation_id>/patch/
    
    Request Body:
        {
            "patch": [{"op": "replace", "path": "/props/className", "value": "p-10"}],
            "description": "Changed padding"
        }
    
    Response:
        {
            "success": true,
            "generation_id": "uuid",
            "schema": {...},
            "patch_count": 5,
            "snapshot_created": false
        }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, generation_id):
        
        serializer = ApplyPatchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid patch data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patch_ops = serializer.validated_data['patch']
        description = serializer.validated_data.get('description', '')
        
        try:
            generation = Generations.objects.select_related('project__user').get(id=generation_id)
            
            if generation.project.user != request.user:
                return Response(
                    {"error": "You do not have permission to modify this generation"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            updated_schema = GenerationCache.apply_patch(str(generation_id), patch_ops)
            
            if updated_schema is None:
                if generation.schema:
                    GenerationCache.store_generation(
                        str(generation_id),
                        generation.schema,
                        generation.metadata.get('code', ''),
                        generation.metadata
                    )
                    updated_schema = GenerationCache.apply_patch(str(generation_id), patch_ops)
                
                if updated_schema is None:
                    return Response(
                        {"error": "Failed to apply patch. Schema not found in cache or database."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            patch_stored = GenerationCache.store_patch(
                str(generation_id),
                patch_ops,
                str(request.user.id),
                description
            )
            
            if not patch_stored:
                logger.warning(f"Failed to store patch in Redis for generation {generation_id}")
            
            with transaction.atomic():
                patch_count = GenerationCache.get_patch_count(str(generation_id))
                snapshot_created = (patch_count % GenerationCache.PATCH_SNAPSHOT_THRESHOLD == 0)
                
                patch_obj = Patch.objects.create(
                    generation=generation,
                    user=request.user,
                    patch_data=patch_ops,
                    description=description,
                    snapshot_created=snapshot_created
                )
                
                if snapshot_created:
                    generation.schema = updated_schema
                    generation.save(update_fields=['schema'])
                    logger.info(f"Created snapshot for generation {generation_id} at patch #{patch_count}")
            
            return Response({
                "success": True,
                "generation_id": str(generation_id),
                "schema": updated_schema,
                "patch_id": str(patch_obj.id),
                "patch_count": patch_count,
                "snapshot_created": snapshot_created,
            }, status=status.HTTP_200_OK)
            
        except Generations.DoesNotExist:
            return Response(
                {"error": "Generation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error applying patch to generation {generation_id}: {e}")
            return Response(
                {"error": "Failed to apply patch", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetSchemaView(APIView):
    """
    Retrieve the current schema for a generation from cache or database.
    
    GET /api/v1/patching/<generation_id>/schema/
    
    Response:
        {
            "generation_id": "uuid",
            "schema": {...},
            "code": "...",
            "patch_count": 5,
            "cached": true
        }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, generation_id):
        try:
            generation = Generations.objects.select_related('project__user').get(id=generation_id)
            
            if generation.project.user != request.user:
                return Response(
                    {"error": "You do not have permission to view this generation"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            cached_data = GenerationCache.get_generation(str(generation_id))
            
            if cached_data:
                patch_count = GenerationCache.get_patch_count(str(generation_id))
                return Response({
                    "generation_id": str(generation_id),
                    "schema": cached_data['schema'],
                    "code": cached_data['code'],
                    "patch_count": patch_count,
                    "cached": True,
                }, status=status.HTTP_200_OK)
            
            if generation.schema:
                code = generation.metadata.get('code', '')
                GenerationCache.store_generation(
                    str(generation_id),
                    generation.schema,
                    code,
                    generation.metadata
                )
                
                return Response({
                    "generation_id": str(generation_id),
                    "schema": generation.schema,
                    "code": code,
                    "patch_count": 0,
                    "cached": False,
                }, status=status.HTTP_200_OK)
            
            return Response(
                {"error": "Schema not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Generations.DoesNotExist:
            return Response(
                {"error": "Generation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving schema for generation {generation_id}: {e}")
            return Response(
                {"error": "Failed to retrieve schema", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListPatchesView(APIView):
    """
    List all patches for a generation with pagination.
    
    GET /api/v1/patching/<generation_id>/patches/?limit=20&offset=0
    
    Response:
        {
            "generation_id": "uuid",
            "total_patches": 15,
            "patches": [
                {
                    "id": "uuid",
                    "patch_data": [...],
                    "description": "...",
                    "user_email": "user@example.com",
                    "applied_at": "2026-01-05T10:30:00Z",
                    "snapshot_created": false
                },
                ...
            ]
        }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, generation_id):
        try:
            generation = Generations.objects.select_related('project__user').get(id=generation_id)
            
            if generation.project.user != request.user:
                return Response(
                    {"error": "You do not have permission to view patches for this generation"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
            
            limit = min(limit, 100)
            
            patches = Patch.objects.filter(generation=generation).order_by('-applied_at')[offset:offset+limit]
            total_patches = Patch.objects.filter(generation=generation).count()
            
            serializer = PatchSerializer(patches, many=True)
            
            return Response({
                "generation_id": str(generation_id),
                "total_patches": total_patches,
                "limit": limit,
                "offset": offset,
                "patches": serializer.data,
            }, status=status.HTTP_200_OK)
            
        except Generations.DoesNotExist:
            return Response(
                {"error": "Generation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Invalid limit or offset parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error listing patches for generation {generation_id}: {e}")
            return Response(
                {"error": "Failed to retrieve patches", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearCacheView(APIView):
    """
    Clear cached data for a generation (admin/debug endpoint).
    
    DELETE /api/v1/patching/<generation_id>/cache/
    
    Response:
        {
            "success": true,
            "message": "Cache cleared for generation"
        }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, generation_id):
        try:
            generation = Generations.objects.select_related('project__user').get(id=generation_id)
            
            if generation.project.user != request.user:
                return Response(
                    {"error": "You do not have permission to clear cache for this generation"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            cleared = GenerationCache.clear_generation(str(generation_id))
            
            if cleared:
                return Response({
                    "success": True,
                    "message": f"Cache cleared for generation {generation_id}",
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "message": "Failed to clear cache",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Generations.DoesNotExist:
            return Response(
                {"error": "Generation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error clearing cache for generation {generation_id}: {e}")
            return Response(
                {"error": "Failed to clear cache", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
