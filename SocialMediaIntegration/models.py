"""
SocialMediaIntegration Models

Models for Instagram publishing automation:
- InstagramAccount: Connected Instagram Business accounts
- ScheduledPost: Posts scheduled for automatic publishing
- PublishingLog: Audit log for publishing attempts
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class InstagramAccountStatus(models.TextChoices):
    """Status of Instagram account connection."""
    CONNECTED = 'connected', 'Conectado'
    DISCONNECTED = 'disconnected', 'Desconectado'
    TOKEN_EXPIRED = 'token_expired', 'Token Expirado'
    ERROR = 'error', 'Erro'


class InstagramAccount(models.Model):
    """
    Connected Instagram Business/Creator account.

    Stores OAuth tokens and account information for Instagram Graph API.
    Tokens are encrypted using Fernet (AES-128) before storage.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='instagram_accounts'
    )

    # Instagram account info
    instagram_user_id = models.CharField(
        max_length=100,
        help_text="Instagram User ID from Graph API"
    )
    instagram_username = models.CharField(
        max_length=100,
        help_text="Instagram @username"
    )
    instagram_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Display name on Instagram"
    )
    profile_picture_url = models.URLField(
        blank=True,
        null=True,
        help_text="Profile picture URL"
    )

    # Facebook Page connection (required for Instagram Business)
    facebook_page_id = models.CharField(
        max_length=100,
        help_text="Connected Facebook Page ID"
    )
    facebook_page_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Facebook Page name"
    )

    # OAuth tokens (encrypted)
    access_token = models.TextField(
        help_text="Encrypted long-lived access token"
    )
    token_expires_at = models.DateTimeField(
        help_text="Token expiration timestamp"
    )

    # Account status
    status = models.CharField(
        max_length=20,
        choices=InstagramAccountStatus.choices,
        default=InstagramAccountStatus.CONNECTED
    )
    last_error = models.TextField(
        blank=True,
        null=True,
        help_text="Last error message if status is ERROR"
    )

    # Sync tracking
    last_sync_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last successful data sync"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instagram_accounts'
        verbose_name = 'Instagram Account'
        verbose_name_plural = 'Instagram Accounts'
        unique_together = ['user', 'instagram_user_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"@{self.instagram_username} ({self.user.email})"

    @property
    def is_token_valid(self):
        """Check if the access token is still valid."""
        if not self.token_expires_at:
            return False
        # Add 1 day buffer before actual expiration
        buffer = timezone.timedelta(days=1)
        return timezone.now() < (self.token_expires_at - buffer)

    @property
    def days_until_expiration(self):
        """Get days until token expiration."""
        if not self.token_expires_at:
            return 0
        delta = self.token_expires_at - timezone.now()
        return max(0, delta.days)


class ScheduledPostStatus(models.TextChoices):
    """Status of a scheduled post."""
    DRAFT = 'draft', 'Rascunho'
    SCHEDULED = 'scheduled', 'Agendado'
    PUBLISHING = 'publishing', 'Publicando'
    PUBLISHED = 'published', 'Publicado'
    FAILED = 'failed', 'Falhou'
    CANCELLED = 'cancelled', 'Cancelado'


class MediaType(models.TextChoices):
    """Type of media for Instagram post."""
    IMAGE = 'IMAGE', 'Imagem'
    VIDEO = 'VIDEO', 'Vídeo'
    CAROUSEL = 'CAROUSEL', 'Carrossel'
    REELS = 'REELS', 'Reels'
    STORY = 'STORY', 'Story'


class ScheduledPost(models.Model):
    """
    Post scheduled for automatic publishing on Instagram.

    Links to PostIdea from IdeaBank and allows scheduling
    for automatic publishing via Instagram Graph API.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='scheduled_posts'
    )
    instagram_account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name='scheduled_posts'
    )

    # Link to IdeaBank content (optional - can also be standalone)
    post_idea = models.ForeignKey(
        'IdeaBank.PostIdea',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_posts',
        help_text="Linked PostIdea from IdeaBank (optional)"
    )

    # Content
    caption = models.TextField(
        help_text="Post caption (max 2200 chars for Instagram)"
    )
    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.IMAGE
    )
    media_urls = models.JSONField(
        default=list,
        help_text="List of media URLs (images/videos)"
    )

    # Scheduling
    scheduled_for = models.DateTimeField(
        help_text="When to publish the post"
    )
    timezone = models.CharField(
        max_length=50,
        default='America/Sao_Paulo',
        help_text="User's timezone for scheduling"
    )

    # Publishing status
    status = models.CharField(
        max_length=20,
        choices=ScheduledPostStatus.choices,
        default=ScheduledPostStatus.DRAFT
    )

    # Instagram response data
    instagram_container_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Media container ID during publishing"
    )
    instagram_media_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Published media ID"
    )
    instagram_permalink = models.URLField(
        blank=True,
        null=True,
        help_text="Permanent link to published post"
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Actual publication timestamp"
    )

    # Error handling
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum retry attempts"
    )
    last_error = models.TextField(
        blank=True,
        null=True,
        help_text="Last error message"
    )
    next_retry_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Next retry attempt timestamp"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scheduled_posts'
        verbose_name = 'Scheduled Post'
        verbose_name_plural = 'Scheduled Posts'
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['instagram_account', 'status']),
        ]

    def __str__(self):
        return f"Post agendado para {self.scheduled_for} (@{self.instagram_account.instagram_username})"

    @property
    def caption_preview(self):
        """Return a preview of the caption (first 100 characters)."""
        return self.caption[:100] + "..." if len(self.caption) > 100 else self.caption

    @property
    def is_ready_to_publish(self):
        """Check if post is ready for publishing."""
        return (
            self.status == ScheduledPostStatus.SCHEDULED and
            self.scheduled_for <= timezone.now() and
            self.instagram_account.is_token_valid and
            self.media_urls and
            len(self.media_urls) > 0
        )

    @property
    def can_retry(self):
        """Check if post can be retried."""
        return (
            self.status == ScheduledPostStatus.FAILED and
            self.retry_count < self.max_retries
        )

    def schedule_retry(self, delay_minutes=15):
        """Schedule a retry attempt with exponential backoff."""
        backoff = delay_minutes * (2 ** self.retry_count)
        self.next_retry_at = timezone.now() + timezone.timedelta(minutes=backoff)
        self.retry_count += 1
        self.save(update_fields=['next_retry_at', 'retry_count', 'updated_at'])


class PublishingLogStatus(models.TextChoices):
    """Status of a publishing attempt."""
    STARTED = 'started', 'Iniciado'
    CONTAINER_CREATED = 'container_created', 'Container Criado'
    PROCESSING = 'processing', 'Processando'
    SUCCESS = 'success', 'Sucesso'
    ERROR = 'error', 'Erro'
    RETRY = 'retry', 'Tentando Novamente'


class PublishingLog(models.Model):
    """
    Audit log for publishing attempts.

    Records each step of the publishing process for debugging
    and monitoring purposes.
    """
    scheduled_post = models.ForeignKey(
        ScheduledPost,
        on_delete=models.CASCADE,
        related_name='publishing_logs'
    )

    # Attempt info
    attempt_number = models.IntegerField(
        default=1,
        help_text="Which attempt this log represents"
    )
    status = models.CharField(
        max_length=20,
        choices=PublishingLogStatus.choices
    )

    # Timing
    started_at = models.DateTimeField(
        auto_now_add=True
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )
    duration_ms = models.IntegerField(
        blank=True,
        null=True,
        help_text="Duration in milliseconds"
    )

    # API response data
    api_endpoint = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="API endpoint called"
    )
    request_data = models.JSONField(
        blank=True,
        null=True,
        help_text="Request payload (sensitive data removed)"
    )
    response_data = models.JSONField(
        blank=True,
        null=True,
        help_text="API response"
    )

    # Error details
    error_code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    error_message = models.TextField(
        blank=True,
        null=True
    )
    error_details = models.JSONField(
        blank=True,
        null=True
    )

    # Step tracking
    step = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Current step: create_container, check_status, publish"
    )

    class Meta:
        db_table = 'publishing_logs'
        verbose_name = 'Publishing Log'
        verbose_name_plural = 'Publishing Logs'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['scheduled_post', 'attempt_number']),
            models.Index(fields=['status', 'started_at']),
        ]

    def __str__(self):
        return f"Log #{self.attempt_number} - {self.status} ({self.scheduled_post_id})"

    def complete(self, status, response_data=None, error_message=None):
        """Mark log entry as completed."""
        self.status = status
        self.completed_at = timezone.now()
        self.duration_ms = int(
            (self.completed_at - self.started_at).total_seconds() * 1000
        )
        if response_data:
            self.response_data = response_data
        if error_message:
            self.error_message = error_message
        self.save()
