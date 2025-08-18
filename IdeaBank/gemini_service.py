import ast
import json
import os
import time
from typing import Dict, List, Tuple

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

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
            return {"percentage": 0, "current_step": 0, "total_steps": 0, "current_step_name": "", "elapsed_time": 0}

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


class GeminiService:
    """Service for interacting with Google Gemini AI."""

    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai não está instalado. Execute: pip install google-generativeai")

        # Get default API key from environment
        self.default_api_key = os.getenv('GEMINI_API_KEY', '')

        # Initialize without API key - will be set per request
        genai.configure(api_key="")
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _build_campaign_prompt(self, user: User, config: Dict) -> str:
        """Build the new structured prompt for campaign generation."""

        # Get user's creator profile
        profile = None
        if user:
            try:
                profile = CreatorProfile.objects.get(user=user)
            except CreatorProfile.DoesNotExist:
                profile = None

        # Build persona section
        persona_complete = self._build_persona_section(config)

        # Build social media details
        social_media_details = self._build_social_media_section(
            profile) if profile else "Não especificado"

        # Build creator profile section
        professional_name = profile.professional_name if profile else "Não especificado"
        profession = profile.profession if profile else "Não especificado"
        specialization = profile.specialization if profile else "Não especificado"
        primary_font = profile.primary_font if profile else "Não especificado"
        secondary_font = profile.secondary_font if profile else "Não especificado"

        # Campaign details
        objective_detail = config.get('title', 'Não especificado')
        product_description = config.get(
            'product_description', 'Não especificado')
        value_proposition = config.get('value_proposition', 'Não especificado')
        campaign_urgency = config.get('campaign_urgency', 'Não especificado')
        voice_tone = config.get('voice_tone', 'professional')

        # Get voice tone display name
        voice_tone_display = dict(VoiceTone.choices).get(
            voice_tone, voice_tone)

        # Build platform and content type section
        platforms = config.get('platforms', [])
        content_types = config.get('content_types', {})

        platform_content_section = ""
        for platform in platforms:
            platform_content_types = content_types.get(platform, [])
            if platform_content_types:
                platform_content_section += f"- {platform}: {', '.join(platform_content_types)}\n"
            else:
                platform_content_section += f"- {platform}: Todos os tipos\n"

        prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais,
especializado em coaching executivo e desenvolvimento de liderança.

## 🎯 CONTEXTO DA CAMPANHA
Objetivo Principal: {objective_detail}
Produto/Serviço: {product_description}
Proposta de Valor: {value_proposition}
Urgência: {campaign_urgency}
Tom de Voz: {voice_tone_display}

## 👤 PERFIL DO CRIADOR
Nome: {professional_name}
Expertise: {profession} especializado em {specialization}

Redes Sociais Ativas:
{social_media_details}

## 🎨 IDENTIDADE VISUAL DA MARCA
Tipografia:
- Títulos: {primary_font}
- Corpo: {secondary_font}

## 🎯 PERSONA ALVO DETALHADA
{persona_complete}

## 📱 PLATAFORMAS E TIPOS DE CONTEÚDO:
{platform_content_section}

## INSTRUÇÕES ESPECÍFICAS:
1. Crie conteúdo ESPECÍFICO APENAS para as plataformas solicitadas: {', '.join(platforms)}
2. Use a paleta de cores EXATA fornecida na composição visual
3. Estruture o conteúdo para {objective_detail}
4. Enderece as dores específicas da persona
5. Inclua gatilhos mentais apropriados para vendas
6. Forneça 3 variações IDÊNTICAS de copy para testes A/B (todas devem ter o mesmo conteúdo)
7. Sugira elementos visuais específicos (não genéricos)
8. IMPORTANTE: Gere conteúdo APENAS para as plataformas especificadas acima
9. Para o campo "tipo_conteudo", use APENAS um destes valores: post, story, reel, video, carousel, live, custom

## FORMATO DE RESPOSTA ESTRUTURADO:
Gere APENAS um JSON para a plataforma solicitada. Se múltiplas plataformas foram solicitadas, gere um JSON para cada uma, mas cada JSON deve ser independente:

