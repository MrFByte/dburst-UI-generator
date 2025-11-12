import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, 
                          editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        
class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier."""

    def create_user(self, email, name="", password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)  # Allows admin login
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email=email, password=password, **extra_fields)
    
    
class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """Application user stored in DB, authenticated via email (no username)."""

    email = models.EmailField(unique=True, max_length=180)
    name = models.CharField(max_length=120, blank=True)
    avatar_url = models.TextField(blank=True, null=True)

    role = models.CharField(max_length=50, default="user")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class AuthProvider(BaseModel):
    """Tracks linked OAuth providers for each user (Google, GitHub, etc.)"""

    class Choices(models.TextChoices):
        GOOGLE = "google", "Google"
        GITHUB = "github", "GitHub"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auth_providers")
    provider = models.CharField(max_length=30, choices=Choices.choices)
    provider_id = models.CharField(max_length=255)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("provider", "provider_id")

    def __str__(self):
        return f"{self.provider} account for {self.user.email}"