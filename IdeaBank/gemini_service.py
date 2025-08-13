import json
import os
from typing import Dict, List

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from CreatorProfile.models import CreatorProfile
from django.contrib.auth.models import User

from IdeaBank.models import CampaignIdea, VoiceTone


class GeminiService:
    """Service for interacting with Google Gemini AI."""

    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai não está instalado. Execute: pip install google-generativeai")

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
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
1. Crie conteúdo ESPECÍFICO para cada plataforma, respeitando suas particularidades
2. Use a paleta de cores EXATA fornecida na composição visual
3. Estruture o conteúdo para {objective_detail}
4. Enderece as dores específicas da persona
5. Inclua gatilhos mentais apropriados para vendas
6. Forneça 3 variações IDÊNTICAS de copy para testes A/B (todas devem ter o mesmo conteúdo)
7. Sugira elementos visuais específicos (não genéricos)

## FORMATO DE RESPOSTA ESTRUTURADO:
Para CADA plataforma selecionada, forneça um JSON separado:

{{
  "plataforma": "youtube",
  "tipo_conteudo": "video",
  "titulo_principal": "...",
  "variacao_a": {{
    "headline": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["..."],
    "visual_description": "...",
    "color_composition": "..."
  }},
  "variacao_b": {{
    "headline": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["..."],
    "visual_description": "...",
    "color_composition": "..."
  }},
  "variacao_c": {{
    "headline": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["..."],
    "visual_description": "...",
    "color_composition": "..."
  }},
  "estrategia_implementacao": "...",
  "metricas_sucesso": ["..."],
  "proximos_passos": ["..."]
}}

{{
  "plataforma": "linkedin",
  "tipo_conteudo": "post",
  "titulo_principal": "...",
  "variacao_a": {{
    "headline": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["..."],
    "visual_description": "...",
    "color_composition": "..."
  }},
  "variacao_b": {{
    "headline": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["..."],
    "visual_description": "...",
    "color_composition": "..."
  }},
  "variacao_c": {{
    "headline": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["..."],
    "visual_description": "...",
    "color_composition": "..."
  }},
  "estrategia_implementacao": "...",
  "metricas_sucesso": ["..."],
  "proximos_passos": ["..."]
}}

IMPORTANTE: 
- Retorne um JSON para CADA plataforma solicitada
- Seja específico e detalhado para cada plataforma
- Use português brasileiro
- Foque na conversão e vendas
- Adapte o tom de voz conforme solicitado
- As 3 variações (a, b, c) devem ter conteúdo IDÊNTICO para facilitar testes A/B
- Gere conteúdo específico para cada plataforma (YouTube, LinkedIn, etc.)
"""

        return prompt

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

    def generate_campaign_ideas(self, user: User, config: Dict) -> List[Dict]:
        """Generate campaign ideas using the new structured prompt."""
        try:
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
        """Parse Gemini response into structured campaign ideas."""
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
                    # Multiple JSONs found - parse each one
                    for match in matches:
                        try:
                            campaign_data = json.loads(match)
                            idea = self._create_idea_from_campaign_data(
                                campaign_data, config)
                            ideas.append(idea)
                        except json.JSONDecodeError:
                            continue

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
        content_type = campaign_data.get('tipo_conteudo', 'post')

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

        # Simple extraction - look for JSON-like structures
        import re
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, response_text)

        for match in matches:
            try:
                campaign_data = json.loads(match)
                idea = self._create_idea_from_campaign_data(
                    campaign_data, config)
                ideas.append(idea)
            except json.JSONDecodeError:
                continue

        return ideas if ideas else self._create_fallback_ideas(config)

    def _create_fallback_ideas(self, config: Dict) -> List[Dict]:
        """Create fallback ideas when parsing fails."""
        ideas = []
        platforms = config.get('platforms', ['instagram'])

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

    def improve_idea(self, user: User, current_idea: CampaignIdea, improvement_prompt: str) -> Dict:
        """Improve an existing campaign idea using AI."""

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

        # Build the improvement prompt
        prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais.
Sua tarefa é melhorar uma ideia de campanha existente baseada no feedback específico do usuário.

{creator_section}

IDEIA ATUAL:
Título: {current_idea.title}
Descrição: {current_idea.description}
Conteúdo: {current_idea.content}
Plataforma: {current_idea.get_platform_display()}
Tipo de Conteúdo: {current_idea.get_content_type_display()}
Status: {current_idea.get_status_display()}

CONTEXTO ORIGINAL DA CAMPANHA:
{self._build_persona_section(config_data) if config_data else "Informações do contexto original não disponíveis."}

SOLICITAÇÃO DE MELHORIA:
{improvement_prompt}

INSTRUÇÕES:
1. Analise a ideia atual e a solicitação de melhoria
2. Mantenha a essência da ideia original, mas implemente as melhorias solicitadas
3. Use todas as informações do perfil do criador e contexto da campanha
4. Mantenha a mesma plataforma e tipo de conteúdo, a menos que especificamente solicitado para mudar
5. Retorne APENAS um JSON válido com os campos melhorados

Formato de resposta (JSON):
{{
    "title": "Título melhorado da ideia",
    "description": "Descrição melhorada (2-3 frases explicando a ideia)",
    "content": "Conteúdo detalhado melhorado da campanha"
}}

IMPORTANTE: Retorne APENAS o JSON válido, sem explicações adicionais.
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

            improved_data = json.loads(response_text)

            # Validate that we have the required fields
            required_fields = ['title', 'description', 'content']
            for field in required_fields:
                if field not in improved_data:
                    raise ValueError(
                        f"Campo obrigatório '{field}' não encontrado na resposta da IA")

            return improved_data

        except json.JSONDecodeError as e:
            raise Exception(f"Erro ao processar resposta da IA: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro na comunicação com a IA: {str(e)}")
