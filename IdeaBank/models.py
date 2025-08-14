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


class VoiceTone(models.TextChoices):
    PROFESSIONAL = 'professional', 'Profissional'
    CASUAL = 'casual', 'Casual'
    INSPIRATIONAL = 'inspirational', 'Inspirador'
    URGENT = 'urgent', 'Urgente'
    EDUCATIONAL = 'educational', 'Educativo'


class Campaign(models.Model):
    """Campaign container for multiple ideas."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Campaign basic info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Campaign objective
    objectives = models.JSONField(default=list)

    # Target persona
    persona_age = models.CharField(max_length=50, blank=True)
    persona_location = models.CharField(max_length=100, blank=True)
    persona_income = models.CharField(max_length=50, blank=True)
    persona_interests = models.TextField(blank=True)
    persona_behavior = models.TextField(blank=True)
    persona_pain_points = models.TextField(blank=True)

    # Social platforms and content types
    platforms = models.JSONField(default=list)
    content_types = models.JSONField(
        default=dict)  # {platform: [content_types]}

    # Voice tone
    voice_tone = models.CharField(
        max_length=20,
        choices=VoiceTone.choices,
        default=VoiceTone.PROFESSIONAL
    )

    # Campaign details (for AI generation)
    product_description = models.TextField(blank=True)
    value_proposition = models.TextField(blank=True)
    campaign_urgency = models.TextField(blank=True)

    # Status
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('active', 'Ativa'),
        ('paused', 'Pausada'),
        ('completed', 'Concluída'),
        ('archived', 'Arquivada'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaigns'
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email} ({self.status})"

    @property
    def ideas_count(self):
        """Return the number of ideas in this campaign."""
        return self.ideas.count()

    @property
    def approved_ideas_count(self):
        """Return the number of approved ideas in this campaign."""
        return self.ideas.filter(status='approved').count()


class CampaignIdea(models.Model):
    """Individual ideas within a campaign."""
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name='ideas')

    # Idea content
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()  # The full generated content

    # Platform and content type
    platform = models.CharField(max_length=20, choices=SocialPlatform.choices)
    content_type = models.CharField(max_length=20, choices=ContentType.choices)

    # AI generation metadata
    variation_type = models.CharField(
        max_length=10,
        choices=[
            ('a', 'Variação A'),
            ('b', 'Variação B'),
            ('c', 'Variação C'),
        ],
        default='a'
    )

    # Content details
    headline = models.TextField(blank=True)
    copy = models.TextField(blank=True)
    cta = models.CharField(max_length=200, blank=True)
    hashtags = models.JSONField(default=list)
    visual_description = models.TextField(blank=True)
    color_composition = models.TextField(blank=True)

    # Status
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('archived', 'Arquivado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign_ideas'
        verbose_name = 'Campaign Idea'
        verbose_name_plural = 'Campaign Ideas'
        ordering = ['-generated_at']
        # Removendo a constraint única que estava causando problemas
        # unique_together = ['campaign', 'platform', 'content_type', 'variation_type']

    def __str__(self):
        return f"{self.title} - {self.platform} ({self.variation_type}) - {self.status}"


# Legacy models for backward compatibility
class IdeaGenerationConfig(models.Model):
    """Legacy configuration model - kept for backward compatibility."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    objectives = models.JSONField(default=list)
    persona_age = models.CharField(max_length=50, blank=True)
    persona_location = models.CharField(max_length=100, blank=True)
    persona_income = models.CharField(max_length=50, blank=True)
    persona_interests = models.TextField(blank=True)
    persona_behavior = models.TextField(blank=True)
    persona_pain_points = models.TextField(blank=True)
    platforms = models.JSONField(default=list)
    content_types = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'idea_generation_config'
        verbose_name = 'Idea Generation Config'
        verbose_name_plural = 'Idea Generation Configs'

    def __str__(self):
        return f"Config for {self.user.email} - {self.created_at}"
