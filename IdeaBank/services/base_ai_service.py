import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from CreatorProfile.models import CreatorProfile
from django.contrib.auth.models import User
from IdeaBank.models import CampaignIdea, VoiceTone


class ProgressTracker:
    """Track real progress of AI generation tasks."""

    def __init__(self):
        self.current_step = 0
        self.total_steps = 0
        self.step_details = []
        self.start_time = None

    def set_steps(self, steps: List[str]):
        """Set the steps for the generation process."""
        self.step_details = steps
        self.total_steps = len(steps)
        self.current_step = 0
        self.start_time = time.time()

    def next_step(self, step_name: str = None):
        """Move to next step."""
        if step_name:
            self.step_details[self.current_step] = step_name
        self.current_step += 1

    def get_progress(self) -> Dict:
        """Get current progress information."""
        if self.total_steps == 0:
            return {
                "percentage": 0,
                "current_step": 0,
                "total_steps": 0,
                "current_step_name": "",
                "elapsed_time": 0
            }

        percentage = min(
            100, int((self.current_step / self.total_steps) * 100))
        current_step_name = self.step_details[self.current_step -
                                              1] if self.current_step > 0 else ""
        elapsed_time = time.time() - self.start_time if self.start_time else 0

        return {
            "percentage": percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_name": current_step_name,
            "elapsed_time": round(elapsed_time, 1)
        }


class BaseAIService(ABC):
    """Base class for AI service implementations."""

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.progress_tracker = ProgressTracker()

    @abstractmethod
    def _validate_credits(self, user: User, estimated_tokens: int, model_name: str) -> bool:
        """Validate if user has sufficient credits."""
        pass

    @abstractmethod
    def _deduct_credits(self, user: User, actual_tokens: int, model_name: str, description: str) -> bool:
        """Deduct credits after AI operation."""
        pass

    @abstractmethod
    def _estimate_tokens(self, prompt: str, model_name: str) -> int:
        """Estimate token count for a prompt."""
        pass

    @abstractmethod
    def _select_optimal_model(self, user: User, estimated_tokens: int, preferred_provider: str = None) -> str:
        """Select the optimal AI model for the operation."""
        pass

    @abstractmethod
    def _make_ai_request(self, prompt: str, model_name: str, api_key: str = None) -> str:
        """Make the actual AI API request."""
        pass

    def _build_campaign_prompt(self, user: User, config: Dict) -> str:
        """Build prompt for campaign idea generation."""
        profile = CreatorProfile.objects.filter(user=user).first()

        # Build persona section
        persona_section = self._build_persona_section(config)

        # Build social media section
        social_media_section = self._build_social_media_section(
            profile) if profile else ""

        # Build objectives section
        objectives = config.get('objectives', [])
        objectives_text = ", ".join(
            objectives) if objectives else "Não especificado"

        # Build platforms section
        platforms = config.get('platforms', [])
        platforms_text = ", ".join(
            platforms) if platforms else "Não especificado"

        # Build content types section
        content_types = config.get('content_types', {})
        content_types_text = ""
        if content_types:
            content_types_text = "\n".join([
                f"- {platform}: {', '.join(types)}"
                for platform, types in content_types.items()
            ])

        # Build voice tone section
        voice_tone = config.get('voice_tone', 'professional')
        voice_tone_text = dict(VoiceTone.choices).get(voice_tone, voice_tone)

        # Build product/service section
        product_description = config.get(
            'product_description', 'Não especificado')
        value_proposition = config.get('value_proposition', 'Não especificado')
        campaign_urgency = config.get('campaign_urgency', 'Não especificado')

        prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais. 
Sua tarefa é gerar EXATAMENTE 1 ideia criativa e estratégica para uma campanha de marketing.

CONTEXTO DA CAMPANHA:
- Título: {config.get('title', 'Não especificado')}
- Descrição: {config.get('description', 'Não especificado')}
- Objetivos: {objectives_text}
- Plataformas: {platforms_text}
- Tipos de Conteúdo: {content_types_text}
- Tom de Voz: {voice_tone_text}
- Produto/Serviço: {product_description}
- Proposta de Valor: {value_proposition}
- Urgência da Campanha: {campaign_urgency}

{persona_section}

{social_media_section}

