"""
Campaign Builder Service - Orquestrador de geração de campanhas.
Reutiliza PostAIService existente (IdeaBank) para geração de conteúdo.
"""

import logging
from datetime import timedelta
from typing import Dict, List
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import time

from django.utils import timezone
from django.db import transaction

from IdeaBank.models import Post, PostIdea
from IdeaBank.services.post_ai_service import PostAIService
from IdeaBank.services.prompt_service import PromptService
from services.ai_service import AiService
from services.s3_sevice import S3Service
from Campaigns.models import Campaign, CampaignPost
from Campaigns.constants import CAMPAIGN_STRUCTURES, DEFAULT_POSTING_TIMES
from Campaigns.services.campaign_visual_context_service import CampaignVisualContextService
from google.genai import types

logger = logging.getLogger(__name__)


class CampaignBuilderService:
    """
    Service para construir e gerar campanhas completas.
    Orquestra: Estrutura → Geração de Posts → Validação.
    
    Suporta 2 modos de geração:
    - Rápido: Prompt direto (90% qualidade, ~70s/imagem)
    - Premium: Análise semântica (98% qualidade, ~90s/imagem)
    """
    
    def __init__(self):
        self.post_ai_service = PostAIService()
        self.visual_context_service = CampaignVisualContextService()
        self.prompt_service = PromptService()
        self.ai_service = AiService()
        self.s3_service = S3Service()
    
    def generate_campaign_content(self, campaign: Campaign, generation_params: Dict, progress_callback=None) -> Dict:
        """
        Gera conteúdo completo da campanha.
        Versão otimizada: gera todos os TEXTOS primeiro, depois IMAGENS em batch.
        
        Args:
            campaign: Objeto Campaign (já salvo no banco)
            generation_params: Parâmetros validados (objective, structure, styles, etc)
            progress_callback: Função callback para atualizar progresso (opcional)
                              Assinatura: callback(current_step, total_steps, action_message)
        
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
                
                # FASE 1: Gerar todos os TEXTOS (rápido, ~5-10s cada)
                generated_posts = []
                total = len(posts_structure)
                
                logger.info(f"📝 FASE 1: Gerando {total} textos...")
                
                for i, post_structure in enumerate(posts_structure, 1):
                    try:
                        # Callback de progress
                        if progress_callback:
                            progress_callback(i, total * 2, f"Gerando texto {i}/{total}...")
                        
                        # Gerar texto SEM imagem ainda
                        post_result = self._generate_single_post(
                            campaign=campaign,
                            post_structure=post_structure,
                            sequence=i,
                            generate_image_now=False  # ⚡ NÃO gerar imagem ainda
                        )
                        
                        generated_posts.append(post_result)
                        
                        logger.info(
                            f"✅ Post {i}/{len(posts_structure)} (texto) gerado para campanha {campaign.id}"
                        )
                        
                    except Exception as e:
                        logger.error(f"Erro ao gerar post {i}: {str(e)}")
                        # Continuar mesmo se 1 post falhar
                        continue
                
                # ✅ FASE 1.5: VALIDAR E AUTO-CORRIGIR TEXTOS
                logger.info(f"🔍 FASE 1.5: Validando qualidade de {len(generated_posts)} posts...")
                
                validation_stats = {}
                if generated_posts:
                    validation_stats = self._validate_and_fix_posts(generated_posts, progress_callback)
                    logger.info(f"✅ Validação completa: {validation_stats}")
                
                # FASE 2: Gerar IMAGENS em batch (paralelo, ~40-60s total)
                logger.info(f"🎨 FASE 2: Gerando {len(generated_posts)} imagens em batch...")
                
                if generated_posts:
                    self._batch_generate_images(
                        generated_posts,
                        campaign,
                        lambda curr, total_imgs, msg: progress_callback(
                            len(posts_structure) + curr,
                            len(posts_structure) * 2,
                            msg
                        ) if progress_callback else None
                    )
                
                # 3. Atualizar campanha
                campaign.status = 'pending_approval'
                
                # ✅ CORRIGIDO: Fazer MERGE do generation_context, não sobrescrever
                existing_context = campaign.generation_context or {}
                campaign.generation_context = {
                    **existing_context,  # Preservar use_semantic_analysis, quality_level, etc.
                    'generated_at': timezone.now().isoformat(),
                    'posts_generated': len(generated_posts),
                    'params': generation_params,
                    'validation_stats': validation_stats  # ✅ NOVO: Incluir stats de validação
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
    
    def _generate_single_post(self, campaign: Campaign, post_structure: Dict, sequence: int, generate_image_now: bool = True) -> Dict:
        """
        Gera um post individual usando PostAIService.
        Reutiliza infraestrutura existente!
        
        Args:
            generate_image_now: Se False, a imagem será gerada depois em batch
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
            image_url='',  # Será preenchido depois no batch se generate_image_now=False
            image_description=result.get('image_description', '')
        )
        
        # Gerar imagem AGORA ou DEPOIS?
        if generate_image_now and post_data.get('include_image'):
            try:
                post_data_with_ids = {
                    **post_data,
                    'post_id': post.id,
                    'post_idea_id': post_idea.id,
                    'post': post,
                    'visual_style': post_structure.get('visual_style', '')
                }
                
                logger.info(f"🎨 Gerando imagem para post {sequence}...")
                
                image_url = self.post_ai_service.generate_image_for_post(
                    user=campaign.user,
                    post_data=post_data_with_ids,
                    content=result.get('content', ''),
                    custom_prompt=None,
                    regenerate=False
                )
                
                # Atualizar PostIdea com a imagem gerada
                post_idea.image_url = image_url
                post_idea.save()
                
                logger.info(f"✅ Imagem gerada para post {sequence}: {image_url[:50] if image_url else 'None'}...")
                
            except Exception as e:
                logger.warning(f"⚠️ Falha ao gerar imagem para post {sequence}: {str(e)}")
                # Continua sem imagem (não quebra a geração da campanha)
        
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
            'post_idea': post_idea,  # Retornar objeto para batch
            'post': post,  # Retornar objeto para batch
            'sequence': sequence,
            'phase': post_structure['phase'],
            'visual_style': post_structure.get('visual_style', ''),
            'content': result.get('content', ''),
            'content_preview': result.get('content', '')[:100] + '...',
            'has_image': bool(post_idea.image_url)
        }
    
    def _batch_generate_images(self, post_ideas_data: List[Dict], campaign: Campaign, progress_callback=None):
        """
        Gera múltiplas imagens em paralelo (respeitando rate limits).
        
        Suporta 2 modos:
        - Rápido: Usa PostAIService.generate_image_for_post() diretamente
        - Premium: Usa análise semântica (como posts individuais)
        
        Args:
            post_ideas_data: Lista de dicts com post_idea, post_id, content, visual_style, etc
            campaign: Campaign object
            progress_callback: Callback para atualizar progress
        """
        # Determinar modo de geração
        use_semantic_analysis = campaign.generation_context.get('use_semantic_analysis', False) if campaign.generation_context else False
        
        # Pegar contexto visual da campanha UMA VEZ (antes do loop)
        visual_context_base = self.visual_context_service.get_visual_context_for_campaign(
            campaign,
            current_post_number=0
        )
        
        def generate_single_image(data):
            """Função para gerar uma única imagem (executada em thread)."""
            try:
                post_idea = data['post_idea']
                post = data['post']
                sequence = data['sequence']
                
                # Atualizar contexto visual com número do post atual
                visual_context = {
                    **visual_context_base,
                    'current_post_number': sequence
                }
                
                # Decidir entre fluxo rápido ou premium
                if use_semantic_analysis:
                    # FLUXO PREMIUM: Análise semântica (como posts individuais)
                    logger.info(f"🎨 Post {sequence}: Gerando com análise semântica (premium)...")
                    image_url = self._generate_image_with_semantic_analysis(
                        post_idea=post_idea,
                        post=post,
                        campaign=campaign,
                        visual_context=visual_context,
                        content=data['content']
                    )
                else:
                    # FLUXO RÁPIDO: Prompt direto (atual)
                    logger.info(f"🎨 Post {sequence}: Gerando com prompt direto (rápido)...")
                    
                    post_data = {
                        'post_id': data['post_id'],
                        'post_idea_id': data['post_idea_id'],
                        'post': post,
                        'visual_style': data.get('visual_style', ''),
                        'type': post.type,
                        'name': post.name,
                        'objective': post.objective,
                        'include_image': True,
                        'campaign_visual_context': visual_context  # NOVO: Contexto de harmonia
                    }
                    
                    image_url = self.post_ai_service.generate_image_for_post(
                        user=campaign.user,
                        post_data=post_data,
                        content=data['content'],
                        custom_prompt=None,
                        regenerate=False
                    )
                
                # Atualizar PostIdea com a imagem
                post_idea.image_url = image_url
                post_idea.save()
                
                logger.info(f"✅ Imagem gerada para post {sequence}: {image_url[:50] if image_url else 'None'}...")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Falha ao gerar imagem para post {data.get('sequence')}: {str(e)}")
                return False
        
        # ✅ CORRIGIDO: Ajustar paralelismo baseado no banco de dados
        import os
        
        # SQLite não suporta writes concorrentes → Sequential
        # MySQL suporta → Paralelo (3 workers)
        if os.getenv('USE_SQLITE'):
            batch_size = 1  # Sequential no SQLite
            max_workers = 1
            logger.info("⚙️ Modo SQLite: Geração sequencial (1 por vez)")
        else:
            batch_size = 3  # Paralelo no MySQL
            max_workers = 3
            logger.info("⚙️ Modo MySQL: Geração paralela (3 por vez)")
        
        total_batches = (len(post_ideas_data) + batch_size - 1) // batch_size
        
        logger.info(f"🚀 Iniciando geração de imagens: {len(post_ideas_data)} imagens em {total_batches} batches")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(post_ideas_data))
            batch = post_ideas_data[start_idx:end_idx]
            
            if progress_callback:
                progress_callback(
                    start_idx,
                    len(post_ideas_data),
                    f"Gerando imagens {start_idx+1}-{end_idx}/{len(post_ideas_data)}..."
                )
            
            # Gerar imagens (paralelo no MySQL, sequencial no SQLite)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(generate_single_image, batch))
            
            # Pausa entre batches para respeitar rate limits
            if batch_num < total_batches - 1:  # Não pausar no último batch
                logger.info(f"⏸️ Pausando 1s entre batches...")
                time.sleep(1)
        
        logger.info(f"✅ Geração de imagens em batch concluída!")
    
    def _generate_image_with_semantic_analysis(
        self,
        post_idea: PostIdea,
        post: Post,
        campaign: Campaign,
        visual_context: Dict,
        content: str
    ) -> str:
        """
        Gera imagem usando análise semântica (modo premium).
        
        Segue o MESMO fluxo de DailyIdeasService._generate_image_for_feed_post():
        1. Análise semântica do conteúdo (IA call #1)
        2. Adaptação ao estilo da marca (IA call #2)
        3. Prompt baseado em semantic_analysis
        4. Enriquecimento com visual_context (harmonia)
        5. Geração da imagem (IA call #3)
        
        Args:
            post_idea: PostIdea object
            post: Post object
            campaign: Campaign object
            visual_context: Contexto visual da campanha
            content: Conteúdo do post
        
        Returns:
            URL da imagem gerada
        """
        try:
            from IdeaBank.utils.json_utils import clean_json_string, safe_json_loads
            
            # Setar usuário no PromptService
            self.prompt_service.set_user(campaign.user)
            
            # 1. ANÁLISE SEMÂNTICA do conteúdo (como posts individuais)
            semantic_prompt = self.prompt_service.semantic_analysis_prompt(content)
            semantic_result = self.ai_service.generate_text(semantic_prompt, campaign.user)
            semantic_json = clean_json_string(semantic_result)
            semantic_loaded = safe_json_loads(semantic_json)
            
            # 2. ADAPTAÇÃO ao estilo da marca
            adapted_semantic_prompt = self.prompt_service.adapted_semantic_analysis_prompt(semantic_loaded)
            adapted_semantic_json = self.ai_service.generate_text(adapted_semantic_prompt, campaign.user)
            adapted_semantic_str = clean_json_string(adapted_semantic_json)
            adapted_semantic_loaded = safe_json_loads(adapted_semantic_str)
            
            semantic_analysis = adapted_semantic_loaded.get('analise_semantica', {})
            
            # 3. PROMPT de imagem baseado em semantic_analysis
            image_prompt_base = self.prompt_service.image_generation_prompt(semantic_analysis)
            
            # 4. ENRIQUECER com contexto de harmonia visual
            harmony_guidelines = visual_context.get('harmony_guidelines', '')
            
            # Combinar prompt semântico + harmonia visual
            enhanced_prompt = f"""
{image_prompt_base}

{harmony_guidelines}

CONTEXTO ADICIONAL DA CAMPANHA:
- Estilo visual predominante: {visual_context.get('visual_patterns', {}).get('most_common_style', 'profissional')}
- Tom emocional da campanha: {visual_context.get('visual_patterns', {}).get('emotional_tone', 'profissional')}
- Este é o post {visual_context['current_post_number']}/{visual_context['total_posts']} da série

A imagem deve ser COESA com os posts anteriores mas ÚNICA e interessante.
"""
            
            # 5. GERAR imagem com Gemini
            logo = self.prompt_service.get_creator_profile_data().get('logo_image', None)
            
            # Tratar logo vazio
            if not logo or (isinstance(logo, str) and logo.strip() == ''):
                logo = None
            
            image_result = self.ai_service.generate_image(
                prompt_list=[enhanced_prompt],
                image_attachment=logo,
                user=campaign.user,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.9,
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="4:5")
                )
            )
            
            if not image_result:
                raise Exception("Análise semântica não gerou imagem")
            
            # 6. UPLOAD S3
            image_url = self.s3_service.upload_image(campaign.user, image_result)
            
            return image_url
            
        except Exception as e:
            logger.error(f"Erro na geração com análise semântica: {str(e)}")
            raise
    
    def _validate_and_fix_posts(self, generated_posts: List[Dict], progress_callback=None) -> Dict:
        """
        Valida qualidade dos posts e aplica auto-correções.
        
        Args:
            generated_posts: Lista de posts gerados
            progress_callback: Callback de progress (opcional)
        
        Returns:
            Dict com estatísticas de validação
        """
        try:
            from Campaigns.services.quality_validator_service import QualityValidatorService
            from IdeaBank.models import PostIdea
            
            validator = QualityValidatorService()
            
            # Coletar post_ideas
            post_ideas = []
            for post_result in generated_posts:
                try:
                    post_idea = PostIdea.objects.get(id=post_result['post_idea_id'])
                    post_ideas.append(post_idea)
                except PostIdea.DoesNotExist:
                    logger.warning(f"PostIdea {post_result['post_idea_id']} não encontrado")
                    continue
            
            # Validar em batch
            validation_results = validator.validate_campaign_posts(post_ideas)
            
            # Estatísticas
            stats = {
                'total': len(post_ideas),
                'passed': len(validation_results['passed']),
                'auto_fixed': len(validation_results['auto_fixed']),
                'needs_attention': len(validation_results['needs_attention']),
                'failed': len(validation_results['failed'])
            }
            
            # Log de correções
            if validation_results['auto_fixed']:
                logger.info(f"🔧 Auto-correções aplicadas em {stats['auto_fixed']} posts:")
                for fixed in validation_results['auto_fixed']:
                    logger.info(f"   Post {fixed['post'].id}: {fixed['issues_resolved']} correções")
            
            return stats
            
        except Exception as e:
            logger.warning(f"Erro na validação, continuando: {str(e)}")
            return {'total': len(generated_posts), 'error': str(e)}
    
    def calculate_estimated_cost(self, post_count: int, include_images: bool = True) -> Decimal:
        """Calcula custo estimado da campanha."""
        
        from Campaigns.constants import calculate_campaign_cost
        return Decimal(str(calculate_campaign_cost(post_count, include_images)))

