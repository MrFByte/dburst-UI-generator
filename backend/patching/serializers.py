from rest_framework import serializers
from .models import Patch
from generation.models import Generations


class PatchSerializer(serializers.ModelSerializer):
    """Serializer for Patch model"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    generation_id = serializers.UUIDField(source='generation.id', read_only=True)
    
    class Meta:
        model = Patch
        fields = [
            'id',
            'generation_id',
            'user_email',
            'patch_data',
            'description',
            'applied_at',
            'snapshot_created',
        ]
        read_only_fields = ['id', 'applied_at', 'snapshot_created']


class ApplyPatchRequestSerializer(serializers.Serializer):
    """Serializer for patch application requests"""
    
    patch = serializers.JSONField(
        help_text="JSON Patch operations array (RFC 6902 format)"
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional description of the change"
    )
    
    def validate_patch(self, value):
        """Validate patch format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Patch must be a list of operations")
        
        for op in value:
            if not isinstance(op, dict):
                raise serializers.ValidationError("Each operation must be a dictionary")
            
            if 'op' not in op:
                raise serializers.ValidationError("Each operation must have an 'op' field")
            
            if op['op'] not in ['add', 'remove', 'replace', 'move', 'copy', 'test']:
                raise serializers.ValidationError(f"Invalid operation: {op['op']}")
            
            if 'path' not in op:
                raise serializers.ValidationError("Each operation must have a 'path' field")
        
        return value


class GetSchemaResponseSerializer(serializers.Serializer):
    """Serializer for schema retrieval response"""
    
    generation_id = serializers.UUIDField()
    schema = serializers.JSONField()
    code = serializers.CharField()
    patch_count = serializers.IntegerField()
    cached = serializers.BooleanField()


class PatchListResponseSerializer(serializers.Serializer):
    """Serializer for patch list response"""
    
    generation_id = serializers.UUIDField()
    total_patches = serializers.IntegerField()
    patches = PatchSerializer(many=True)
