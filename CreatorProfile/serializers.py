import re

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import CreatorProfile, OnboardingTempData, VisualStylePreference


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for profile context."""

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'email']


# === STEP-BASED SERIALIZERS FOR ONBOARDING ===


class Step1BusinessSerializer(serializers.ModelSerializer):
    """Step 1: Business information - business_name, specialization, business_instagram_handle, business_website, business_city, business_description, target demographics"""

    class Meta:
        model = CreatorProfile
        fields = [
            'business_name',
            'business_phone',
            'business_website',
            'business_instagram_handle',
            'specialization',
            'business_description',
            'business_purpose',
            'brand_personality',
            'products_services',
            'business_location',
            'target_audience',
            'target_interests',
            'main_competitors',
            'reference_profiles'
        ]

    def validate_business_name(self, value):
        """Validate business name is required and has proper length."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Nome do negócio é obrigatório e deve ter pelo menos 2 caracteres."
            )
        if len(value.strip()) > 200:
            raise serializers.ValidationError(
                "Nome do negócio não pode ter mais de 200 caracteres."
            )
        return value.strip()

    def validate_business_phone(self, value):
        """Validate business phone format."""
        if value:
            # Remove common separators
            cleaned = ''.join(filter(str.isdigit, value))
            if len(cleaned) < 10 or len(cleaned) > 15:
                raise serializers.ValidationError(
                    "Número de telefone deve ter entre 10 e 15 dígitos."
                )
        return value.strip() if value else value

    def validate_business_website(self, value):
        """Validate website URL format."""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError(
                "Website deve começar com http:// ou https://"
            )
        return value

    def validate_business_instagram_handle(self, value):
        """Validate Instagram handle format."""
        if value:
            # Remove @ if present
            cleaned = value.strip().lstrip('@')
            if not cleaned.replace('_', '').replace('.', '').isalnum():
                raise serializers.ValidationError(
                    "Handle do Instagram deve conter apenas letras, números, pontos e underscores."
                )
            if len(cleaned) > 30:
                raise serializers.ValidationError(
                    "Handle do Instagram não pode ter mais de 30 caracteres."
                )
            return cleaned
        return value

    def validate_specialization(self, value):
        """Validate specialization field."""
        if value and len(value.strip()) > 200:
            raise serializers.ValidationError(
                "Nicho de atuação não pode ter mais de 200 caracteres."
            )
        return value.strip() if value else value

    def validate_business_description(self, value):
        """Validate business description."""
        if value:
            if len(value.strip()) < 10:
                raise serializers.ValidationError(
                    "Descrição do negócio deve ter pelo menos 10 caracteres."
                )
            if len(value.strip()) > 2000:
                raise serializers.ValidationError(
                    "Descrição do negócio não pode ter mais de 2000 caracteres."
                )
        return value.strip() if value else value

    def validate_business_purpose(self, value):
        """Validate business purpose."""
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError(
                "Propósito do negócio não pode ter mais de 1000 caracteres."
            )
        return value.strip() if value else value

    def validate_brand_personality(self, value):
        """Validate brand personality."""
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError(
                "Personalidade da marca não pode ter mais de 1000 caracteres."
            )
        return value.strip() if value else value

    def validate_products_services(self, value):
        """Validate products/services description."""
        if value and len(value.strip()) > 2000:
            raise serializers.ValidationError(
                "Descrição de produtos/serviços não pode ter mais de 2000 caracteres."
            )
        return value.strip() if value else value

    def validate_business_location(self, value):
        """Validate business location."""
        if value and len(value.strip()) > 100:
            raise serializers.ValidationError(
                "Localização do negócio não pode ter mais de 100 caracteres."
            )
        return value.strip() if value else value

    def validate_target_audience(self, value):
        """Validate target audience description."""
        if value and len(value.strip()) > 500:
            raise serializers.ValidationError(
                "Descrição do público-alvo não pode ter mais de 500 caracteres."
            )
        return value.strip() if value else value

    def validate_target_interests(self, value):
        """Validate target interests."""
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError(
                "Interesses do público-alvo não pode ter mais de 1000 caracteres."
            )
        return value.strip() if value else value

    def validate_main_competitors(self, value):
        """Validate main competitors."""
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError(
                "Lista de principais concorrentes não pode ter mais de 1000 caracteres."
            )
        return value.strip() if value else value

    def validate_reference_profiles(self, value):
        """Validate reference profiles."""
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError(
                "Perfis de referência não pode ter mais de 1000 caracteres."
            )
        return value.strip() if value else value


