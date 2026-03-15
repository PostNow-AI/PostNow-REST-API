import json
import logging
import random

from django.contrib.auth.models import User

from CreatorProfile.models import CreatorProfile, GeneratedVisualStyle
from services.color_extraction import format_colors_for_prompt
from services.get_creator_profile_data import get_creator_profile_data

logger = logging.getLogger(__name__)

# Mapeamento das preferencias do onboarding para diretrizes esteticas ricas
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

DEFAULT_STYLE_DIRECTION = {
    "direction": "Professional and visually engaging, adapted to the brand's niche",
    "references": "editorial magazine layouts, modern social media design, brand-appropriate aesthetics",
    "typography": "clean sans-serif, medium to bold weight, good readability",
    "lighting": "soft natural daylight, diffused and even",
    "avoid": "generic stock photo aesthetic, cluttered layouts",
}

STYLE_GENERATION_PROMPT_SYSTEM = (
    "You are a world-class Art Director creating visual styles for Instagram posts.\n\n"
    "You have deep knowledge of design movements, photography styles, and visual culture.\n"
    "Your styles are specific, vivid, and produce striking images — never generic or corporate.\n\n"
    "Before creating, you must reason about the best visual strategy.\n"
    "Analyze the brand context, market intelligence, audience, and content — then create.\n\n"
    "Return ONLY a valid JSON object. No markdown, no explanation, no code blocks."
)

