from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for returning user profile details."""

    class Meta:
        model = User
        fields = ["id", "email", "name", "avatar_url", "role"]
