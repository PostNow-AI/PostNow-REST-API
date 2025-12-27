"""
Django Admin configuration for Campaigns app.
"""

from django.contrib import admin
from .models import (
    Campaign,
    CampaignPost,
    CampaignDraft,
    VisualStyle,
    CampaignTemplate,
    CampaignJourneyEvent,
)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'user', 'type', 'structure', 'status',
        'post_count', 'posts_approved_count', 'created_at'
    ]
    list_filter = ['type', 'structure', 'status', 'created_at']
    search_fields = ['name', 'user__username', 'user__email', 'objective']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'name', 'type', 'objective', 'main_message')
        }),
        ('Estrutura', {
            'fields': ('structure', 'duration_days', 'post_count', 'post_frequency')
        }),
        ('Datas', {
            'fields': ('start_date', 'end_date')
        }),
        ('Configurações', {
            'fields': ('visual_styles', 'content_mix', 'briefing_data', 'generation_context')
        }),
        ('Status', {
            'fields': ('status', 'is_auto_generated')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'approved_at', 'completed_at')
        }),
    )
    
    def posts_approved_count(self, obj):
        return f"{obj.posts_approved_count}/{obj.post_count}"
    posts_approved_count.short_description = 'Posts Aprovados'


@admin.register(CampaignPost)
class CampaignPostAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'campaign', 'sequence_order', 'post', 'phase',
        'scheduled_date', 'is_approved', 'is_published'
    ]
    list_filter = ['is_approved', 'is_published', 'phase', 'scheduled_date']
    search_fields = ['campaign__name', 'post__name', 'theme']
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'published_at']
    
    fieldsets = (
        ('Relacionamentos', {
            'fields': ('campaign', 'post')
        }),
        ('Posição', {
            'fields': ('sequence_order', 'scheduled_date', 'scheduled_time')
        }),
        ('Contexto', {
            'fields': ('phase', 'theme', 'visual_style')
        }),
        ('Status', {
            'fields': ('is_approved', 'approved_at', 'is_published', 'published_at')
        }),
        ('Instagram', {
            'fields': ('instagram_media_id', 'instagram_container_id')
        }),
    )


@admin.register(CampaignDraft)
class CampaignDraftAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'current_phase', 'status',
        'interaction_count', 'updated_at'
    ]
    list_filter = ['status', 'current_phase', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user', 'status')
        }),
        ('Progresso', {
            'fields': ('current_phase', 'completed_campaign')
        }),
        ('Estado Salvo', {
            'fields': (
                'briefing_data', 'structure_chosen', 'styles_chosen',
                'duration_days', 'post_count', 'posts_data'
            )
        }),
        ('Tracking', {
            'fields': ('total_time_spent', 'interaction_count', 'hesitation_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(VisualStyle)
class VisualStyleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'global_success_rate',
        'is_active', 'sort_order'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description', 'tags']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'category', 'description', 'tags')
        }),
        ('Performance', {
            'fields': ('global_success_rate', 'success_rate_by_niche')
        }),
        ('Configuração Técnica', {
            'fields': ('image_prompt_modifiers', 'preview_image_url')
        }),
        ('Recomendações', {
            'fields': ('best_for_campaign_types', 'best_for_niches')
        }),
        ('Status', {
            'fields': ('is_active', 'sort_order')
        }),
    )


@admin.register(CampaignTemplate)
class CampaignTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'user', 'campaign_type', 'structure',
        'times_used', 'avg_approval_rate', 'created_at'
    ]
    list_filter = ['campaign_type', 'structure', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'times_used']


@admin.register(CampaignJourneyEvent)
class CampaignJourneyEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'campaign_draft', 'event_type',
        'phase', 'timestamp'
    ]
    list_filter = ['event_type', 'phase', 'timestamp']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['timestamp']
