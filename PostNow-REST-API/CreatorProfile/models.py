import re
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


# Validators
def validate_hex_color(value):
    """
    Valida que o valor é uma cor HEX válida no formato #RRGGBB ou #RGB.
    Aceita string vazia (campo opcional).
    """
    if not value:
        return  # Campo opcional, vazio é válido

    hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    if not re.match(hex_pattern, value):
        raise ValidationError(
            f'"{value}" não é uma cor HEX válida. Use o formato #RRGGBB (ex: #8B5CF6).'
        )


def validate_visual_style_ids(value):
    """
    Valida que visual_style_ids é uma lista de inteiros positivos.
    """
    if not isinstance(value, list):
        raise ValidationError('visual_style_ids deve ser uma lista.')

    for item in value:
        if not isinstance(item, int) or item < 1:
            raise ValidationError(
                f'Cada item em visual_style_ids deve ser um inteiro positivo. Encontrado: {item}'
            )


# Regex validator para telefone (aceita formatos comuns)
phone_validator = RegexValidator(
    regex=r'^[\d\s\-\+\(\)]{8,20}$',
    message='Telefone inválido. Use apenas números, espaços, hífens e parênteses.'
)


class VisualStylePreference(models.Model):
    """
    Modelo para armazenar os 18 estilos visuais disponíveis para seleção.
    Cada estilo tem um nome, descrição detalhada e opcionalmente uma imagem de preview.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    preview_image_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'creatorprofile_visualstylepreference'
        verbose_name = 'Visual Style Preference'
        verbose_name_plural = 'Visual Style Preferences'

    def __str__(self):
        return self.name


class CreatorProfile(models.Model):
    """
    Perfil do criador de conteúdo com todas as informações de onboarding.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')

    # Business info
    business_name = models.CharField(max_length=255, blank=True)
    business_phone = models.CharField(max_length=50, blank=True, validators=[phone_validator])
    business_website = models.URLField(max_length=500, blank=True)
    business_instagram_handle = models.CharField(max_length=100, blank=True)
    business_description = models.TextField(blank=True)
    business_purpose = models.TextField(blank=True)
    business_location = models.CharField(max_length=255, blank=True)

    # Brand identity
    specialization = models.CharField(max_length=255, blank=True)
    brand_personality = models.TextField(blank=True)
    products_services = models.TextField(blank=True)

    # Target audience
    target_audience = models.TextField(blank=True)
    target_interests = models.TextField(blank=True)

    # Competition
    main_competitors = models.TextField(blank=True)
    reference_profiles = models.TextField(blank=True)

    # Voice and style
    voice_tone = models.CharField(max_length=100, blank=True)

    # Color palette (5 colors in HEX format)
    color_1 = models.CharField(max_length=7, blank=True, validators=[validate_hex_color])
    color_2 = models.CharField(max_length=7, blank=True, validators=[validate_hex_color])
    color_3 = models.CharField(max_length=7, blank=True, validators=[validate_hex_color])
    color_4 = models.CharField(max_length=7, blank=True, validators=[validate_hex_color])
    color_5 = models.CharField(max_length=7, blank=True, validators=[validate_hex_color])

    # Visual style preferences (list of IDs)
    visual_style_ids = models.JSONField(default=list, blank=True, validators=[validate_visual_style_ids])

    # Onboarding progress tracking
    step_1_completed = models.BooleanField(default=False)
    step_2_completed = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)

    # Weekly context
    weekly_context_policy_override = models.CharField(max_length=50, null=True, blank=True)

    # Logo
    logo = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'creatorprofile_creatorprofile'
        verbose_name = 'Creator Profile'
        verbose_name_plural = 'Creator Profiles'

    def __str__(self):
        return f"{self.business_name} - {self.user.username}"
