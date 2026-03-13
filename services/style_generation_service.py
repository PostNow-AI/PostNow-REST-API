import json
import logging

from django.contrib.auth.models import User

from CreatorProfile.models import CreatorProfile, GeneratedVisualStyle
from services.color_extraction import format_colors_for_prompt
from services.get_creator_profile_data import get_creator_profile_data

logger = logging.getLogger(__name__)

# Mapeamento das preferências do onboarding para diretrizes estéticas ricas
STYLE_DIRECTIONS = {
    "minimalista": {
        "direction": "Clean minimalist with generous negative space",
        "references": "Swiss International Style, Dieter Rams, Apple product pages, Kinfolk magazine",
        "typography": "thin or light-weight geometric sans-serif (like Futura, Helvetica Neue Light), generous letter-spacing and line-height",
        "lighting": "soft overcast nordic daylight, flat and even, no harsh shadows",
        "avoid": "clutter, heavy textures, ornamental elements, drop shadows",
    },
    "colorido": {
        "direction": "Bold, vibrant, and energetic with dynamic color combinations",
        "references": "Memphis Design, Pop Art, Spotify Wrapped, Brazilian Carnival posters, Keith Haring",
        "typography": "heavy bold display sans-serif (like Impact, Montserrat Black), tight letter-spacing, playful sizing",
        "lighting": "bright flat studio lighting, saturated and punchy, no shadows",
        "avoid": "muted tones, excessive whitespace, corporate feel, neutral palettes",
    },
    "elegante": {
        "direction": "Luxurious and refined with sophisticated restraint",
        "references": "Vogue editorials, Chanel branding, Art Deco posters, luxury hotel design, Tom Ford ads",
        "typography": "elegant high-contrast serif (like Didot, Playfair Display) or refined thin sans-serif, wide tracking",
        "lighting": "dramatic side lighting with soft shadows, warm golden accents, chiaroscuro touch",
        "avoid": "bright neon colors, playful elements, casual typography, cartoonish graphics",
    },
    "moderno": {
        "direction": "Contemporary geometric design with clean structure",
        "references": "Bauhaus, Google Material Design, architectural photography, Zaha Hadid lines, tech startup landing pages",
        "typography": "geometric sans-serif (like Poppins, Inter, DM Sans), medium weight, clean and structured",
        "lighting": "cool ambient studio light, clean and even, subtle gradient backgrounds",
        "avoid": "organic shapes, hand-drawn elements, vintage textures, ornate decorations",
    },
    "rustico": {
        "direction": "Warm organic aesthetic with natural textures and earthy presence",
        "references": "Scandinavian hygge, farmhouse branding, Kinfolk lifestyle, artisan bakery packaging, botanical illustration",
        "typography": "humanist serif (like Lora, Merriweather) or hand-lettering style, warm and approachable",
        "lighting": "warm golden hour sunlight, soft and diffused, natural window light with gentle shadows",
        "avoid": "neon colors, geometric precision, high-tech elements, cold lighting",
    },
    "ousado": {
        "direction": "High-contrast, impactful design that demands attention",
        "references": "Nike campaign posters, streetwear branding, brutalist web design, punk zine layouts, Shepard Fairey",
        "typography": "ultra-bold condensed sans-serif (like Anton, Bebas Neue), uppercase, tight spacing, oversized",
        "lighting": "dramatic high-contrast lighting, deep shadows, spotlight effect or neon glow",
        "avoid": "pastel colors, delicate elements, subtle gradients, thin typography",
    },
}

# Direção default quando o usuário não escolheu estilo no onboarding
DEFAULT_STYLE_DIRECTION = {
    "direction": "Professional and visually engaging, adapted to the brand's niche",
    "references": "editorial magazine layouts, modern social media design, brand-appropriate aesthetics",
    "typography": "clean sans-serif, medium to bold weight, good readability",
    "lighting": "soft natural daylight, diffused and even",
    "avoid": "generic stock photo aesthetic, cluttered layouts",
}

