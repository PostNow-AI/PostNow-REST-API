from django.contrib.auth.models import User
from django.db import models


class CampaignObjective(models.TextChoices):
    SALES = 'sales', 'Vendas'
    BRANDING = 'branding', 'Branding'
    ENGAGEMENT = 'engagement', 'Engajamento'


class ContentType(models.TextChoices):
    POST = 'post', 'Post'
    STORY = 'story', 'Story'
    REEL = 'reel', 'Reel'
    VIDEO = 'video', 'Vídeo'
    CAROUSEL = 'carousel', 'Carrossel'
    LIVE = 'live', 'Live'
    CUSTOM = 'custom', 'Custom'


class SocialPlatform(models.TextChoices):
    INSTAGRAM = 'instagram', 'Instagram'
    TIKTOK = 'tiktok', 'TikTok'
    YOUTUBE = 'youtube', 'YouTube'
    LINKEDIN = 'linkedin', 'LinkedIn'


class IdeaGenerationConfig(models.Model):
    """Configuration for idea generation requests."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Campaign objective
    # List of CampaignObjective choices
    objectives = models.JSONField(default=list)

    # Target persona
    persona_age = models.CharField(max_length=50, blank=True)
    persona_location = models.CharField(max_length=100, blank=True)
    persona_income = models.CharField(max_length=50, blank=True)
    persona_interests = models.TextField(blank=True)
    persona_behavior = models.TextField(blank=True)
    persona_pain_points = models.TextField(blank=True)

    # Social platforms
    # List of SocialPlatform choices
    platforms = models.JSONField(default=list)

    # Content types per platform
    content_types = models.JSONField(
        default=dict)  # {platform: [content_types]}

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'idea_generation_config'
        verbose_name = 'Idea Generation Config'
        verbose_name_plural = 'Idea Generation Configs'

    def __str__(self):
        return f"Config for {self.user.email} - {self.created_at}"


class CampaignIdea(models.Model):
    """Generated campaign ideas."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    config = models.ForeignKey(
        IdeaGenerationConfig, on_delete=models.CASCADE, null=True, blank=True)

    # Idea content
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()  # The full generated content
    platform = models.CharField(max_length=20, choices=SocialPlatform.choices)
    content_type = models.CharField(max_length=20, choices=ContentType.choices)

    # Status
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('approved', 'Aprovado'),
        ('archived', 'Arquivado'),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft')

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign_ideas'
        verbose_name = 'Campaign Idea'
        verbose_name_plural = 'Campaign Ideas'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.title} - {self.platform} ({self.status})"
