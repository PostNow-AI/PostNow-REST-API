"""
Campaign Builder Service - Orquestrador de geração de campanhas.
Reutiliza PostAIService existente (IdeaBank) para geração de conteúdo.
"""

import logging
from datetime import timedelta
from typing import Dict, List
from decimal import Decimal

from django.utils import timezone
from django.db import transaction

from IdeaBank.models import Post, PostIdea
from IdeaBank.services.post_ai_service import PostAIService
from Campaigns.models import Campaign, CampaignPost
from Campaigns.constants import CAMPAIGN_STRUCTURES, DEFAULT_POSTING_TIMES

logger = logging.getLogger(__name__)


class CampaignBuilderService:
    """
    Service para construir e gerar campanhas completas.
    Orquestra: Estrutura → Geração de Posts → Validação.
    """
    
    def __init__(self):
        self.post_ai_service = PostAIService()
    
    def generate_campaign_content(self, campaign: Campaign, generation_params: Dict) -> Dict:
        """
        Gera conteúdo completo da campanha.
        
        Args:
            campaign: Objeto Campaign (já salvo no banco)
            generation_params: Parâmetros validados (objective, structure, styles, etc)
        
        Returns:
            Dict com posts gerados e metadata
        """
        
        try:
            with transaction.atomic():
                # 1. Criar estrutura de posts baseada no framework
                posts_structure = self._build_campaign_structure(
                    campaign=campaign,
                    params=generation_params
                )
                
                # 2. Gerar conteúdo para cada post
                generated_posts = []
                
                for i, post_structure in enumerate(posts_structure, 1):
                    try:
                        # Gerar usando PostAIService (reutilização!)
                        post_result = self._generate_single_post(
                            campaign=campaign,
                            post_structure=post_structure,
                            sequence=i
                        )
                        
                        generated_posts.append(post_result)
                        
                        logger.info(
                            f"Post {i}/{len(posts_structure)} gerado para campanha {campaign.id}"
                        )
                        
                    except Exception as e:
                        logger.error(f"Erro ao gerar post {i}: {str(e)}")
                        # Continuar mesmo se 1 post falhar
                        continue
                
                # 3. Atualizar campanha
                campaign.status = 'pending_approval'
                campaign.generation_context = {
                    'generated_at': timezone.now().isoformat(),
                    'posts_generated': len(generated_posts),
                    'params': generation_params
                }
                campaign.save()
                
                return {
                    'campaign_id': campaign.id,
                    'posts': generated_posts,
                    'total_generated': len(generated_posts),
                    'success_rate': len(generated_posts) / len(posts_structure),
                    'message': f'{len(generated_posts)} posts gerados com sucesso!'
                }
        
        except Exception as e:
            logger.error(f"Erro crítico ao gerar campanha: {str(e)}", exc_info=True)
            raise
    
    def _build_campaign_structure(self, campaign: Campaign, params: Dict) -> List[Dict]:
        """
        Constrói estrutura de posts baseada no framework escolhido.
        
        Returns:
            Lista de dicts com: sequence, date, type, phase, objective, theme
        """
        
        structure_key = params.get('structure', campaign.structure)
        structure_config = CAMPAIGN_STRUCTURES.get(structure_key)
        
        if not structure_config:
            raise ValueError(f"Estrutura inválida: {structure_key}")
        
        post_count = params.get('post_count', campaign.post_count)
        duration_days = params.get('duration_days', campaign.duration_days)
        content_mix = params.get('content_mix', campaign.content_mix or {})
        
        # Calcular start_date se não definido
        start_date = campaign.start_date or timezone.now().date()
        
        posts_structure = []
        current_day = 0
        posts_per_phase = self._distribute_posts_by_phases(
            post_count,
            structure_config['phases']
        )
        
        for phase in structure_config['phases']:
            phase_post_count = posts_per_phase[phase['key']]
            
            for i in range(phase_post_count):
                # Determinar tipo de conteúdo (feed, reel, story)
                post_type = self._select_post_type(content_mix, len(posts_structure))
                
                # Calcular data de publicação
                post_date = start_date + timedelta(days=current_day)
                
                # Selecionar horário baseado no tipo
                post_time = self._select_posting_time(post_type, i)
                
                # Determinar estilo visual
                visual_style = self._select_visual_style(
                    params.get('visual_styles', []),
                    len(posts_structure),
                    phase['key']
                )
                
                posts_structure.append({
                    'sequence': len(posts_structure) + 1,
                    'date': post_date,
                    'time': post_time,
                    'type': post_type,
                    'phase': phase['key'],
                    'phase_name': phase['name'],
                    'objective': phase['objective'],
                    'theme': self._generate_theme(phase, i, campaign),
                    'visual_style': visual_style,
                })
                
                # Calcular próximo dia (espaçamento)
                current_day += self._calculate_day_spacing(
                    post_count,
                    duration_days,
                    len(posts_structure)
                )
        
        return posts_structure
    
    def _distribute_posts_by_phases(self, total_posts: int, phases: List[Dict]) -> Dict[str, int]:
        """Distribui posts pelas fases baseado nos weights."""
        
        distribution = {}
        remaining = total_posts
        
        for i, phase in enumerate(phases):
            if i == len(phases) - 1:
                # Última fase recebe o que sobrou
                distribution[phase['key']] = remaining
            else:
                phase_posts = int(total_posts * phase['weight'])
                distribution[phase['key']] = phase_posts
                remaining -= phase_posts
        
        return distribution
    
    def _select_post_type(self, content_mix: Dict, current_index: int) -> str:
        """Seleciona tipo de post (feed, reel, story) baseado no mix."""
        
        if not content_mix:
            # Default: 50% feed, 30% reel, 20% story
            content_mix = {'feed': 0.5, 'reel': 0.3, 'story': 0.2}
        
        # Distribuição simples baseada em índice
        feed_threshold = content_mix.get('feed', 0.5)
        reel_threshold = feed_threshold + content_mix.get('reel', 0.3)
        
        position_ratio = (current_index % 10) / 10
        
        if position_ratio < feed_threshold:
            return 'post'  # feed
        elif position_ratio < reel_threshold:
            return 'reel'
        else:
            return 'story'
    
    def _select_posting_time(self, post_type: str, index: int) -> str:
        """Seleciona horário baseado no tipo de post."""
        
        times = DEFAULT_POSTING_TIMES.get(post_type, ['09:00:00'])
        return times[index % len(times)]
    
    def _select_visual_style(self, styles: List[str], current_index: int, phase: str) -> str:
        """Seleciona estilo visual (alterna entre os escolhidos)."""
        
        if not styles:
            return 'minimal'  # Fallback
        
        # Alterna entre os estilos selecionados
        return styles[current_index % len(styles)]
    
    def _calculate_day_spacing(self, total_posts: int, duration_days: int, current_post: int) -> int:
        """Calcula espaçamento entre posts."""
        
        avg_spacing = duration_days / total_posts
        return max(1, int(avg_spacing))
    
    def _generate_theme(self, phase: Dict, index: int, campaign: Campaign) -> str:
        """Gera tema específico do post baseado na fase."""
        
        # Temas base por fase (podem ser customizados)
        themes = {
            'awareness': f"Post {index + 1} - Capturar atenção",
            'interest': f"Post {index + 1} - Desenvolver interesse",
            'desire': f"Post {index + 1} - Criar desejo",
            'action': f"Post {index + 1} - Call-to-action",
            'problem': f"Post {index + 1} - Identificar problema",
            'agitate': f"Post {index + 1} - Amplificar urgência",
            'solve': f"Post {index + 1} - Apresentar solução",
            'top': f"Post {index + 1} - Educação e awareness",
            'middle': f"Post {index + 1} - Consideração",
            'bottom': f"Post {index + 1} - Conversão",
        }
        
        return themes.get(phase['key'], f"Post {index + 1} - {phase['name']}")
    
    def _generate_single_post(self, campaign: Campaign, post_structure: Dict, sequence: int) -> Dict:
        """
        Gera um post individual usando PostAIService.
        Reutiliza infraestrutura existente!
        """
        
        # Preparar dados do post para PostAIService
        post_data = {
            'name': f"{campaign.name} - Post {sequence}",
            'objective': post_structure['objective'],
            'type': post_structure['type'],
            'further_details': f"{post_structure['theme']}. Fase da campanha: {post_structure['phase_name']}. Objetivo da campanha: {campaign.objective}",
            'include_image': True  # Campanhas sempre incluem imagem
        }
        
        # Gerar conteúdo usando PostAIService (REUTILIZAÇÃO!)
        result = self.post_ai_service.generate_post_content(
            user=campaign.user,
            post_data=post_data
        )
        
        # Criar Post no banco
        post = Post.objects.create(
            user=campaign.user,
            name=post_data['name'],
            objective=post_data['objective'],
            type=post_data['type'],
            further_details=post_data['further_details'],
            include_image=True,
            is_automatically_generated=True
        )
        
        # Criar PostIdea com conteúdo gerado
        post_idea = PostIdea.objects.create(
            post=post,
            content=result.get('content', ''),
            image_url=result.get('image_url', ''),
            image_description=result.get('image_description', '')
        )
        
        # Criar CampaignPost (vincula à campanha)
        campaign_post = CampaignPost.objects.create(
            campaign=campaign,
            post=post,
            sequence_order=sequence,
            scheduled_date=post_structure['date'],
            scheduled_time=post_structure['time'],
            phase=post_structure['phase'],
            theme=post_structure['theme'],
            visual_style=post_structure['visual_style']
        )
        
        return {
            'campaign_post_id': campaign_post.id,
            'post_id': post.id,
            'post_idea_id': post_idea.id,
            'sequence': sequence,
            'phase': post_structure['phase'],
            'content_preview': post_idea.content[:100] + '...',
            'has_image': bool(post_idea.image_url)
        }
    
    def calculate_estimated_cost(self, post_count: int, include_images: bool = True) -> Decimal:
        """Calcula custo estimado da campanha."""
        
        from Campaigns.constants import calculate_campaign_cost
        return Decimal(str(calculate_campaign_cost(post_count, include_images)))

