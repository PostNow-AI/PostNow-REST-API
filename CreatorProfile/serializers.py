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
    Comprehensive serializer for CreatorProfile with validation.
    Supports partial updates for progressive profiling.
    """

    user = UserBasicSerializer(read_only=True)
    completeness_percentage = serializers.IntegerField(read_only=True)
    onboarding_completed = serializers.BooleanField(read_only=True)
    onboarding_completed_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CreatorProfile
        fields = [
            # User relationship
            'user',

            # Required fields (onboarding)
            'main_platform',
            'niche',
            'experience_level',
            'primary_goal',
            'time_available',

            # Important fields (level 2)
            'specific_profession',
            'target_audience',
            'communication_tone',
            'expertise_areas',
            'preferred_duration',
            'complexity_level',
            'theme_diversity',
            'publication_frequency',

            # Optional fields (level 3)
            'instagram_username',
            'linkedin_url',
            'twitter_username',
            'tiktok_username',
            'revenue_stage',
            'team_size',
            'revenue_goal',
            'authority_goal',
            'leads_goal',
            'has_designer',
            'current_tools',
            'tools_budget',
            'preferred_hours',

            # Completion tracking
            'onboarding_completed',
            'completeness_percentage',
            'created_at',
            'updated_at',
            'onboarding_completed_at',
        ]

    def validate_niche(self, value):
        """Validate niche has minimum length."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Nicho deve ter pelo menos 3 caracteres."
            )
        return value.strip()

    def validate_theme_diversity(self, value):
        """Validate theme diversity is within range."""
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError(
                "Diversidade de temas deve estar entre 0 e 10."
            )
        return value

    def validate_expertise_areas(self, value):
        """Validate expertise areas is a list."""
        if value is not None and not isinstance(value, list):
            raise serializers.ValidationError(
                "Áreas de expertise deve ser uma lista."
            )
        return value

    def validate_current_tools(self, value):
        """Validate current tools is a list."""
        if value is not None and not isinstance(value, list):
            raise serializers.ValidationError(
                "Ferramentas atuais deve ser uma lista."
            )
        return value

    def validate_preferred_hours(self, value):
        """Validate preferred hours is a list."""
        if value is not None and not isinstance(value, list):
            raise serializers.ValidationError(
                "Horários preferenciais deve ser uma lista."
            )
        return value


class OnboardingSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for onboarding process.
    Only includes the 5 required fields for quick completion.
    """

    class Meta:
        model = CreatorProfile
        fields = [
            'main_platform',
            'niche',
            'experience_level',
            'primary_goal',
            'time_available',
        ]

    def validate_niche(self, value):
        """Validate niche has minimum length."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Nicho deve ter pelo menos 3 caracteres."
            )
        return value.strip()


class ProfileCompletionSerializer(serializers.Serializer):
    """
    Serializer for profile completion status response.
    Used to inform frontend about onboarding requirements.
    """

    onboarding_completed = serializers.BooleanField()
    completeness_percentage = serializers.IntegerField()
    required_fields_missing = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )
    total_fields = serializers.IntegerField()
    filled_fields = serializers.IntegerField()


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
    average_completeness = serializers.FloatField()
    most_common_platform = serializers.CharField()
    most_common_niche = serializers.CharField()
    completion_rate = serializers.FloatField()
