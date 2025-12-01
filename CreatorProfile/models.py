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
    Creator Profile model for 2-step onboarding process.
    Step 1: Business info, Step 2: Branding
    """

    # === RELATIONSHIP ===
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='creator_profile')

    # === STEP 1: BUSINESS INFORMATION ===

    business_name = models.CharField(
        max_length=200,
        default='',
        verbose_name="Nome do Negócio",
        help_text="Nome da sua empresa/marca"
    )

    business_phone = models.CharField(
        max_length=20,
        default='',
        verbose_name="WhatsApp",
        help_text="Número do WhatsApp com DDD"
    )

    business_website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Website do Negócio",
        help_text="Site da sua empresa"
    )

    business_instagram_handle = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Instagram do Negócio",
        help_text="@ do Instagram do seu negócio (sem o @)"
    )

    specialization = models.CharField(
        max_length=200,
        default='',
        verbose_name="Nicho de Atuação",
        help_text="Ex: Tributário, Executivo, Empresarial"
    )

    business_description = models.TextField(
        default='',
        verbose_name="Descrição do Negócio",
        help_text="Conte sobre seu negócio e o que você faz"
    )

    business_purpose = models.TextField(
        default='',
        verbose_name="Propósito do Negócio",
        help_text="Qual o propósito/missão do seu negócio?"
    )

    brand_personality = models.TextField(
        default='',
        verbose_name="Personalidade da Marca",
        help_text="Descreva a personalidade da sua marca"
    )

    products_services = models.TextField(
        default='',
        verbose_name="Produtos/Serviços",
        help_text="Quais produtos ou serviços você oferece?"
    )

    business_location = models.CharField(
        max_length=100,
        default="Remoto",
        verbose_name="Localização do Negócio",
        help_text="Localização onde atua"
    )

    # Target Audience Fields
    target_audience = models.CharField(
        max_length=50,
        default='',
        verbose_name="Público-Alvo",
        help_text="Descrição geral do seu público-alvo"
    )

    target_interests = models.TextField(
        blank=True,
        null=True,
        verbose_name="Interesses do Público-Alvo",
        help_text="Interesses e hobbies do seu público-alvo"
    )

    # Competition
    main_competitors = models.TextField(
        blank=True,
        null=True,
        verbose_name="Principais Concorrentes",
        help_text="Liste seus principais concorrentes"
    )

    reference_profiles = models.TextField(
        blank=True,
        null=True,
        verbose_name="Perfis de Referência",
        help_text="Perfis que você admira ou se inspira"
    )

    # === STEP 2: BRANDING ===
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

    visual_style_ids = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Estilos Visuais Preferidos",
        help_text="Lista de IDs das preferências de estilos visuais selecionadas"
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
        return f"{self.business_name or 'Sem nome'} - {self.specialization or 'Sem especialização'}"

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
            self.business_name and self.business_name.strip() and
            self.specialization and self.specialization.strip() and
            self.business_description and self.business_description.strip()
        )

        self.step_2_completed = bool(
            self.voice_tone and self.voice_tone.strip() and
            any([self.color_1, self.color_2, self.color_3, self.color_4, self.color_5])
        )

        self.step_3_completed = self.step_2_completed  # No additional step for now

        # Update overall onboarding status
        was_completed = self.onboarding_completed
        self.onboarding_completed = (
            self.step_1_completed and
            self.step_2_completed
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
        """Return the current step number (1, 2, or 3 if completed)."""
        if not self.step_1_completed:
            return 1
        elif not self.step_2_completed:
            return 2
        else:
            return 3  # Completed

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


class VisualStylePreference(models.Model):
    """
    Store user's visual style preferences.
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Nome da Preferência",
        help_text="Nome descritivo da preferência de estilo visual"
    )
    description = models.TextField(
        verbose_name="Descrição da Preferência",
        help_text="Descrição detalhada da preferência de estilo visual"
    )

    class Meta:
        verbose_name = "Preferência de Estilo Visual"
        verbose_name_plural = "Preferências de Estilo Visual"

    def __str__(self):
        return f"{self.name} - {self.description}"
