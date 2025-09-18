from django.contrib.auth.models import User
from django.db import models


class PostType(models.TextChoices):
    LIVE = 'live', 'Live'
    REEL = 'reel', 'Reel'
    POST = 'post', 'Post'
    CAROUSEL = 'carousel', 'Carousel'
    STORY = 'story', 'Story'


class PostObjective(models.TextChoices):
    SALES = 'sales', 'Vendas'
    BRANDING = 'branding', 'Branding'
    ENGAGEMENT = 'engagement', 'Engajamento'
    AWARENESS = 'awareness', 'Conscientização'
    LEAD_GENERATION = 'lead_generation', 'Geração de Leads'
    EDUCATION = 'education', 'Educação'


class Gender(models.TextChoices):
    MALE = 'male', 'Masculino'
    FEMALE = 'female', 'Feminino'
    ALL = 'all', 'Todos'
    NON_BINARY = 'non_binary', 'Não Binário'


class Post(models.Model):
    """Post configuration for AI content generation."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Required fields
    name = models.CharField(max_length=200, help_text="Nome do post")
    objective = models.CharField(
        max_length=50,
        choices=PostObjective.choices,
        help_text="Objetivo do post"
    )
    type = models.CharField(
        max_length=20,
        choices=PostType.choices,
        help_text="Tipo de conteúdo"
    )

    # Target public fields (all optional)
    target_gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
        null=True,
        help_text="Gênero do público-alvo"
    )
    target_age = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Idade do público-alvo (ex: 18-25, 25-35)"
    )
    target_location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Localização do público-alvo"
    )
    target_salary = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Salário ou renda mensal do público-alvo"
    )
    target_interests = models.TextField(
        blank=True,
        null=True,
        help_text="Interesses do público-alvo"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_type_display()} ({self.get_objective_display()})"

    @property
    def has_target_audience(self):
        """Check if post has any target audience defined."""
        return any([
            self.target_gender,
            self.target_age,
            self.target_location,
            self.target_salary,
            self.target_interests
        ])


class PostIdea(models.Model):
    """AI-generated ideas for posts."""
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='ideas')

    # AI-generated content
    content = models.TextField(
        help_text="Conteúdo completo gerado pela IA (Título, Texto, CTA)"
    )
    image_url = models.TextField(
        blank=True,
        null=True,
        help_text="URL da imagem gerada ou base64 data"
    )

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

    # AI generation metadata (for tracking which AI model was used)
    ai_provider = models.CharField(max_length=50, blank=True, null=True)
    ai_model = models.CharField(max_length=100, blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'post_ideas'
        verbose_name = 'Post Idea'
        verbose_name_plural = 'Post Ideas'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ideia para {self.post.name} - {self.get_status_display()}"

    @property
    def content_preview(self):
        """Return a preview of the content (first 100 characters)."""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content


# Legacy models - keeping temporarily for migration purposes
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

    # New field for generated image URL or base64 data
    image_url = models.TextField(
        blank=True, null=True, help_text="Can store URL or base64 image data")

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
