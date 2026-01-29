"""
Admin configuration for Social Media Integration app
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    InstagramAccount,
    InstagramConnectionAttempt,
    InstagramMetrics,
    InstagramNotification,
)


@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    """Admin for Instagram Account model"""

    list_display = [
        'username_display',
        'user_email',
        'account_type',
        'connection_status_badge',
        'followers_count',
        'last_synced_display',
        'expires_in_display',
        'is_active'
    ]

    list_filter = [
        'connection_status',
        'account_type',
        'is_active',
        'created_at'
    ]

    search_fields = [
        'username',
        'instagram_user_id',
        'user__email',
        'user__username'
    ]

    readonly_fields = [
        'instagram_user_id',
        'created_at',
        'updated_at',
        'connected_at',
        'last_synced_at'
    ]

    fieldsets = (
        ('Account Info', {
            'fields': (
                'user',
                'instagram_user_id',
                'username',
                'account_type',
                'profile_picture_url'
            )
        }),
        ('Metrics', {
            'fields': (
                'followers_count',
                'following_count',
                'media_count'
            )
        }),
        ('Connection', {
            'fields': (
                'connection_status',
                'is_active',
                'sync_error_message',
                'last_synced_at',
                'expires_at'
            )
        }),
        ('Tokens', {
            'fields': (
                'access_token',
                'token_type'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'connected_at',
                'created_at',
                'updated_at'
            )
        })
    )

    actions = ['refresh_tokens', 'mark_as_disconnected']

    def username_display(self, obj):
        """Display username with @ symbol"""
        return f"@{obj.username}"
    username_display.short_description = 'Instagram'

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'

    def connection_status_badge(self, obj):
        """Display connection status with color badge"""
        colors = {
            'connected': 'green',
            'disconnected': 'gray',
            'error': 'red',
            'token_expired': 'orange',
        }
        color = colors.get(obj.connection_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_connection_status_display()
        )
    connection_status_badge.short_description = 'Status'

    def last_synced_display(self, obj):
        """Display last sync time"""
        if obj.last_synced_at:
            from django.utils import timezone
            diff = timezone.now() - obj.last_synced_at
            if diff.days > 0:
                return f"{diff.days}d ago"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600}h ago"
            else:
                return f"{diff.seconds // 60}m ago"
        return "Never"
    last_synced_display.short_description = 'Last Sync'

    def expires_in_display(self, obj):
        """Display token expiration"""
        days = obj.days_until_expiration()
        if days is None:
            return "Unknown"
        elif days <= 0:
            return format_html('<span style="color: red;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        else:
            return f"{days} days"
    expires_in_display.short_description = 'Token Expires'

    def refresh_tokens(self, request, queryset):
        """Bulk refresh tokens"""
        from .services.token_refresh_service import TokenRefreshService

        refreshed = 0
        for account in queryset:
            if TokenRefreshService.refresh_token_if_needed(account):
                refreshed += 1

        self.message_user(
            request, f"{refreshed} tokens refreshed successfully")
    refresh_tokens.short_description = "Refresh selected tokens"

    def mark_as_disconnected(self, request, queryset):
        """Bulk disconnect accounts"""
        count = queryset.update(
            is_active=False, connection_status='disconnected')
        self.message_user(request, f"{count} accounts marked as disconnected")
    mark_as_disconnected.short_description = "Disconnect selected accounts"


@admin.register(InstagramMetrics)
class InstagramMetricsAdmin(admin.ModelAdmin):
    """Admin for Instagram Metrics model"""

    list_display = [
        'account_username',
        'date',
        'impressions',
        'reach',
        'engagement_display',
        'profile_views',
        'followers_count'
    ]

    list_filter = [
        'date',
        'account__username'
    ]

    search_fields = [
        'account__username',
        'account__user__email'
    ]

    readonly_fields = ['created_at']

    date_hierarchy = 'date'

    def account_username(self, obj):
        """Display account username"""
        return f"@{obj.account.username}"
    account_username.short_description = 'Account'

    def engagement_display(self, obj):
        """Display engagement with rate"""
        rate = obj.engagement_rate()
        return f"{obj.engagement} ({rate:.1f}%)"
    engagement_display.short_description = 'Engagement'


@admin.register(InstagramNotification)
class InstagramNotificationAdmin(admin.ModelAdmin):
    """Admin for Instagram Notification model"""

    list_display = [
        'user_email',
        'notification_type',
        'message_preview',
        'is_read',
        'created_at'
    ]

    list_filter = [
        'notification_type',
        'is_read',
        'created_at'
    ]

    search_fields = [
        'user__email',
        'message'
    ]

    readonly_fields = ['created_at', 'read_at']

    date_hierarchy = 'created_at'

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'

    def message_preview(self, obj):
        """Display message preview"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'


@admin.register(InstagramConnectionAttempt)
class InstagramConnectionAttemptAdmin(admin.ModelAdmin):
    """Admin for Instagram Connection Attempt model"""

    list_display = [
        'user_email',
        'step',
        'started_at',
        'completed_at',
        'duration_display',
        'has_error'
    ]

    list_filter = [
        'step',
        'started_at'
    ]

    search_fields = [
        'user__email',
        'error_message'
    ]

    readonly_fields = ['started_at']

    date_hierarchy = 'started_at'

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'

    def duration_display(self, obj):
        """Display duration"""
        if obj.duration_seconds:
            return f"{obj.duration_seconds}s"
        return "-"
    duration_display.short_description = 'Duration'

    def has_error(self, obj):
        """Check if has error"""
        return bool(obj.error_message)
    has_error.boolean = True
    has_error.short_description = 'Error?'