INSTRUÇÕES CRÍTICAS:
1. Gere EXATAMENTE 1 ideia criativa e estratégica
2. Cada ideia DEVE ser específica para as plataformas e tipos de conteúdo solicitados
3. NÃO gere ideias para plataformas não solicitadas
4. NÃO gere tipos de conteúdo não solicitados
5. Cada ideia deve incluir:
   - Título atrativo e específico
   - Descrição clara e estratégica
   - Conteúdo principal detalhado
   - Plataforma específica (apenas as solicitadas)
   - Tipo de conteúdo específico (apenas os solicitados)
   - EXATAMENTE 3 variações (A, B, C) com:
     * Headline impactante
     * Copy persuasivo e detalhado
     * CTA claro e acionável
     * Hashtags relevantes e estratégicos
     * Descrição visual detalhada
     * Composição de cores específica
   - Estratégia de implementação
   - Métricas de sucesso
   - Próximos passos

FORMATO DE RESPOSTA OBRIGATÓRIO:
Retorne APENAS um JSON válido com a seguinte estrutura:
{{
  "ideas": [
    {{
      "title": "Título da Ideia",
      "description": "Descrição detalhada da ideia",
      "content": {{
        "plataforma": "plataforma_solicitada",
        "tipo_conteudo": "tipo_solicitado",
        "titulo_principal": "Título principal da ideia",
        "variacao_a": {{
          "headline": "Headline da variação A",
          "copy": "Copy detalhado da variação A",
          "cta": "Call to action da variação A",
          "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
          "visual_description": "Descrição visual detalhada da variação A",
          "color_composition": "Composição de cores da variação A"
        }},
        "variacao_b": {{
          "headline": "Headline da variação B",
          "copy": "Copy detalhado da variação B",
          "cta": "Call to action da variação B",
          "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
          "visual_description": "Descrição visual detalhada da variação B",
          "color_composition": "Composição de cores da variação B"
        }},
        "variacao_c": {{
          "headline": "Headline da variação C",
          "copy": "Copy detalhado da variação C",
          "cta": "Call to action da variação C",
          "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
          "visual_description": "Descrição visual detalhada da variação C",
          "color_composition": "Composição de cores da variação C"
        }},
        "estrategia_implementacao": "Estratégia detalhada de implementação",
        "metricas_sucesso": ["Métrica 1", "Métrica 2", "Métrica 3"],
        "proximos_passos": ["Passo 1", "Passo 2", "Passo 3"]
      }},
      "platform": "plataforma_solicitada",
      "content_type": "tipo_solicitado"
    }}
  ]
}}

