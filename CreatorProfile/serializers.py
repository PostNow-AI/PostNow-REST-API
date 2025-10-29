from django.contrib.auth.models import User
from rest_framework import serializers

from core.serializers import BaseModelSerializer, BaseSerializer

from .models import CreatorProfile, UserBehavior


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for profile context."""

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'email']


# === STEP-BASED SERIALIZERS FOR ONBOARDING ===

class Step1PersonalSerializer(BaseModelSerializer):
    """Step 1: Personal information - professional_name, profession, instagram_handle, whatsapp_number"""

    class Meta:
        model = CreatorProfile
        fields = [
            'professional_name',
            'profession',
            'instagram_handle',
            'whatsapp_number'
        ]

    def validate_professional_name(self, value):
        """Validate professional name is required and has minimum length."""
        return self.validate_required_string(value, "Nome profissional", min_length=2)

    def validate_profession(self, value):
        """Validate profession is required and has minimum length."""
        return self.validate_required_string(value, "Profissão", min_length=2)

    def validate_whatsapp_number(self, value):
        """Validate WhatsApp number is required."""
        return self.validate_phone_number(value, "WhatsApp")

    def validate_instagram_handle(self, value):
        """Clean instagram handle by removing @ if present."""
        if value:
            value = value.strip()
            if value.startswith('@'):
                value = value[1:]
        return value if value else None


class Step2BusinessSerializer(BaseModelSerializer):
    """Step 2: Business information - business_name, specialization, business_instagram_handle, business_website, business_city, business_description, target demographics"""

    class Meta:
        model = CreatorProfile
        fields = [
            'business_name',
            'specialization',
            'business_instagram_handle',
            'business_website',
            'business_city',
            'business_description',
            'target_gender',
            'target_age_range',
            'target_interests',
            'target_location'
        ]

    def validate_business_name(self, value):
        """Validate business name is required."""
        return self.validate_required_string(value, "Nome do negócio", min_length=2)

    def validate_specialization(self, value):
        """Validate specialization is required."""
        return self.validate_required_string(value, "Especialização", min_length=2)

    def validate_business_city(self, value):
        """Validate business city is required."""
        return self.validate_required_string(value, "Cidade do negócio", min_length=2)

    def validate_business_description(self, value):
        """Validate business description is required."""
        return self.validate_required_string(value, "Descrição do negócio", min_length=10)

    def validate_target_gender(self, value):
        """Validate target gender is required."""
        return self.validate_required_string(value, "Gênero do público-alvo", min_length=1)

    def validate_target_age_range(self, value):
        """Validate target age range is required."""
        return self.validate_required_string(value, "Faixa etária do público-alvo", min_length=1)

    def validate_target_location(self, value):
        """Validate target location is required."""
        return self.validate_required_string(value, "Localização do público-alvo", min_length=2)

    def validate_business_instagram_handle(self, value):
        """Clean business instagram handle by removing @ if present."""
        if value:
            value = value.strip()
            if value.startswith('@'):
                value = value[1:]
        return value if value else None


class Step3BrandingSerializer(BaseModelSerializer):
    """Step 3: Branding information - logo, voice_tone, colors (optional, default to random)"""

    class Meta:
        model = CreatorProfile
        fields = [
            'logo',
            'voice_tone',
            'color_1',
            'color_2',
            'color_3',
            'color_4',
            'color_5'
        ]

    def validate_voice_tone(self, value):
        """Validate voice tone is required."""
        return self.validate_required_string(value, "Tom de voz", min_length=2)

    def _validate_color(self, value, field_name):
        """Validate color format if provided."""
        if value and not value.startswith('#'):
            raise serializers.ValidationError(
                f"{field_name} deve estar no formato hexadecimal (ex: #FFFFFF)."
            )
        return value

    def validate_color_1(self, value):
        """Validate color format if provided."""
        return self._validate_color(value, "Cor 1")

    def validate_color_2(self, value):
        """Validate color format if provided."""
        return self._validate_color(value, "Cor 2")

    def validate_color_3(self, value):
        """Validate color format if provided."""
        return self._validate_color(value, "Cor 3")

    def validate_color_4(self, value):
        """Validate color format if provided."""
        return self._validate_color(value, "Cor 4")

    def validate_color_5(self, value):
        """Validate color format if provided."""
        return self._validate_color(value, "Cor 5")


# === MAIN CREATOR PROFILE SERIALIZER ===

class CreatorProfileSerializer(BaseModelSerializer):
    """Complete Creator Profile serializer with all fields and step status."""

    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = CreatorProfile
        fields = [
            # User relationship
            'user',

            # Step 1: Personal information
            'professional_name',
            'profession',
            'instagram_handle',
            'whatsapp_number',

            # Step 2: Business information
            'business_name',
            'specialization',
            'business_description',
            'target_gender',
            'target_age_range',
            'target_interests',
            'target_location',

            # Step 3: Branding
            'logo',
            'voice_tone',
            'color_1',
            'color_2',
            'color_3',
            'color_4',
            'color_5',


            # Metadata
            'created_at',
            'updated_at',
        ]


# === ONBOARDING STATUS SERIALIZER ===

class OnboardingStatusSerializer(BaseSerializer):
    """Serializer for onboarding status response."""

    current_step = serializers.IntegerField()
    step_1_completed = serializers.BooleanField()
    step_2_completed = serializers.BooleanField()
    step_3_completed = serializers.BooleanField()
    onboarding_completed = serializers.BooleanField()
    profile_exists = serializers.BooleanField()


# === USER BEHAVIOR SERIALIZER ===

class UserBehaviorSerializer(BaseModelSerializer):
    """
    Serializer for user behavioral data tracking.
    Used for personalization and analytics.
    """

    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = UserBehavior
        fields = [
            'user',
            'ideas_selected',
            'ideas_rejected',
            'avg_time_per_idea',
            'preferred_topics',
            'preferred_complexity',
            'preferred_length',
            'peak_hours',
            'usage_frequency',
            'avg_session_duration',
            'total_interactions',
            'last_activity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_activity']

    def validate_preferred_complexity(self, value):
        """Validate complexity is within valid range."""
        if value < 1 or value > 10:
            raise serializers.ValidationError(
                "Complexidade preferida deve estar entre 1 e 10."
            )
        return value

    def validate_ideas_selected(self, value):
        """Validate ideas selected is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Ideias selecionadas deve ser uma lista."
            )
        return value

    def validate_ideas_rejected(self, value):
        """Validate ideas rejected is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Ideias rejeitadas deve ser uma lista."
            )
        return value

    def validate_preferred_topics(self, value):
        """Validate preferred topics is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Tópicos preferidos deve ser uma lista."
            )
        return value

    def validate_peak_hours(self, value):
        """Validate peak hours is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Horários de pico deve ser uma lista."
            )
        return value
