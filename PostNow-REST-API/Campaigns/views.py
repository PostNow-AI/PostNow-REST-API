"""
Views para o app Campaigns.
Seguindo padrão de IdeaBank: Class-based para CRUD + Function-based para custom operations.
"""

import logging
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from AuditSystem.services import AuditService
from .models import (
    Campaign,
    CampaignPost,
    CampaignDraft,
    VisualStyle,
    CampaignTemplate,
)
from .serializers import (
    CampaignSerializer,
    CampaignCreateSerializer,
    CampaignWithPostsSerializer,
    CampaignPostSerializer,
    CampaignDraftSerializer,
    VisualStyleSerializer,
    CampaignTemplateSerializer,
    CampaignGenerationRequestSerializer,
    PostRegenerationRequestSerializer,
)
from .constants import CAMPAIGN_STRUCTURES, CAMPAIGN_DEFAULTS

logger = logging.getLogger(__name__)


# ============================================================================
# CRUD VIEWS - CAMPAIGN
# ============================================================================

class CampaignListView(generics.ListCreateAPIView):
    """Listar e criar campanhas."""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignSerializer
    
    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user).prefetch_related(
            'campaign_posts',
            'campaign_posts__post',
            'campaign_posts__post__ideas'
        )
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CampaignCreateSerializer
        return CampaignSerializer
    
    def perform_create(self, serializer):
        campaign = serializer.save(user=self.request.user)
        
        # Log criação
        AuditService.log_operation(
            user=self.request.user,
            operation_category='campaign',
            action='campaign_created',
            status='success',
            resource_type='Campaign',
            resource_id=str(campaign.id),
            details={
                'campaign_name': campaign.name,
                'campaign_type': campaign.type,
                'structure': campaign.structure,
                'post_count': campaign.post_count
            }
        )


class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detalhes, atualizar e deletar campanha."""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignWithPostsSerializer
    
    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user).select_related(
            'user',
            'user__creator_profile'
        ).prefetch_related(
            'campaign_posts',
            'campaign_posts__post',
            'campaign_posts__post__ideas'
        )
    
    def perform_update(self, serializer):
        campaign = serializer.save()
        
        AuditService.log_operation(
            user=self.request.user,
            operation_category='campaign',
            action='campaign_updated',
            status='success',
            resource_type='Campaign',
            resource_id=str(campaign.id)
        )
    
    def perform_destroy(self, instance):
        campaign_id = instance.id
        campaign_name = instance.name
        instance.delete()
        
        AuditService.log_operation(
            user=self.request.user,
            operation_category='campaign',
            action='campaign_deleted',
            status='success',
            resource_type='Campaign',
            resource_id=str(campaign_id),
            details={'campaign_name': campaign_name}
        )


# ============================================================================
# CRUD VIEWS - DRAFT
# ============================================================================

class CampaignDraftListView(generics.ListAPIView):
    """Listar drafts do usuário."""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignDraftSerializer
    
    def get_queryset(self):
        return CampaignDraft.objects.filter(
            user=self.request.user,
            status='in_progress'
        ).order_by('-updated_at')


class CampaignDraftDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detalhes de draft."""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignDraftSerializer
    
    def get_queryset(self):
        return CampaignDraft.objects.filter(user=self.request.user)


# ============================================================================
# CRUD VIEWS - TEMPLATES
# ============================================================================

class CampaignTemplateListView(generics.ListCreateAPIView):
    """Listar e criar templates."""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignTemplateSerializer
    
    def get_queryset(self):
        return CampaignTemplate.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        template = serializer.save(user=self.request.user)
        
        AuditService.log_operation(
            user=self.request.user,
            operation_category='campaign',
            action='template_created',
            status='success',
            resource_type='CampaignTemplate',
            resource_id=str(template.id)
        )


class CampaignTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detalhes de template."""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignTemplateSerializer
    
    def get_queryset(self):
        return CampaignTemplate.objects.filter(user=self.request.user)


# ============================================================================
# CUSTOM OPERATIONS - GENERATION
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_campaign_content(request, pk):
    """
    Gera conteúdo completo da campanha (todos os posts).
    Endpoint principal de geração.
    """
    
    # Validar request
    serializer = CampaignGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'success': False,
                'error': 'Dados inválidos',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        campaign = get_object_or_404(
            Campaign,
            id=pk,
            user=request.user
        )
        
        # Importar service de geração
        from .services.campaign_builder_service import CampaignBuilderService
        
        builder_service = CampaignBuilderService()
        result = builder_service.generate_campaign_content(
            campaign=campaign,
            generation_params=serializer.validated_data
        )
        
        # Log sucesso
        AuditService.log_operation(
            user=request.user,
            operation_category='campaign',
            action='campaign_generated',
            status='success',
            resource_type='Campaign',
            resource_id=str(campaign.id),
            details={
                'posts_generated': len(result['posts']),
                'structure': campaign.structure
            }
        )
        
        return Response({
            'success': True,
            'data': result,
            'message': f'Campanha gerada com {len(result["posts"])} posts!'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating campaign: {str(e)}", exc_info=True)
        
        AuditService.log_operation(
            user=request.user,
            operation_category='campaign',
            action='campaign_generation_failed',
            status='error',
            resource_type='Campaign',
            resource_id=str(pk),
            error_message=str(e)
        )
        
        return Response(
            {
                'success': False,
                'error': 'Erro ao gerar campanha',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# CUSTOM OPERATIONS - APPROVAL
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_campaign(request, pk):
    """Aprovar campanha completa (todos os posts)."""
    
    try:
        campaign = get_object_or_404(
            Campaign,
            id=pk,
            user=request.user
        )
        
        # Aprovar todos os posts
        campaign_posts = campaign.campaign_posts.all()
        approved_count = 0
        
        for campaign_post in campaign_posts:
            if not campaign_post.is_approved:
                campaign_post.approve()
                approved_count += 1
        
        # Atualizar status da campanha
        campaign.status = 'approved'
        campaign.approved_at = timezone.now()
        campaign.save()
        
        AuditService.log_operation(
            user=request.user,
            operation_category='campaign',
            action='campaign_approved',
            status='success',
            resource_type='Campaign',
            resource_id=str(campaign.id),
            details={'posts_approved': approved_count}
        )
        
        return Response({
            'success': True,
            'data': {
                'campaign_id': campaign.id,
                'posts_approved': approved_count,
                'total_posts': campaign_posts.count()
            },
            'message': f'Campanha aprovada! {approved_count} posts prontos.'
        })
        
    except Exception as e:
        logger.error(f"Error approving campaign: {str(e)}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_campaign_post(request, campaign_id, post_id):
    """Aprovar post individual."""
    
    try:
        campaign_post = get_object_or_404(
            CampaignPost,
            campaign_id=campaign_id,
            id=post_id,
            campaign__user=request.user
        )
        
        campaign_post.approve()
        
        AuditService.log_operation(
            user=request.user,
            operation_category='campaign',
            action='campaign_post_approved',
            status='success',
            resource_type='CampaignPost',
            resource_id=str(campaign_post.id)
        )
        
        return Response({
            'success': True,
            'message': 'Post aprovado!'
        })
        
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# CUSTOM OPERATIONS - AUTO-SAVE
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_campaign_draft(request):
    """Auto-save de draft em progresso."""
    
    try:
        data = request.data
        draft_id = data.get('id')
        
        if draft_id:
            # Atualizar draft existente
            draft = CampaignDraft.objects.get(id=draft_id, user=request.user)
            serializer = CampaignDraftSerializer(draft, data=data, partial=True)
        else:
            # Criar novo draft
            serializer = CampaignDraftSerializer(data=data)
        
        if serializer.is_valid():
            draft = serializer.save(user=request.user)
            
            return Response({
                'success': True,
                'data': {'draft_id': draft.id},
                'message': 'Rascunho salvo!'
            })
        else:
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error saving draft: {str(e)}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# HELPER ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_available_structures(request):
    """Retorna estruturas narrativas disponíveis."""
    
    return Response({
        'success': True,
        'data': CAMPAIGN_STRUCTURES
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_visual_styles(request):
    """Retorna estilos visuais disponíveis."""
    
    styles = VisualStyle.objects.filter(is_active=True)
    
    # Filtrar por categoria se solicitado
    category = request.query_params.get('category')
    if category:
        styles = styles.filter(category=category)
    
    # Ordenar por relevância para o nicho do usuário
    # (lógica de curadoria será implementada em service)
    
    serializer = VisualStyleSerializer(styles, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_structure_suggestion(request):
    """
    Sugere estrutura narrativa usando Thompson Sampling.
    """
    try:
        from Analytics.services.structure_suggestion_service import make_structure_suggestion
        from CreatorProfile.models import CreatorProfile
        
        # Buscar perfil
        try:
            profile = CreatorProfile.objects.get(user=request.user)
            niche = profile.specialization[:20] if profile.specialization else "general"
        except CreatorProfile.DoesNotExist:
            niche = "general"
        
        # Campaign type (pode vir do request ou inferir)
        campaign_type = request.GET.get('campaign_type', 'branding')
        
        # Gerar sugestão com Thompson Sampling
        suggested, decision_id = make_structure_suggestion(
            user=request.user,
            campaign_type=campaign_type,
            niche=niche
        )
        
        return Response({
            'success': True,
            'data': {
                'suggested': suggested,
                'decision_id': decision_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error suggesting structure: {str(e)}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def get_briefing_suggestion(request):
    """
    Gera sugestão de objetivo usando Contextual Bandits.
    """
    try:
        from Analytics.services.contextual_briefing_service import make_briefing_suggestion_decision
        from CreatorProfile.models import CreatorProfile
        
        # Buscar perfil do usuário
        try:
            profile = CreatorProfile.objects.get(user=request.user)
            profile_data = {
                'business_name': profile.business_name,
                'specialization': profile.specialization,
                'business_description': profile.business_description,
                'target_audience': profile.target_audience,
                'products_services': profile.products_services,
            }
        except CreatorProfile.DoesNotExist:
            # Fallback genérico
            return Response({
                'success': True,
                'data': {
                    'suggestion': 'Criar campanha de marketing para seu negócio.',
                    'decision_id': None
                }
            })
        
        # Gerar sugestão com Contextual Bandits
        suggestion, decision_id = make_briefing_suggestion_decision(
            user=request.user,
            profile_data=profile_data
        )
        
        return Response({
            'success': True,
            'data': {
                'suggestion': suggestion,
                'decision_id': decision_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating briefing suggestion: {str(e)}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# STUBS - A SEREM IMPLEMENTADOS NAS PRÓXIMAS FASES
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reorganize_campaign_posts(request, pk):
    """Reorganizar ordem dos posts (será implementado na Fase 6)."""
    return Response({
        'success': False,
        'error': 'Not implemented yet'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def regenerate_campaign_post(request, campaign_id, post_id):
    """Regenerar post com feedback (será implementado na Fase 5)."""
    return Response({
        'success': False,
        'error': 'Not implemented yet'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_weekly_context_opportunities(request, pk):
    """Buscar oportunidades Weekly Context (será implementado na Fase 8)."""
    return Response({
        'success': False,
        'error': 'Not implemented yet'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_opportunity_to_campaign(request, pk, opportunity_id):
    """Adicionar oportunidade à campanha (será implementado na Fase 8)."""
    return Response({
        'success': False,
        'error': 'Not implemented yet'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def calculate_visual_harmony(request, pk):
    """Calcular harmonia visual (será implementado na Fase 6)."""
    return Response({
        'success': False,
        'error': 'Not implemented yet'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)