STYLE_GENERATION_PROMPT_SYSTEM = """You are a world-class Art Director creating visual styles for Instagram posts.

You have deep knowledge of design movements, photography styles, and visual culture.
Your styles are specific, vivid, and produce striking images — never generic or corporate.

Return ONLY a valid JSON object. No markdown, no explanation, no code blocks."""

STYLE_GENERATION_PROMPT_TEMPLATE = """
### BRAND ###
- Business: {business_name}
- Niche: {specialization}
- Personality: {brand_personality}
- Voice: {voice_tone}
- Brand colors:
{colors_formatted}

### CONTENT ###
- Theme: {tema_principal}
- Visual scene: {contexto_visual_sugerido}
- Key elements: {objetos_relevantes}
- Emotions: {emocoes_associadas}
- Feeling: {sensacao_geral}

### AESTHETIC DIRECTION ###
{style_direction}

### VISUAL REPERTOIRE (choose from these, combine, or be inspired by) ###

Lighting options:
- "soft overcast nordic daylight" — clean, flat, editorial
- "warm golden hour sunlight streaming through window" — cozy, inviting
- "dramatic side lighting with deep shadows" — bold, cinematic
- "cool ambient neon glow against dark background" — tech, futuristic
- "bright flat studio lighting, no shadows" — pop, energetic
- "cinematic backlight with subtle lens flare" — aspirational, dreamy
- "soft candlelight warmth" — intimate, artisanal

Color vocabulary (use descriptive names, NEVER hex codes):
- Reds: cherry, cranberry, scarlet, ruby, wine, burgundy, brick, coral, ember
- Oranges: tangerine, apricot, rust, amber, copper, burnt orange, saffron, terracotta
- Yellows: lemon, canary, gold, butter, mustard, sunflower, honey, champagne
- Greens: emerald, olive, sage, forest, moss, mint, jade, pistachio, eucalyptus
- Blues: sky, navy, royal, sapphire, indigo, ice blue, teal, cobalt, glacier, steel
- Purples: lavender, plum, violet, orchid, amethyst, mauve, lilac, wisteria
- Neutrals: ivory, cream, linen, parchment, charcoal, graphite, slate, onyx, smoke
- Browns: chocolate, coffee, cinnamon, caramel, toffee, walnut, sand, taupe, sienna
- Pinks: rose, blush, flamingo, cotton candy, peach, raspberry, cherry blossom

Modifiers: pale, soft, pastel, bright, deep, vivid, bold, dark, muted, rich, warm, cool, metallic

### RULES ###
1. Use the brand colors as PRIMARY palette — adapt them creatively (lighter/darker/gradient variations)
2. The aesthetic MUST match the niche: a bakery looks different from a law firm
3. Be SPECIFIC: not "modern design" but "bold geometric composition inspired by Bauhaus posters with overlapping shapes"
4. Pick ONE lighting — do not mix conflicting light sources
5. Colors must be memory color names (descriptive), NEVER hex codes
6. Limit to 2-3 dominant colors + 1 accent — more creates visual noise
7. The style must work for Instagram feed (4:5 vertical)

### OUTPUT (JSON only) ###
{{
    "name": "Creative style name in Portuguese (3-5 words)",
    "aesthetic": "Vivid, specific aesthetic description in English. Reference recognizable styles, textures, or movements. Describe what the viewer SEES, not abstract concepts.",
    "colors": {{
        "background": "specific memory color with modifier (e.g. 'soft warm linen', 'deep midnight navy gradient')",
        "primary": "specific memory color for main visual elements",
        "accent": "contrasting memory color for details and highlights",
        "text": "high-contrast memory color for readability"
    }},
    "lighting": "ONE specific lighting setup with direction and quality",
    "typography": "specific font style with weight, spacing, and personality",
    "composition": "layout with exact positions: where title goes, where visual goes, percentages",
    "mood": "2-3 evocative mood words",
    "references": ["2 specific, recognizable aesthetic references the AI image model knows well"]
}}
"""


