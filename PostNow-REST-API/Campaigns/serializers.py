"""
Serializers para o app Campaigns.
Seguindo padrão de IdeaBank: List, Create, WithNested, Request validators.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    Campaign,
    CampaignPost,
    CampaignDraft,
    VisualStyle,
    CampaignTemplate,
)
from IdeaBank.serializers import PostSerializer, PostIdeaSerializer

User = get_user_model()


# ============================================================================
# CAMPAIGN SERIALIZERS
# ============================================================================

class CampaignSerializer(serializers.ModelSerializer):
    """Serializer para listagem de campanhas."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    structure_display = serializers.CharField(source='get_structure_display', read_only=True)
    
    posts_count = serializers.SerializerMethodField()
    posts_approved_count = serializers.SerializerMethodField()
    is_fully_approved = serializers.ReadOnlyField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'type', 'type_display', 'objective', 'main_message',
            'structure', 'structure_display', 'duration_days', 'post_count', 'post_frequency',
            'start_date', 'end_date', 'visual_styles', 'content_mix',
            'status', 'status_display', 'is_auto_generated',
            'posts_count', 'posts_approved_count', 'is_fully_approved',
            'created_at', 'updated_at', 'approved_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved_at', 'completed_at']
    
    def get_posts_count(self, obj):
        return obj.campaign_posts.count()
    
    def get_posts_approved_count(self, obj):
        return obj.posts_approved_count


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de campanhas."""
    
    class Meta:
        model = Campaign
        fields = [
            'name', 'type', 'objective', 'main_message',
            'structure', 'duration_days', 'post_count', 'post_frequency',
            'start_date', 'end_date', 'visual_styles', 'content_mix',
            'briefing_data', 'is_auto_generated'
        ]


class CampaignPostSerializer(serializers.ModelSerializer):
    """Serializer para posts de campanha."""
    
    post = PostSerializer(read_only=True)
    phase_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CampaignPost
        fields = [
            'id', 'campaign', 'post', 'sequence_order',
            'scheduled_date', 'scheduled_time', 'phase', 'phase_display',
            'theme', 'visual_style', 'is_approved', 'approved_at',
            'is_published', 'published_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'approved_at', 'published_at']
    
    def get_phase_display(self, obj):
        """Retorna nome bonito da fase."""
        phase_names = {
            'awareness': 'Atenção/Awareness',
            'interest': 'Interesse',
            'desire': 'Desejo',
            'action': 'Ação',
            'problem': 'Problema',
            'agitate': 'Agitação',
            'solve': 'Solução',
            'top': 'Topo do Funil',
            'middle': 'Meio do Funil',
            'bottom': 'Fundo do Funil',
        }
        return phase_names.get(obj.phase, obj.phase.title())


class CampaignWithPostsSerializer(serializers.ModelSerializer):
    """Serializer completo com posts nested."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    structure_display = serializers.CharField(source='get_structure_display', read_only=True)
    campaign_posts = CampaignPostSerializer(many=True, read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'type', 'type_display', 'objective', 'main_message',
            'structure', 'structure_display', 'duration_days', 'post_count',
            'start_date', 'end_date', 'visual_styles', 'content_mix',
            'status', 'status_display', 'campaign_posts',
            'created_at', 'updated_at'
        ]


# ============================================================================
# REQUEST/RESPONSE SERIALIZERS
# ============================================================================

class CampaignGenerationRequestSerializer(serializers.Serializer):
    """Validação de request para geração de campanha."""
    
    # Briefing
    objective = serializers.CharField(
        required=True,
        min_length=10,
        help_text="Objetivo específico da campanha"
    )
    main_message = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Mensagem principal (opcional)"
    )
    
    # Estrutura
    structure = serializers.ChoiceField(
        choices=['aida', 'pas', 'funil', 'bab', 'storytelling', 'simple'],
        required=True
    )
    duration_days = serializers.IntegerField(
        required=True,
        min_value=5,
        max_value=30
    )
    post_count = serializers.IntegerField(
        required=True,
        min_value=4,
        max_value=20
    )
    
    # Estilos
    visual_styles = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        min_length=1,
        max_length=3,
        help_text="1-3 estilos visuais"
    )
    
    # Dados Adicionais (Opcional)
    briefing_data = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Dados extras do briefing (cases, materiais, etc)"
    )
    
    def validate(self, data):
        """Validações cross-field."""
        
        # Validar posts_count vs. duration
        posts_per_week = (data['post_count'] / data['duration_days']) * 7
        
        if posts_per_week > 7:
            raise serializers.ValidationError(
                "Muitos posts para a duração. Máximo 7 posts por semana."
            )
        
        if posts_per_week < 2:
            raise serializers.ValidationError(
                "Poucos posts para a duração. Mínimo 2 posts por semana."
            )
        
        return data


class PostRegenerationRequestSerializer(serializers.Serializer):
    """Request para regenerar post com feedback específico."""
    
    feedback_items = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Lista de problemas identificados (ex: ['text_too_long', 'cta_weak'])"
    )
    user_note = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Nota livre do usuário sobre o que quer mudar"
    )


# ============================================================================
# DRAFT SERIALIZERS
# ============================================================================

class CampaignDraftSerializer(serializers.ModelSerializer):
    """Serializer para drafts (auto-save)."""
    
    class Meta:
        model = CampaignDraft
        fields = [
            'id', 'user', 'status', 'current_phase',
            'briefing_data', 'structure_chosen', 'styles_chosen',
            'duration_days', 'post_count', 'posts_data',
            'completed_campaign', 'total_time_spent', 'interaction_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


# ============================================================================
# VISUAL STYLE SERIALIZERS
# ============================================================================

class VisualStyleSerializer(serializers.ModelSerializer):
    """Serializer para estilos visuais."""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = VisualStyle
        fields = [
            'id', 'name', 'slug', 'category', 'category_display',
            'description', 'tags', 'global_success_rate',
            'success_rate_by_niche', 'preview_image_url',
            'best_for_campaign_types', 'best_for_niches',
            'is_active'
        ]
        read_only_fields = ['id']


# ============================================================================
# TEMPLATE SERIALIZERS
# ============================================================================

class CampaignTemplateSerializer(serializers.ModelSerializer):
    """Serializer para templates salvos."""
    
    campaign_type_display = serializers.CharField(
        source='get_campaign_type_display', read_only=True
    )
    structure_display = serializers.CharField(
        source='get_structure_display', read_only=True
    )
    
    class Meta:
        model = CampaignTemplate
        fields = [
            'id', 'name', 'description', 'campaign_type', 'campaign_type_display',
            'structure', 'structure_display', 'duration_days', 'post_count',
            'post_frequency', 'visual_styles', 'content_mix',
            'phase_distribution', 'style_mapping',
            'success_rate', 'times_used', 'avg_approval_rate',
            'created_at'
        ]
        read_only_fields = ['id', 'times_used', 'avg_approval_rate', 'created_at']

