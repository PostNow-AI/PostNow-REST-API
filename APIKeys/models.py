from django.contrib.auth.models import User
from django.db import models


class UserAPIKey(models.Model):
    """Stores per-user API keys for external providers like Gemini."""

    PROVIDER_CHOICES = [
        ('gemini', 'Google Gemini'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='api_keys')
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    api_key = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'provider')
        db_table = 'user_api_keys'

    def __str__(self):
        return f"{self.user.username}:{self.provider}"
