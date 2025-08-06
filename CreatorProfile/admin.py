from django.contrib import admin

from .models import CreatorProfile, UserBehavior


@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for CreatorProfile with simplified display and filtering.
    """

    list_display = [
        'user_display',
        'professional_name',
        'profession',
        'specialization',
        'onboarding_completed',
        'onboarding_skipped',
        'created_at',
    ]

    list_filter = [
        'onboarding_completed',
        'onboarding_skipped',
        'profession',
        'created_at',
    ]

    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'professional_name',
        'profession',
        'specialization',
    ]

    readonly_fields = [
        'user',
        'onboarding_completed',
        'onboarding_skipped',
        'onboarding_completed_at',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('Status do Onboarding', {
            'fields': (
                'onboarding_completed',
                'onboarding_skipped',
                'onboarding_completed_at',
            ),
            'classes': ('collapse',),
        }),
        ('Informações Profissionais', {
            'fields': (
                'professional_name',
                'profession',
                'specialization',
            )
        }),
        ('Redes Sociais', {
            'fields': (
                'linkedin_url',
                'instagram_username',
                'youtube_channel',
                'tiktok_username',
            ),
            'classes': ('collapse',),
        }),
        ('Brandbook - Cores', {
            'fields': (
                'primary_color',
                'secondary_color',
                'accent_color_1',
                'accent_color_2',
                'accent_color_3',
            ),
            'classes': ('collapse',),
        }),
        ('Brandbook - Tipografia', {
            'fields': (
                'primary_font',
                'secondary_font',
            ),
            'classes': ('collapse',),
        }),
    )

    def user_display(self, obj):
        """Display user name and email."""
        return f"{obj.user.get_full_name()} ({obj.user.email})"
    user_display.short_description = 'Usuário'

    def get_queryset(self, request):
        """Optimize queries by selecting related user."""
        return super().get_queryset(request).select_related('user')


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    """
    Admin interface for UserBehavior with analytics display.
    """

    list_display = [
        'user_display',
        'total_interactions',
        'avg_time_per_idea_display',
        'preferred_length',
        'usage_frequency',
        'last_activity',
    ]

    list_filter = [
        'preferred_length',
        'usage_frequency',
        'preferred_complexity',
        'last_activity',
        'created_at',
    ]

    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'preferred_topics',
    ]

    readonly_fields = [
        'user',
        'created_at',
        'updated_at',
        'last_activity',
    ]

    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('user', 'created_at', 'updated_at', 'last_activity')
        }),
        ('Padrões de Clique', {
            'fields': (
                'ideas_selected',
                'ideas_rejected',
                'avg_time_per_idea',
                'total_interactions',
            )
        }),
        ('Preferências Inferidas', {
            'fields': (
                'preferred_topics',
                'preferred_complexity',
                'preferred_length',
            )
        }),
        ('Padrões de Uso', {
            'fields': (
                'peak_hours',
                'usage_frequency',
                'avg_session_duration',
            )
        }),
    )

    def user_display(self, obj):
        """Display user name and email."""
        return f"{obj.user.get_full_name()} ({obj.user.email})"
    user_display.short_description = 'Usuário'

    def avg_time_per_idea_display(self, obj):
        """Display average time per idea in a readable format."""
        if obj.avg_time_per_idea:
            return f"{obj.avg_time_per_idea:.1f}s"
        return "N/A"
    avg_time_per_idea_display.short_description = 'Tempo Médio/Ideia'

    def get_queryset(self, request):
        """Optimize queries by selecting related user."""
        return super().get_queryset(request).select_related('user')


# Customize admin site headers
admin.site.site_header = "Sonora - Administração"
admin.site.site_title = "Sonora Admin"
admin.site.index_title = "Gestão de Perfis de Criadores"