class Step2BrandingSerializer(serializers.ModelSerializer):
    """Step 3: Branding information - logo, voice_tone, colors (optional, default to random)"""

    visual_style_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = CreatorProfile
        fields = [
            'logo',
            'voice_tone',
            'color_1',
            'color_2',
            'color_3',
            'color_4',
            'color_5',
            'visual_style_ids'
        ]

    def validate_voice_tone(self, value):
        """Validate voice tone is required."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Tom de voz é obrigatório."
            )
        return value.strip()

    def _validate_hex_color(self, value, field_name):
        """Helper method to validate hex color format."""
        if not value:
            return value

        # Check if it's a valid hex color (with or without #)
        if not value.startswith('#'):
            value = f"#{value}"

        if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError(
                f"{field_name} deve estar no formato hexadecimal válido (ex: #FFFFFF)."
            )
        return value.upper()

    def validate_color_1(self, value):
        """Validate color 1 format if provided."""
        return self._validate_hex_color(value, "Cor 1")

    def validate_color_2(self, value):
        """Validate color 2 format if provided."""
        return self._validate_hex_color(value, "Cor 2")

    def validate_color_3(self, value):
        """Validate color 3 format if provided."""
        return self._validate_hex_color(value, "Cor 3")

    def validate_color_4(self, value):
        """Validate color 4 format if provided."""
        return self._validate_hex_color(value, "Cor 4")

    def validate_color_5(self, value):
        """Validate color 5 format if provided."""
        return self._validate_hex_color(value, "Cor 5")


# === MAIN CREATOR PROFILE SERIALIZER ===

class CreatorProfileSerializer(serializers.ModelSerializer):
    """Complete Creator Profile serializer with all fields and step status."""

    user = UserBasicSerializer(read_only=True)
    visual_style_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = CreatorProfile
        fields = [
            # User relationship
            'user',

            # Step 1: Business information
            'business_name',
            'business_phone',
            'business_website',
            'business_instagram_handle',
            'specialization',
            'business_description',
            'business_purpose',
            'brand_personality',
            'products_services',
            'business_location',
            'target_audience',
            'target_interests',
            'main_competitors',
            'reference_profiles',

            # Step 2: Branding
            'logo',
            'voice_tone',
            'color_1',
            'color_2',
            'color_3',
            'color_4',
            'color_5',
            'visual_style_ids',

            # Status fields
            'step_1_completed',
            'step_2_completed',
            'onboarding_completed',

            # Metadata
            'created_at',
            'updated_at',
            'onboarding_completed_at',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'onboarding_completed_at',
            'step_1_completed',
            'step_2_completed',
            'onboarding_completed'
        ]

    def validate(self, attrs):
        """Cross-field validation."""
        # Validate that if Instagram handle is provided, it doesn't conflict with business name
        instagram_handle = attrs.get('business_instagram_handle')
        business_name = attrs.get('business_name')

        if instagram_handle and business_name:
            # Clean both for comparison
            clean_handle = instagram_handle.lower().replace('_', '').replace('.', '')
            clean_business = business_name.lower().replace(
                ' ', '').replace('_', '').replace('.', '')

            # Warn if they're too similar (might be confusing)
            if clean_handle == clean_business:
                # This is actually good - they match
                pass

        return attrs


# === ONBOARDING STATUS SERIALIZER ===

class OnboardingStatusSerializer(serializers.Serializer):
    """Serializer for onboarding status response."""

    current_step = serializers.IntegerField()
    step_1_completed = serializers.BooleanField()
    step_2_completed = serializers.BooleanField()
    onboarding_completed = serializers.BooleanField()
    profile_exists = serializers.BooleanField()


class VisualStylePreferenceSerializer(serializers.ModelSerializer):
    """Serializer for Visual Style Preference."""

    class Meta:
        model = VisualStylePreference
        fields = '__all__'


class OnboardingTempDataSerializer(serializers.Serializer):
    """
    Serializer for saving temporary onboarding data before signup.
    Accepts all onboarding fields + session_id.
    """

    # Required
    session_id = serializers.CharField(max_length=100, required=True)

    # Step 1: Business Information (all optional for temp save)
    business_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    business_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    business_website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    business_instagram_handle = serializers.CharField(max_length=100, required=False, allow_blank=True)
    specialization = serializers.CharField(max_length=200, required=False, allow_blank=True)
    business_description = serializers.CharField(required=False, allow_blank=True)
    business_purpose = serializers.CharField(required=False, allow_blank=True)
    brand_personality = serializers.CharField(required=False, allow_blank=True)
    products_services = serializers.CharField(required=False, allow_blank=True)
    business_location = serializers.CharField(max_length=100, required=False, allow_blank=True)
    target_audience = serializers.CharField(max_length=500, required=False, allow_blank=True)
    target_interests = serializers.CharField(required=False, allow_blank=True)
    main_competitors = serializers.CharField(required=False, allow_blank=True)
    reference_profiles = serializers.CharField(required=False, allow_blank=True)

    # Step 2: Branding (all optional for temp save)
    logo = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    voice_tone = serializers.CharField(max_length=100, required=False, allow_blank=True)
    color_1 = serializers.CharField(max_length=7, required=False, allow_blank=True, allow_null=True)
    color_2 = serializers.CharField(max_length=7, required=False, allow_blank=True, allow_null=True)
    color_3 = serializers.CharField(max_length=7, required=False, allow_blank=True, allow_null=True)
    color_4 = serializers.CharField(max_length=7, required=False, allow_blank=True, allow_null=True)
    color_5 = serializers.CharField(max_length=7, required=False, allow_blank=True, allow_null=True)
    visual_style_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True
    )

    def validate_session_id(self, value):
        """Validate session_id is provided and not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("session_id é obrigatório.")
        return value.strip()

    def validate_business_instagram_handle(self, value):
        """Clean Instagram handle."""
        if value:
            return value.strip().lstrip('@')
        return value
