"""
Serializers for Social Media Integration app
"""

from rest_framework import serializers

from .models import (
    InstagramAccount,
    InstagramConnectionAttempt,
    InstagramMetrics,
    InstagramNotification,
)

# Error messages in Portuguese
ERROR_MESSAGES = {
    'invalid_account_type': (
        'Sua conta Instagram precisa ser Business ou Creator. '
        'Veja como converter: /docs/instagram-business-setup'
    ),
    'facebook_page_required': (
        'Conecte uma Facebook Page ao seu Instagram primeiro. '
        'Tutorial: /docs/facebook-page-setup'
    ),
    'rate_limit_exceeded': (
        'Muitas atualizações recentes. '
        'Próxima sincronização disponível em {minutes} minutos.'
    ),
    'token_expired': (
        'Sua conexão com o Instagram expirou. '
        'Reconecte para continuar vendo insights.'
    ),
    'instagram_api_error': (
        'Instagram temporariamente indisponível. '
        'Tente novamente em alguns minutos.'
    ),
}


class InstagramAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for InstagramAccount model.
    Handles display and validation of Instagram account connections.
    """

    username_display = serializers.CharField(
        source='username',
        read_only=True
    )

    connection_status_display = serializers.CharField(
        source='get_connection_status_display',
        read_only=True
    )

    account_type_display = serializers.CharField(
        source='get_account_type_display',
        read_only=True
    )

    days_until_expiration = serializers.SerializerMethodField()
    is_token_expiring_soon = serializers.SerializerMethodField()

    # Don't expose the actual token
    access_token = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = InstagramAccount
        fields = [
            'id',
            'instagram_user_id',
            'username',
            'username_display',
            'account_type',
            'account_type_display',
            'profile_picture_url',
            'followers_count',
            'following_count',
            'media_count',
            'connection_status',
            'connection_status_display',
            'is_active',
            'sync_error_message',
            'last_synced_at',
            'connected_at',
            'expires_at',
            'days_until_expiration',
            'is_token_expiring_soon',
            'access_token',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'instagram_user_id',
            'connection_status',
            'sync_error_message',
            'last_synced_at',
            'connected_at',
            'created_at',
            'updated_at',
        ]

    def get_days_until_expiration(self, obj):
        """Get days until token expires"""
        return obj.days_until_expiration()

    def get_is_token_expiring_soon(self, obj):
        """Check if token expires soon (< 7 days)"""
        return obj.is_token_expiring_soon()

    def validate_account_type(self, value):
        """Validate that account is Business or Creator"""
        if value == 'PERSONAL':
            raise serializers.ValidationError(
                ERROR_MESSAGES['invalid_account_type'])
        return value


class InstagramAccountStatusSerializer(serializers.Serializer):
    """
    Serializer for Instagram account connection status.
    Used for the status endpoint to show connection state.
    """

    is_connected = serializers.BooleanField()
    connection_status = serializers.CharField(required=False)
    account_info = InstagramAccountSerializer(required=False, allow_null=True)
    last_sync = serializers.DateTimeField(required=False, allow_null=True)
    next_sync_available = serializers.DateTimeField(
        required=False, allow_null=True)
    expires_in_days = serializers.IntegerField(required=False, allow_null=True)
    has_errors = serializers.BooleanField()
    error_message = serializers.CharField(required=False, allow_null=True)


class InstagramMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for Instagram metrics/insights data.
    """

    engagement_rate = serializers.SerializerMethodField()
    account_username = serializers.CharField(
        source='account.username',
        read_only=True
    )

    class Meta:
        model = InstagramMetrics
        fields = [
            'id',
            'account',
            'account_username',
            'date',
            'impressions',
            'reach',
            'engagement',
            'engagement_rate',
            'profile_views',
            'followers_count',
            'media_count',
            'raw_metrics',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_engagement_rate(self, obj):
        """Calculate and return engagement rate"""
        return round(obj.engagement_rate(), 2)


class InstagramMetricsTimelineSerializer(serializers.Serializer):
    """
    Serializer for metrics timeline data (for charts).
    """

    date = serializers.DateField()
    impressions = serializers.IntegerField()
    reach = serializers.IntegerField()
    engagement = serializers.IntegerField()
    engagement_rate = serializers.FloatField()
    profile_views = serializers.IntegerField()
    followers_count = serializers.IntegerField()


class InstagramNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Instagram notifications.
    """

    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )

    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = InstagramNotification
        fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'message',
            'action_url',
            'is_read',
            'created_at',
            'read_at',
            'time_ago',
        ]
        read_only_fields = ['id', 'created_at', 'read_at']

    def get_time_ago(self, obj):
        """Get human-readable time since notification"""
        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()
        diff = now - obj.created_at

        if diff < timedelta(minutes=1):
            return 'agora mesmo'
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f'há {minutes} minuto{"s" if minutes > 1 else ""}'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f'há {hours} hora{"s" if hours > 1 else ""}'
        elif diff < timedelta(days=7):
            days = diff.days
            return f'há {days} dia{"s" if days > 1 else ""}'
        else:
            return obj.created_at.strftime('%d/%m/%Y')


class InstagramConnectionAttemptSerializer(serializers.ModelSerializer):
    """
    Serializer for connection attempt tracking.
    """

    step_display = serializers.CharField(
        source='get_step_display',
        read_only=True
    )

    class Meta:
        model = InstagramConnectionAttempt
        fields = [
            'id',
            'user',
            'step',
            'step_display',
            'error_message',
            'user_agent',
            'ip_address',
            'started_at',
            'completed_at',
            'duration_seconds',
        ]
        read_only_fields = ['id', 'started_at']


class InstagramConnectRequestSerializer(serializers.Serializer):
    """
    Serializer for initiating Instagram connection.
    """
    pass  # No input needed, just generates URL


class InstagramCallbackSerializer(serializers.Serializer):
    """
    Serializer for Instagram OAuth callback.
    """

    code = serializers.CharField(
        required=True,
        help_text="Authorization code from Instagram"
    )

    state = serializers.CharField(
        required=True,
        help_text="State token for CSRF protection"
    )


class InstagramSyncRequestSerializer(serializers.Serializer):
    """
    Serializer for manual sync request.
    """

    account_id = serializers.IntegerField(
        required=True,
        help_text="ID of the Instagram account to sync"
    )
