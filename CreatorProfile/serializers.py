from django.contrib.auth.models import User
from rest_framework import serializers

from .models import CreatorProfile, UserBehavior


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for profile context."""

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'email']


class CreatorProfileSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for CreatorProfile with new onboarding fields.
    All fields are optional for flexible onboarding.
    """

    user = UserBasicSerializer(read_only=True)
    onboarding_completed = serializers.BooleanField(read_only=True)
    onboarding_skipped = serializers.BooleanField(read_only=True)
    onboarding_completed_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CreatorProfile
        fields = [
            # User relationship
            'user',

            # Basic user info
            'avatar',

            # Professional information
            'professional_name',
            'profession',
            'specialization',

            # Social media
            'linkedin_url',
            'instagram_username',
            'youtube_channel',
            'tiktok_username',

            # Brandbook - Colors
            'primary_color',
            'secondary_color',
            'accent_color_1',
            'accent_color_2',
            'accent_color_3',

            # Brandbook - Typography
            'primary_font',
            'secondary_font',

            # Metadata
            'onboarding_completed',
            'onboarding_skipped',
            'created_at',
            'updated_at',
            'onboarding_completed_at',
        ]

    def validate_professional_name(self, value):
        """Validate professional name has minimum length."""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Nome profissional deve ter pelo menos 2 caracteres."
            )
        return value.strip() if value else value

    def validate_profession(self, value):
        """Validate profession has minimum length."""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Profissão deve ter pelo menos 2 caracteres."
            )
        return value.strip() if value else value

    def validate_specialization(self, value):
        """Validate specialization has minimum length."""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Especialização deve ter pelo menos 2 caracteres."
            )
        return value.strip() if value else value

    def validate_primary_color(self, value):
        """Validate primary color is a valid hex color."""
        if value and not value.startswith('#'):
            raise serializers.ValidationError(
                "Cor deve estar no formato hexadecimal (ex: #FFFFFF)."
            )
        return value

    def validate_secondary_color(self, value):
        """Validate secondary color is a valid hex color."""
        if value and not value.startswith('#'):
            raise serializers.ValidationError(
                "Cor deve estar no formato hexadecimal (ex: #FFFFFF)."
            )
        return value

    def validate_accent_color_1(self, value):
        """Validate accent color 1 is a valid hex color."""
        if value and not value.startswith('#'):
            raise serializers.ValidationError(
                "Cor deve estar no formato hexadecimal (ex: #FFFFFF)."
            )
        return value

    def validate_accent_color_2(self, value):
        """Validate accent color 2 is a valid hex color."""
        if value and not value.startswith('#'):
            raise serializers.ValidationError(
                "Cor deve estar no formato hexadecimal (ex: #FFFFFF)."
            )
        return value

    def validate_accent_color_3(self, value):
        """Validate accent color 3 is a valid hex color."""
        if value and not value.startswith('#'):
            raise serializers.ValidationError(
                "Cor deve estar no formato hexadecimal (ex: #FFFFFF)."
            )
        return value


class OnboardingSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for onboarding process.
    All fields are optional for flexible onboarding.
    """

    class Meta:
        model = CreatorProfile
        fields = [
            'professional_name',
            'profession',
            'specialization',
            'linkedin_url',
            'instagram_username',
            'youtube_channel',
            'tiktok_username',
            'primary_color',
            'secondary_color',
            'accent_color_1',
            'accent_color_2',
            'accent_color_3',
            'primary_font',
            'secondary_font',
        ]

    def validate_professional_name(self, value):
        """Validate professional name has minimum length."""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Nome profissional deve ter pelo menos 2 caracteres."
            )
        return value.strip() if value else value

    def validate_profession(self, value):
        """Validate profession has minimum length."""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Profissão deve ter pelo menos 2 caracteres."
            )
        return value.strip() if value else value

    def validate_specialization(self, value):
        """Validate specialization has minimum length."""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Especialização deve ter pelo menos 2 caracteres."
            )
        return value.strip() if value else value


class OnboardingStatusSerializer(serializers.Serializer):
    """
    Serializer for onboarding status response.
    Used to inform frontend about onboarding status.
    """

    onboarding_completed = serializers.BooleanField()
    onboarding_skipped = serializers.BooleanField()
    has_data = serializers.BooleanField()
    filled_fields_count = serializers.IntegerField()
    total_fields_count = serializers.IntegerField()


class UserBehaviorSerializer(serializers.ModelSerializer):
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


class ProfileStatsSerializer(serializers.Serializer):
    """
    Serializer for profile statistics and insights.
    Used for dashboard and analytics display.
    """

    total_users = serializers.IntegerField()
    completed_onboarding = serializers.IntegerField()
    skipped_onboarding = serializers.IntegerField()
    average_completion_rate = serializers.FloatField()
    most_common_profession = serializers.CharField()
    completion_rate = serializers.FloatField()
