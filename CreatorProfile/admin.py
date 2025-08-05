from django.contrib import admin
from django.utils.html import format_html

from .models import CreatorProfile, UserBehavior


@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for CreatorProfile with comprehensive display and filtering.
    """

    list_display = [
        'user_display',
        'niche',
        'main_platform',
        'experience_level',
        'primary_goal',
        'onboarding_completed',
        'completeness_display',
        'created_at',
    ]

    list_filter = [
        'onboarding_completed',
        'main_platform',
        'experience_level',
        'primary_goal',
        'communication_tone',
        'revenue_stage',
        'team_size',
        'created_at',
    ]

    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'niche',
        'specific_profession',
        'target_audience',
    ]

    readonly_fields = [
        'user',
        'completeness_percentage',
        'onboarding_completed',
        'onboarding_completed_at',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('Status de Completude', {
            'fields': (
                'onboarding_completed',
                'onboarding_completed_at',
                'completeness_percentage',
            ),
            'classes': ('collapse',),
        }),
        ('Campos Obrigatórios (Onboarding)', {
            'fields': (
                'main_platform',
                'niche',
                'experience_level',
                'primary_goal',
                'time_available',
            )
        }),
        ('Contexto Profissional (Nível 2)', {
            'fields': (
                'specific_profession',
                'target_audience',
                'communication_tone',
                'expertise_areas',
            ),
            'classes': ('collapse',),
        }),
        ('Preferências de Conteúdo (Nível 2)', {
            'fields': (
                'preferred_duration',
                'complexity_level',
                'theme_diversity',
                'publication_frequency',
            ),
            'classes': ('collapse',),
        }),
        ('Redes Sociais (Nível 3)', {
            'fields': (
                'instagram_username',
                'linkedin_url',
                'twitter_username',
                'tiktok_username',
            ),
            'classes': ('collapse',),
        }),
        ('Contexto de Negócio (Nível 3)', {
            'fields': (
                'revenue_stage',
                'team_size',
                'revenue_goal',
                'authority_goal',
                'leads_goal',
            ),
            'classes': ('collapse',),
        }),
        ('Recursos Disponíveis (Nível 3)', {
            'fields': (
                'has_designer',
                'current_tools',
                'tools_budget',
                'preferred_hours',
            ),
            'classes': ('collapse',),
        }),
    )

    def user_display(self, obj):
        """Display user name and email."""
        return f"{obj.user.get_full_name()} ({obj.user.email})"
    user_display.short_description = 'Usuário'

    def completeness_display(self, obj):
        """Display completeness percentage with color coding."""
        percentage = obj.completeness_percentage
        if percentage >= 80:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} %</span>',
            color,
            percentage
        )
    completeness_display.short_description = 'Completude'

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
