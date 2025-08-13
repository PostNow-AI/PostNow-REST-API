from django.contrib import admin

from .models import Campaign, CampaignIdea


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status',
                    'objectives', 'platforms', 'created_at']
    list_filter = ['status', 'voice_tone', 'created_at']
    search_fields = ['title', 'description', 'user__email']
    readonly_fields = ['created_at', 'updated_at',
                       'ideas_count', 'approved_ideas_count']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'title', 'description', 'status')
        }),
        ('Objetivos e Persona', {
            'fields': ('objectives', 'persona_age', 'persona_location', 'persona_income',
                       'persona_interests', 'persona_behavior', 'persona_pain_points')
        }),
        ('Plataformas e Conteúdo', {
            'fields': ('platforms', 'content_types')
        }),
        ('Tom de Voz e Detalhes', {
            'fields': ('voice_tone', 'product_description', 'value_proposition', 'campaign_urgency')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at', 'ideas_count', 'approved_ideas_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CampaignIdea)
class CampaignIdeaAdmin(admin.ModelAdmin):
    list_display = ['title', 'campaign', 'platform',
                    'content_type', 'variation_type', 'status', 'generated_at']
    list_filter = ['status', 'platform', 'content_type',
                   'variation_type', 'generated_at']
    search_fields = ['title', 'description', 'campaign__title']
    readonly_fields = ['generated_at', 'updated_at']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('campaign', 'title', 'description', 'content', 'status')
        }),
        ('Plataforma e Tipo', {
            'fields': ('platform', 'content_type', 'variation_type')
        }),
        ('Conteúdo Detalhado', {
            'fields': ('headline', 'copy', 'cta', 'hashtags', 'visual_description', 'color_composition'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('generated_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
