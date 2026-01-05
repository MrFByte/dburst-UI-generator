import uuid
from django.db import models
from users.models import User, BaseModel
from generation.models import Generations


class Patch(BaseModel):
    """
    Persistent storage for JSON patches applied to UI generations.
    Patches are stored in both Redis (for fast access) and database (for persistence).
    """
    
    generation = models.ForeignKey(
        Generations, 
        on_delete=models.CASCADE, 
        related_name="patches"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="patches"
    )
    patch_data = models.JSONField(
        help_text="JSON Patch operations (RFC 6902 format)"
    )
    description = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Optional description of what this patch changes"
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    snapshot_created = models.BooleanField(
        default=False,
        help_text="Whether a snapshot was created after this patch"
    )
    
    class Meta:
        ordering = ['-applied_at']  # Newest first
        indexes = [
            models.Index(fields=['generation', '-applied_at']),
            models.Index(fields=['user', '-applied_at']),
        ]
    
    def __str__(self):
        return f"Patch for {self.generation.id} by {self.user.email} at {self.applied_at}"