REGRAS OBRIGATÓRIAS:
- Gere ideias APENAS para as plataformas solicitadas: {platforms_text}
- Use APENAS os tipos de conteúdo solicitados: {content_types_text}
- Cada ideia deve ter EXATAMENTE 3 variações (A, B, C)
- Inclua SEMPRE estratégia, métricas e próximos passos
- Retorne APENAS o JSON, sem texto adicional
- Use o idioma português brasileiro
- Seja criativo, estratégico e específico
- Foque nos objetivos solicitados: {objectives_text}
"""
        return prompt.strip()

    def _build_persona_section(self, config: Dict) -> str:
        """Build persona section for the prompt."""
        sections = []

        if config.get('persona_age'):
            sections.append(f"Idade: {config['persona_age']}")
        if config.get('persona_location'):
            sections.append(f"Localização: {config['persona_location']}")
        if config.get('persona_income'):
            sections.append(f"Renda: {config['persona_income']}")
        if config.get('persona_interests'):
            sections.append(f"Interesses: {config['persona_interests']}")
        if config.get('persona_behavior'):
            sections.append(f"Comportamento: {config['persona_behavior']}")
        if config.get('persona_pain_points'):
            sections.append(
                f"Dores e necessidades: {config['persona_pain_points']}")

        if sections:
            return "PERSONA ALVO:\n" + "\n".join(f"- {section}" for section in sections)
        return ""

    def _build_social_media_section(self, profile: CreatorProfile) -> str:
        """Build social media section for the prompt."""
        if not profile:
            return ""

        sections = []
        if profile.instagram_username:
            sections.append(f"Instagram: @{profile.instagram_username}")
        if profile.tiktok_username:
            sections.append(f"TikTok: @{profile.tiktok_username}")
        if profile.youtube_channel:
            sections.append(f"YouTube: {profile.youtube_channel}")
        if profile.linkedin_url:
            sections.append(f"LinkedIn: {profile.linkedin_url}")

        if sections:
            return "REDES SOCIAIS EXISTENTES:\n" + "\n".join(f"- {section}" for section in sections)
        return ""

    def _normalize_content_type(self, raw_content_type: str, platform: str) -> str:
        """Normalize content type based on platform."""
        content_type_mapping = {
            'post': 'post',
            'story': 'story',
            'reel': 'reel',
            'video': 'video',
            'carousel': 'carousel',
            'live': 'live',
            'ad': 'ad',
            'tweet': 'post' if platform == 'twitter' else 'post',
            'thread': 'carousel' if platform == 'twitter' else 'post',
        }

        normalized = content_type_mapping.get(
            raw_content_type.lower(), raw_content_type.lower())

        # Platform-specific adjustments
        if platform == 'instagram' and normalized == 'tweet':
            normalized = 'post'
        elif platform == 'tiktok' and normalized in ['post', 'carousel']:
            normalized = 'video'

        return normalized

    def _parse_campaign_response(self, response_text: str, config: Dict) -> List[Dict]:
        """Parse AI response for campaign ideas."""
        try:
            # Try to extract JSON from response
            ideas_data = self._extract_multiple_json_objects(
                response_text, config)

            if not ideas_data:
                # Fallback to simple parsing
                ideas_data = self._create_fallback_ideas(config)

            return ideas_data

        except Exception as e:
            print(f"Error parsing campaign response: {e}")
            return self._create_fallback_ideas(config)

    def _extract_multiple_json_objects(self, response_text: str, config: Dict) -> List[Dict]:
        """Extract multiple JSON objects from response text."""
        try:
            # Try to find JSON array
            start_idx = response_text.find('{')
            if start_idx == -1:
                return []

            # Find the end of the JSON
            brace_count = 0
            end_idx = start_idx

            for i, char in enumerate(response_text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

            if end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                parsed_data = json.loads(json_text)

                if 'ideas' in parsed_data and isinstance(parsed_data['ideas'], list):
                    return parsed_data['ideas']

                # If response is directly a list of ideas
                if isinstance(parsed_data, list):
                    return parsed_data

        except Exception as e:
            print(f"Error extracting JSON: {e}")

        return []

    def _create_fallback_ideas(self, config: Dict) -> List[Dict]:
        """Create fallback ideas if AI response parsing fails."""
        platforms = config.get('platforms', ['instagram'])
        content_types = config.get('content_types', {})
        objectives = config.get('objectives', ['engagement'])

        fallback_ideas = []
        for i, platform in enumerate(platforms[:1]):  # Max 1 idea
            # Get content types for this platform
            platform_content_types = content_types.get(platform, ['post'])
            content_type = platform_content_types[0] if platform_content_types else 'post'

            idea = {
                'title': f"Ideia {i+1} para {platform.title()} - {content_type.title()}",
                'description': f"Conteúdo estratégico para {platform} ({content_type}) focado em {', '.join(objectives)}",
                'content': {
                    'plataforma': platform,
                    'tipo_conteudo': content_type,
                    'titulo_principal': f"Ideia {i+1} para {platform.title()}",
                    'variacao_a': {
                        'headline': f"Headline A para {platform}",
                        'copy': f"Copy da variação A para {platform} focado em {', '.join(objectives)}",
                        'cta': "Clique aqui para saber mais",
                        'hashtags': [f"#{platform}", "#marketing", "#conteudo"],
                        'visual_description': f"Imagem atrativa para {platform}",
                        'color_composition': "Cores vibrantes e contrastantes"
                    },
                    'variacao_b': {
                        'headline': f"Headline B para {platform}",
                        'copy': f"Copy da variação B para {platform} focado em {', '.join(objectives)}",
                        'cta': "Saiba mais na bio",
                        'hashtags': [f"#{platform}", "#estrategia", "#engajamento"],
                        'visual_description': f"Vídeo curto para {platform}",
                        'color_composition': "Tons neutros com detalhes coloridos"
                    },
                    'variacao_c': {
                        'headline': f"Headline C para {platform}",
                        'copy': f"Copy da variação C para {platform} focado em {', '.join(objectives)}",
                        'cta': "Descubra mais",
                        'hashtags': [f"#{platform}", "#resultados", "#sucesso"],
                        'visual_description': f"Carrossel para {platform}",
                        'color_composition': "Paleta monocromática elegante"
                    },
                    'estrategia_implementacao': f"Implementar {content_type} no {platform} com foco em {', '.join(objectives)}",
                    'metricas_sucesso': ["Engajamento", "Alcance", "Conversões"],
                    'proximos_passos': ["Criar conteúdo", "Agendar publicação", "Monitorar resultados"]
                },
                'platform': platform,
                'content_type': content_type
            }
            fallback_ideas.append(idea)

        return fallback_ideas

    def generate_campaign_ideas_with_progress(self, user: User, config: Dict, progress_callback=None) -> Tuple[List[Dict], Dict]:
        """Generate campaign ideas with progress tracking."""
        steps = [
            "Inicializando geração de campanha...",
            "Validando créditos do usuário...",
            "Construindo prompt da campanha...",
            "Conectando com IA...",
            "Gerando ideias da campanha...",
            "Processando resposta da IA...",
            "Validando formato dos dados...",
            "Estruturando ideias finais...",
            "Finalizando geração..."
        ]

        self.progress_tracker.set_steps(steps)

        try:
            # Step 1: Initialize
            self.progress_tracker.next_step()
            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 2: Validate credits (skip for public users)
            self.progress_tracker.next_step()
            if user and user.is_authenticated:
                estimated_tokens = self._estimate_tokens(
                    self._build_campaign_prompt(user, config), self.model_name)
                if not self._validate_credits(user, estimated_tokens, self.model_name):
                    raise Exception(
                        "Créditos insuficientes para gerar campanha")

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 3: Build prompt
            self.progress_tracker.next_step()
            prompt = self._build_campaign_prompt(user, config)

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 4: Connect to AI
            self.progress_tracker.next_step()
            api_key = config.get('gemini_api_key')
            response_text = self._make_ai_request(
                prompt, self.model_name, api_key)

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 5: Generate ideas
            self.progress_tracker.next_step()

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 6: Process response
            self.progress_tracker.next_step()
            ideas_data = self._parse_campaign_response(response_text, config)

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 7: Validate data
            self.progress_tracker.next_step()
            if not ideas_data:
                raise Exception("Falha ao gerar ideias da campanha")

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 8: Structure final ideas
            self.progress_tracker.next_step()
            final_ideas = []
            for idea_data in ideas_data[:1]:  # Ensure max 1 idea
                final_idea = self._create_idea_from_campaign_data(
                    idea_data, config)
                final_ideas.append(final_idea)

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 9: Finalize
            self.progress_tracker.next_step()
            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Deduct credits (only for authenticated users)
            if user and user.is_authenticated:
                actual_tokens = self._estimate_tokens(
                    prompt + str(ideas_data), self.model_name)
                self._deduct_credits(user, actual_tokens,
                                     self.model_name, "Geração de campanha")

            return final_ideas, self.progress_tracker.get_progress()

        except Exception as e:
            print(f"Error in generate_campaign_ideas_with_progress: {e}")
            raise e

    def _create_idea_from_campaign_data(self, campaign_data: Dict, config: Dict) -> Dict:
        """Create a structured idea from campaign data."""
        platform = campaign_data.get(
            'platform', config.get('platforms', ['instagram'])[0])
        content_type = campaign_data.get('content_type', 'post')

        # Normalize content type
        normalized_content_type = self._normalize_content_type(
            content_type, platform)

        # Check if we have structured content with variations
        content = campaign_data.get('content', {})
        has_structured_content = (
            isinstance(content, dict) and
            'variacao_a' in content and
            'variacao_b' in content and
            'variacao_c' in content
        )

        # Only add fallback variations if we don't have structured content
        variations = []
        if not has_structured_content:
            variations = campaign_data.get('variations', [])
            if not variations:
                # Create default variation
                variations = [{
                    'headline': campaign_data.get('title', 'Título padrão'),
                    'copy': campaign_data.get('description', 'Descrição padrão'),
                    'cta': 'Clique aqui para saber mais',
                    'hashtags': [f"#{platform}", "#marketing"],
                    'visual_description': 'Imagem atrativa e relevante',
                    'color_composition': 'Cores vibrantes e contrastantes'
                }]

        return {
            'title': campaign_data.get('title', 'Ideia sem título'),
            'description': campaign_data.get('description', 'Descrição não fornecida'),
            'content': campaign_data.get('content', 'Conteúdo não fornecido'),
            'platform': platform,
            'content_type': normalized_content_type,
            'variations': variations if variations else None
        }

    def improve_idea_with_progress(self, user: User, current_idea: CampaignIdea, improvement_prompt: str, api_key: str = None, progress_callback=None) -> Tuple[Dict, Dict]:
        """Improve an existing idea with progress tracking."""
        steps = [
            "Inicializando melhoria da ideia...",
            "Validando créditos do usuário...",
            "Construindo prompt de melhoria...",
            "Conectando com IA...",
            "Gerando melhoria da ideia...",
            "Processando resposta da IA...",
            "Validando dados melhorados...",
            "Estruturando ideia final...",
            "Finalizando melhoria..."
        ]

        self.progress_tracker.set_steps(steps)

        try:
            # Step 1: Initialize
            self.progress_tracker.next_step()
            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 2: Validate credits
            self.progress_tracker.next_step()
            prompt = self._build_improvement_prompt(
                user, current_idea, improvement_prompt)
            estimated_tokens = self._estimate_tokens(prompt, self.model_name)
            if not self._validate_credits(user, estimated_tokens, self.model_name):
                raise Exception("Créditos insuficientes para melhorar ideia")

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 3: Build prompt
            self.progress_tracker.next_step()

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 4: Connect to AI
            self.progress_tracker.next_step()
            response_text = self._make_ai_request(
                prompt, self.model_name, api_key)

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 5: Generate improvement
            self.progress_tracker.next_step()

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 6: Process response
            self.progress_tracker.next_step()
            improved_data = self._process_improved_idea(
                response_text, current_idea)

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 7: Validate data
            self.progress_tracker.next_step()
            if not improved_data:
                raise Exception("Falha ao melhorar ideia")

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 8: Structure final idea
            self.progress_tracker.next_step()

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 9: Finalize
            self.progress_tracker.next_step()
            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Deduct credits
            actual_tokens = self._estimate_tokens(
                prompt + str(improved_data), self.model_name)
            self._deduct_credits(user, actual_tokens,
                                 self.model_name, "Melhoria de ideia")

            return improved_data, self.progress_tracker.get_progress()

        except Exception as e:
            print(f"Error in improve_idea_with_progress: {e}")
            raise e

    def _build_improvement_prompt(self, user: User, current_idea: CampaignIdea, improvement_prompt: str) -> str:
        """Build prompt for idea improvement."""
        profile = CreatorProfile.objects.filter(user=user).first()

        # Try to parse the existing structured content
        current_content = {}
        try:
            if isinstance(current_idea.content, str):
                # Remove any extra quotes and parse
                content_str = current_idea.content.strip("'\"")
                current_content = eval(
                    content_str) if content_str.startswith('{') else {}
            elif isinstance(current_idea.content, dict):
                current_content = current_idea.content
        except:
            current_content = {}

        prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais.
Sua tarefa é melhorar uma ideia de campanha existente baseada no feedback fornecido.

IDEIA ATUAL:
- Título: {current_idea.title}
- Descrição: {current_idea.description}
- Plataforma: {current_idea.platform}
- Tipo de Conteúdo: {current_idea.content_type}

ESTRUTURA ATUAL DO CONTEÚDO:
{json.dumps(current_content, indent=2, ensure_ascii=False) if current_content else "Estrutura não disponível"}

FEEDBACK PARA MELHORIA:
{improvement_prompt}

CONTEXTO DO CRIADOR:
{self._build_social_media_section(profile) if profile else "Perfil não disponível"}

INSTRUÇÕES CRÍTICAS:
1. Analise a ideia atual e o feedback fornecido
2. Melhore a ideia mantendo sua essência e estrutura
3. Aplique as melhorias solicitadas
4. MANTENHA EXATAMENTE a mesma estrutura de conteúdo com todas as variações
5. Seja criativo e estratégico
6. Preserve todos os campos: plataforma, tipo_conteudo, titulo_principal, variacao_a, variacao_b, variacao_c, estrategia_implementacao, metricas_sucesso, proximos_passos

FORMATO DE RESPOSTA OBRIGATÓRIO:
Retorne APENAS um JSON válido com a estrutura COMPLETA melhorada:
{{
  "title": "Título melhorado",
  "description": "Descrição melhorada",
  "content": {{
    "plataforma": "{current_idea.platform}",
    "tipo_conteudo": "{current_idea.content_type}",
    "titulo_principal": "Título principal melhorado",
    "variacao_a": {{
      "headline": "Headline melhorado da variação A",
      "copy": "Copy melhorado da variação A",
      "cta": "CTA melhorado da variação A",
      "hashtags": ["hashtag1", "hashtag2"],
      "visual_description": "Descrição visual melhorada da variação A",
      "color_composition": "Composição de cores melhorada da variação A"
    }},
    "variacao_b": {{
      "headline": "Headline melhorado da variação B",
      "copy": "Copy melhorado da variação B",
      "cta": "CTA melhorado da variação B",
      "hashtags": ["hashtag1", "hashtag2"],
      "visual_description": "Descrição visual melhorada da variação B",
      "color_composition": "Composição de cores melhorada da variação B"
    }},
    "variacao_c": {{
      "headline": "Headline melhorado da variação C",
      "copy": "Copy melhorado da variação C",
      "cta": "CTA melhorado da variação C",
      "hashtags": ["hashtag1", "hashtag2"],
      "visual_description": "Descrição visual melhorada da variação C",
      "color_composition": "Composição de cores melhorada da variação C"
    }},
    "estrategia_implementacao": "Estratégia melhorada",
    "metricas_sucesso": ["Métrica 1", "Métrica 2", "Métrica 3"],
    "proximos_passos": ["Passo 1", "Passo 2", "Passo 3"]
  }}
}}

REGRAS OBRIGATÓRIAS:
- MANTENHA EXATAMENTE a mesma estrutura de conteúdo
- Preserve todas as variações (A, B, C)
- Inclua SEMPRE estratégia, métricas e próximos passos
- Retorne APENAS o JSON, sem texto adicional
- Use o idioma português brasileiro
- Aplique as melhorias solicitadas no feedback
- Mantenha a qualidade e relevância
"""
        return prompt.strip()

    def _process_improved_idea(self, response_text: str, current_idea: CampaignIdea) -> Dict:
        """Process improved idea response."""
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            if start_idx == -1:
                return None

            end_idx = response_text.rfind('}') + 1
            json_text = response_text[start_idx:end_idx]

            improved_data = json.loads(json_text)

            # Extract the improved content structure
            improved_content = improved_data.get('content', {})

            # Get the primary variation for the main fields
            primary_variation = None
            if isinstance(improved_content, dict):
                if 'variacao_a' in improved_content:
                    primary_variation = improved_content['variacao_a']
                elif 'variacao_b' in improved_content:
                    primary_variation = improved_content['variacao_b']
                elif 'variacao_c' in improved_content:
                    primary_variation = improved_content['variacao_c']

            return {
                'title': improved_data.get('title', current_idea.title),
                'description': improved_data.get('description', current_idea.description),
                'content': improved_content,
                'platform': improved_content.get('plataforma', current_idea.platform) if isinstance(improved_content, dict) else current_idea.platform,
                'content_type': improved_content.get('tipo_conteudo', current_idea.content_type) if isinstance(improved_content, dict) else current_idea.content_type,
                'headline': primary_variation.get('headline', '') if primary_variation else '',
                'copy': primary_variation.get('copy', '') if primary_variation else '',
                'cta': primary_variation.get('cta', '') if primary_variation else '',
                'hashtags': primary_variation.get('hashtags', []) if primary_variation else [],
                'visual_description': primary_variation.get('visual_description', '') if primary_variation else '',
                'color_composition': primary_variation.get('color_composition', '') if primary_variation else ''
            }

        except Exception as e:
            print(f"Error processing improved idea: {e}")
            return None
