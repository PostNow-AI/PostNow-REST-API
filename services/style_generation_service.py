import json
import logging

from django.contrib.auth.models import User

from CreatorProfile.models import GeneratedVisualStyle
from services.color_extraction import format_colors_for_prompt
from services.get_creator_profile_data import get_creator_profile_data

logger = logging.getLogger(__name__)

STYLE_GENERATION_PROMPT_SYSTEM = """
You are a Senior Art Director specialized in social media visual design.
Your task is to create a unique visual style for an Instagram post image,
tailored to the brand profile and content being created.

You must return ONLY a valid JSON object with the structure specified below.
No markdown, no explanation, no code blocks — just the raw JSON.
"""

STYLE_GENERATION_PROMPT_TEMPLATE = """
### BRAND PROFILE ###

- Business: {business_name}
- Niche: {specialization}
- Description: {business_description}
- Brand personality: {brand_personality}
- Voice tone: {voice_tone}
- Brand color palette (use these as primary reference):
{colors_formatted}

### CONTENT CONTEXT ###

- Main theme: {tema_principal}
- Visual context: {contexto_visual_sugerido}
- Relevant elements: {objetos_relevantes}
- Associated emotions: {emocoes_associadas}
- Overall feeling: {sensacao_geral}
- Suggested color tones: {tons_de_cor_sugeridos}

### INSTRUCTIONS ###

Create a complete visual style for this specific post. The style must:

1. Prioritize the brand's color palette (converted to descriptive color names above)
2. Match the content's theme and emotional tone
3. Be specific and actionable (not vague adjectives)
4. Use memory colors (descriptive names like "warm terracotta", "deep cobalt blue")
   — NEVER use hex codes
5. Specify ONE lighting source and ONE atmosphere
6. Include a recognizable aesthetic reference (art movement, brand style, photography type)
7. Consider Instagram feed consistency

### REQUIRED OUTPUT (JSON only) ###

{{
    "name": "Short style name in Portuguese (3-5 words, e.g. 'Editorial Minimalista Quente')",
    "aesthetic": "Detailed aesthetic description in English using recognizable references (e.g. 'Clean minimalist design inspired by editorial magazine layouts, with Swiss typography influence')",
    "colors": {{
        "background": "memory color for background (e.g. 'warm ivory')",
        "primary": "memory color for main elements (e.g. 'deep cobalt blue')",
        "accent": "memory color for accent details (e.g. 'vivid coral')",
        "text": "memory color for text (e.g. 'dark charcoal')"
    }},
    "lighting": "Specific lighting description in English (e.g. 'soft overcast nordic daylight, diffused and even')",
    "typography": "Typography style in English (e.g. 'modern bold sans-serif with generous letter-spacing')",
    "composition": "Layout description in English with positioning (e.g. 'title upper third centered, main visual centered 40% of frame, logo bottom-right 8%')",
    "mood": "2-3 mood keywords in English (e.g. 'confident, professional, aspirational')",
    "references": ["1-2 recognizable aesthetic references (e.g. 'editorial magazine layout', 'Apple product page')"]
}}
"""


def generate_style(
    user: User,
    semantic_analysis: dict,
    ai_service,
    source_post_id: int | None = None,
) -> GeneratedVisualStyle:
    """
    Gera um estilo visual único via IA e salva no banco.

    Args:
        user: Usuário dono do perfil
        semantic_analysis: Resultado da análise semântica do conteúdo
        ai_service: Instância de AiService para chamada à IA
        source_post_id: ID do post que originou o estilo (opcional)

    Returns:
        GeneratedVisualStyle salvo no banco
    """
    profile_data = get_creator_profile_data(user)
    colors_formatted = format_colors_for_prompt(profile_data.get('color_palette', []))

    prompt_body = STYLE_GENERATION_PROMPT_TEMPLATE.format(
        business_name=profile_data.get('business_name', ''),
        specialization=profile_data.get('specialization', ''),
        business_description=profile_data.get('business_description', ''),
        brand_personality=profile_data.get('brand_personality', ''),
        voice_tone=profile_data.get('voice_tone', ''),
        colors_formatted=colors_formatted,
        tema_principal=semantic_analysis.get('tema_principal', ''),
        contexto_visual_sugerido=semantic_analysis.get('contexto_visual_sugerido', ''),
        objetos_relevantes=', '.join(semantic_analysis.get('objetos_relevantes', [])),
        emocoes_associadas=', '.join(semantic_analysis.get('emoções_associadas', [])),
        sensacao_geral=semantic_analysis.get('sensação_geral', ''),
        tons_de_cor_sugeridos=', '.join(semantic_analysis.get('tons_de_cor_sugeridos', [])),
    )

    prompt_list = [STYLE_GENERATION_PROMPT_SYSTEM, prompt_body]

    result_text = ai_service.generate_text(prompt_list, user)
    style_data = _parse_style_json(result_text)

    style = GeneratedVisualStyle.objects.create(
        user=user,
        name=style_data.get('name', 'Estilo Gerado'),
        style_data=style_data,
        source_post_id=source_post_id,
    )

    logger.info("Estilo visual '%s' gerado para user %s (id=%d)", style.name, user.email, style.id)
    return style


def _parse_style_json(raw_text: str) -> dict:
    """
    Parseia o JSON retornado pela IA, tratando markdown code blocks.

    Returns:
        Dict com os dados do estilo. Em caso de falha, retorna estilo padrão.
    """
    cleaned = raw_text.strip()

    # Remove markdown code blocks se presentes
    if cleaned.startswith('```'):
        # Remove ```json ou ``` no início
        first_newline = cleaned.index('\n') if '\n' in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
        # Remove ``` no final
        if cleaned.rstrip().endswith('```'):
            cleaned = cleaned.rstrip()[:-3].rstrip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning("Falha ao parsear JSON do estilo: %s. Raw: %s", e, raw_text[:200])
        return _default_style()

    # Valida campos obrigatórios
    required_fields = ['aesthetic', 'colors', 'lighting', 'typography', 'composition']
    missing = [f for f in required_fields if f not in data]
    if missing:
        logger.warning("Estilo gerado sem campos obrigatórios: %s", missing)
        # Preenche campos faltantes com defaults
        defaults = _default_style()
        for field in missing:
            data[field] = defaults[field]

    return data


def _default_style() -> dict:
    """Estilo fallback caso a IA retorne JSON inválido."""
    return {
        "name": "Minimalista Profissional",
        "aesthetic": "Clean minimalist design with professional corporate feel",
        "colors": {
            "background": "warm ivory",
            "primary": "deep cobalt blue",
            "accent": "vivid coral",
            "text": "dark charcoal",
        },
        "lighting": "soft natural daylight, diffused and even",
        "typography": "modern sans-serif, bold, clean",
        "composition": "title upper third centered, main visual centered, logo bottom-right 8%",
        "mood": "professional, clean, confident",
        "references": ["editorial magazine layout"],
    }
