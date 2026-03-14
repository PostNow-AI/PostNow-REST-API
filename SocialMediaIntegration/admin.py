"""
Admin configuration for SocialMediaIntegration models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    InstagramAccount,
    PublishingLog,
    ScheduledPost,
)


@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    """Admin for Instagram Account management."""

    list_display = [
        'instagram_username',
        'user_email',
        'status_badge',
        'token_status',
        'last_sync_at',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['instagram_username', 'user__email', 'instagram_name']
    readonly_fields = [
        'instagram_user_id',
        'created_at',
        'updated_at',
        'token_expires_at',
        'last_sync_at',
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Instagram Info', {
            'fields': (
                'user',
                'instagram_user_id',
                'instagram_username',
                'instagram_name',
                'profile_picture_url',
            )
        }),
        ('Facebook Page', {
            'fields': (
                'facebook_page_id',
                'facebook_page_name',
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'last_error',
                'last_sync_at',
            )
        }),
        ('Token Info', {
            'fields': (
                'token_expires_at',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def status_badge(self, obj):
        colors = {
            'connected': 'green',
            'disconnected': 'gray',
            'token_expired': 'orange',
            'error': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def token_status(self, obj):
        if obj.is_token_valid:
            days = obj.days_until_expiration
            if days > 30:
                color = 'green'
            elif days > 7:
                color = 'orange'
            else:
                color = 'red'
            return format_html(
                '<span style="color: {};">{} dias</span>',
                color,
                days
            )
        return format_html(
            '<span style="color: red;">Expirado</span>'
        )
    token_status.short_description = 'Token'


class PublishingLogInline(admin.TabularInline):
    """Inline admin for publishing logs."""
    model = PublishingLog
    extra = 0
    readonly_fields = [
        'attempt_number',
        'status',
        'started_at',
        'completed_at',
        'duration_ms',
        'step',
        'error_message',
    ]
    can_delete = False
    ordering = ['-started_at']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    """Admin for Scheduled Post management."""

    list_display = [
        'id',
        'caption_preview_display',
        'instagram_account_display',
        'media_type',
        'status_badge',
        'scheduled_for',
        'retry_info',
        'created_at',
    ]
    list_filter = ['status', 'media_type', 'scheduled_for', 'created_at']
    search_fields = [
        'caption',
        'user__email',
        'instagram_account__instagram_username',
    ]
    readonly_fields = [
        'instagram_container_id',
        'instagram_media_id',
        'instagram_permalink',
        'published_at',
        'retry_count',
        'next_retry_at',
        'created_at',
        'updated_at',
    ]
    ordering = ['-scheduled_for']
    date_hierarchy = 'scheduled_for'
    inlines = [PublishingLogInline]

    fieldsets = (
        ('Post Info', {
            'fields': (
                'user',
                'instagram_account',
                'post_idea',
            )
        }),
        ('Content', {
            'fields': (
                'caption',
                'media_type',
                'media_urls',
            )
        }),
        ('Scheduling', {
            'fields': (
                'scheduled_for',
                'timezone',
                'status',
            )
        }),
        ('Publishing Result', {
            'fields': (
                'instagram_container_id',
                'instagram_media_id',
                'instagram_permalink',
                'published_at',
            ),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': (
                'retry_count',
                'max_retries',
                'next_retry_at',
                'last_error',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def caption_preview_display(self, obj):
        return obj.caption_preview
    caption_preview_display.short_description = 'Caption'

    def instagram_account_display(self, obj):
        return f"@{obj.instagram_account.instagram_username}"
    instagram_account_display.short_description = 'Account'

    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'scheduled': 'blue',
            'publishing': 'orange',
            'published': 'green',
            'failed': 'red',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def retry_info(self, obj):
        if obj.status == 'failed' and obj.can_retry:
            return format_html(
                '<span style="color: orange;">{}/{}</span>',
                obj.retry_count,
                obj.max_retries
            )
        elif obj.retry_count > 0:
            return f"{obj.retry_count}/{obj.max_retries}"
        return '-'
    retry_info.short_description = 'Retries'

    actions = ['cancel_posts', 'retry_posts']

    @admin.action(description='Cancel selected posts')
    def cancel_posts(self, request, queryset):
        count = queryset.filter(
            status__in=['draft', 'scheduled', 'failed']
        ).update(status='cancelled')
        self.message_user(request, f'{count} posts cancelled.')

    @admin.action(description='Retry failed posts')
    def retry_posts(self, request, queryset):
        count = 0
        for post in queryset.filter(status='failed'):
            if post.can_retry:
                post.status = 'scheduled'
                post.save(update_fields=['status', 'updated_at'])
                count += 1
        self.message_user(request, f'{count} posts scheduled for retry.')


@admin.register(PublishingLog)
class PublishingLogAdmin(admin.ModelAdmin):
    """Admin for Publishing Log viewing."""

    list_display = [
        'id',
        'scheduled_post_id',
        'attempt_number',
        'status_badge',
        'step',
        'duration_display',
        'started_at',
    ]
    list_filter = ['status', 'step', 'started_at']
    search_fields = ['scheduled_post__id', 'error_message']
    readonly_fields = [
        'scheduled_post',
        'attempt_number',
        'status',
        'started_at',
        'completed_at',
        'duration_ms',
        'api_endpoint',
        'request_data',
        'response_data',
        'error_code',
        'error_message',
        'error_details',
        'step',
    ]
    ordering = ['-started_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def status_badge(self, obj):
        colors = {
            'started': 'blue',
            'container_created': 'blue',
            'processing': 'orange',
            'success': 'green',
            'error': 'red',
            'retry': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def duration_display(self, obj):
        if obj.duration_ms:
            if obj.duration_ms < 1000:
                return f"{obj.duration_ms}ms"
            return f"{obj.duration_ms / 1000:.2f}s"
        return '-'
    duration_display.short_description = 'Duration'
