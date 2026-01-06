import json
import logging
import time
from typing import Dict, List

from django.contrib.auth.models import User
from django.db import transaction

from CreatorProfile.models import CreatorProfile
from IdeaBank.models import Post, PostObjective, PostType
from Carousel.models import (
    CarouselPost, CarouselSlide,
    CarouselGenerationSource, CarouselMetrics
)
from services.ai_service import AiService
from services.ai_prompt_service import AIPromptService
from services.s3_sevice import S3Service

logger = logging.getLogger(__name__)


class CarouselGenerationService:
    """Service para geração de carrosséis Instagram."""

    def __init__(self):
        self.ai_service = AiService()
        self.prompt_service = AIPromptService()
        self.s3_service = S3Service()

    @transaction.atomic
    def generate_from_manual_input(self, user: User, theme: str) -> CarouselPost:
        """
        Gera carrossel a partir de input manual do usuário.
        
        Args:
            user: Usuário que está criando o carrossel
            theme: Tema do carrossel fornecido pelo usuário
            
        Returns:
            CarouselPost: Instância do carrossel gerado
        """
        start_time = time.time()
        logger.info(f"Iniciando geração de carrossel para usuário {user.id} com tema: {theme}")

        try:
            # 1. Criar Post base (padrão IdeaBank)
            post = Post.objects.create(
                user=user,
                name=f"Carrossel: {theme[:50]}",
                objective=PostObjective.ENGAGEMENT,
                type=PostType.CAROUSEL,
                further_details=theme,
                include_image=True,
            )

            # 2. Criar CarouselPost
            carousel = CarouselPost.objects.create(
                post=post,
                slide_count=7,
                narrative_type='list',
            )

            # 3. Gerar estrutura de slides via IA
            logger.info(f"Gerando estrutura de slides para carrossel {carousel.id}")
            structure_prompt = self._build_structure_prompt(user, theme)
            structure_response = self.ai_service.generate_text(
                prompt=structure_prompt,
                user=user,
            )
            slides_data = self._parse_structure_response(structure_response)

            # 4. Gerar imagem para cada slide (análise semântica 3 etapas)
            logger.info(f"Gerando imagens para {len(slides_data)} slides")
            for idx, slide_data in enumerate(slides_data, start=1):
                logger.info(f"Gerando slide {idx}/{len(slides_data)}")
                
                image_url = self._generate_image_with_semantic_analysis(
                    user=user,
                    slide_title=slide_data['title'],
                    slide_content=slide_data['content'],
                    slide_number=idx,
                    total_slides=7,
                )

                CarouselSlide.objects.create(
                    carousel=carousel,
                    sequence_order=idx,
                    title=slide_data['title'],
                    content=slide_data['content'],
                    image_url=image_url,
                    image_description=slide_data.get('image_description', ''),
                    has_arrow=True,
                    has_numbering=True,
                )

            # 5. Registrar origem e métricas
            CarouselGenerationSource.objects.create(
                carousel=carousel,
                source_type='manual',
                original_theme=theme,
            )

            generation_time = time.time() - start_time
            CarouselMetrics.objects.create(
                carousel=carousel,
                generation_time=generation_time,
                generation_source='manual',
            )

            logger.info(f"Carrossel {carousel.id} gerado com sucesso em {generation_time:.2f}s")
            return carousel

        except Exception as e:
            logger.error(f"Erro ao gerar carrossel: {str(e)}", exc_info=True)
            raise

    def _build_structure_prompt(self, user: User, theme: str) -> str:
        """Constrói prompt para gerar estrutura de slides."""
        self.prompt_service.set_user(user)
        profile_data = self.prompt_service._get_creator_profile_data()

        prompt = f"""Você é um especialista em criação de conteúdo para Instagram.

CONTEXTO DO NEGÓCIO:
- Nome: {profile_data.get('business_name', 'N/A')}
- Especialização: {profile_data.get('specialization', 'N/A')}
- Descrição: {profile_data.get('business_description', 'N/A')}
- Tom de voz: {profile_data.get('voice_tone', 'N/A')}
- Público-alvo: {profile_data.get('target_audience', 'N/A')}

TAREFA:
Crie a estrutura de um carrossel Instagram de 7 slides sobre o tema: "{theme}"

FORMATO DE CARROSSEL (Lista/Checklist):
- Slide 1: Título chamativo que desperta curiosidade
- Slides 2-6: Pontos da lista (um conceito por slide)
- Slide 7: Conclusão + CTA

REQUISITOS:
1. Cada slide deve ter:
   - Título curto e impactante (máx 50 caracteres)
   - Conteúdo complementar (máx 150 caracteres)
   - Descrição de imagem sugerida

2. Use linguagem do público-alvo
3. Mantenha consistência com o tom de voz da marca
4. Inclua elementos que incentivem o swipe (curiosidade, numeração)

RESPONDA EM JSON (apenas JSON, sem texto adicional):
{{
  "slides": [
    {{
      "title": "Título do slide 1",
      "content": "Conteúdo complementar",
      "image_description": "Descrição da imagem ideal"
    }},
    ... (7 slides no total)
  ]
}}
"""
        return prompt

    def _parse_structure_response(self, response: str) -> List[Dict]:
        """Parse da resposta da IA para extrair estrutura de slides."""
        try:
            # Tentar fazer parse direto
            data = json.loads(response)
            slides = data.get('slides', [])
            
            if len(slides) != 7:
                logger.warning(f"Esperado 7 slides, recebido {len(slides)}. Ajustando...")
                # Se recebeu menos, duplicar últimos até ter 7
                while len(slides) < 7:
                    slides.append(slides[-1].copy())
                # Se recebeu mais, cortar
                slides = slides[:7]
            
            return slides
        
        except json.JSONDecodeError:
            # Fallback: extrair slides do texto
            logger.warning("Falha no parse JSON, usando fallback")
            return self._fallback_slide_structure(response)

    def _fallback_slide_structure(self, text: str) -> List[Dict]:
        """Estrutura fallback caso o parse JSON falhe."""
        return [
            {
                "title": f"Slide {i+1}",
                "content": "Conteúdo gerado pela IA",
                "image_description": "Imagem profissional relacionada ao tema"
            }
            for i in range(7)
        ]

    def _generate_image_with_semantic_analysis(
        self, user: User, slide_title: str, slide_content: str,
        slide_number: int, total_slides: int
    ) -> str:
        """
        REUSO 100% do DailyIdeasService.
        Análise semântica em 3 etapas + logo da empresa.
        
        Este método implementa o mesmo fluxo de qualidade dos Posts Diários:
        1. Análise de contexto
        2. Adaptação à marca
        3. Geração de imagem com logo
        """
        self.prompt_service.set_user(user)
        
        # Combinar título e conteúdo para análise
        combined_content = f"{slide_title}\n{slide_content}"

        # Etapa 1: Análise de contexto
        context_prompt = self._build_semantic_context_prompt(combined_content, slide_number, total_slides)
        context_analysis = self.ai_service.generate_text(context_prompt, user)

        # Etapa 2: Adaptação à marca
        brand_prompt = self._build_brand_adaptation_prompt(context_analysis)
        brand_adaptation = self.ai_service.generate_text(brand_prompt, user)

        # Etapa 3: Prompt de imagem otimizado
        image_prompt_final = self._build_final_image_prompt(
            brand_adaptation, slide_number, total_slides
        )

        # Buscar logo (igual DailyIdeasService)
        try:
            creator_profile = CreatorProfile.objects.get(user=user)
            logo_base64 = creator_profile.logo or ""
        except CreatorProfile.DoesNotExist:
            logger.warning(f"CreatorProfile não encontrado para usuário {user.id}")
            logo_base64 = ""

        # Gerar imagem com logo
        image_url = self.ai_service.generate_image(
            prompt_list=[image_prompt_final],
            image_attachment=logo_base64,  # Logo incluída!
            user=user,
        )

        return image_url

    def _build_semantic_context_prompt(self, content: str, slide_number: int, total_slides: int) -> str:
        """Etapa 1: Análise de contexto semântico."""
        return f"""Você é um especialista em análise de conteúdo para redes sociais.

CONTEXTO:
Este é o slide {slide_number} de {total_slides} de um carrossel Instagram.

CONTEÚDO DO SLIDE:
{content}

TAREFA:
Analise o conteúdo e extraia:
1. Conceito principal do slide
2. Emoção/sentimento a transmitir
3. Elementos visuais que reforçam a mensagem
4. Estilo visual recomendado (profissional, descontraído, moderno, etc)

RESPONDA EM FORMATO ESTRUTURADO (JSON):
{{
  "conceito": "...",
  "emocao": "...",
  "elementos_visuais": ["...", "..."],
  "estilo": "..."
}}
"""

    def _build_brand_adaptation_prompt(self, context_analysis: str) -> str:
        """Etapa 2: Adaptação à identidade da marca."""
        profile_data = self.prompt_service._get_creator_profile_data()
        
        colors = profile_data.get('color_palette', [])
        color_info = f"Paleta: {', '.join([c for c in colors if c])}" if colors else "Cores da marca"

        return f"""Você é um especialista em branding visual para Instagram.

ANÁLISE DO CONTEÚDO:
{context_analysis}

IDENTIDADE DA MARCA:
- Nome: {profile_data.get('business_name', 'N/A')}
- Tom de voz: {profile_data.get('voice_tone', 'N/A')}
- Estilo visual: {profile_data.get('visual_style', 'N/A')}
- {color_info}

TAREFA:
Adapte a análise para refletir a identidade da marca.
Sugira como integrar os elementos visuais com:
1. Cores da marca
2. Estilo visual da marca
3. Tom de voz visual

RESPONDA EM TEXTO CORRIDO (não JSON):
Descreva a imagem ideal que transmite o conceito adaptado à marca.
"""

    def _build_final_image_prompt(self, brand_adaptation: str, slide_number: int, total_slides: int) -> str:
        """Etapa 3: Prompt final otimizado para geração de imagem."""
        position_context = ""
        if slide_number == 1:
            position_context = "Este é o slide de CAPA, deve chamar atenção imediata."
        elif slide_number == total_slides:
            position_context = "Este é o slide FINAL, deve ter conclusão e CTA visual."
        else:
            position_context = f"Este é o slide {slide_number} de {total_slides}."

        return f"""Crie uma imagem profissional para Instagram (formato 4:5, 1080x1350px).

{position_context}

DESCRIÇÃO DA IMAGEM:
{brand_adaptation}

REQUISITOS TÉCNICOS:
- Alta qualidade visual
- Composição equilibrada
- Espaço para texto (se necessário)
- Estilo consistente com a marca
- Formato vertical (4:5 ratio)

A logo da marca será automaticamente adicionada pela ferramenta.
"""

    def _build_carousel_caption(self, theme: str, user: User) -> str:
        """Gera legenda para o carrossel completo."""
        self.prompt_service.set_user(user)
        profile_data = self.prompt_service._get_creator_profile_data()

        prompt = f"""Crie uma legenda engajante para um carrossel Instagram sobre: "{theme}"

CONTEXTO DO NEGÓCIO:
- Nome: {profile_data.get('business_name', 'N/A')}
- Tom de voz: {profile_data.get('voice_tone', 'N/A')}
- Público-alvo: {profile_data.get('target_audience', 'N/A')}

ESTRUTURA DA LEGENDA:
1. Gancho inicial (1-2 linhas que prendem atenção)
2. Contexto/valor do carrossel (2-3 linhas)
3. Incentivo ao swipe ("Deslize para ver →")
4. CTA final
5. Hashtags relevantes (5-10)

FORMATO: Texto natural, sem JSON.
"""
        return self.ai_service.generate_text(prompt, user)

