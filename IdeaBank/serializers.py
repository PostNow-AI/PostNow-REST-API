from rest_framework import serializers

from .models import (
    Campaign,
    CampaignIdea,
    CampaignObjective,
    IdeaGenerationConfig,
    SocialPlatform,
    VoiceTone,
)


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for campaigns."""
    ideas_count = serializers.ReadOnlyField()
    approved_ideas_count = serializers.ReadOnlyField()
    platform_display = serializers.SerializerMethodField()
    voice_tone_display = serializers.CharField(
        source='get_voice_tone_display', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'description', 'objectives', 'persona_age',
            'persona_location', 'persona_income', 'persona_interests',
            'persona_behavior', 'persona_pain_points', 'platforms',
            'platform_display', 'content_types', 'voice_tone', 'voice_tone_display',
            'product_description', 'value_proposition', 'campaign_urgency',
            'status', 'status_display', 'ideas_count', 'approved_ideas_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ideas_count',
                            'approved_ideas_count', 'created_at', 'updated_at']

    def get_platform_display(self, obj):
        """Get platform display names."""
        return [dict(SocialPlatform.choices).get(platform, platform) for platform in obj.platforms]


class CampaignDetailSerializer(CampaignSerializer):
    """Detailed campaign serializer with ideas."""
    ideas = serializers.SerializerMethodField()

    class Meta(CampaignSerializer.Meta):
        fields = CampaignSerializer.Meta.fields + ['ideas']

    def get_ideas(self, obj):
        """Get ideas grouped by platform and content type."""
        ideas = obj.ideas.all().order_by('platform', 'content_type', 'variation_type')
        return CampaignIdeaSerializer(ideas, many=True).data


class CampaignIdeaSerializer(serializers.ModelSerializer):
    """Serializer for campaign ideas."""
    platform_display = serializers.CharField(
        source='get_platform_display', read_only=True)
    content_type_display = serializers.CharField(
        source='get_content_type_display', read_only=True)
    variation_type_display = serializers.CharField(
        source='get_variation_type_display', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    def to_representation(self, instance):
        """Custom representation with debug logging."""
        data = super().to_representation(instance)

        # Debug logging for content field
        if 'content' in data:
            print("=== DEBUG: Serializer content ===")
            print(f"Content type: {type(data['content'])}")
            print(f"Content value: {data['content'][:200]}...")
            print(f"Content length: {len(str(data['content']))}")

        return data

    class Meta:
        model = CampaignIdea
        fields = [
            'id', 'title', 'description', 'content', 'platform',
            'platform_display', 'content_type', 'content_type_display',
            'variation_type', 'variation_type_display', 'headline', 'copy',
            'cta', 'hashtags', 'visual_description', 'color_composition',
            'status', 'status_display', 'generated_at', 'updated_at'
        ]
        read_only_fields = ['id', 'generated_at', 'updated_at']


class CampaignIdeaUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating campaign ideas."""

    class Meta:
        model = CampaignIdea
        fields = ['title', 'description', 'content', 'status']


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating campaigns."""

    class Meta:
        model = Campaign
        fields = [
            'title', 'description', 'objectives', 'persona_age',
            'persona_location', 'persona_income', 'persona_interests',
            'persona_behavior', 'persona_pain_points', 'platforms',
            'content_types', 'voice_tone', 'product_description',
            'value_proposition', 'campaign_urgency'
        ]


class IdeaGenerationRequestSerializer(serializers.Serializer):
    """Serializer for AI idea generation requests."""

    # Campaign details
    title = serializers.CharField(
        max_length=200, required=False, allow_blank=True)
    objectives = serializers.ListField(
        child=serializers.ChoiceField(choices=CampaignObjective.choices),
        required=True
    )
    platforms = serializers.ListField(
        child=serializers.ChoiceField(choices=SocialPlatform.choices),
        required=True
    )
    content_types = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        required=False
    )

    # Product/service details
    product_description = serializers.CharField(
        required=False, allow_blank=True)
    value_proposition = serializers.CharField(required=False, allow_blank=True)
    campaign_urgency = serializers.CharField(required=False, allow_blank=True)

    # Voice and style
    voice_tone = serializers.ChoiceField(
        choices=VoiceTone.choices,
        default='professional'
    )

    # Persona details
    persona_age = serializers.CharField(required=False, allow_blank=True)
    persona_location = serializers.CharField(required=False, allow_blank=True)
    persona_income = serializers.CharField(required=False, allow_blank=True)
    persona_interests = serializers.CharField(required=False, allow_blank=True)
    persona_behavior = serializers.CharField(required=False, allow_blank=True)
    persona_pain_points = serializers.CharField(
        required=False, allow_blank=True)

    # AI model preferences
    preferred_provider = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default='google',
        help_text="Preferred AI provider (e.g., 'Google', 'OpenAI', 'Anthropic')"
    )
    preferred_model = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default='',
        help_text="Specific AI model name (e.g., 'gemini-1.5-flash', 'gpt-4')"
    )

    # Optional fields

    def validate(self, data):
        """Validate the request data."""
        # Ensure at least one platform is selected
        if not data.get('platforms'):
            raise serializers.ValidationError(
                "At least one platform must be selected.")

        # Ensure at least one objective is selected
        if not data.get('objectives'):
            raise serializers.ValidationError(
                "At least one objective must be selected.")

        # Validate content types if provided
        platforms = data.get('platforms', [])
        content_types = data.get('content_types', {})

        for platform in platforms:
            if platform in content_types and not content_types[platform]:
                raise serializers.ValidationError(
                    f"Content types for {platform} cannot be empty if specified."
                )

        return data


class IdeaGenerationResponseSerializer(serializers.Serializer):
    """Serializer for idea generation responses."""
    campaign = CampaignSerializer()
    ideas = CampaignIdeaSerializer(many=True)


# Legacy serializers for backward compatibility
class IdeaGenerationConfigSerializer(serializers.ModelSerializer):
    """Legacy serializer for idea generation configuration."""

    class Meta:
        model = IdeaGenerationConfig
        fields = [
            'id', 'objectives', 'persona_age', 'persona_location',
            'persona_income', 'persona_interests', 'persona_behavior',
            'persona_pain_points', 'platforms', 'content_types',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LegacyIdeaGenerationResponseSerializer(serializers.Serializer):
    """Legacy serializer for idea generation responses."""
    ideas = CampaignIdeaSerializer(many=True)
    config = IdeaGenerationConfigSerializer()
