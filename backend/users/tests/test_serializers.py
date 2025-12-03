import pytest
from users.models import User
from users.serializers import UserSerializer


@pytest.mark.django_db
def test_user_serializer_output():
    """Serializer should return correct user data."""
    user = User.objects.create_user(
        email="test@example.com",
        name="Test User",
        avatar_url="http://example.com/avatar.png",
        role="user",
        password="pass123"
    )

    serializer = UserSerializer(user)
    data = serializer.data

    assert set(data.keys()) == {"id", "email", "name", "avatar_url", "role"}

    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["avatar_url"] == "http://example.com/avatar.png"
    assert data["role"] == "user"

    assert isinstance(data["id"], str)
    assert len(data["id"]) > 10

    assert "password" not in data


@pytest.mark.django_db
def test_user_serializer_blank_optional_fields():
    """Optional fields like name and avatar_url should serialize as empty."""
    user = User.objects.create_user(
        email="test@example.com",
        name="",
        avatar_url=None,
        password="pass123"
    )

    data = UserSerializer(user).data

    assert data["name"] == ""
    assert data["avatar_url"] is None


@pytest.mark.django_db
def test_user_serializer_role_default():
    """Role defaults to 'user' when not provided."""
    user = User.objects.create_user(
        email="abc@example.com",
        password="pass123"
    )

    data = UserSerializer(user).data
    assert data["role"] == "user"
