import random

from django.contrib.auth.models import User
from django.db import models


def generate_random_colors():
    """Generate 5 random hex colors."""
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D2B4DE'
    ]
    return random.sample(colors, 5)


class CreatorProfile(models.Model):
    """
    Creator Profile model for 3-step onboarding process.
    Step 1: Personal info, Step 2: Business info, Step 3: Branding
    """

    # === RELATIONSHIP ===
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='creator_profile')

    # === STEP 1: PERSONAL INFORMATION ===
    professional_name = models.CharField(
        max_length=200,
        default='',
        verbose_name="Nome Profissional",
        help_text="Nome que será usado em campanhas e conteúdo"
    )

    profession = models.CharField(
        max_length=200,
        default='',
        verbose_name="Profissão",
        help_text="Ex: Advogado, Coach, Consultor"
    )

    instagram_handle = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Instagram Handle",
        help_text="Seu @ do Instagram (sem o @)"
    )

    whatsapp_number = models.CharField(
        max_length=20,
        default='',
        verbose_name="WhatsApp",
        help_text="Número do WhatsApp com DDD"
    )

    # === STEP 2: BUSINESS INFORMATION ===
    business_name = models.CharField(
        max_length=200,
        default='',
        verbose_name="Nome do Negócio",
        help_text="Nome da sua empresa/marca"
    )

    specialization = models.CharField(
        max_length=200,
        default='',
        verbose_name="Especialização",
        help_text="Ex: Tributário, Executivo, Empresarial"
    )

    business_instagram_handle = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Instagram do Negócio",
        help_text="@ do Instagram do seu negócio (sem o @)"
    )

    business_website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Website do Negócio",
        help_text="Site da sua empresa"
    )

    business_city = models.CharField(
        max_length=100,
        default="Remoto",
        verbose_name="Cidade do Negócio",
        help_text="Cidade onde atua"
    )

    business_description = models.TextField(
        default='',
        verbose_name="Descrição do Negócio",
        help_text="Conte sobre seu negócio e o que você faz"
    )

    # === STEP 3: BRANDING ===
    logo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Logo",
        help_text="Logo da sua marca em formato base64 (opcional)"
    )

    voice_tone = models.CharField(
        max_length=100,
        default='',
        verbose_name="Tom de Voz",
        help_text="Ex: Profissional, Descontraído, Amigável"
    )

    # Five color palette - defaults to random colors
    color_1 = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor 1",
        help_text="Primeira cor da paleta (hex: #FFFFFF)"
    )

    color_2 = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor 2",
        help_text="Segunda cor da paleta"
    )

    color_3 = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor 3",
        help_text="Terceira cor da paleta"
    )

    color_4 = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor 4",
        help_text="Quarta cor da paleta"
    )

    color_5 = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Cor 5",
        help_text="Quinta cor da paleta"
    )

    # === ONBOARDING STATUS ===
    step_1_completed = models.BooleanField(
        default=False,
        verbose_name="Etapa 1 Completada"
    )

    step_2_completed = models.BooleanField(
        default=False,
        verbose_name="Etapa 2 Completada"
    )

    step_3_completed = models.BooleanField(
        default=False,
        verbose_name="Etapa 3 Completada"
    )

    onboarding_completed = models.BooleanField(
        default=False,
        verbose_name="Onboarding Completado"
    )

    # === METADATA ===
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
        return f"{self.professional_name} - {self.profession}"

    def save(self, *args, **kwargs):
        """Override save to manage onboarding status and assign random colors."""
        # Assign random colors if none are set
        if not any([self.color_1, self.color_2, self.color_3, self.color_4, self.color_5]):
            random_colors = generate_random_colors()
            self.color_1 = random_colors[0]
            self.color_2 = random_colors[1]
            self.color_3 = random_colors[2]
            self.color_4 = random_colors[3]
            self.color_5 = random_colors[4]

        # Check step completion status
        self.step_1_completed = bool(
            self.professional_name and self.professional_name.strip() and
            self.profession and self.profession.strip() and
            self.whatsapp_number and self.whatsapp_number.strip()
        )

        self.step_2_completed = bool(
            self.business_name and self.business_name.strip() and
            self.specialization and self.specialization.strip() and
            self.business_city and self.business_city.strip() and
            self.business_description and self.business_description.strip()
        )

        self.step_3_completed = bool(
            self.voice_tone and self.voice_tone.strip()
        )

        # Update overall onboarding status
        was_completed = self.onboarding_completed
        self.onboarding_completed = (
            self.step_1_completed and
            self.step_2_completed and
            self.step_3_completed
        )

        # Set completion timestamp if just completed
        if self.onboarding_completed and not was_completed:
            from django.utils import timezone
            self.onboarding_completed_at = timezone.now()
        elif not self.onboarding_completed:
            self.onboarding_completed_at = None

        super().save(*args, **kwargs)

    @property
    def current_step(self):
        """Return the current step number (1, 2, 3, or 4 if completed)."""
        if not self.step_1_completed:
            return 1
        elif not self.step_2_completed:
            return 2
        elif not self.step_3_completed:
            return 3
        else:
            return 4  # Completed

    @property
    def color_palette(self):
        """Return the complete color palette as a list."""
        return [
            self.color_1,
            self.color_2,
            self.color_3,
            self.color_4,
            self.color_5
        ]


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