STYLE_GENERATION_PROMPT_TEMPLATE = """
### BRAND ###
- Business: {business_name}
- Niche: {specialization}
- Personality: {brand_personality}
- Voice: {voice_tone}
- Purpose: {business_purpose}
- Products/Services: {products_services}
- Brand colors:
{colors_formatted}

### TARGET AUDIENCE ###
- Who: {target_audience}
- Interests: {target_interests}
{audience_context}

### MARKET INTELLIGENCE (this week) ###
{market_context}

### COMPETITION ###
{competition_context}

### CONTENT (this specific post) ###
- Theme: {tema_principal}
- Visual scene: {contexto_visual_sugerido}
- Key elements: {objetos_relevantes}
- Emotions: {emocoes_associadas}
- Feeling: {sensacao_geral}
{content_type_context}

### AESTHETIC DIRECTION (user preference) ###
{style_direction}

### FAVORITE STYLES (user loves these — use as strong inspiration) ###
{favorite_styles}

### PREVIOUS STYLES (avoid repetition) ###
{previous_styles}

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

### TOP PERFORMING STYLES (proven engagement) ###
{performance_data}

### MANDATORY VISUAL APPROACH FOR THIS POST ###
{visual_approach}

### RULES ###
1. Brand colors are your STARTING POINT, not a constraint. Use them for ONE element (logo area, accent, or text). The rest of the palette should COMPLEMENT the brand but come from DIFFERENT color families. If brand is purple, try warm gold + sage green, or coral + navy.
2. The aesthetic MUST match the niche: a bakery looks different from a law firm
3. Be SPECIFIC: not "modern design" but "bold geometric composition inspired by Bauhaus posters with overlapping shapes"
4. Pick ONE lighting — do not mix conflicting light sources
5. Colors must be memory color names (descriptive), NEVER hex codes
6. Limit to 2-3 dominant colors + 1 accent — more creates visual noise
7. The style must work for Instagram feed (4:5 vertical)
8. Consider the TARGET AUDIENCE — design for who will SEE this, not just the brand
9. Consider MARKET CONTEXT — align with or intentionally contrast current trends
10. DIFFERENTIATE from competition — if they use cold corporate, go warm and human
11. The "rationale" must explain WHY this style works for this specific case
12. If FAVORITE STYLES exist, take INSPIRATION from them (shared mood or composition), but the visual execution (colors, technique, aesthetic) MUST be noticeably different. Do NOT copy the same style.
13. If TOP PERFORMING STYLES exist, incorporate elements that drove engagement
14. NEVER repeat visual clichés from PREVIOUS STYLES. If previous styles used glassmorphism, do NOT use glassmorphism. If they used isometric 3D, try flat illustration or photography. Actively choose a DIFFERENT visual technique.
15. Do NOT include decorative icons like rockets, lightbulbs, or generic tech symbols unless the content specifically requires them. Prefer concrete, topic-specific imagery.
16. The image MUST be primarily VISUAL, not textual. Typography should be limited to the post title only. NEVER design a style where text/typography covers more than 30% of the canvas. The AI image model cannot generate extended text without errors — so the visual must rely on imagery, illustration, photography, or graphic elements, NOT walls of text.
17. If a FAVORITE STYLE is typography-heavy, do NOT replicate the typography-heavy approach. Instead, inherit the mood, color energy, or compositional boldness — but express it through VISUAL elements (illustration, photography, graphic shapes).

### OUTPUT (JSON only) ###
{{
    "rationale": "2-3 sentences explaining the strategic reasoning: WHY this visual approach for this brand + audience + market moment + content. Reference specific data from the context.",
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
    content_type: str | None = None,
    opportunity_score: int | None = None,
) -> GeneratedVisualStyle:
    """Gera um estilo visual unico via IA e salva no banco."""
    profile_data = get_creator_profile_data(user)
    colors_formatted = format_colors_for_prompt(
        profile_data.get('color_palette', []),
    )
    style_direction = _get_style_direction(user)
    market_ctx, comp_ctx, audience_ctx = _gather_market_context(user)
    previous_styles = _gather_previous_styles(user)
    favorite_styles = _gather_favorite_styles(user)
    performance_data = _gather_performance_data(user)
    content_ctx = _format_content_type_context(content_type, opportunity_score)

    visual_approach = _pick_visual_approach(user)

    prompt_body = STYLE_GENERATION_PROMPT_TEMPLATE.format(
        business_name=profile_data.get('business_name', ''),
        specialization=profile_data.get('specialization', ''),
        brand_personality=profile_data.get('brand_personality', ''),
        voice_tone=profile_data.get('voice_tone', ''),
        business_purpose=profile_data.get('business_purpose', ''),
        products_services=profile_data.get('products_services', ''),
        colors_formatted=colors_formatted,
        target_audience=profile_data.get('target_audience', ''),
        target_interests=profile_data.get('target_interests', ''),
        audience_context=audience_ctx,
        market_context=market_ctx,
        competition_context=comp_ctx,
        tema_principal=semantic_analysis.get('tema_principal', ''),
        contexto_visual_sugerido=semantic_analysis.get(
            'contexto_visual_sugerido', '',
        ),
        objetos_relevantes=', '.join(
            semantic_analysis.get('objetos_relevantes', []),
        ),
        emocoes_associadas=', '.join(
            semantic_analysis.get(
                'emocoes_associadas',
                semantic_analysis.get('emoções_associadas', []),
            ),
        ),
        sensacao_geral=semantic_analysis.get(
            'sensacao_geral',
            semantic_analysis.get('sensação_geral', ''),
        ),
        content_type_context=content_ctx,
        style_direction=style_direction,
        favorite_styles=favorite_styles,
        previous_styles=previous_styles,
        performance_data=performance_data,
        visual_approach=visual_approach,
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

    logger.info(
        "Estilo visual '%s' gerado para user %s (id=%d)",
        style.name, user.email, style.id,
    )
    return style


VISUAL_APPROACHES = [
    {
        "technique": "Editorial photography",
        "description": "High-quality lifestyle or product photography with editorial magazine styling. Real textures, real materials, real light. Think Kinfolk, Cereal Magazine, or Apple product shots.",
        "color_strategy": "Muted earth tones with one bold accent. Warm neutrals (sand, linen, cream) dominate.",
    },
    {
        "technique": "Flat illustration",
        "description": "Bold flat vector illustration with geometric shapes, clean lines, no gradients. Think Mailchimp, Slack, or Headspace app illustrations. Characters or objects are stylized and simple.",
        "color_strategy": "Vibrant complementary pair (e.g. teal + coral, mustard + navy). Flat solid fills, no shadows.",
    },
    {
        "technique": "Data visualization / Infographic",
        "description": "Clean data-driven layout with charts, numbers, and structured information hierarchy. Think The Economist, FiveThirtyEight, or annual report design. Information is the hero.",
        "color_strategy": "Monochromatic base with color used for data emphasis. White/light background, dark text, colored data points.",
    },
    {
        "technique": "Collage / Mixed media",
        "description": "Layered composition mixing photography cutouts, paper textures, hand-drawn elements, and typography. Think 90s zine aesthetic, Wes Anderson, or modern editorial collage.",
        "color_strategy": "Warm vintage palette (terracotta, mustard, olive) or cool editorial (ice blue, charcoal, blush).",
    },
    {
        "technique": "Photographic texture close-up",
        "description": "Macro or close-up photography of real textures and materials as background — paper grain, fabric weave, wood grain, concrete, marble, coffee foam. The texture becomes the canvas. Minimal overlaid elements. Think Aesop branding, Muji, or artisan packaging.",
        "color_strategy": "Natural material palette — the colors come from the real texture. Warm browns, creams, grays. One accent color for text/logo contrast.",
    },
    {
        "technique": "3D render / Clay style",
        "description": "Soft 3D rendered objects with clay/matte material. Rounded shapes, soft shadows, playful depth. Think Figma 3D illustrations, Notion icons, or Google Material You.",
        "color_strategy": "Pastel palette with depth (soft lavender, mint, peach). Subtle shadows create dimension.",
    },
    {
        "technique": "Split composition",
        "description": "Canvas divided into distinct zones (half/half, thirds, diagonal). Each zone has different visual treatment — photo vs solid color, before vs after, problem vs solution.",
        "color_strategy": "Contrasting palettes per zone. One warm, one cool. Creates visual tension.",
    },
    {
        "technique": "Gradient abstract",
        "description": "Flowing gradient backgrounds with minimal elements floating on top. Ethereal, modern, tech-forward. Think Stripe, Linear, or Arc browser aesthetics.",
        "color_strategy": "Rich gradient transitions (deep navy to warm sunset, forest to emerald). Avoid flat solids.",
    },
]


def _pick_visual_approach(user: User) -> str:
    """Seleciona uma abordagem visual diferente das usadas recentemente."""
    recent_styles = list(
        GeneratedVisualStyle.objects
        .filter(user=user)
        .order_by('-created_at')
        .values_list('style_data', flat=True)[:6]
    )

    # Extrai técnicas usadas recentemente dos aesthetics
    recent_aesthetics = []
    for sd in recent_styles:
        if isinstance(sd, dict):
            recent_aesthetics.append(sd.get('aesthetic', '').lower())
        elif isinstance(sd, str):
            try:
                parsed = json.loads(sd)
                recent_aesthetics.append(parsed.get('aesthetic', '').lower())
            except (json.JSONDecodeError, AttributeError):
                pass

    recent_text = ' '.join(recent_aesthetics)

    # Pontua cada approach pela distância das recentes
    scored = []
    for approach in VISUAL_APPROACHES:
        technique_lower = approach['technique'].lower()
        keywords = technique_lower.split(' / ') + technique_lower.split()

        # Penaliza se keywords do approach aparecem nos estilos recentes
        overlap = sum(1 for kw in keywords if kw in recent_text and len(kw) > 3)
        scored.append((approach, overlap))

    # Ordena por menor overlap (mais diferente)
    scored.sort(key=lambda x: x[1])

    # Pega os 3 mais diferentes e escolhe aleatoriamente
    top_candidates = [s[0] for s in scored[:3]]
    chosen = random.choice(top_candidates)

    return (
        f"You MUST use this visual technique: **{chosen['technique']}**\n"
        f"Description: {chosen['description']}\n"
        f"Color strategy: {chosen['color_strategy']}\n"
        f"Do NOT use glassmorphism, isometric 3D dioramas, or holographic UI overlays "
        f"unless the chosen technique specifically calls for it."
    )


def _gather_market_context(user: User) -> tuple[str, str, str]:
    """Busca dados do ClientContext para informar o estilo."""
    try:
        from ClientContext.models import ClientContext
        context = ClientContext.objects.filter(user=user).first()
    except Exception:
        return ("No market data available.", "No competition data available.", "")

    if not context:
        return ("No market data available.", "No competition data available.", "")

    # Market
    market_lines = []
    if context.market_panorama:
        market_lines.append(
            "- Market overview: " + context.market_panorama[:300],
        )
    if context.market_tendencies:
        items = (
            context.market_tendencies[:5]
            if isinstance(context.market_tendencies, list) else []
        )
        if items:
            joined = ', '.join(str(t) for t in items)
            market_lines.append("- Trending now: " + joined)
    if context.discovered_trends and isinstance(context.discovered_trends, list):
        joined = ', '.join(str(t) for t in context.discovered_trends[:3])
        market_lines.append("- Validated trends: " + joined)
    if context.brand_communication_style:
        market_lines.append(
            "- Recommended tone this week: "
            + context.brand_communication_style[:200],
        )
    market_text = (
        "\n".join(market_lines)
        if market_lines else "No market data available."
    )

    # Competition
    comp_lines = []
    if context.competition_strategies:
        comp_lines.append(
            "- What competitors are doing: "
            + context.competition_strategies[:300],
        )
    if context.competition_opportunities:
        comp_lines.append(
            "- Opportunities vs competition: "
            + context.competition_opportunities[:200],
        )
    comp_text = (
        "\n".join(comp_lines)
        if comp_lines else "No competition data available."
    )

    # Audience (from weekly research)
    audience_lines = []
    if context.target_audience_behaviors:
        audience_lines.append(
            "- Current behaviors: "
            + context.target_audience_behaviors[:200],
        )
    if context.target_audience_interests:
        interests = context.target_audience_interests
        if isinstance(interests, list) and interests:
            joined = ', '.join(str(i) for i in interests[:5])
            audience_lines.append("- Researched interests: " + joined)
    audience_text = "\n".join(audience_lines) if audience_lines else ""

    return (market_text, comp_text, audience_text)


def _gather_previous_styles(user: User, limit: int = 10) -> str:
    """Busca estilos anteriores do usuario, separados por feedback."""
    previous = list(
        GeneratedVisualStyle.objects
        .filter(user=user)
        .order_by('-created_at')[:limit]
    )

    if not previous:
        return "No previous styles -- this is the first generation. Be creative!"

    def _format_style(s):
        data = s.style_data or {}
        colors = data.get('colors', {})
        bg = colors.get("background", "")
        prim = colors.get("primary", "")
        accent = colors.get("accent", "")
        light = data.get("lighting", "")[:40]
        aes = data.get("aesthetic", "")[:80]
        return (
            '- "' + s.name + '": ' + aes + '... '
            '(colors: ' + bg + ' / ' + prim + ' / ' + accent
            + ' | lighting: ' + light + ')'
        )

    accepted = [s for s in previous if s.feedback_signal == 'accepted']
    rejected = [s for s in previous if s.feedback_signal == 'rejected']
    pending = [s for s in previous if s.feedback_signal == 'pending']

    # If all pending, keep original behavior
    if not accepted and not rejected:
        lines = [_format_style(s) for s in previous]
        lines.append(
            "-> Generate something DIFFERENT from these. "
            "Vary the aesthetic, colors, and lighting."
        )
        return "\n".join(lines)

    sections = []
    if accepted:
        sections.append("Styles the user LIKED (published):")
        sections.extend(_format_style(s) for s in accepted)
    if rejected:
        sections.append("Styles the user REJECTED (regenerated) — avoid similar:")
        sections.extend(_format_style(s) for s in rejected)
    if pending:
        sections.append("Recent styles (no feedback) — vary from these:")
        sections.extend(_format_style(s) for s in pending)

    sections.append(
        "-> Use LIKED styles as positive reference, AVOID patterns from REJECTED styles, "
        "and vary from pending styles."
    )
    return "\n".join(sections)


def _gather_favorite_styles(user: User, limit: int = 3) -> str:
    """Busca estilos favoritos do usuario como referencia forte."""
    favorites = list(
        GeneratedVisualStyle.objects
        .filter(user=user, is_favorite=True)
        .order_by('-created_at')[:limit]
    )

    if not favorites:
        return "No favorite styles yet."

    lines = []
    for s in favorites:
        data = s.style_data or {}
        aes = data.get("aesthetic", "")[:100]
        colors = data.get('colors', {})
        mood = data.get("mood", "")
        lines.append(f'- "{s.name}": {aes} (mood: {mood}, colors: {colors.get("primary", "")}, {colors.get("accent", "")})')

    lines.append(
        "-> Take INSPIRATION from favorites (mood, energy, quality level), "
        "but the visual execution MUST be different. Same vibe, different look."
    )
    return "\n".join(lines)


def _gather_performance_data(user: User, limit: int = 5) -> str:
    """Busca estilos com maior engagement_score."""
    top = list(
        GeneratedVisualStyle.objects
        .filter(user=user, engagement_score__isnull=False)
        .order_by('-engagement_score')[:limit]
    )

    if not top:
        return ""

    lines = []
    for s in top:
        data = s.style_data or {}
        aes = data.get("aesthetic", "")[:80]
        lines.append(
            f'- "{s.name}" (engagement score: {s.engagement_score:.1f}): {aes}'
        )

    lines.append(
        "-> Incorporate elements from top performing styles to maximize engagement."
    )
    return "\n".join(lines)


def _format_content_type_context(
    content_type: str | None,
    opportunity_score: int | None,
) -> str:
    """Formata contexto do tipo de oportunidade do conteudo."""
    if not content_type:
        return ""

    type_visual_mapping = {
        "Polemica": (
            "High-contrast, attention-grabbing. Bold colors, dramatic lighting. "
            "Think protest poster or breaking news."
        ),
        "Educativo": (
            "Clear, structured, trustworthy. Clean layout, good readability. "
            "Think textbook meets infographic."
        ),
        "Newsjacking": (
            "Urgent, current, dynamic. News-inspired layout, bold typography. "
            "Think newspaper front page meets social media."
        ),
        "Entretenimento": (
            "Fun, vibrant, scroll-stopping. Playful colors, energetic composition. "
            "Think meme culture meets branded content."
        ),
        "Estudo de Caso": (
            "Professional, data-driven, authoritative. Structured layout, "
            "confident colors. Think business presentation meets editorial."
        ),
        "Futuro": (
            "Visionary, innovative, forward-looking. Gradient/futuristic palette, "
            "modern composition. Think sci-fi meets TED talk."
        ),
    }

    lines = ["- Content type: " + content_type]
    if content_type in type_visual_mapping:
        lines.append(
            "- Visual approach for this type: "
            + type_visual_mapping[content_type]
        )
    if opportunity_score is not None:
        if opportunity_score >= 80:
            lines.append(
                "- Impact score: " + str(opportunity_score) + "/100 "
                "(HIGH -- make the style bold and attention-grabbing)"
            )
        elif opportunity_score >= 50:
            lines.append(
                "- Impact score: " + str(opportunity_score) + "/100 "
                "(MEDIUM -- balanced between impact and professionalism)"
            )
        else:
            lines.append(
                "- Impact score: " + str(opportunity_score) + "/100 "
                "(MODERATE -- focus on clarity and brand alignment)"
            )
    return "\n".join(lines)


def _get_style_direction(user: User) -> str:
    """Monta a direcao estetica baseada na preferencia do onboarding."""
    try:
        profile = CreatorProfile.objects.get(user=user)
        style_ids = profile.visual_style_ids or []
    except CreatorProfile.DoesNotExist:
        style_ids = []

    if not style_ids:
        direction = DEFAULT_STYLE_DIRECTION
    else:
        first = style_ids[0]
        primary_style = first if isinstance(first, str) else str(first)
        direction = STYLE_DIRECTIONS.get(primary_style, DEFAULT_STYLE_DIRECTION)

    lines = [
        "- Direction: " + direction['direction'],
        "- Reference artists/styles: " + direction['references'],
        "- Typography tendency: " + direction['typography'],
        "- Lighting tendency: " + direction['lighting'],
        "- Avoid: " + direction['avoid'],
    ]
    return "\n".join(lines)


def _parse_style_json(raw_text: str) -> dict:
    """Parseia o JSON retornado pela IA, tratando markdown code blocks."""
    cleaned = raw_text.strip()

    if cleaned.startswith('```'):
        idx = cleaned.index('\n') if '\n' in cleaned else len(cleaned)
        cleaned = cleaned[idx + 1:]
        if cleaned.rstrip().endswith('```'):
            cleaned = cleaned.rstrip()[:-3].rstrip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(
            "Falha ao parsear JSON do estilo: %s. Raw: %s",
            e, raw_text[:200],
        )
        return _default_style()

    required_fields = [
        'aesthetic', 'colors', 'lighting', 'typography', 'composition',
    ]
    missing = [f for f in required_fields if f not in data]
    if missing:
        logger.warning("Estilo gerado sem campos obrigatorios: %s", missing)
        defaults = _default_style()
        for field in missing:
            data[field] = defaults[field]

    return data


def _default_style() -> dict:
    """Estilo fallback caso a IA retorne JSON invalido."""
    return {
        "name": "Minimalista Profissional",
        "aesthetic": (
            "Clean minimalist design with generous whitespace, "
            "inspired by Kinfolk magazine editorial layouts"
        ),
        "colors": {
            "background": "warm ivory",
            "primary": "deep cobalt blue",
            "accent": "vivid coral",
            "text": "dark charcoal",
        },
        "lighting": "soft overcast nordic daylight, diffused and even",
        "typography": (
            "modern geometric sans-serif, light weight, generous letter-spacing"
        ),
        "composition": (
            "title upper third centered, main visual centered 40% of frame, "
            "logo bottom-right 8%"
        ),
        "mood": "professional, refined, confident",
        "references": [
            "Kinfolk magazine editorial",
            "Swiss International Style poster",
        ],
    }
