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
        return Campaign.objects.filter(
            user=self.request.user
        ).prefetch_related(
            'campaign_posts',
            'campaign_posts__post',
            'campaign_posts__post__ideas'
        ).order_by('-created_at')  # ✅ Mais recentes primeiro
    
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
    Inicia geração assíncrona de campanha.
    Retorna task_id para tracking de progress.
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
        
        # Enfileirar task assíncrona
        from .tasks import generate_campaign_async
        
        task = generate_campaign_async.delay(
            campaign_id=campaign.id,
            generation_params=serializer.validated_data
        )
        
        # Log início
        AuditService.log_operation(
            user=request.user,
            operation_category='campaign',
            action='campaign_generation_started',
            status='success',
            resource_type='Campaign',
            resource_id=str(campaign.id),
            details={
                'task_id': task.id,
                'structure': campaign.structure
            }
        )
        
        return Response({
            'success': True,
            'task_id': task.id,
            'message': 'Geração iniciada! Use o task_id para acompanhar o progresso.'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error starting campaign generation: {str(e)}", exc_info=True)
        
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
                'error': 'Erro ao iniciar geração',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_generation_progress(request, pk):
    """
    Retorna status de geração da campanha.
    Endpoint para polling do frontend.
    """
    try:
        campaign = get_object_or_404(Campaign, id=pk, user=request.user)
        
        try:
            from .models import CampaignGenerationProgress
            progress = campaign.generation_progress
            
            return Response({
                'success': True,
                'data': {
                    'status': progress.status,
                    'current_step': progress.current_step,
                    'total_steps': progress.total_steps,
                    'current_action': progress.current_action,
                    'percentage': int((progress.current_step / progress.total_steps) * 100) if progress.total_steps > 0 else 0,
                    'error_message': progress.error_message,
                    'started_at': progress.started_at.isoformat(),
                    'completed_at': progress.completed_at.isoformat() if progress.completed_at else None
                }
            })
            
        except CampaignGenerationProgress.DoesNotExist:
            return Response({
                'success': True,
                'data': {
                    'status': 'not_started',
                    'current_step': 0,
                    'total_steps': 0,
                    'percentage': 0,
                    'current_action': '',
                    'error_message': None,
                    'started_at': None,
                    'completed_at': None
                }
            })
        
    except Exception as e:
        logger.error(f"Error fetching progress: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
def get_style_suggestions(request):
    """
    Retorna estilos ranqueados por Thompson Sampling.
    FALLBACK: Se service não existir, retorna lista normal.
    """
    try:
        from Analytics.services.style_suggestion_service import rank_visual_styles
        from Campaigns.models import VisualStyle
        
        # Buscar todos estilos
        all_styles = list(VisualStyle.objects.filter(is_active=True))
        
        # Ranquear com Thompson Sampling
        ranked = rank_visual_styles(
            user=request.user,
            available_styles=all_styles,
            top_n=18  # Todos, mas ranqueados
        )
        
        # Serializar
        from Campaigns.serializers import VisualStyleSerializer
        serialized = VisualStyleSerializer(ranked, many=True).data
        
        return Response({
            'success': True,
            'data': serialized
        })
        
    except (ImportError, Exception) as e:
        logger.warning(f"Thompson Sampling não disponível, usando fallback: {str(e)}")
        # Fallback: retornar lista normal (sem ranking)
        return get_visual_styles(request)


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
# JORNADAS ADAPTATIVAS
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def suggest_journey(request):
    """
    Sugere jornada ideal para o usuário baseado em seu perfil e histórico.
    
    POST /api/v1/campaigns/suggest-journey/
    Body (opcional):
        {
            "explicit_choice": "quick" | "guided" | "advanced",
            "urgency": true | false
        }
    
    Returns:
        {
            "success": true,
            "data": {
                "journey": "guided",
                "title": "Jornada Guiada",
                "description": "Crie campanhas em 15-30 minutos",
                "benefits": [...],
                "ideal_for": "...",
                "reasons": [...]
            }
        }
    """
    try:
        from .services.journey_detection_service import JourneyDetectionService
        
        service = JourneyDetectionService()
        
        # Contexto da requisição
        context = {
            'explicit_choice': request.data.get('explicit_choice'),
            'urgency': request.data.get('urgency', False)
        }
        
        # Detectar jornada
        detected_journey = service.detect_user_journey_type(
            user=request.user,
            context=context
        )
        
        # Obter raciocínio
        reasoning = service.get_journey_reasoning(
            user=request.user,
            detected_journey=detected_journey
        )
        
        return Response({
            'success': True,
            'data': reasoning
        })
        
    except Exception as e:
        logger.error(f"Error suggesting journey: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'Erro ao sugerir jornada',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def track_journey_event(request):
    """
    Registra evento de jornada para aprendizado do sistema.
    
    POST /api/v1/campaigns/track-journey/
    Body:
        {
            "campaign_id": "uuid",
            "event_type": "started" | "completed" | "abandoned" | "switched",
            "journey_type": "quick" | "guided" | "advanced",
            "time_spent_seconds": 120,  # opcional
            "satisfaction_rating": 8     # opcional, 1-10
        }
    
    Returns:
        {
            "success": true,
            "message": "Evento registrado com sucesso"
        }
    """
    try:
        from .services.journey_detection_service import JourneyDetectionService
        
        # Validar dados
        campaign_id = request.data.get('campaign_id')
        event_type = request.data.get('event_type')
        journey_type = request.data.get('journey_type')
        
        if not all([campaign_id, event_type, journey_type]):
            return Response(
                {
                    'success': False,
                    'error': 'Campos obrigatórios: campaign_id, event_type, journey_type'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar campanha
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            user=request.user
        )
        
        # Processar tempo gasto
        time_spent = None
        if request.data.get('time_spent_seconds'):
            time_spent = timedelta(seconds=int(request.data['time_spent_seconds']))
        
        # Registrar evento
        service = JourneyDetectionService()
        service.track_journey_event(
            user=request.user,
            campaign=campaign,
            event_type=event_type,
            journey_type=journey_type,
            time_spent=time_spent,
            satisfaction_rating=request.data.get('satisfaction_rating')
        )
        
        return Response({
            'success': True,
            'message': 'Evento registrado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Error tracking journey event: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'Erro ao registrar evento',
                'details': str(e)
            },
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
