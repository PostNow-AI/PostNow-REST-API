"""
Scheduled Post Serializers

Serializers for scheduled posts and publishing logs.
"""

from django.utils import timezone
from rest_framework import serializers

from IdeaBank.serializers import PostIdeaSerializer

from ..models import (
    InstagramAccount,
    MediaType,
    PublishingLog,
    ScheduledPost,
    ScheduledPostStatus,
)
from .instagram_account_serializers import InstagramAccountListSerializer


class PublishingLogSerializer(serializers.ModelSerializer):
    """Serializer for publishing log entries."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = PublishingLog
        fields = [
            'id',
            'attempt_number',
            'status',
            'status_display',
            'started_at',
            'completed_at',
            'duration_ms',
            'step',
            'error_code',
            'error_message',
        ]
        read_only_fields = fields


class ScheduledPostSerializer(serializers.ModelSerializer):
    """Base serializer for ScheduledPost."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    media_type_display = serializers.CharField(
        source='get_media_type_display',
        read_only=True
    )
    caption_preview = serializers.CharField(read_only=True)
    is_ready_to_publish = serializers.BooleanField(read_only=True)
    can_retry = serializers.BooleanField(read_only=True)

    class Meta:
        model = ScheduledPost
        fields = [
            'id',
            'caption',
            'caption_preview',
            'media_type',
            'media_type_display',
            'media_urls',
            'scheduled_for',
            'timezone',
            'status',
            'status_display',
            'instagram_media_id',
            'instagram_permalink',
            'published_at',
            'retry_count',
            'max_retries',
            'last_error',
            'is_ready_to_publish',
            'can_retry',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'instagram_media_id',
            'instagram_permalink',
            'published_at',
            'retry_count',
            'last_error',
            'created_at',
            'updated_at',
        ]


class ScheduledPostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating scheduled posts."""

    instagram_account_id = serializers.IntegerField(write_only=True)
    post_idea_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = ScheduledPost
        fields = [
            'instagram_account_id',
            'post_idea_id',
            'caption',
            'media_type',
            'media_urls',
            'scheduled_for',
            'timezone',
        ]

    def validate_instagram_account_id(self, value):
        """Validate Instagram account exists and belongs to user."""
        user = self.context['request'].user
        try:
            account = InstagramAccount.objects.get(
                id=value,
                user=user,
                status='connected'
            )
            if not account.is_token_valid:
                raise serializers.ValidationError(
                    "O token da conta Instagram expirou. "
                    "Por favor, reconecte sua conta."
                )
            return value
        except InstagramAccount.DoesNotExist:
            raise serializers.ValidationError(
                "Conta Instagram não encontrada ou não conectada."
            )

    def validate_caption(self, value):
        """Validate caption length (Instagram limit: 2200 chars)."""
        if len(value) > 2200:
            raise serializers.ValidationError(
                f"A legenda deve ter no máximo 2200 caracteres. "
                f"Atual: {len(value)}"
            )
        return value

    def validate_media_urls(self, value):
        """Validate media URLs."""
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "Pelo menos uma URL de mídia é obrigatória."
            )
        if len(value) > 10:
            raise serializers.ValidationError(
                "O carrossel permite no máximo 10 itens."
            )
        return value

    def validate_scheduled_for(self, value):
        """Validate scheduled_for is in the future."""
        now = timezone.now()
        # Allow a 5-minute buffer for form submission delay
        min_time = now - timezone.timedelta(minutes=5)
        if value < min_time:
            raise serializers.ValidationError(
                "A data de agendamento deve estar no futuro."
            )
        return value

    def validate(self, data):
        """Cross-field validation."""
        media_type = data.get('media_type', MediaType.IMAGE)
        media_urls = data.get('media_urls', [])

        # Validate carousel has multiple items
        if media_type == MediaType.CAROUSEL and len(media_urls) < 2:
            raise serializers.ValidationError({
                'media_urls': "O carrossel precisa de pelo menos 2 itens."
            })

        # Validate single media for non-carousel
        if media_type != MediaType.CAROUSEL and len(media_urls) > 1:
            raise serializers.ValidationError({
                'media_urls': f"{media_type} aceita apenas 1 mídia."
            })

        return data

    def create(self, validated_data):
        """Create scheduled post."""
        user = self.context['request'].user
        account_id = validated_data.pop('instagram_account_id')
        post_idea_id = validated_data.pop('post_idea_id', None)

        account = InstagramAccount.objects.get(id=account_id)

        scheduled_post = ScheduledPost.objects.create(
            user=user,
            instagram_account=account,
            post_idea_id=post_idea_id,
            status=ScheduledPostStatus.SCHEDULED,
            **validated_data
        )

        return scheduled_post


class ScheduledPostListSerializer(serializers.ModelSerializer):
    """Serializer for listing scheduled posts."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    media_type_display = serializers.CharField(
        source='get_media_type_display',
        read_only=True
    )
    caption_preview = serializers.CharField(read_only=True)
    instagram_username = serializers.CharField(
        source='instagram_account.instagram_username',
        read_only=True
    )
    profile_picture_url = serializers.URLField(
        source='instagram_account.profile_picture_url',
        read_only=True
    )

    class Meta:
        model = ScheduledPost
        fields = [
            'id',
            'caption_preview',
            'media_type',
            'media_type_display',
            'media_urls',
            'scheduled_for',
            'status',
            'status_display',
            'instagram_username',
            'profile_picture_url',
            'instagram_permalink',
            'published_at',
            'created_at',
        ]


class ScheduledPostDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single scheduled post."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    media_type_display = serializers.CharField(
        source='get_media_type_display',
        read_only=True
    )
    caption_preview = serializers.CharField(read_only=True)
    is_ready_to_publish = serializers.BooleanField(read_only=True)
    can_retry = serializers.BooleanField(read_only=True)

    instagram_account = InstagramAccountListSerializer(read_only=True)
    post_idea = PostIdeaSerializer(read_only=True)
    publishing_logs = PublishingLogSerializer(many=True, read_only=True)

    class Meta:
        model = ScheduledPost
        fields = [
            'id',
            'instagram_account',
            'post_idea',
            'caption',
            'caption_preview',
            'media_type',
            'media_type_display',
            'media_urls',
            'scheduled_for',
            'timezone',
            'status',
            'status_display',
            'instagram_container_id',
            'instagram_media_id',
            'instagram_permalink',
            'published_at',
            'retry_count',
            'max_retries',
            'next_retry_at',
            'last_error',
            'is_ready_to_publish',
            'can_retry',
            'publishing_logs',
            'created_at',
            'updated_at',
        ]


class ScheduledPostUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating scheduled posts."""

    class Meta:
        model = ScheduledPost
        fields = [
            'caption',
            'media_type',
            'media_urls',
            'scheduled_for',
            'timezone',
        ]

    def validate_caption(self, value):
        """Validate caption length."""
        if len(value) > 2200:
            raise serializers.ValidationError(
                f"A legenda deve ter no máximo 2200 caracteres. "
                f"Atual: {len(value)}"
            )
        return value

    def validate(self, data):
        """Validate post can be updated."""
        instance = self.instance
        if instance and instance.status not in ['draft', 'scheduled', 'failed']:
            raise serializers.ValidationError(
                "Apenas posts em rascunho, agendados ou com falha "
                "podem ser editados."
            )
        return data


class CalendarEventSerializer(serializers.Serializer):
    """Serializer for calendar events."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    media_type = serializers.CharField()
    instagram_username = serializers.CharField()
    thumbnail_url = serializers.URLField(allow_null=True)
