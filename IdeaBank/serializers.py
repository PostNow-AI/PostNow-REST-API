from rest_framework import serializers

from .models import (
    CampaignIdea,
    CampaignObjective,
    ContentType,
    IdeaGenerationConfig,
    SocialPlatform,
)


class IdeaGenerationConfigSerializer(serializers.ModelSerializer):
    """Serializer for idea generation configuration."""

    class Meta:
        model = IdeaGenerationConfig
        fields = [
            'id', 'objectives', 'persona_age', 'persona_location',
            'persona_income', 'persona_interests', 'persona_behavior',
            'persona_pain_points', 'platforms', 'content_types',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CampaignIdeaSerializer(serializers.ModelSerializer):
    """Serializer for campaign ideas."""
    config = IdeaGenerationConfigSerializer(read_only=True)
    platform_display = serializers.CharField(
        source='get_platform_display', read_only=True)
    content_type_display = serializers.CharField(
        source='get_content_type_display', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = CampaignIdea
        fields = [
            'id', 'title', 'description', 'content', 'platform',
            'platform_display', 'content_type', 'content_type_display',
            'status', 'status_display', 'config', 'generated_at', 'updated_at'
        ]
        read_only_fields = ['id', 'generated_at', 'updated_at']


class IdeaGenerationRequestSerializer(serializers.Serializer):
    """Serializer for idea generation requests."""
    objectives = serializers.ListField(
        child=serializers.ChoiceField(choices=CampaignObjective.choices),
        required=True
    )
    persona_age = serializers.CharField(
        max_length=50, required=False, allow_blank=True)
    persona_location = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    persona_income = serializers.CharField(
        max_length=50, required=False, allow_blank=True)
    persona_interests = serializers.CharField(required=False, allow_blank=True)
    persona_behavior = serializers.CharField(required=False, allow_blank=True)
    persona_pain_points = serializers.CharField(
        required=False, allow_blank=True)
    platforms = serializers.ListField(
        child=serializers.ChoiceField(choices=SocialPlatform.choices),
        required=True
    )
    content_types = serializers.DictField(
        child=serializers.ListField(
            child=serializers.ChoiceField(choices=ContentType.choices)
        ),
        required=True
    )


class IdeaGenerationResponseSerializer(serializers.Serializer):
    """Serializer for idea generation responses."""
    ideas = CampaignIdeaSerializer(many=True)
    config = IdeaGenerationConfigSerializer()


class CampaignIdeaUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating campaign ideas."""

    class Meta:
        model = CampaignIdea
        fields = ['title', 'description', 'content', 'status']
