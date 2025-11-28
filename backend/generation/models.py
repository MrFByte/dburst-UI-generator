from email.policy import default
import uuid
from django.db import models
from projects.models import Project

# Create your models here.

class Generations(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
    
    class Provider(models.TextChoices):
        GROQ = "groq", "Groq"
        GEMINI = "gemini", "Gemini"
        OPENAI = "openai", "OpenAI"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="generations")
    prompt = models.TextField(default='')
    schema = models.JSONField(default=dict) 
    code_bundle_url = models.TextField(blank=True, null=True)
    llm_provider = models.CharField(max_length=30, choices=Provider.choices)
    token_usage = models.IntegerField(default=0)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} → {self.status}"
