"""
Weekly Context Integration Service - Integra oportunidades com campanhas.
"""

import logging
from typing import List, Dict, Optional

from django.db.models import Q

from Campaigns.models import Campaign, CampaignPost
from IdeaBank.models import Post, PostIdea

logger = logging.getLogger(__name__)


class WeeklyContextIntegrationService:
    """
    Adapter entre Weekly Context (ClientContext) e Campaigns.
    """
    
    def find_relevant_for_campaign(
        self,
        campaign: Campaign,
        min_score: int = 90,
        limit: int = 3
    ) -> List[Dict]:
        """
        Busca oportunidades do Weekly Context relevantes para campanha específica.
        
        Args:
            campaign: Campanha para buscar oportunidades
            min_score: Score mínimo de relevância (0-100)
            limit: Máximo de oportunidades a retornar
        
        Returns:
            Lista de oportunidades filtradas e rankeadas
        """
        
        try:
            # Importar service de Weekly Context
            from ClientContext.services.weekly_context_service import WeeklyContextService
            
            # Buscar contexto semanal do usuário
            # (Implementação completa depende da estrutura do WeeklyContext)
            # Por ora, retornar estrutura esperada vazia
            
            # TODO: Implementar lógica completa quando integrar com WeeklyContext
            # Filtros a aplicar:
            # 1. Score de relevância >= min_score
            # 2. Alinhamento com objetivo da campanha
            # 3. Alinhamento com mensagem principal
            # 4. Não duplicar oportunidades já adicionadas
            
            opportunities = []
            
            logger.info(
                f"Buscando oportunidades para campanha {campaign.id}: "
                f"tipo={campaign.type}, min_score={min_score}"
            )
            
            return opportunities[:limit]
        
        except Exception as e:
            logger.error(f"Erro ao buscar oportunidades: {str(e)}")
            return []
    
    def add_opportunity_to_campaign(
        self,
        campaign: Campaign,
        opportunity_data: Dict,
        position: Optional[int] = None
    ) -> CampaignPost:
        """
        Adiciona post de oportunidade à campanha.
        
        Args:
            campaign: Campanha destino
            opportunity_data: Dados da oportunidade do Weekly Context
            position: Posição desejada (None = automático)
        
        Returns:
            CampaignPost criado
        """
        
        # Gerar post baseado na oportunidade
        post_data = {
            'name': f"{campaign.name} - Oportunidade: {opportunity_data.get('title', 'Notícia')}",
            'objective': 'awareness',  # Oportunidades geralmente são awareness
            'type': 'post',  # Feed post
            'further_details': f"Post sobre: {opportunity_data.get('title', '')}. {opportunity_data.get('summary', '')}",
            'include_image': True
        }
        
        # Usar PostAIService para gerar
        from IdeaBank.services.post_ai_service import PostAIService
        
        ai_service = PostAIService()
        result = ai_service.generate_post_content(
            user=campaign.user,
            post_data=post_data
        )
        
        # Criar Post
        post = Post.objects.create(
            user=campaign.user,
            name=post_data['name'],
            objective=post_data['objective'],
            type=post_data['type'],
            further_details=post_data['further_details'],
            include_image=True,
            is_automatically_generated=True
        )
        
        # Criar PostIdea
        post_idea = PostIdea.objects.create(
            post=post,
            content=result.get('content', ''),
            image_url=result.get('image_url', ''),
            image_description=result.get('image_description', '')
        )
        
        # Determinar posição
        if position is None:
            # Inserir no meio da campanha (strategic position)
            total_posts = campaign.campaign_posts.count()
            position = total_posts // 2 + 1
        
        # Criar CampaignPost
        campaign_post = CampaignPost.objects.create(
            campaign=campaign,
            post=post,
            sequence_order=position,
            scheduled_date=campaign.start_date or timezone.now().date(),
            phase='opportunity',  # Fase especial para oportunidades
            theme='Newsjacking - Oportunidade do Weekly Context',
            visual_style=campaign.visual_styles[0] if campaign.visual_styles else 'minimal'
        )
        
        # Reorganizar sequências se necessário
        self._reorder_sequences(campaign)
        
        logger.info(
            f"Oportunidade adicionada à campanha {campaign.id} "
            f"na posição {position}"
        )
        
        return campaign_post
    
    def _reorder_sequences(self, campaign: Campaign):
        """
        Reorganiza sequências dos posts para manter ordem correta.
        Chamado após adicionar post no meio.
        """
        
        posts = campaign.campaign_posts.order_by('sequence_order')
        
        for i, campaign_post in enumerate(posts, 1):
            if campaign_post.sequence_order != i:
                campaign_post.sequence_order = i
                campaign_post.save(update_fields=['sequence_order'])
    
    def calculate_opportunity_relevance(
        self,
        opportunity: Dict,
        campaign: Campaign
    ) -> float:
        """
        Calcula relevância de uma oportunidade para campanha específica.
        
        Returns:
            Score 0-100
        """
        
        scores = {}
        
        # 1. Alinhamento temático (keywords)
        scores['topic_alignment'] = self._calculate_topic_alignment(
            opportunity,
            campaign.objective,
            campaign.main_message
        )
        
        # 2. Timing (quão recente é a oportunidade)
        scores['timing'] = self._calculate_timing_relevance(opportunity)
        
        # 3. Qualidade da fonte
        scores['source_quality'] = opportunity.get('score', 50)
        
        # Weighted average
        final_score = (
            scores['topic_alignment'] * 0.4 +
            scores['timing'] * 0.2 +
            scores['source_quality'] * 0.4
        )
        
        return final_score
    
    def _calculate_topic_alignment(
        self,
        opportunity: Dict,
        objective: str,
        main_message: str
    ) -> float:
        """
        Calcula alinhamento de tópico (0-100).
        Simplificado - versão completa usaria NLP/embeddings.
        """
        
        # Por ora, retornar score da oportunidade
        return opportunity.get('score', 50)
    
    def _calculate_timing_relevance(self, opportunity: Dict) -> float:
        """Calcula relevância temporal (0-100)."""
        
        # Oportunidades mais recentes têm score maior
        # Por ora, retornar score fixo
        return 80.0

