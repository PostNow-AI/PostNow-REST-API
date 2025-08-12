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

from IdeaBank.models import CampaignIdea


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

    def _build_prompt(self, user: User, config: Dict) -> str:
        """Build a comprehensive prompt for idea generation."""

        # Get user's creator profile (only if user is authenticated)
        profile = None
        if user:
            try:
                profile = CreatorProfile.objects.get(user=user)
            except CreatorProfile.DoesNotExist:
                profile = None

        # Build persona section
        persona_section = self._build_persona_section(config)

        # Build platform section
        platform_section = self._build_platform_section(config)

        # Build creator profile section
        creator_section = self._build_creator_section(
            profile) if profile else ""

        # Adjust prompt based on whether user is authenticated
        if user and profile:
            prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais. 
Sua tarefa é gerar ideias criativas e estratégicas para campanhas de marketing digital.

## PERFIL DO CRIADOR:
{creator_section}

## OBJETIVOS DA CAMPANHA:
{', '.join(config['objectives'])}

## PERSONA ALVO:
{persona_section}

## PLATAFORMAS E TIPOS DE CONTEÚDO:
{platform_section}

## INSTRUÇÕES:
1. Gere ideias específicas para cada plataforma selecionada
2. Considere o perfil do criador e sua expertise
3. Foque nos objetivos da campanhas (vendas, branding, engajamento)
4. Adapte o conteúdo para a persona alvo
5. Use a paleta de cores e tipografia do criador quando relevante
6. Seja criativo e estratégico
7. Forneça ideias práticas e executáveis

## FORMATO DE RESPOSTA:
Para cada plataforma, forneça:
- Título da ideia
- Descrição breve
- Conteúdo detalhado (texto, hashtags, call-to-action)
- Tipo de conteúdo específico
- Estratégia de implementação

Responda em português brasileiro e seja específico e detalhado.
"""
        else:
            prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais. 
Sua tarefa é gerar ideias criativas e estratégicas para campanhas de marketing digital.

## OBJETIVOS DA CAMPANHA:
{', '.join(config['objectives'])}

## PERSONA ALVO:
{persona_section}

## PLATAFORMAS E TIPOS DE CONTEÚDO:
{platform_section}

## INSTRUÇÕES:
1. Gere ideias específicas para cada plataforma selecionada
2. Foque nos objetivos da campanhas (vendas, branding, engajamento)
3. Adapte o conteúdo para a persona alvo
4. Seja criativo e estratégico
5. Forneça ideias práticas e executáveis
6. Note: Estas ideias são para usuários sem perfil personalizado, então use estratégias gerais mas eficazes

## FORMATO DE RESPOSTA:
Para cada plataforma, forneça:
- Título da ideia
- Descrição breve
- Conteúdo detalhado (texto, hashtags, call-to-action)
- Tipo de conteúdo específico
- Estratégia de implementação

Responda em português brasileiro e seja específico e detalhado.
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

    def _build_platform_section(self, config: Dict) -> str:
        """Build the platform section of the prompt."""
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
        """Build the creator profile section of the prompt."""
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

    def generate_ideas(self, user: User, config: Dict) -> List[Dict]:
        """Generate campaign ideas using Gemini."""
        try:
            prompt = self._build_prompt(user, config)

            print(prompt)
            response = self.model.generate_content(prompt)

            # Parse the response and structure it
            ideas = self._parse_gemini_response(response.text, config)

            return ideas

        except Exception as e:
            raise Exception(f"Erro na geração de ideias: {str(e)}")

    def _parse_gemini_response(self, response_text: str, config: Dict) -> List[Dict]:
        """Parse Gemini response into structured ideas."""
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
        if hasattr(current_idea, 'config') and current_idea.config:
            config = current_idea.config
            config_data = {
                'objectives': config.objectives,
                'persona_age': config.persona_age,
                'persona_location': config.persona_location,
                'persona_income': config.persona_income,
                'persona_interests': config.persona_interests,
                'persona_behavior': config.persona_behavior,
                'persona_pain_points': config.persona_pain_points,
                'platforms': config.platforms,
                'content_types': config.content_types,
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

            import json
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