{{
  "plataforma": "{platforms[0] if len(platforms) == 1 else 'plataforma_solicitada'}",
  "tipo_conteudo": "post",
  "titulo_principal": "texto aqui",
  "variacao_a": {{
    "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "variacao_b": {{
    "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "variacao_c": {{
    "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "estrategia_implementacao": "texto aqui",
  "metricas_sucesso": ["texto aqui"],
  "proximos_passos": ["texto aqui"]
}}

IMPORTANTE: 
- Retorne um JSON para CADA plataforma solicitada
- Se apenas uma plataforma foi especificada, retorne apenas um JSON
- Seja específico e detalhado para cada plataforma solicitada
- Use português brasileiro
- Foque na conversão e vendas
- Adapte o tom de voz conforme solicitado
- As 3 variações (a, b, c) devem ter conteúdo IDÊNTICO para facilitar testes A/B
- Gere conteúdo APENAS para as plataformas especificadas pelo usuário
- NÃO gere conteúdo para plataformas não solicitadas
"""

        return prompt

    def _normalize_content_type(self, raw_content_type: str, platform: str) -> str:
        """Normalize content type to fit database constraints and valid choices."""
        if not raw_content_type:
            return 'post'

        # Convert to lowercase and remove extra spaces
        normalized = raw_content_type.lower().strip()

        # Map common variations to valid choices
        content_type_mapping = {
            'post': 'post',
            'story': 'story',
            'reel': 'reel',
            'video': 'video',
            'carousel': 'carousel',
            'live': 'live',
            'custom': 'custom',
            # Common variations
            'posts': 'post',
            'stories': 'story',
            'reels': 'reel',
            'videos': 'video',
            'carousels': 'carousel',
            'lives': 'live',
            'customs': 'custom',
            # Platform-specific variations
            'tipo_adequado_para_plataforma': 'post',
            'tipo adequado para plataforma': 'post',
            'tipo adequado': 'post',
            'tipo': 'post',
            # Platform-specific defaults
            'tiktok': 'video',
            'youtube': 'video',
            'instagram': 'post',
            'linkedin': 'post'
        }

        # Try exact match first
        if normalized in content_type_mapping:
            return content_type_mapping[normalized]

        # Try partial matches
        for key, value in content_type_mapping.items():
            if key in normalized or normalized in key:
                return value

        # Platform-specific fallbacks
        platform_defaults = {
            'tiktok': 'video',
            'youtube': 'video',
            'instagram': 'post',
            'linkedin': 'post'
        }

        return platform_defaults.get(platform, 'post')

    def _build_persona_section(self, config: Dict) -> str:
        """Build the persona section of the prompt."""
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

        return '\n'.join(sections) if sections else "Não especificado"

    def _build_social_media_section(self, profile: CreatorProfile) -> str:
        """Build the social media section of the prompt."""
        if not profile:
            return "Não especificado"

        social_media = []
        if profile.linkedin_url:
            social_media.append(f"LinkedIn: {profile.linkedin_url}")
        if profile.instagram_username:
            social_media.append(f"Instagram: @{profile.instagram_username}")
        if profile.youtube_channel:
            social_media.append(f"YouTube: {profile.youtube_channel}")
        if profile.tiktok_username:
            social_media.append(f"TikTok: @{profile.tiktok_username}")

        return '\n'.join(social_media) if social_media else "Não especificado"

    def _configure_api_key(self, api_key: str = None):
        """Configure the Gemini API key for this request."""
        # Use provided key, fallback to user key, then to default env key
        if api_key:
            genai.configure(api_key=api_key)
        elif self.default_api_key:
            genai.configure(api_key=self.default_api_key)
        else:
            raise ValueError("API key é obrigatória para usar o Gemini")

    def generate_campaign_ideas(self, user: User, config: Dict) -> List[Dict]:
        """Generate campaign ideas using the new structured prompt."""
        try:
            # Configure API key if provided, otherwise use default
            api_key = config.get('gemini_api_key')
            self._configure_api_key(api_key)

            prompt = self._build_campaign_prompt(user, config)

            print("=== PROMPT ENVIADO PARA GEMINI ===")
            print(prompt)
            print("=====================================")

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            print("=== RESPOSTA DO GEMINI ===")
            print(response_text)
            print("=============================")

            # Parse the response and structure it
            ideas = self._parse_campaign_response(response_text, config)
            return ideas

        except Exception as e:
            raise Exception(f"Erro na geração de campanhas: {str(e)}")

    def _parse_campaign_response(self, response_text: str, config: Dict) -> List[Dict]:
        """Parse Gemini response into structured campaign ideas.

        This method ensures that only one idea per platform is created,
        preventing duplicate ideas with different variation types.
        """
        ideas = []

        try:
            # Clean the response text
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Try to parse as multiple JSONs first
            try:
                # Look for multiple JSON objects
                import re
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                matches = re.findall(json_pattern, response_text)

                if len(matches) > 1:
                    # Multiple JSONs found - parse each one, but limit to one per platform
                    platform_ideas = {}
                    for match in matches:
                        try:
                            campaign_data = json.loads(match)
                            platform = campaign_data.get(
                                'plataforma', 'unknown')

                            # Only keep one idea per platform to prevent duplicates
                            if platform not in platform_ideas:
                                idea = self._create_idea_from_campaign_data(
                                    campaign_data, config)
                                platform_ideas[platform] = idea
                        except json.JSONDecodeError:
                            continue

                    # Convert to list
                    ideas = list(platform_ideas.values())
                    if ideas:
                        return ideas

                # If multiple JSONs didn't work, try single JSON
                campaign_data = json.loads(response_text)
                ideas.append(self._create_idea_from_campaign_data(
                    campaign_data, config))

            except json.JSONDecodeError:
                # If parsing fails, try to extract multiple JSONs
                ideas = self._extract_multiple_json_objects(
                    response_text, config)

            return ideas

        except Exception as e:
            print(f"Erro ao processar resposta: {str(e)}")
            # Fallback: create basic ideas for each platform
            return self._create_fallback_ideas(config)

    def _create_idea_from_campaign_data(self, campaign_data: Dict, config: Dict) -> Dict:
        """Create idea data from parsed campaign response."""
        platform = campaign_data.get('plataforma', 'instagram')
        raw_content_type = campaign_data.get('tipo_conteudo', 'post')

        # Normalize and validate content_type to fit database constraints
        content_type = self._normalize_content_type(raw_content_type, platform)

        # Validate that the platform is one of the requested platforms
        requested_platforms = config.get('platforms', [])
        if requested_platforms and platform not in requested_platforms:
            # If platform is not in requested list, use the first requested platform
            platform = requested_platforms[0]
            campaign_data['plataforma'] = platform

        # Ensure all variations exist and are equal
        variations = []
        base_variation = None

        # Find the first complete variation as base
        for var_type in ['a', 'b', 'c']:
            var_key = f'variacao_{var_type}'
            if var_key in campaign_data and campaign_data[var_key]:
                base_variation = campaign_data[var_key]
                break

        # If no base variation found, create a default one
        if not base_variation:
            base_variation = {
                'headline': campaign_data.get('titulo_principal', f'Campanha para {platform}'),
                'copy': campaign_data.get('estrategia_implementacao', ''),
                'cta': 'Clique para saber mais!',
                'hashtags': ['#campanha', '#marketing', '#conteudo'],
                'visual_description': 'Descrição visual padrão',
                'color_composition': 'Paleta de cores padrão'
            }

        # Create all three variations with the same content
        for var_type in ['a', 'b', 'c']:
            variations.append({
                'variation_type': var_type,
                'headline': base_variation.get('headline', ''),
                'copy': base_variation.get('copy', ''),
                'cta': base_variation.get('cta', ''),
                'hashtags': base_variation.get('hashtags', []),
                'visual_description': base_variation.get('visual_description', ''),
                'color_composition': base_variation.get('color_composition', ''),
            })

        return {
            'platform': platform,
            'content_type': content_type,
            'title': campaign_data.get('titulo_principal', f'Ideia para {platform}'),
            'description': campaign_data.get('estrategia_implementacao', ''),
            'content': json.dumps(campaign_data, ensure_ascii=False),
            'variations': variations,
            'strategy': campaign_data.get('estrategia_implementacao', ''),
            'metrics': campaign_data.get('metricas_sucesso', []),
            'next_steps': campaign_data.get('proximos_passos', [])
        }

    def _extract_multiple_json_objects(self, response_text: str, config: Dict) -> List[Dict]:
        """Extract multiple JSON objects from response text."""
        ideas = []
        platform_ideas = {}

        # Simple extraction - look for JSON-like structures
        import re
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, response_text)

        for match in matches:
            try:
                campaign_data = json.loads(match)
                platform = campaign_data.get('plataforma', 'unknown')

                # Only keep one idea per platform
                if platform not in platform_ideas:
                    idea = self._create_idea_from_campaign_data(
                        campaign_data, config)
                    platform_ideas[platform] = idea
            except json.JSONDecodeError:
                continue

        # Convert to list
        ideas = list(platform_ideas.values())
        return ideas if ideas else self._create_fallback_ideas(config)

    def _create_fallback_ideas(self, config: Dict) -> List[Dict]:
        """Create fallback ideas when parsing fails."""
        ideas = []
        platforms = config.get('platforms', ['instagram'])

        # Only create one idea per platform
        for platform in platforms:
            content_types = config.get(
                'content_types', {}).get(platform, ['post'])
            content_type = content_types[0] if content_types else 'post'

            # Create base variation data
            base_variation = {
                'headline': f'Campanha para {platform}',
                'copy': f'Conteúdo para {platform} - {config.get("title", "Campanha")}',
                'cta': 'Clique para saber mais!',
                'hashtags': ['#campanha', '#marketing', '#conteudo'],
                'visual_description': f'Descrição visual para {platform}',
                'color_composition': 'Paleta de cores padrão'
            }

            idea = {
                'platform': platform,
                'content_type': content_type,
                'title': f'Campanha para {platform}',
                'description': config.get('description', ''),
                'content': json.dumps({
                    'plataforma': platform,
                    'tipo_conteudo': content_type,
                    'titulo_principal': f'Campanha para {platform}',
                    'variacao_a': base_variation,
                    'variacao_b': base_variation,
                    'variacao_c': base_variation,
                    'estrategia_implementacao': f'Implementar campanha no {platform}',
                    'metricas_sucesso': ['Engajamento', 'Alcance', 'Conversões'],
                    'proximos_passos': ['Monitorar resultados', 'Otimizar campanha']
                }, ensure_ascii=False),
                'variations': [
                    {**base_variation, 'variation_type': 'a'},
                    {**base_variation, 'variation_type': 'b'},
                    {**base_variation, 'variation_type': 'c'}
                ],
                'strategy': f'Implementar campanha no {platform}',
                'metrics': ['Engajamento', 'Alcance', 'Conversões'],
                'next_steps': ['Monitorar resultados', 'Otimizar campanha']
            }

            ideas.append(idea)
            # Break after first platform to ensure only one idea is created
            break

        return ideas

    # Legacy methods for backward compatibility
    def generate_ideas(self, user: User, config: Dict) -> List[Dict]:
        """Legacy method - now redirects to generate_campaign_ideas."""
        return self.generate_campaign_ideas(user, config)

    def _build_prompt(self, user: User, config: Dict) -> str:
        """Legacy method - now redirects to _build_campaign_prompt."""
        return self._build_campaign_prompt(user, config)

    def _build_platform_section(self, config: Dict) -> str:
        """Legacy method - kept for backward compatibility."""
        platforms = config.get('platforms', [])
        content_types = config.get('content_types', {})

        sections = []
        for platform in platforms:
            platform_content_types = content_types.get(platform, [])
            content_types_str = ', '.join(
                platform_content_types) if platform_content_types else "Todos os tipos"
            sections.append(f"- {platform}: {content_types_str}")

        return '\n'.join(sections)

    def _build_creator_section(self, profile: CreatorProfile) -> str:
        """Legacy method - kept for backward compatibility."""
        sections = []

        if profile.professional_name:
            sections.append(f"Nome Profissional: {profile.professional_name}")
        if profile.profession:
            sections.append(f"Profissão: {profile.profession}")
        if profile.specialization:
            sections.append(f"Especialização: {profile.specialization}")

        # Social media
        social_media = []
        if profile.linkedin_url:
            social_media.append("LinkedIn")
        if profile.instagram_username:
            social_media.append("Instagram")
        if profile.youtube_channel:
            social_media.append("YouTube")
        if profile.tiktok_username:
            social_media.append("TikTok")

        if social_media:
            sections.append(f"Redes Sociais: {', '.join(social_media)}")

        # Brand colors
        colors = []
        if profile.primary_color:
            colors.append(f"Cor Primária: {profile.primary_color}")
        if profile.secondary_color:
            colors.append(f"Cor Secundária: {profile.secondary_color}")
        if profile.accent_color_1:
            colors.append(f"Cor de Destaque 1: {profile.accent_color_1}")
        if profile.accent_color_2:
            colors.append(f"Cor de Destaque 2: {profile.accent_color_2}")
        if profile.accent_color_3:
            colors.append(f"Cor de Destaque 3: {profile.accent_color_3}")

        if colors:
            sections.append("Paleta de Cores:\n" + '\n'.join(colors))

        # Typography
        fonts = []
        if profile.primary_font:
            fonts.append(f"Fonte Primária: {profile.primary_font}")
        if profile.secondary_font:
            fonts.append(f"Fonte Secundária: {profile.secondary_font}")

        if fonts:
            sections.append("Tipografia:\n" + '\n'.join(fonts))

        return '\n'.join(sections)

    def _parse_gemini_response(self, response_text: str, config: Dict) -> List[Dict]:
        """Legacy method - kept for backward compatibility."""
        ideas = []

        # Simple parsing - in production, you might want more sophisticated parsing
        platforms = config.get('platforms', [])

        # Split response by platform or create ideas for each platform
        for platform in platforms:
            idea = {
                'title': f"Ideia para {platform}",
                'description': f"Conteúdo gerado para {platform}",
                'content': response_text,
                'platform': platform,
                'content_type': 'post',  # Default
                'status': 'draft'
            }
            ideas.append(idea)

        return ideas

    def improve_idea(self, user: User, current_idea: CampaignIdea, improvement_prompt: str, api_key: str = None) -> Dict:
        """Improve an existing campaign idea using AI."""

        # Configure API key if provided, otherwise use default
        self._configure_api_key(api_key)

        # Get user's creator profile
        try:
            profile = CreatorProfile.objects.get(user=user)
        except CreatorProfile.DoesNotExist:
            profile = None

        # Get the original configuration if available
        config_data = {}
        if hasattr(current_idea, 'campaign') and current_idea.campaign:
            campaign = current_idea.campaign
            config_data = {
                'objectives': campaign.objectives,
                'persona_age': campaign.persona_age,
                'persona_location': campaign.persona_location,
                'persona_income': campaign.persona_income,
                'persona_interests': campaign.persona_interests,
                'persona_behavior': campaign.persona_behavior,
                'persona_pain_points': campaign.persona_pain_points,
                'platforms': campaign.platforms,
                'content_types': campaign.content_types,
            }

        # Build creator profile section
        creator_section = self._build_creator_section(
            profile) if profile else ""

        # Expor JSON atual (se possível) para orientar a IA
        try:
            current_json = json.loads(current_idea.content)
            current_json_pretty = json.dumps(
                current_json, ensure_ascii=False, indent=2)
        except Exception:
            current_json_pretty = "<sem JSON válido>"

        # Build the improvement prompt exigindo o MESMO schema das ideias geradas
        prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais.
Sua tarefa é melhorar uma ideia de campanha existente baseada no feedback específico do usuário.

{creator_section}

IDEIA ATUAL (metadados):
- Título: {current_idea.title}
- Descrição: {current_idea.description}
- Plataforma: {current_idea.platform}
- Tipo de Conteúdo: {current_idea.content_type}
- Status: {current_idea.status}

CONTEÚDO ATUAL (JSON, quando disponível):
{current_json_pretty}

CONTEXTO ORIGINAL DA CAMPANHA:
{self._build_persona_section(config_data) if config_data else "Informações do contexto original não disponíveis."}

SOLICITAÇÃO DE MELHORIA:
{improvement_prompt}

INSTRUÇÕES CRÍTICAS (SIGA À RISCA):
1. Mantenha a mesma plataforma (plataforma) e o mesmo tipo de conteúdo (tipo_conteudo) da ideia atual, salvo instrução explícita em contrário.
2. Retorne APENAS um JSON VÁLIDO (RFC 8259) usando aspas duplas em chaves e strings.
3. O JSON DEVE seguir EXATAMENTE o mesmo schema usado na geração de ideias (abaixo).
4. As variações variacao_a, variacao_b e variacao_c DEVEM ter o MESMO conteúdo (cópias idênticas) para testes A/B.
5. Campos de lista devem ser arrays JSON (por exemplo: hashtags, metricas_sucesso, proximos_passos).
6. Não inclua comentários, texto fora do JSON, explicações ou markdown. Apenas o objeto JSON.
7. IMPORTANTE: Gere conteúdo APENAS para a plataforma {current_idea.platform}, não para outras plataformas.
8. Para o campo "tipo_conteudo", use APENAS um destes valores: post, story, reel, video, carousel, live, custom

SCHEMA OBRIGATÓRIO (substitua pelos seus valores, mantendo as chaves):
{{
            "plataforma": "{current_idea.platform}",
  "tipo_conteudo": "post",
  "titulo_principal": "texto aqui",
  "variacao_a": {{
                "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "variacao_b": {{
                "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "variacao_c": {{
                "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "estrategia_implementacao": "texto aqui",
  "metricas_sucesso": ["texto aqui"],
  "proximos_passos": ["texto aqui"]
}}

RETORNE APENAS este objeto JSON único, válido e completo.
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean and parse JSON response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse robusto do JSON
            try:
                campaign_data = json.loads(response_text)
            except json.JSONDecodeError:
                try:
                    py_obj = ast.literal_eval(response_text)
                    campaign_data = json.loads(json.dumps(py_obj))
                except Exception as e:
                    raise Exception(
                        f"Resposta da IA não é JSON válido: {str(e)}")

            if not isinstance(campaign_data, dict):
                raise Exception("Resposta da IA não é um objeto JSON.")

            # Garantias mínimas de schema
            campaign_data.setdefault('plataforma', current_idea.platform)
            campaign_data.setdefault(
                'tipo_conteudo', current_idea.content_type)

            # Normalizar variações (replicar base se faltar)
            base_variation = None
            for key in ['variacao_a', 'variacao_b', 'variacao_c']:
                if key in campaign_data and campaign_data[key]:
                    base_variation = campaign_data[key]
                    break
            if not base_variation:
                base_variation = {
                    'headline': campaign_data.get('titulo_principal', current_idea.title),
                    'copy': campaign_data.get('estrategia_implementacao', current_idea.description),
                    'cta': 'Clique para saber mais!',
                    'hashtags': ['#campanha', '#marketing', '#conteudo'],
                    'visual_description': 'Descrição visual padrão',
                    'color_composition': 'Paleta de cores padrão'
                }
            for key in ['variacao_a', 'variacao_b', 'variacao_c']:
                campaign_data[key] = {
                    'headline': base_variation.get('headline', ''),
                    'copy': base_variation.get('copy', ''),
                    'cta': base_variation.get('cta', ''),
                    'hashtags': base_variation.get('hashtags', []),
                    'visual_description': base_variation.get('visual_description', ''),
                    'color_composition': base_variation.get('color_composition', ''),
                }

            # Saída padronizada para o frontend
            improved_data = {
                'title': campaign_data.get('titulo_principal', current_idea.title),
                'description': campaign_data.get('estrategia_implementacao', current_idea.description),
                'content': json.dumps(campaign_data, ensure_ascii=False)
            }

            return improved_data

        except json.JSONDecodeError as e:
            raise Exception(f"Erro ao processar resposta da IA: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro na comunicação com a IA: {str(e)}")

    def generate_single_idea(self, user: User, campaign: Dict, idea_params: Dict) -> Dict:
        """Generate a single idea for an existing campaign."""

        # Get user's creator profile
        profile = None
        if user:
            try:
                profile = CreatorProfile.objects.get(user=user)
            except CreatorProfile.DoesNotExist:
                profile = None

        # Build persona section
        persona_complete = self._build_persona_section(campaign)

        # Build creator profile section
        professional_name = profile.professional_name if profile else "Não especificado"
        profession = profile.profession if profile else "Não especificado"
        specialization = profile.specialization if profile else "Não especificado"
        primary_font = profile.primary_font if profile else "Não especificado"
        secondary_font = profile.secondary_font if profile else "Não especificado"

        # Campaign details
        objective_detail = campaign.get('title', 'Não especificado')
        product_description = campaign.get(
            'product_description', 'Não especificado')
        value_proposition = campaign.get(
            'value_proposition', 'Não especificado')
        campaign_urgency = campaign.get('campaign_urgency', 'Não especificado')
        voice_tone = campaign.get('voice_tone', 'professional')

        # Get voice tone display name
        voice_tone_display = dict(VoiceTone.choices).get(
            voice_tone, voice_tone)

        # Idea specific parameters
        platform = idea_params.get('platform', 'instagram')
        content_type = idea_params.get('content_type', 'post')
        variation_type = idea_params.get('variation_type', 'a')

        # Optional pre-filled content
        title = idea_params.get('title', '')
        description = idea_params.get('description', '')
        content = idea_params.get('content', '')

        prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais,
especializado em coaching executivo e desenvolvimento de liderança.

## 🎯 CONTEXTO DA CAMPANHA EXISTENTE
Título da Campanha: {objective_detail}
Produto/Serviço: {product_description}
Proposta de Valor: {value_proposition}
Urgência: {campaign_urgency}
Tom de Voz: {voice_tone_display}

## 👤 PERFIL DO CRIADOR
Nome: {professional_name}
Expertise: {profession} especializado em {specialization}

## 🎨 IDENTIDADE VISUAL DA MARCA
Tipografia:
- Títulos: {primary_font}
- Corpo: {secondary_font}

## 🎯 PERSONA ALVO DETALHADA
{persona_complete}

## 📱 IDEIA ESPECÍFICA SOLICITADA
Plataforma: {platform}
Tipo de Conteúdo: {content_type}
Variação: {variation_type}

## 📝 CONTEÚDO PRÉ-PREENCHIDO (OPCIONAL)
Título: {title if title else 'Gerar automaticamente'}
Descrição: {description if description else 'Gerar automaticamente'}
Conteúdo: {content if content else 'Gerar automaticamente'}

## INSTRUÇÕES ESPECÍFICAS:
1. Crie conteúdo ESPECÍFICO para a plataforma {platform}
2. Use a paleta de cores EXATA fornecida na composição visual
3. Estruture o conteúdo para {objective_detail}
4. Enderece as dores específicas da persona
5. Inclua gatilhos mentais apropriados para vendas
6. Se o usuário forneceu título/descrição/conteúdo, use como base mas melhore
7. Se não forneceu, gere conteúdo completo e original
8. Sugira elementos visuais específicos para {platform}
9. Adapte o tom de voz conforme solicitado
10. Foque na conversão e engajamento
11. IMPORTANTE: Gere 3 variações (A, B, C) com conteúdo IDÊNTICO para testes A/B

## FORMATO DE RESPOSTA ESTRUTURADO:
Gere APENAS um JSON válido com a seguinte estrutura (sem quebras de linha no conteúdo):

{{
  "title": "Título da ideia gerada",
  "description": "Descrição detalhada da ideia",
  "content": {{
    "plataforma": "{platform}",
    "tipo_conteudo": "{content_type}",
    "titulo_principal": "Título principal da ideia",
    "variacao_a": {{
      "headline": "Headline para capturar atenção",
      "copy": "Copy principal do conteúdo - deve ser um texto rico e detalhado, não apenas uma linha. Para {platform}, gere conteúdo específico e envolvente. Use parágrafos bem estruturados e linguagem persuasiva.",
      "cta": "Call-to-action específico",
      "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
      "visual_description": "Descrição detalhada dos elementos visuais",
      "color_composition": "Composição de cores específica para {platform}"
    }},
    "variacao_b": {{
      "headline": "Headline para capturar atenção",
      "copy": "Copy principal do conteúdo - deve ser um texto rico e detalhado, não apenas uma linha. Para {platform}, gere conteúdo específico e envolvente. Use parágrafos bem estruturados e linguagem persuasiva.",
      "cta": "Call-to-action específico",
      "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
      "visual_description": "Descrição detalhada dos elementos visuais",
      "color_composition": "Composição de cores específica para {platform}"
    }},
    "variacao_c": {{
      "headline": "Headline para capturar atenção",
      "copy": "Copy principal do conteúdo - deve ser um texto rico e detalhado, não apenas uma linha. Para {platform}, gere conteúdo específico e envolvente. Use parágrafos bem estruturados e linguagem persuasiva.",
      "cta": "Call-to-action específico",
      "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
      "visual_description": "Descrição detalhada dos elementos visuais",
      "color_composition": "Composição de cores específica para {platform}"
    }},
    "estrategia_implementacao": "Como implementar esta ideia",
    "metricas_sucesso": ["Métrica 1", "Métrica 2"],
    "proximos_passos": ["Passo 1", "Passo 2"]
  }},
  "headline": "Headline principal para capturar atenção",
  "copy": "Copy principal do conteúdo",
  "cta": "Call-to-action específico",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
  "visual_description": "Descrição detalhada dos elementos visuais",
  "color_composition": "Composição de cores específica para {platform}",
  "estrategia_implementacao": "Como implementar esta ideia",
  "metricas_sucesso": ["Métrica 1", "Métrica 2"],
  "proximos_passos": ["Passo 1", "Passo 2"]
}}

EXEMPLO DE ESTRUTURA CORRETA:
{{
  "title": "Transforme sua Liderança com Coaching Executivo",
  "description": "Descubra como o coaching executivo pode elevar sua performance e resultados",
  "content": {{
    "plataforma": "{platform}",
    "tipo_conteudo": "{content_type}",
    "titulo_principal": "Transforme sua Liderança com Coaching Executivo",
    "variacao_a": {{
      "headline": "Eleve sua Liderança ao Próximo Nível",
      "copy": "O coaching executivo é uma ferramenta poderosa para líderes que desejam alcançar seu potencial máximo. Através de sessões personalizadas, você desenvolverá habilidades essenciais como comunicação eficaz, tomada de decisão estratégica e gestão de equipes de alto desempenho. Nossa metodologia comprovada já transformou centenas de executivos em líderes excepcionais.",
      "cta": "Agende sua sessão gratuita agora",
      "hashtags": ["#coachingexecutivo", "#liderança", "#desenvolvimento"],
      "visual_description": "Imagem de um executivo confiante em ambiente corporativo",
      "color_composition": "Tons profissionais de azul e cinza"
    }},
    "variacao_b": {{
      "headline": "Eleve sua Liderança ao Próximo Nível",
      "copy": "O coaching executivo é uma ferramenta poderosa para líderes que desejam alcançar seu potencial máximo. Através de sessões personalizadas, você desenvolverá habilidades essenciais como comunicação eficaz, tomada de decisão estratégica e gestão de equipes de alto desempenho. Nossa metodologia comprovada já transformou centenas de executivos em líderes excepcionais.",
      "cta": "Agende sua sessão gratuita agora",
      "hashtags": ["#coachingexecutivo", "#liderança", "#desenvolvimento"],
      "visual_description": "Imagem de um executivo confiante em ambiente corporativo",
      "color_composition": "Tons profissionais de azul e cinza"
    }},
    "variacao_c": {{
      "headline": "Eleve sua Liderança ao Próximo Nível",
      "copy": "O coaching executivo é uma ferramenta poderosa para líderes que desejam alcançar seu potencial máximo. Através de sessões personalizadas, você desenvolverá habilidades essenciais como comunicação eficaz, tomada de decisão estratégica e gestão de equipes de alto desempenho. Nossa metodologia comprovada já transformou centenas de executivos em líderes excepcionais.",
      "cta": "Agende sua sessão gratuita agora",
      "hashtags": ["#coachingexecutivo", "#liderança", "#desenvolvimento"],
      "visual_description": "Imagem de um executivo confiante em ambiente corporativo",
      "color_composition": "Tons profissionais de azul e cinza"
    }},
    "estrategia_implementacao": "Implemente em 3 fases: diagnóstico, desenvolvimento e acompanhamento",
    "metricas_sucesso": ["Aumento de produtividade", "Melhoria na gestão de equipes"],
    "proximos_passos": ["Agendar consulta inicial", "Definir objetivos específicos"]
  }},
  "headline": "Eleve sua Liderança ao Próximo Nível",
  "copy": "Descubra o poder do coaching executivo personalizado",
  "cta": "Agende sua sessão gratuita agora",
  "hashtags": ["#coachingexecutivo", "#liderança", "#desenvolvimento"],
  "visual_description": "Imagem de um executivo confiante em ambiente corporativo",
  "color_composition": "Tons profissionais de azul e cinza",
  "estrategia_implementacao": "Implemente em 3 fases: diagnóstico, desenvolvimento e acompanhamento",
  "metricas_sucesso": ["Aumento de produtividade", "Melhoria na gestão de equipes"],
  "proximos_passos": ["Agendar consulta inicial", "Definir objetivos específicos"]
}}

IMPORTANTE: 
- Retorne APENAS o JSON acima
- Use português brasileiro
- Seja específico para {platform}
- Gere conteúdo original e criativo
- Foque na conversão e engajamento
- O campo "content" é OBRIGATÓRIO e deve conter um objeto JSON válido
- NÃO deixe o campo "content" vazio ou com texto genérico
- O campo "content.copy" deve conter pelo menos 3-4 parágrafos de conteúdo
- NÃO use quebras de linha ou caracteres especiais no JSON
- Certifique-se de que o JSON seja válido e parseável
- O campo "content" deve ser um objeto JSON, não uma string
- As 3 variações (A, B, C) devem ter conteúdo IDÊNTICO para facilitar testes A/B
- Cada variação deve ter headline, copy, cta, hashtags, visual_description e color_composition
"""

        try:
            # Configure API key for this request
            api_key = campaign.get('gemini_api_key') or self.default_api_key
            if api_key:
                genai.configure(api_key=api_key)

            # Generate content
            response = self.model.generate_content(prompt)

            if response and response.text:
                # Parse JSON response
                content_text = response.text.strip()

                print(
                    f"=== DEBUG: Raw AI response: {content_text[:500]}... ===")

                # Remove markdown code blocks if present
                if content_text.startswith('```json'):
                    content_text = content_text[7:]
                if content_text.endswith('```'):
                    content_text = content_text[:-3]

                content_text = content_text.strip()
                print(
                    f"=== DEBUG: Cleaned content text: {content_text[:500]}... ===")

                # Parse JSON
                try:
                    parsed_content = json.loads(content_text)
                    print(
                        f"=== DEBUG: Successfully parsed JSON with keys: {list(parsed_content.keys())} ===")

                    # Validate that content field exists and is not empty
                    if 'content' not in parsed_content or not parsed_content['content']:
                        print(
                            "=== DEBUG: Content field missing or empty in parsed JSON ===")
                        # Generate fallback content
                        parsed_content[
                            'content'] = f"Conteúdo gerado para {platform} - {content_type}. {parsed_content.get('title', '')} - {parsed_content.get('description', '')}"
                        print(
                            f"=== DEBUG: Generated fallback content: {parsed_content['content']} ===")

                    return parsed_content
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Raw content: {content_text}")

                    # Try to extract content using regex as fallback
                    import re
                    content_match = re.search(
                        r'"content"\s*:\s*"([^"]+)"', content_text)
                    title_match = re.search(
                        r'"title"\s*:\s*"([^"]+)"', content_text)
                    description_match = re.search(
                        r'"description"\s*:\s*"([^"]+)"', content_text)

                    if content_match or title_match or description_match:
                        fallback_content = {
                            'title': title_match.group(1) if title_match else 'Título Gerado por IA',
                            'description': description_match.group(1) if description_match else 'Descrição Gerada por IA',
                            'content': content_match.group(1) if content_match else f'Conteúdo para {platform} - {content_type}',
                            'headline': 'Headline Gerado por IA',
                            'copy': 'Copy Gerado por IA',
                            'cta': 'Call-to-Action Gerado por IA',
                            'hashtags': ['#ia', '#conteudo', '#marketing'],
                            'visual_description': 'Descrição visual gerada por IA',
                            'color_composition': 'Composição de cores gerada por IA',
                            'estrategia_implementacao': 'Estratégia gerada por IA',
                            'metricas_sucesso': ['Métrica 1', 'Métrica 2'],
                            'proximos_passos': ['Passo 1', 'Passo 2']
                        }
                        print(
                            f"=== DEBUG: Using fallback content: {fallback_content} ===")
                        return fallback_content

                    return None
            else:
                print("No response from Gemini")
                return None

        except Exception as e:
            print(f"Error generating single idea: {e}")
            return None

    def generate_campaign_ideas_with_progress(self, user: User, config: Dict, progress_callback=None) -> Tuple[List[Dict], Dict]:
        """Generate campaign ideas with real progress tracking."""
        progress = ProgressTracker()

        # Define the actual steps of the generation process
        steps = [
            "Inicializando geração de campanha...",
            "Analisando perfil do usuário...",
            "Processando configurações da campanha...",
            "Construindo prompt para IA...",
            "Conectando com Gemini AI...",
            "Gerando conteúdo para plataforma 1...",
            "Gerando conteúdo para plataforma 2...",
            "Gerando conteúdo para plataforma 3...",
            "Processando respostas da IA...",
            "Estruturando dados das ideias...",
            "Validando formato das ideias...",
            "Finalizando geração..."
        ]

        progress.set_steps(steps)

        try:
            # Step 1: Initialize
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 2: Analyze user profile
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 3: Process campaign config
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 4: Build prompt
            progress.next_step()
            prompt = self._build_campaign_prompt(user, config)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 5: Connect to Gemini
            progress.next_step()
            api_key = config.get('gemini_api_key')
            self._configure_api_key(api_key)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 6-8: Generate content for each platform
            platforms = config.get('platforms', ['instagram'])
            for i, platform in enumerate(platforms[:3]):  # Max 3 platforms
                progress.next_step(f"Gerando conteúdo para {platform}...")
                if progress_callback:
                    progress_callback(progress.get_progress())
                time.sleep(0.5)  # Simulate processing time

            # Step 9: Process AI responses
            progress.next_step()
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 10: Structure data
            progress.next_step()
            ideas = self._parse_campaign_response(response_text, config)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 11: Validate format
            progress.next_step()
            # Validation logic here
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 12: Finalize
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            return ideas, progress.get_progress()

        except Exception as e:
            error_progress = progress.get_progress()
            error_progress["error"] = str(e)
            raise Exception(f"Erro na geração de campanhas: {str(e)}")

    def generate_single_idea_with_progress(self, user: User, campaign: Dict, idea_params: Dict, progress_callback=None) -> Tuple[Dict, Dict]:
        """Generate a single idea with real progress tracking."""
        progress = ProgressTracker()

        # Define the actual steps for single idea generation
        steps = [
            "Inicializando geração de ideia...",
            "Analisando campanha existente...",
            "Processando parâmetros da ideia...",
            "Construindo prompt específico...",
            "Conectando com Gemini AI...",
            "Gerando conteúdo da ideia...",
            "Processando resposta da IA...",
            "Validando formato JSON...",
            "Estruturando dados finais...",
            "Finalizando geração..."
        ]

        progress.set_steps(steps)

        try:
            # Step 1: Initialize
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 2: Analyze campaign
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 3: Process idea params
            progress.next_step()
            platform = idea_params.get('platform', 'instagram')
            content_type = idea_params.get('content_type', 'post')
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 4: Build specific prompt
            progress.next_step()
            prompt = self._build_single_idea_prompt(
                user, campaign, idea_params)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 5: Connect to Gemini
            progress.next_step()
            api_key = campaign.get('gemini_api_key') or self.default_api_key
            if api_key:
                genai.configure(api_key=api_key)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 6: Generate content
            progress.next_step()
            response = self.model.generate_content(prompt)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 7: Process response
            progress.next_step()
            if response and response.text:
                content_text = response.text.strip()
                if progress_callback:
                    progress_callback(progress.get_progress())
            else:
                raise Exception("Sem resposta do Gemini")

            # Step 8: Validate JSON format
            progress.next_step()
            try:
                # Clean the response text - remove any markdown formatting
                cleaned_text = content_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                # Try to parse the JSON
                parsed_content = json.loads(cleaned_text)
                if progress_callback:
                    progress_callback(progress.get_progress())
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Raw response: {content_text[:500]}...")
                print(f"Cleaned text: {cleaned_text[:500]}...")
                raise Exception(
                    f"Resposta da IA não é JSON válido. Erro: {str(e)}")

            # Step 9: Structure final data
            progress.next_step()
            # Ensure content field exists
            if 'content' not in parsed_content or not parsed_content['content']:
                parsed_content[
                    'content'] = f"Conteúdo gerado para {platform} - {content_type}. {parsed_content.get('title', '')} - {parsed_content.get('description', '')}"

            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 10: Finalize
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            return parsed_content, progress.get_progress()

        except Exception as e:
            error_progress = progress.get_progress()
            error_progress["error"] = str(e)
            raise Exception(f"Erro na geração de ideia: {str(e)}")

    def improve_idea_with_progress(self, user: User, current_idea: CampaignIdea, improvement_prompt: str, api_key: str = None, progress_callback=None) -> Tuple[Dict, Dict]:
        """Improve an existing idea with real progress tracking."""
        progress = ProgressTracker()

        # Define the actual steps for idea improvement
        steps = [
            "Inicializando melhoria da ideia...",
            "Analisando ideia atual...",
            "Processando solicitação de melhoria...",
            "Construindo prompt de melhoria...",
            "Conectando com Gemini AI...",
            "Gerando conteúdo melhorado...",
            "Processando resposta da IA...",
            "Validando formato JSON...",
            "Aplicando melhorias...",
            "Finalizando melhoria..."
        ]

        progress.set_steps(steps)

        try:
            # Step 1: Initialize
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 2: Analyze current idea
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 3: Process improvement request
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 4: Build improvement prompt
            progress.next_step()
            prompt = self._build_improvement_prompt(
                user, current_idea, improvement_prompt)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 5: Connect to Gemini
            progress.next_step()
            self._configure_api_key(api_key)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 6: Generate improved content
            progress.next_step()
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 7: Process response
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 8: Validate JSON format
            progress.next_step()
            try:
                # Clean common wrappers and formatting issues
                cleaned_text = response_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith('```'):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                # First attempt: direct JSON parse
                try:
                    campaign_data = json.loads(cleaned_text)
                except json.JSONDecodeError as e_json:
                    # Second attempt: Python-literal style dict (single quotes)
                    try:
                        import ast
                        py_obj = ast.literal_eval(cleaned_text)
                        campaign_data = json.loads(
                            json.dumps(py_obj, ensure_ascii=False))
                    except Exception as e_ast:
                        # Third attempt: extract the first JSON-like object
                        try:
                            import re
                            match = re.search(r'\{[\s\S]*\}', cleaned_text)
                            if not match:
                                raise Exception(
                                    "Nenhum objeto JSON encontrado na resposta da IA")
                            candidate = match.group(0)
                            try:
                                campaign_data = json.loads(candidate)
                            except Exception:
                                py_obj2 = ast.literal_eval(candidate)
                                campaign_data = json.loads(
                                    json.dumps(py_obj2, ensure_ascii=False))
                        except Exception as e_regex:
                            # Log context to aid debugging
                            print("=== DEBUG: Improve Idea - JSON parse failed ===")
                            print(
                                f"Raw response (first 500): {response_text[:500]}")
                            print(f"Cleaned (first 500): {cleaned_text[:500]}")
                            raise Exception(
                                f"Resposta da IA não é JSON válido. Erros: JSON={str(e_json)} | AST={str(e_ast)} | REGEX={str(e_regex)}"
                            )

                if progress_callback:
                    progress_callback(progress.get_progress())
            except Exception as e:
                raise Exception(
                    f"Resposta da IA não é JSON válido. Detalhes: {str(e)}")

            # Step 9: Apply improvements
            progress.next_step()
            improved_data = self._process_improved_idea(
                campaign_data, current_idea)
            if progress_callback:
                progress_callback(progress.get_progress())

            # Step 10: Finalize
            progress.next_step()
            if progress_callback:
                progress_callback(progress.get_progress())

            return improved_data, progress.get_progress()

        except Exception as e:
            error_progress = progress.get_progress()
            error_progress["error"] = str(e)
            raise Exception(f"Erro na melhoria da ideia: {str(e)}")

    def _build_single_idea_prompt(self, user: User, campaign: Dict, idea_params: Dict) -> str:
        """Build prompt for single idea generation."""
        # Get user's creator profile
        profile = None
        if user:
            try:
                profile = CreatorProfile.objects.get(user=user)
            except CreatorProfile.DoesNotExist:
                profile = None

        # Build persona section
        persona_complete = self._build_persona_section(campaign)

        # Build creator profile section
        professional_name = profile.professional_name if profile else "Não especificado"
        profession = profile.profession if profile else "Não especificado"
        specialization = profile.specialization if profile else "Não especificado"
        primary_font = profile.primary_font if profile else "Não especificado"
        secondary_font = profile.secondary_font if profile else "Não especificado"

        # Campaign details
        objective_detail = campaign.get('title', 'Não especificado')
        product_description = campaign.get(
            'product_description', 'Não especificado')
        value_proposition = campaign.get(
            'value_proposition', 'Não especificado')
        campaign_urgency = campaign.get('campaign_urgency', 'Não especificado')
        voice_tone = campaign.get('voice_tone', 'professional')

        # Get voice tone display name
        voice_tone_display = dict(VoiceTone.choices).get(
            voice_tone, voice_tone)

        # Idea specific parameters
        platform = idea_params.get('platform', 'instagram')
        content_type = idea_params.get('content_type', 'post')
        variation_type = idea_params.get('variation_type', 'a')

        # Optional pre-filled content
        title = idea_params.get('title', '')
        description = idea_params.get('description', '')
        content = idea_params.get('content', '')

        prompt = f"""
Você é um especialista em marketing digital. Gere uma ideia de conteúdo para {platform}.

CONTEXTO:
- Campanha: {objective_detail}
- Produto: {product_description}
- Valor: {value_proposition}
- Tom: {voice_tone_display}
- Plataforma: {platform}
- Tipo: {content_type}

INSTRUÇÕES:
1. Gere APENAS um JSON válido
2. Use português brasileiro
3. Seja específico para {platform}
4. Foque em conversão e engajamento

FORMATO OBRIGATÓRIO - RETORNE APENAS ESTE JSON:

{{
  "title": "Título da ideia",
  "description": "Descrição da ideia",
  "content": {{
    "plataforma": "{platform}",
    "tipo_conteudo": "{content_type}",
    "titulo_principal": "Título principal",
    "variacao_a": {{
      "headline": "Headline para {platform}",
      "copy": "Copy específico para {platform} com linguagem persuasiva e foco em conversão",
      "cta": "Call-to-action para {platform}",
      "hashtags": ["#marketing", "#conteudo", "#{platform}"],
      "visual_description": "Descrição visual para {platform}",
      "color_composition": "Paleta de cores para {platform}"
    }},
    "variacao_b": {{
      "headline": "Headline para {platform}",
      "copy": "Copy específico para {platform} com linguagem persuasiva e foco em conversão",
      "cta": "Call-to-action para {platform}",
      "hashtags": ["#marketing", "#conteudo", "#{platform}"],
      "visual_description": "Descrição visual para {platform}",
      "color_composition": "Paleta de cores para {platform}"
    }},
    "variacao_c": {{
      "headline": "Headline para {platform}",
      "copy": "Copy específico para {platform} com linguagem persuasiva e foco em conversão",
      "cta": "Call-to-action para {platform}",
      "hashtags": ["#marketing", "#conteudo", "#{platform}"],
      "visual_description": "Descrição visual para {platform}",
      "color_composition": "Paleta de cores para {platform}"
    }},
    "estrategia_implementacao": "Estratégia para implementar em {platform}",
    "metricas_sucesso": ["Engajamento", "Conversões"],
    "proximos_passos": ["Criar visual", "Agendar post"]
  }},
  "headline": "Headline principal",
  "copy": "Copy principal",
  "cta": "Call-to-action principal",
  "hashtags": ["#marketing", "#conteudo", "#{platform}"],
  "visual_description": "Descrição visual",
  "color_composition": "Paleta de cores",
  "estrategia_implementacao": "Estratégia de implementação",
  "metricas_sucesso": ["Engajamento", "Conversões"],
  "proximos_passos": ["Criar visual", "Agendar post"]
}}

IMPORTANTE: 
- Retorne APENAS o JSON acima, sem texto adicional, explicações ou markdown
- Use APENAS aspas duplas (") para chaves e valores, NUNCA aspas simples (')
- Certifique-se de que o JSON seja válido e parseável
- NÃO use quebras de linha ou caracteres especiais no JSON
"""
        return prompt

    def _build_improvement_prompt(self, user: User, current_idea: CampaignIdea, improvement_prompt: str) -> str:
        """Build prompt for idea improvement."""
        # Get user's creator profile
        try:
            profile = CreatorProfile.objects.get(user=user)
        except CreatorProfile.DoesNotExist:
            profile = None

        # Get the original configuration if available
        config_data = {}
        if hasattr(current_idea, 'campaign') and current_idea.campaign:
            campaign = current_idea.campaign
            config_data = {
                'objectives': campaign.objectives,
                'persona_age': campaign.persona_age,
                'persona_location': campaign.persona_location,
                'persona_income': campaign.persona_income,
                'persona_interests': campaign.persona_interests,
                'persona_behavior': campaign.persona_behavior,
                'persona_pain_points': campaign.persona_pain_points,
                'platforms': campaign.platforms,
                'content_types': campaign.content_types,
            }

        # Build creator profile section
        creator_section = self._build_creator_section(
            profile) if profile else ""

        # Expor JSON atual (se possível) para orientar a IA
        try:
            current_json = json.loads(current_idea.content)
            current_json_pretty = json.dumps(
                current_json, ensure_ascii=False, indent=2)
        except Exception:
            current_json_pretty = "<sem JSON válido>"

        # Build the improvement prompt exigindo o MESMO schema das ideias geradas
        prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais.
Sua tarefa é melhorar uma ideia de campanha existente baseada no feedback específico do usuário.

{creator_section}

IDEIA ATUAL (metadados):
- Título: {current_idea.title}
- Descrição: {current_idea.description}
- Plataforma: {current_idea.platform}
- Tipo de Conteúdo: {current_idea.content_type}
- Status: {current_idea.status}

CONTEÚDO ATUAL (JSON, quando disponível):
{current_json_pretty}

CONTEXTO ORIGINAL DA CAMPANHA:
{self._build_persona_section(config_data) if config_data else "Informações do contexto original não disponíveis."}

SOLICITAÇÃO DE MELHORIA:
{improvement_prompt}

INSTRUÇÕES CRÍTICAS (SIGA À RISCA):
1. Mantenha a mesma plataforma (plataforma) e o mesmo tipo de conteúdo (tipo_conteudo) da ideia atual, salvo instrução explícita em contrário.
2. Retorne APENAS um JSON VÁLIDO (RFC 8259) usando aspas duplas em chaves e strings.
3. O JSON DEVE seguir EXATAMENTE o mesmo schema usado na geração de ideias (abaixo).
4. As variações variacao_a, variacao_b e variacao_c DEVEM ter o MESMO conteúdo (cópias idênticas) para testes A/B.
5. Campos de lista devem ser arrays JSON (por exemplo: hashtags, metricas_sucesso, proximos_passos).
6. Não inclua comentários, texto fora do JSON, explicações ou markdown. Apenas o objeto JSON.
7. IMPORTANTE: Gere conteúdo APENAS para a plataforma {current_idea.platform}, não para outras plataformas.
8. Para o campo "tipo_conteudo", use APENAS um destes valores: post, story, reel, video, carousel, live, custom

SCHEMA OBRIGATÓRIO (substitua pelos seus valores, mantendo as chaves):
{{
  "plataforma": "{current_idea.platform}",
  "tipo_conteudo": "post",
  "titulo_principal": "texto aqui",
  "variacao_a": {{
    "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "variacao_b": {{
    "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "variacao_c": {{
    "headline": "texto aqui",
    "copy": "texto aqui",
    "cta": "texto aqui",
    "hashtags": ["texto aqui"],
    "visual_description": "texto aqui",
    "color_composition": "texto aqui"
  }},
  "estrategia_implementacao": "texto aqui",
  "metricas_sucesso": ["texto aqui"],
  "proximos_passos": ["texto aqui"]
}}

RETORNE APENAS este objeto JSON único, válido e completo.
"""
        return prompt

    def _process_improved_idea(self, campaign_data: Dict, current_idea: CampaignIdea) -> Dict:
        """Process and validate improved idea data."""
        # Garantias mínimas de schema
        campaign_data.setdefault('plataforma', current_idea.platform)
        campaign_data.setdefault('tipo_conteudo', current_idea.content_type)

        # Normalizar variações (replicar base se faltar)
        base_variation = None
        for key in ['variacao_a', 'variacao_b', 'variacao_c']:
            if key in campaign_data and campaign_data[key]:
                base_variation = campaign_data[key]
                break
        if not base_variation:
            base_variation = {
                'headline': campaign_data.get('titulo_principal', current_idea.title),
                'copy': campaign_data.get('estrategia_implementacao', current_idea.description),
                'cta': 'Clique para saber mais!',
                'hashtags': ['#campanha', '#marketing', '#conteudo'],
                'visual_description': 'Descrição visual padrão',
                'color_composition': 'Paleta de cores padrão'
            }
        for key in ['variacao_a', 'variacao_b', 'variacao_c']:
            campaign_data[key] = {
                'headline': base_variation.get('headline', ''),
                'copy': base_variation.get('copy', ''),
                'cta': base_variation.get('cta', ''),
                'hashtags': base_variation.get('hashtags', []),
                'visual_description': base_variation.get('visual_description', ''),
                'color_composition': base_variation.get('color_composition', ''),
            }

        # Saída padronizada para o frontend
        improved_data = {
            'title': campaign_data.get('titulo_principal', current_idea.title),
            'description': campaign_data.get('estrategia_implementacao', current_idea.description),
            'content': json.dumps(campaign_data, ensure_ascii=False)
        }

        return improved_data
