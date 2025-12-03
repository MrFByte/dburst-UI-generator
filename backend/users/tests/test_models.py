import pytest
from users.models import User, AuthProvider

# User Provider Model

@pytest.mark.django_db
def test_create_user():
    """Create a normal user"""
    user = User.objects.create_user(
        email="test@example.com",
        name="Test User",
        password="testpass123",
        is_active=True
    )

    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.is_active is True
    assert user.is_staff is False 
    assert user.is_superuser is False 
    assert user.role == "user" 
    assert str(user) == "test@example.com"
    assert user.id is not None 
    assert user.created_at is not None
    assert user.updated_at is not None
    
@pytest.mark.django_db
def test_create_superuser():
    """Create a superuser → manager should set flags correctly"""
    admin = User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass123",
    )

    assert admin.email == "admin@example.com"
    assert admin.is_active is True
    assert admin.is_staff is True
    assert admin.is_superuser is True
    
@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    """Email is required → error"""
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="pass123")

# Auth Provider Model
    
@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123"
    )


@pytest.mark.django_db
def test_create_auth_provider(user):
    """Create OAuth provider entry for user"""
    provider = AuthProvider.objects.create(
        user=user,
        provider=AuthProvider.Choices.GOOGLE,
        provider_id="google123"
    )

    assert provider.user == user
    assert provider.provider == "google"
    assert provider.provider_id == "google123"
    assert provider.linked_at is not None 
    assert str(provider) == f"google account for {user.email}"


@pytest.mark.django_db
def test_auth_provider_unique_constraint(user):
    """provider + provider_id must be unique together"""
    AuthProvider.objects.create(
        user=user,
        provider=AuthProvider.Choices.GOOGLE,
        provider_id="google123",
    )

    with pytest.raises(Exception):
        AuthProvider.objects.create(
            user=user,
            provider=AuthProvider.Choices.GOOGLE,
            provider_id="google123",
        )


@pytest.mark.django_db
def test_user_can_have_multiple_providers(user):
    """User can link both Google + GitHub accounts"""
    google = AuthProvider.objects.create(
        user=user, provider="google", provider_id="g123"
    )
    github = AuthProvider.objects.create(
        user=user, provider="github", provider_id="gh123"
    )

    assert user.auth_providers.count() == 2
    assert google in user.auth_providers.all()
    assert github in user.auth_providers.all()