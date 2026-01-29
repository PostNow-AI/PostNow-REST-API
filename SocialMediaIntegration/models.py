"""
Social Media Integration Models
Handles Instagram account connections, metrics, notifications, and connection tracking.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class InstagramAccount(models.Model):
    """
    Stores Instagram account connection details and OAuth tokens.
    Each user can connect multiple Instagram accounts (personal, business, etc.)
    """

    CONNECTION_STATUS_CHOICES = [
        ('connected', 'Conectado'),
        ('disconnected', 'Desconectado'),
        ('error', 'Erro'),
        ('token_expired', 'Token Expirado'),
    ]

    ACCOUNT_TYPE_CHOICES = [
        ('BUSINESS', 'Business'),
        ('CREATOR', 'Creator'),
        ('PERSONAL', 'Personal'),
    ]

    # === RELATIONSHIPS ===
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='instagram_accounts',
        verbose_name="Usuário"
    )

    # === INSTAGRAM ACCOUNT INFO ===
    instagram_user_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Instagram User ID",
        help_text="ID único do Instagram"
    )

    username = models.CharField(
        max_length=100,
        verbose_name="Username",
        help_text="@ do Instagram"
    )

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default='BUSINESS',
        verbose_name="Tipo de Conta"
    )

    profile_picture_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Foto de Perfil URL"
    )

    # === METRICS (cached from API) ===
    followers_count = models.IntegerField(
        default=0,
        verbose_name="Seguidores"
    )

    following_count = models.IntegerField(
        default=0,
        verbose_name="Seguindo"
    )

    media_count = models.IntegerField(
        default=0,
        verbose_name="Total de Posts"
    )

    # === OAUTH TOKENS (encrypted in database) ===
    access_token = models.TextField(
        verbose_name="Access Token",
        help_text="Token de acesso criptografado"
    )

    token_type = models.CharField(
        max_length=50,
        default='Bearer',
        verbose_name="Tipo de Token"
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Token Expira Em",
        help_text="Data/hora de expiração do token (60 dias)"
    )

    # === CONNECTION STATUS ===
    connection_status = models.CharField(
        max_length=20,
        choices=CONNECTION_STATUS_CHOICES,
        default='connected',
        verbose_name="Status da Conexão"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se a conexão está ativa"
    )

    sync_error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Mensagem de Erro",
        help_text="Último erro de sincronização"
    )

    # === SYNC INFO ===
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Última Sincronização"
    )

    connected_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Conectado Em"
    )

    # === TIMESTAMPS ===
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado Em"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado Em"
    )

    class Meta:
        verbose_name = "Conta Instagram"
        verbose_name_plural = "Contas Instagram"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['instagram_user_id']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"@{self.username} ({self.user.email})"

    def is_token_expiring_soon(self, days=7):
        """Check if token expires in less than specified days"""
        if not self.expires_at:
            return False
        return (self.expires_at - timezone.now()).days < days

    def days_until_expiration(self):
        """Get number of days until token expires"""
        if not self.expires_at:
            return None
        delta = self.expires_at - timezone.now()
        return delta.days if delta.days > 0 else 0


class InstagramMetrics(models.Model):
    """
    Stores daily Instagram metrics/insights for analysis and dashboard.
    One row per account per day.
    """

    # === RELATIONSHIPS ===
    account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name='metrics',
        verbose_name="Conta Instagram"
    )

    # === METRICS DATE ===
    date = models.DateField(
        verbose_name="Data",
        help_text="Data das métricas"
    )

    # === ENGAGEMENT METRICS ===
    impressions = models.IntegerField(
        default=0,
        verbose_name="Impressões",
        help_text="Vezes que o conteúdo apareceu"
    )

    reach = models.IntegerField(
        default=0,
        verbose_name="Alcance",
        help_text="Pessoas únicas que viram"
    )

    engagement = models.IntegerField(
        default=0,
        verbose_name="Engajamento",
        help_text="Total de interações (likes, comments, saves)"
    )

    profile_views = models.IntegerField(
        default=0,
        verbose_name="Visualizações de Perfil"
    )

    # === AUDIENCE METRICS ===
    followers_count = models.IntegerField(
        default=0,
        verbose_name="Seguidores",
        help_text="Total de seguidores nesta data"
    )

    media_count = models.IntegerField(
        default=0,
        verbose_name="Total de Posts"
    )

    # === RAW DATA ===
    raw_metrics = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métricas Brutas",
        help_text="Dados completos da API do Instagram"
    )

    # === TIMESTAMPS ===
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado Em"
    )

    class Meta:
        verbose_name = "Métrica Instagram"
        verbose_name_plural = "Métricas Instagram"
        ordering = ['-date']
        unique_together = ['account', 'date']
        indexes = [
            models.Index(fields=['account', '-date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"@{self.account.username} - {self.date}"

    def engagement_rate(self):
        """Calculate engagement rate percentage"""
        if self.reach == 0:
            return 0
        return (self.engagement / self.reach) * 100


class InstagramNotification(models.Model):
    """
    User notifications related to Instagram integration.
    Token expiration warnings, sync errors, connection success, etc.
    """

    NOTIFICATION_TYPE_CHOICES = [
        ('token_expiring', 'Token Expirando'),
        ('sync_error', 'Erro de Sincronização'),
        ('first_connection', 'Primeira Conexão'),
        ('sync_success', 'Sincronização Bem-Sucedida'),
        ('connection_lost', 'Conexão Perdida'),
        ('achievement_unlocked', 'Conquista Desbloqueada'),
    ]

    # === RELATIONSHIPS ===
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='instagram_notifications',
        verbose_name="Usuário"
    )

    # === NOTIFICATION DATA ===
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name="Tipo"
    )

    message = models.TextField(
        verbose_name="Mensagem",
        help_text="Conteúdo da notificação"
    )

    action_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL de Ação",
        help_text="Link para ação (ex: /settings/instagram)"
    )

    # === STATUS ===
    is_read = models.BooleanField(
        default=False,
        verbose_name="Lida"
    )

    # === TIMESTAMPS ===
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado Em"
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Lida Em"
    )

    class Meta:
        verbose_name = "Notificação Instagram"
        verbose_name_plural = "Notificações Instagram"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_notification_type_display()}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class InstagramConnectionAttempt(models.Model):
    """
    Tracks user attempts to connect Instagram for analytics and funnel optimization.
    Used to understand where users drop off and improve UX.
    """

    STEP_CHOICES = [
        ('initiated', 'Iniciado'),
        ('oauth_started', 'OAuth Iniciado'),
        ('oauth_callback', 'Callback Recebido'),
        ('completed', 'Completado'),
        ('abandoned', 'Abandonado'),
        ('error', 'Erro'),
    ]

    # === RELATIONSHIPS ===
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='instagram_connection_attempts',
        verbose_name="Usuário"
    )

    # === ATTEMPT DATA ===
    step = models.CharField(
        max_length=20,
        choices=STEP_CHOICES,
        verbose_name="Etapa"
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Mensagem de Erro"
    )

    user_agent = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="User Agent",
        help_text="Browser/device info"
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address"
    )

    # === TIMING ===
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Iniciado Em"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completado Em"
    )

    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Duração (segundos)",
        help_text="Tempo para completar o fluxo"
    )

    class Meta:
        verbose_name = "Tentativa de Conexão"
        verbose_name_plural = "Tentativas de Conexão"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['step']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_step_display()}"
