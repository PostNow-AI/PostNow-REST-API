from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class PostType(models.TextChoices):
    LIVE = 'live', _('Live')
    REEL = 'reel', _('Reel')
    POST = 'post', _('Post')
    CAROUSEL = 'carousel', _('Carousel')
    STORY = 'story', _('Story')


class PostObjective(models.TextChoices):
    SALES = 'sales', _('Vendas')
    BRANDING = 'branding', _('Branding')
    ENGAGEMENT = 'engagement', _('Engajamento')
    AWARENESS = 'awareness', _('Conscientização')
    LEAD_GENERATION = 'lead_generation', _('Geração de Leads')
    EDUCATION = 'education', _('Educação')


class Gender(models.TextChoices):
    MALE = 'male', _('Masculino')
    FEMALE = 'female', _('Feminino')
    ALL = 'all', _('Todos')
    NON_BINARY = 'non_binary', _('Não Binário')


def validate_post_name(value):
    """Validate post name is not empty and has reasonable length."""
    if not value or not value.strip():
        raise ValidationError(_('Nome do post não pode estar vazio.'))
    if len(value.strip()) < 3:
        raise ValidationError(
            _('Nome do post deve ter pelo menos 3 caracteres.'))


def validate_further_details(value):
    """Validate further details don't exceed reasonable length."""
    if value and len(value) > 2000:
        raise ValidationError(
            _('Detalhes adicionais não podem exceder 2000 caracteres.'))


class PostManager(models.Manager):
    """Custom manager for Post model."""

    def active(self):
        """Return only active posts."""
        return self.filter(is_active=True)

    def by_user(self, user):
        """Return posts for a specific user."""
        return self.filter(user=user)

    def automatically_generated(self):
        """Return only automatically generated posts."""
        return self.filter(is_automatically_generated=True)


class Post(models.Model):
    """Post configuration for AI content generation."""

    objects = PostManager()

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text=_("Usuário proprietário do post")
    )

    # Required fields with validation
    name = models.CharField(
        max_length=200,
        help_text=_("Nome descritivo do post (mínimo 3 caracteres)"),
        blank=True,
        null=True,
        validators=[validate_post_name]
    )
    objective = models.CharField(
        max_length=50,
        choices=PostObjective.choices,
        help_text=_(
            "Objetivo principal do post - define o tom e foco do conteúdo")
    )
    type = models.CharField(
        max_length=20,
        choices=PostType.choices,
        help_text=_("Tipo de conteúdo a ser gerado (Live, Reel, Post, etc.)")
    )
    further_details = models.TextField(
        help_text=_(
            "Detalhes adicionais para orientar a geração de conteúdo pela IA"),
        default="",
        blank=True,
        validators=[validate_further_details]
    )

    # Configuration flags
    include_image = models.BooleanField(
        default=False,
        help_text=_(
            "Se marcado, uma imagem será gerada automaticamente pela IA")
    )
    is_automatically_generated = models.BooleanField(
        default=False,
        help_text=_(
            "Indica se este post foi criado automaticamente pelo sistema")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Posts inativos não aparecem nas listagens principais")
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Data e hora de criação do post")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Data e hora da última atualização")
    )

    class Meta:
        db_table = 'posts'
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_active', 'is_automatically_generated']),
            models.Index(fields=['type', 'objective']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__isnull=False) | models.Q(name__gt=''),
                name='post_name_not_empty'
            ),
        ]

    def __str__(self):
        return f"{self.name or 'Sem nome'} - {self.get_type_display()} ({self.get_objective_display()})"

    def clean(self):
        """Custom validation for the model."""
        super().clean()
        if self.name:
            self.name = self.name.strip()
        if not self.objective:
            raise ValidationError(_('Objetivo é obrigatório.'))
        if not self.type:
            raise ValidationError(_('Tipo é obrigatório.'))

    def save(self, *args, **kwargs):
        """Override save to ensure validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def ideas_count(self):
        """Return the number of ideas for this post."""
        return self.ideas.count()

    @property
    def has_image_ideas(self):
        """Check if any ideas have images."""
        return self.ideas.filter(image_url__isnull=False).exists()

    @property
    def display_name(self):
        """Return a display name for the post."""
        return self.name or f"Post {self.id}"


class PostIdeaManager(models.Manager):
    """Custom manager for PostIdea model."""

    def with_images(self):
        """Return only ideas that have images."""
        return self.filter(image_url__isnull=False)

    def by_post(self, post):
        """Return ideas for a specific post."""
        return self.filter(post=post)


class PostIdea(models.Model):
    """AI-generated ideas for posts."""

    objects = PostIdeaManager()

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='ideas',
        help_text=_("Post ao qual esta ideia está associada")
    )

    # AI-generated content with validation
    content = models.TextField(
        help_text=_(
            "Conteúdo completo gerado pela IA incluindo título, texto e CTA"),
        validators=[MinLengthValidator(10, message=_(
            "Conteúdo deve ter pelo menos 10 caracteres."))]
    )
    image_url = models.TextField(
        blank=True,
        null=True,
        help_text=_("URL da imagem gerada pela IA ou dados base64")
    )
    image_description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Descrição da imagem usada como prompt para geração"),
        validators=[MaxLengthValidator(1000, message=_(
            "Descrição da imagem não pode exceder 1000 caracteres."))]
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Data e hora de criação da ideia")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Data e hora da última atualização")
    )

    class Meta:
        db_table = 'post_ideas'
        verbose_name = _('Post Idea')
        verbose_name_plural = _('Post Ideas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(content__isnull=False) & models.Q(
                    content__gt=''),
                name='postidea_content_not_empty'
            ),
        ]

    def __str__(self):
        return f"Ideia para {self.post.display_name}"

    def clean(self):
        """Custom validation for the model."""
        super().clean()
        if not self.content or not self.content.strip():
            raise ValidationError(_('Conteúdo é obrigatório.'))
        if self.image_description and len(self.image_description) > 1000:
            raise ValidationError(
                _('Descrição da imagem não pode exceder 1000 caracteres.'))

    def save(self, *args, **kwargs):
        """Override save to ensure validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def content_preview(self):
        """Return a preview of the content (first 100 characters)."""
        content = self.content.strip()
        return content[:100] + "..." if len(content) > 100 else content

    @property
    def has_image(self):
        """Check if this idea has an associated image."""
        return bool(self.image_url)

    @property
    def word_count(self):
        """Return the word count of the content."""
        return len(self.content.split()) if self.content else 0
