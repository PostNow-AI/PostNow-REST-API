"""
Campaign Visual Context Service - Gerencia contexto visual coletivo da campanha.

Responsável por:
- Extrair paleta de cores da marca
- Coletar estilos visuais da campanha
- Analisar posts já gerados
- Extrair padrões visuais (composição, tom, elementos)
- Fornecer diretrizes de harmonia para próximos posts

Objetivo: Garantir coesão visual entre todos os posts da mesma campanha.
"""

import logging
from typing import Dict, List, Optional
from collections import Counter

from django.db.models import Q

from Campaigns.models import Campaign, VisualStyle, CampaignPost
from IdeaBank.models import Post, PostIdea
from CreatorProfile.models import CreatorProfile

logger = logging.getLogger(__name__)


class CampaignVisualContextService:
    """
    Gerencia o contexto visual coletivo de uma campanha.
    Garante harmonia e coesão entre posts.
    """
    
    def get_visual_context_for_campaign(
        self, 
        campaign: Campaign,
        current_post_number: int = 0
    ) -> Dict:
        """
        Retorna contexto visual completo da campanha.
        
        Args:
            campaign: Campanha sendo gerada
            current_post_number: Número do post atual (para saber quantos já foram gerados)
        
        Returns:
            dict com:
            - color_palette: Cores da marca
            - visual_styles: Estilos escolhidos
            - existing_posts: Posts já gerados
            - visual_patterns: Padrões detectados
            - harmony_guidelines: Diretrizes de harmonia
        """
        
        # 1. Paleta de cores da marca
        brand_colors = self._get_brand_colors(campaign.user)
        
        # 2. Estilos visuais da campanha
        campaign_styles = self._get_campaign_styles(campaign)
        
        # 3. Posts já gerados (para análise de padrões)
        existing_posts = self._get_existing_post_context(campaign)
        
        # 4. Extrair padrões visuais dos posts existentes
        visual_patterns = self._extract_visual_patterns(existing_posts) if existing_posts else {}
        
        # 5. Gerar diretrizes de harmonia
        harmony_guidelines = self._build_harmony_guidelines(
            brand_colors,
            campaign_styles,
            visual_patterns,
            current_post_number,
            campaign.post_count
        )
        
        return {
            'color_palette': brand_colors,
            'visual_styles': campaign_styles,
            'existing_posts': existing_posts,
            'visual_patterns': visual_patterns,
            'harmony_guidelines': harmony_guidelines,
            'current_post_number': current_post_number,
            'total_posts': campaign.post_count
        }
    
    def _get_brand_colors(self, user) -> List[str]:
        """
        Extrai paleta de cores do CreatorProfile.
        
        Returns:
            Lista de cores em hex (ex: ['#85C1E9', '#F8C471', ...])
        """
        try:
            profile = CreatorProfile.objects.filter(user=user).first()
            
            if not profile:
                return []
            
            # Coletar todas as cores definidas
            colors = []
            for i in range(1, 6):  # color_1 até color_5
                color = getattr(profile, f'color_{i}', None)
                if color and color.strip():
                    colors.append(color.strip())
            
            return colors
            
        except Exception as e:
            logger.warning(f"Erro ao buscar cores do perfil: {str(e)}")
            return []
    
    def _get_campaign_styles(self, campaign: Campaign) -> List[Dict]:
        """
        Retorna estilos visuais escolhidos para a campanha.
        
        Returns:
            Lista de dicts com name, category, modifiers
        """
        if not campaign.visual_styles:
            return []
        
        try:
            # visual_styles pode ser lista de IDs ou nomes
            style_identifiers = campaign.visual_styles
            
            styles_data = []
            
            for identifier in style_identifiers:
                # Tentar como ID primeiro
                try:
                    style_id = int(identifier)
                    style = VisualStyle.objects.filter(id=style_id).first()
                except (ValueError, TypeError):
                    # Se não for ID, tentar como nome
                    style = VisualStyle.objects.filter(name=identifier).first()
                
                if style:
                    styles_data.append({
                        'id': style.id,
                        'name': style.name,
                        'category': style.category,
                        'modifiers': style.image_prompt_modifiers or []
                    })
            
            return styles_data
            
        except Exception as e:
            logger.warning(f"Erro ao buscar estilos da campanha: {str(e)}")
            return []
    
    def _get_existing_post_context(self, campaign: Campaign) -> List[Dict]:
        """
        Retorna contexto dos posts já gerados da campanha.
        
        Returns:
            Lista de dicts com: sequence, content_preview, image_url, visual_style
        """
        try:
            # Buscar posts já criados desta campanha
            existing_posts = CampaignPost.objects.filter(
                campaign=campaign
            ).select_related('post').prefetch_related('post__ideas').order_by('sequence_order')
            
            posts_context = []
            
            for cp in existing_posts:
                post_idea = cp.post.ideas.first() if cp.post.ideas.exists() else None
                
                if post_idea and post_idea.image_url:
                    posts_context.append({
                        'sequence': cp.sequence_order,
                        'content_preview': post_idea.content[:200] if post_idea.content else '',
                        'image_url': post_idea.image_url,
                        'visual_style': cp.visual_style,
                        'phase': cp.phase
                    })
            
            return posts_context
            
        except Exception as e:
            logger.warning(f"Erro ao buscar posts existentes: {str(e)}")
            return []
    
    def _extract_visual_patterns(self, existing_posts: List[Dict]) -> Dict:
        """
        Analisa posts existentes e extrai padrões visuais recorrentes.
        
        Returns:
            dict com:
            - composition_pattern: Padrão de composição dominante
            - emotional_tone: Tom emocional predominante
            - visual_elements: Elementos visuais recorrentes
            - style_distribution: Distribuição de estilos usados
        """
        if not existing_posts:
            return {}
        
        try:
            # Contar estilos usados
            styles = [post['visual_style'] for post in existing_posts if post.get('visual_style')]
            style_counter = Counter(styles)
            most_common_style = style_counter.most_common(1)[0][0] if style_counter else None
            
            # Contar fases
            phases = [post['phase'] for post in existing_posts if post.get('phase')]
            phase_counter = Counter(phases)
            
            return {
                'composition_pattern': 'vertical_centered',  # Padrão Feed Instagram
                'emotional_tone': self._infer_emotional_tone(existing_posts),
                'visual_elements': self._infer_visual_elements(existing_posts),
                'style_distribution': dict(style_counter),
                'most_common_style': most_common_style,
                'phase_distribution': dict(phase_counter),
                'total_existing': len(existing_posts)
            }
            
        except Exception as e:
            logger.warning(f"Erro ao extrair padrões visuais: {str(e)}")
            return {}
    
    def _infer_emotional_tone(self, existing_posts: List[Dict]) -> str:
        """
        Infere tom emocional predominante dos posts.
        
        Baseado nas fases (awareness, interest, desire, action).
        """
        if not existing_posts:
            return 'profissional e inspirador'
        
        # Mapear fases para tons emocionais
        tone_map = {
            'awareness': 'informativo e inspirador',
            'interest': 'engajador e curioso',
            'desire': 'aspiracional e motivador',
            'action': 'urgente e convidativo'
        }
        
        # Pegar fase mais comum
        phases = [post.get('phase', 'awareness') for post in existing_posts]
        most_common_phase = Counter(phases).most_common(1)[0][0] if phases else 'awareness'
        
        return tone_map.get(most_common_phase, 'profissional e inspirador')
    
    def _infer_visual_elements(self, existing_posts: List[Dict]) -> List[str]:
        """
        Infere elementos visuais recorrentes.
        
        Por enquanto retorna elementos genéricos baseados em estilos.
        V2: Pode usar IA para analisar imagens existentes.
        """
        # Elementos base por categoria de estilo
        style_elements = {
            'minimalista': ['espaço negativo', 'tipografia limpa', 'composição simples'],
            'corporativo': ['ambientes profissionais', 'pessoas em contexto business', 'elementos estruturados'],
            'bold': ['cores vibrantes', 'elementos dinâmicos', 'composição energética'],
            'criativo': ['perspectivas únicas', 'elementos artísticos', 'composição expressiva'],
            'moderno': ['formas geométricas', 'design limpo', 'estética contemporânea']
        }
        
        # Pegar elementos baseados nos estilos usados
        elements = set()
        
        for post in existing_posts:
            style_name = post.get('visual_style', '')
            
            # Tentar mapear para categoria
            for category, category_elements in style_elements.items():
                if category in style_name.lower():
                    elements.update(category_elements)
                    break
        
        return list(elements) if elements else ['elementos visuais consistentes']
    
    def _build_harmony_guidelines(
        self,
        brand_colors: List[str],
        campaign_styles: List[Dict],
        visual_patterns: Dict,
        current_post_number: int,
        total_posts: int
    ) -> str:
        """
        Constrói texto de diretrizes de harmonia para incluir no prompt.
        
        Returns:
            String formatada para inserir no prompt de geração de imagem
        """
        if current_post_number <= 1:
            # Primeiro post - sem contexto anterior
            return ""
        
        guidelines = f"""

═══════════════════════════════════════════════════════════
HARMONIA VISUAL DA CAMPANHA (CONTEXTO COLETIVO)
═══════════════════════════════════════════════════════════

Esta imagem é o Post {current_post_number}/{total_posts} de uma campanha coesa.

Posts já criados: {visual_patterns.get('total_existing', 0)}

MANTER CONSISTÊNCIA VISUAL COM A CAMPANHA:

🎨 PALETA DE CORES (ESTRITAMENTE):
{', '.join(brand_colors) if brand_colors else 'Usar tons profissionais'}

🎭 TOM EMOCIONAL PREDOMINANTE:
{visual_patterns.get('emotional_tone', 'profissional e inspirador')}

🖼️ PADRÃO DE COMPOSIÇÃO:
{visual_patterns.get('composition_pattern', 'vertical centralizada')}

🔍 ELEMENTOS VISUAIS RECORRENTES:
{', '.join(visual_patterns.get('visual_elements', [])) if visual_patterns.get('visual_elements') else 'Elementos consistentes com a marca'}

📊 DISTRIBUIÇÃO DE ESTILOS NA CAMPANHA:
{', '.join([f"{k}: {v} posts" for k, v in visual_patterns.get('style_distribution', {}).items()]) or 'Variado'}

⚠️ IMPORTANTE PARA HARMONIA:

1. Esta imagem DEVE usar a mesma paleta de cores dos posts anteriores
2. O tom emocional deve ser COERENTE com a campanha
3. A composição pode variar MAS deve manter o mesmo "feeling"
4. Elementos visuais podem ser únicos MAS dentro da mesma família visual
5. Evite repetir elementos EXATOS dos posts anteriores

OBJETIVO: Criar uma imagem que seja PARTE de um feed harmonioso quando vista
junto com os outros posts, mas ainda ÚNICA e interessante por si só.

═══════════════════════════════════════════════════════════
"""
        
        return guidelines

