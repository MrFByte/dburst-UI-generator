import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class OTP(models.Model):
    """A single one-time-password request for an email address."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["email", "created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.email} (expires {self.expires_at.isoformat()})"

    @classmethod
    def create_for_email(cls, email, raw_code):
        return cls.objects.create(
            email=email,
            code_hash=make_password(raw_code),
            expires_at=timezone.now() + timezone.timedelta(minutes=settings.OTP_TTL_MINUTES),
        )

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_locked(self):
        return self.attempts >= settings.OTP_MAX_VERIFY_ATTEMPTS

    def check_code(self, raw_code):
        return check_password(raw_code, self.code_hash)
