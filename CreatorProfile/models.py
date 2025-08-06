from django.contrib.auth.models import User
from django.db import models


class CreatorProfile(models.Model):
    """
    Simplified Creator Profile model for new onboarding system.
    Handles user data for campaign personalization.
    """

    # === BASIC USER INFO ===
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='creator_profile')

    # Avatar field for profile image
    avatar = models.TextField(
        blank=True,
        null=True,
        verbose_name="Avatar",
        help_text="Base64 encoded image data (max 1MB)"
    )

    # Professional information
    professional_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nome Profissional",
        help_text="Nome que será usado em campanhas e conteúdo"
    )

    profession = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Profissão",
        help_text="Ex: Advogado, Coach, Consultor"
    )

    specialization = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Especialização",
        help_text="Ex: Tributário, Executivo, Empresarial"
    )

    # === SOCIAL MEDIA ===
    linkedin_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="LinkedIn URL"
    )

    instagram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Instagram Username"
    )

    youtube_channel = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="YouTube Channel"
    )

    tiktok_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="TikTok Username"
    )

    # === BRANDBOOK ===
    primary_color = models.CharField(
        max_length=7,  # Hex color code
        blank=True,
        null=True,
        verbose_name="Cor Primária",
        help_text="Cor principal da marca (formato hex: #FFFFFF)"
    )

    secondary_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor Secundária"
    )

    accent_color_1 = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor de Destaque 1"
    )

    accent_color_2 = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor de Destaque 2"
    )

    accent_color_3 = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor de Destaque 3"
    )

    primary_font = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Fonte Primária",
        help_text="Ex: Inter, Roboto, Open Sans"
    )

    secondary_font = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Fonte Secundária",
        help_text="Ex: Poppins, Montserrat"
    )

    # === METADATA ===
    onboarding_completed = models.BooleanField(
        default=False,
        verbose_name="Onboarding Completado"
    )

    onboarding_skipped = models.BooleanField(
        default=False,
        verbose_name="Onboarding Pulado"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    onboarding_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Conclusão do Onboarding"
    )

    class Meta:
        verbose_name = "Perfil do Criador"
        verbose_name_plural = "Perfis dos Criadores"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.profession or 'Sem profissão'}"

    def save(self, *args, **kwargs):
        """Override save to automatically set onboarding status."""
        # Check if any onboarding data is filled
        has_data = any([
            self.professional_name,
            self.profession,
            self.specialization,
            self.linkedin_url,
            self.instagram_username,
            self.youtube_channel,
            self.tiktok_username,
            self.primary_color,
            self.secondary_color,
            self.accent_color_1,
            self.accent_color_2,
            self.accent_color_3,
            self.primary_font,
            self.secondary_font,
        ])

        if has_data and not self.onboarding_completed:
            self.onboarding_completed = True
            if not self.onboarding_completed_at:
                from django.utils import timezone
                self.onboarding_completed_at = timezone.now()

        super().save(*args, **kwargs)


class UserBehavior(models.Model):
    """
    Track user behavioral data for personalization.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='behavior_profile')

    # Click Patterns
    ideas_selected = models.JSONField(
        default=list,
        verbose_name="Ideias Selecionadas",
        help_text="Lista de IDs das ideias selecionadas pelo usuário"
    )

    ideas_rejected = models.JSONField(
        default=list,
        verbose_name="Ideias Rejeitadas",
        help_text="Lista de IDs das ideias rejeitadas pelo usuário"
    )

    avg_time_per_idea = models.FloatField(
        default=0.0,
        verbose_name="Tempo Médio por Ideia",
        help_text="Tempo médio em segundos analisando cada ideia"
    )

    # Preferences (inferred from behavior)
    preferred_topics = models.JSONField(
        default=list,
        verbose_name="Tópicos Preferidos",
        help_text="Lista de tópicos preferidos baseados no comportamento"
    )

    preferred_complexity = models.IntegerField(
        default=5,
        verbose_name="Complexidade Preferida",
        help_text="Escala 1-10 baseada no comportamento"
    )

    preferred_length = models.CharField(
        max_length=20,
        choices=[('short', 'Curto'), ('medium', 'Médio'), ('long', 'Longo')],
        default='medium',
        verbose_name="Comprimento Preferido"
    )

    # Usage Patterns
    peak_hours = models.JSONField(
        default=list,
        verbose_name="Horários de Pico",
        help_text="Horários de maior uso baseados no comportamento"
    )

    usage_frequency = models.CharField(
        max_length=20,
        choices=[('daily', 'Diário'), ('weekly', 'Semanal'),
                 ('monthly', 'Mensal')],
        default='weekly',
        verbose_name="Frequência de Uso"
    )

    avg_session_duration = models.FloatField(
        default=0.0,
        verbose_name="Duração Média da Sessão",
        help_text="Duração média da sessão em minutos"
    )

    # Metadata
    total_interactions = models.IntegerField(
        default=0,
        verbose_name="Total de Interações"
    )

    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atividade"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Comportamento do Usuário"
        verbose_name_plural = "Comportamentos dos Usuários"

    def __str__(self):
        return f"Comportamento - {self.user.get_full_name()}"
