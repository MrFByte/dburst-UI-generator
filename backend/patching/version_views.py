import logging
import jsonpatch
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from generation.models import Generations
from generation.codegen import ReactCodeGenerator
from .models import Patch

logger = logging.getLogger(__name__)


class GetVersionView(APIView):
    """
    Get a specific version of the schema by applying patches up to a point.
    
    GET /api/v1/patching/<generation_id>/version/<patch_id>/
    
    Response:
        {
            "generation_id": "uuid",
            "version_id": "uuid",
            "schema": {...},
            "code": "...",
            "patch_count": 5
        }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, generation_id, patch_id):
        try:
            generation = Generations.objects.select_related('project__user').get(id=generation_id)
            
            if generation.project.user != request.user:
                return Response(
                    {"error": "You do not have permission to view this generation"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            target_patch = Patch.objects.get(id=patch_id, generation=generation)
            
            patches = Patch.objects.filter(
                generation=generation,
                applied_at__lte=target_patch.applied_at
            ).order_by('applied_at')
            
            schema = generation.schema.copy()
            
            for patch in patches:
                try:
                    schema = jsonpatch.apply_patch(schema, patch.patch_data)
                except Exception as e:
                    logger.error(f"Failed to apply patch {patch.id}: {e}")
                    continue
            
            try:
                generator = ReactCodeGenerator(schema)
                code = generator.generate()
            except Exception as e:
                logger.error(f"Failed to generate code: {e}")
                code = ""
            
            return Response({
                "generation_id": str(generation_id),
                "version_id": str(patch_id),
                "schema": schema,
                "code": code,
                "patch_count": patches.count(),
            }, status=status.HTTP_200_OK)
            
        except Generations.DoesNotExist:
            return Response(
                {"error": "Generation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Patch.DoesNotExist:
            return Response(
                {"error": "Version not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting version: {e}")
            return Response(
                {"error": "Failed to retrieve version", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UndoView(APIView):
    """
    Undo the last patch.
    
    POST /api/v1/patching/<generation_id>/undo/
    
    Response:
        {
            "success": true,
            "schema": {...},
            "code": "...",
            "patch_count": 4
        }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, generation_id):
        try:
            generation = Generations.objects.select_related('project__user').get(id=generation_id)
            
            if generation.project.user != request.user:
                return Response(
                    {"error": "You do not have permission to modify this generation"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            last_patch = Patch.objects.filter(
                generation=generation
            ).order_by('-applied_at').first()
            
            if not last_patch:
                return Response(
                    {"error": "No patches to undo"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            patches = Patch.objects.filter(
                generation=generation,
                applied_at__lt=last_patch.applied_at
            ).order_by('applied_at')
            
            schema = generation.schema.copy()
            
            for patch in patches:
                try:
                    schema = jsonpatch.apply_patch(schema, patch.patch_data)
                except Exception as e:
                    logger.error(f"Failed to apply patch {patch.id}: {e}")
                    continue
            
            try:
                generator = ReactCodeGenerator(schema)
                code = generator.generate()
            except Exception as e:
                logger.error(f"Failed to generate code: {e}")
                code = ""
            
            last_patch.delete()
            
            return Response({
                "success": True,
                "schema": schema,
                "code": code,
                "patch_count": patches.count(),
            }, status=status.HTTP_200_OK)
            
        except Generations.DoesNotExist:
            return Response(
                {"error": "Generation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error undoing patch: {e}")
            return Response(
                {"error": "Failed to undo", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
