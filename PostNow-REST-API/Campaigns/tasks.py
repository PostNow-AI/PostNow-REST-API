"""
Celery tasks para geração assíncrona de campanhas.
"""
import logging
from celery import shared_task
from django.utils import timezone
from .models import Campaign, CampaignGenerationProgress
from .services.campaign_builder_service import CampaignBuilderService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='campaigns.generate_campaign_async')
def generate_campaign_async(self, campaign_id: int, generation_params: dict):
    """
    Task assíncrona para gerar campanha completa.
    Atualiza progress a cada post gerado para permitir polling do frontend.
    
    Args:
        self: Task instance (bind=True)
        campaign_id: ID da campanha a ser gerada
        generation_params: Parâmetros de geração (objective, structure, etc)
    
    Returns:
        dict: Resultado da geração com posts criados
    """
    progress = None
    
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        
        # Criar ou atualizar progress tracking
        progress, created = CampaignGenerationProgress.objects.get_or_create(
            campaign=campaign,
            defaults={
                'task_id': self.request.id,
                'total_steps': generation_params.get('post_count', 8)
            }
        )
        
        if not created:
            # Se já existe, atualizar task_id e status
            progress.task_id = self.request.id
            progress.total_steps = generation_params.get('post_count', 8)
        
        progress.status = 'processing'
        progress.current_step = 0
        progress.current_action = 'Iniciando geração da campanha...'
        progress.save()
        
        logger.info(f"✅ Iniciando geração assíncrona da campanha {campaign_id}")
        
        # Inicializar service
        builder_service = CampaignBuilderService()
        
        # Hook para atualizar progress
        def update_progress(current, total, action):
            """Callback para atualizar progresso no banco."""
            progress.current_step = current
            progress.total_steps = total
            progress.current_action = action
            progress.save()
            logger.info(f"📊 Progress: {current}/{total} - {action}")
        
        # Gerar campanha com callback de progress
        result = builder_service.generate_campaign_content(
            campaign=campaign,
            generation_params=generation_params,
            progress_callback=update_progress
        )
        
        # Marcar como completo
        progress.status = 'completed'
        progress.completed_at = timezone.now()
        progress.current_action = 'Campanha gerada com sucesso!'
        progress.save()
        
        logger.info(f"✅ Campanha {campaign_id} gerada com sucesso!")
        
        return result
        
    except Campaign.DoesNotExist:
        error_msg = f"Campanha {campaign_id} não encontrada"
        logger.error(error_msg)
        
        if progress:
            progress.status = 'failed'
            progress.error_message = error_msg
            progress.completed_at = timezone.now()
            progress.save()
        
        raise
        
    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"❌ Erro ao gerar campanha {campaign_id}: {error_msg}",
            exc_info=True
        )
        
        # Marcar como falho
        if progress:
            progress.status = 'failed'
            progress.error_message = error_msg
            progress.completed_at = timezone.now()
            progress.save()
        
        raise


@shared_task(name='campaigns.cleanup_old_progress')
def cleanup_old_progress_records():
    """
    Task agendada para limpar registros de progress antigos.
    Mantém apenas os últimos 30 dias.
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_count, _ = CampaignGenerationProgress.objects.filter(
        started_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    ).delete()
    
    logger.info(f"🧹 Limpeza: {deleted_count} registros de progress removidos")
    
    return {'deleted_count': deleted_count}