def generate_style(
    user: User,
    semantic_analysis: dict,
    ai_service,
    source_post_id: int | None = None,
) -> GeneratedVisualStyle:
    """Gera um estilo visual único via IA e salva no banco."""
    profile_data = get_creator_profile_data(user)
    colors_formatted = format_colors_for_prompt(profile_data.get('color_palette', []))
    style_direction = _get_style_direction(user)

    prompt_body = STYLE_GENERATION_PROMPT_TEMPLATE.format(
        business_name=profile_data.get('business_name', ''),
        specialization=profile_data.get('specialization', ''),
        brand_personality=profile_data.get('brand_personality', ''),
        voice_tone=profile_data.get('voice_tone', ''),
        colors_formatted=colors_formatted,
        tema_principal=semantic_analysis.get('tema_principal', ''),
        contexto_visual_sugerido=semantic_analysis.get('contexto_visual_sugerido', ''),
        objetos_relevantes=', '.join(semantic_analysis.get('objetos_relevantes', [])),
        emocoes_associadas=', '.join(semantic_analysis.get('emoções_associadas', [])),
        sensacao_geral=semantic_analysis.get('sensação_geral', ''),
        style_direction=style_direction,
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


def _get_style_direction(user: User) -> str:
    """Monta a direção estética baseada na preferência do onboarding."""
    try:
        profile = CreatorProfile.objects.get(user=user)
        style_ids = profile.visual_style_ids or []
    except CreatorProfile.DoesNotExist:
        style_ids = []

    if not style_ids:
        direction = DEFAULT_STYLE_DIRECTION
    else:
        # Pega a primeira preferência (principal) do onboarding
        primary_style = style_ids[0] if isinstance(style_ids[0], str) else str(style_ids[0])
        direction = STYLE_DIRECTIONS.get(primary_style, DEFAULT_STYLE_DIRECTION)

    lines = [
        f"- Direction: {direction['direction']}",
        f"- Reference artists/styles: {direction['references']}",
        f"- Typography tendency: {direction['typography']}",
        f"- Lighting tendency: {direction['lighting']}",
        f"- Avoid: {direction['avoid']}",
    ]
    return "\n".join(lines)


def _parse_style_json(raw_text: str) -> dict:
    """Parseia o JSON retornado pela IA, tratando markdown code blocks."""
    cleaned = raw_text.strip()

    if cleaned.startswith('```'):
        first_newline = cleaned.index('\n') if '\n' in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
        if cleaned.rstrip().endswith('```'):
            cleaned = cleaned.rstrip()[:-3].rstrip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning("Falha ao parsear JSON do estilo: %s. Raw: %s", e, raw_text[:200])
        return _default_style()

    required_fields = ['aesthetic', 'colors', 'lighting', 'typography', 'composition']
    missing = [f for f in required_fields if f not in data]
    if missing:
        logger.warning("Estilo gerado sem campos obrigatórios: %s", missing)
        defaults = _default_style()
        for field in missing:
            data[field] = defaults[field]

    return data


def _default_style() -> dict:
    """Estilo fallback caso a IA retorne JSON inválido."""
    return {
        "name": "Minimalista Profissional",
        "aesthetic": "Clean minimalist design with generous whitespace, inspired by Kinfolk magazine editorial layouts",
        "colors": {
            "background": "warm ivory",
            "primary": "deep cobalt blue",
            "accent": "vivid coral",
            "text": "dark charcoal",
        },
        "lighting": "soft overcast nordic daylight, diffused and even",
        "typography": "modern geometric sans-serif, light weight, generous letter-spacing",
        "composition": "title upper third centered, main visual centered 40% of frame, logo bottom-right 8%",
        "mood": "professional, refined, confident",
        "references": ["Kinfolk magazine editorial", "Swiss International Style poster"],
    }
