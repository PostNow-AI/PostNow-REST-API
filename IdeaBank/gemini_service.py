import os
from typing import Dict, List

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from CreatorProfile.models import CreatorProfile


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

    def _build_prompt(self, user: 'User', config: Dict) -> str:
        """Build a comprehensive prompt for idea generation."""

        # Get user's creator profile
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

        return prompt

    def _build_persona_section(self, config: Dict) -> str:
        """Build the persona section of the prompt."""
        persona = config.get('persona', {})

        sections = []
        if persona.get('age'):
            sections.append(f"Idade: {persona['age']}")
        if persona.get('location'):
            sections.append(f"Localização: {persona['location']}")
        if persona.get('income'):
            sections.append(f"Renda: {persona['income']}")
        if persona.get('interests'):
            sections.append(f"Interesses: {persona['interests']}")
        if persona.get('behavior'):
            sections.append(f"Comportamento: {persona['behavior']}")
        if persona.get('pain_points'):
            sections.append(f"Dores e necessidades: {persona['pain_points']}")

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

    def generate_ideas(self, user: 'User', config: Dict) -> List[Dict]:
        """Generate campaign ideas using Gemini."""
        try:
            prompt = self._build_prompt(user, config)

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
