import colorsys
import logging

logger = logging.getLogger(__name__)

# Memory colors organizadas por família HSL.
# Cada entrada: (hue_min, hue_max, sat_min, sat_max, light_min, light_max, nome)
# Hue em graus (0-360), Sat e Light em 0-1.
# Ordem: do mais específico ao mais genérico (primeiro match vence).
MEMORY_COLORS = [
    # === WHITES / VERY LIGHT (lightness > 0.90) ===
    (0, 360, 0.0, 0.05, 0.95, 1.0, "pure white"),
    (0, 360, 0.0, 0.10, 0.90, 0.95, "snow white"),
    (30, 60, 0.10, 0.50, 0.90, 0.97, "warm ivory"),
    (60, 120, 0.10, 0.50, 0.90, 0.97, "pale mint"),
    (200, 260, 0.10, 0.50, 0.90, 0.97, "ice blue"),
    (0, 30, 0.10, 0.50, 0.90, 0.97, "pale blush"),
    (0, 360, 0.05, 0.30, 0.85, 0.92, "cream"),

    # === BLACKS / VERY DARK (lightness < 0.12) ===
    (0, 360, 0.0, 0.10, 0.0, 0.05, "pure black"),
    (200, 270, 0.10, 1.0, 0.05, 0.15, "deep midnight navy"),
    (0, 360, 0.0, 0.10, 0.05, 0.12, "onyx black"),

    # === GRAYS (saturation < 0.10) ===
    (0, 360, 0.0, 0.10, 0.75, 0.90, "light silver"),
    (0, 360, 0.0, 0.10, 0.55, 0.75, "pewter gray"),
    (0, 360, 0.0, 0.10, 0.35, 0.55, "slate gray"),
    (0, 360, 0.0, 0.10, 0.20, 0.35, "charcoal"),
    (0, 360, 0.0, 0.10, 0.12, 0.20, "dark charcoal"),

    # === ORANGES / TERRACOTTA (hue 10-45) — before reds to catch warm orangey-reds ===
    (10, 30, 0.50, 1.0, 0.50, 0.70, "warm terracotta"),

    # === REDS (hue 0-10, 345-360) ===
    (345, 360, 0.70, 1.0, 0.40, 0.60, "vivid scarlet"),
    (0, 10, 0.70, 1.0, 0.40, 0.60, "vivid scarlet"),
    (345, 360, 0.50, 0.70, 0.40, 0.60, "rich cherry red"),
    (0, 10, 0.50, 0.70, 0.40, 0.60, "rich cherry red"),
    (345, 360, 0.30, 0.60, 0.20, 0.40, "deep wine red"),
    (0, 10, 0.30, 0.60, 0.20, 0.40, "deep wine red"),
    (345, 360, 0.60, 1.0, 0.60, 0.80, "soft coral red"),
    (0, 10, 0.60, 1.0, 0.60, 0.80, "soft coral red"),
    (345, 360, 0.20, 0.50, 0.15, 0.30, "dark burgundy"),
    (0, 10, 0.20, 0.50, 0.15, 0.30, "dark burgundy"),
    (15, 30, 0.70, 1.0, 0.40, 0.55, "burnt orange"),
    (30, 45, 0.70, 1.0, 0.45, 0.65, "bright tangerine"),
    (15, 30, 0.40, 0.70, 0.30, 0.50, "warm rust"),
    (30, 45, 0.30, 0.60, 0.30, 0.50, "rich amber"),
    (15, 45, 0.50, 1.0, 0.65, 0.80, "soft apricot"),
    (15, 30, 0.60, 1.0, 0.25, 0.40, "deep copper"),

    # === YELLOWS (hue 45-65) ===
    (45, 55, 0.80, 1.0, 0.45, 0.60, "warm antique gold"),
    (50, 65, 0.80, 1.0, 0.55, 0.70, "bright sunflower"),
    (45, 65, 0.60, 0.90, 0.40, 0.55, "rich golden"),
    (45, 65, 0.30, 0.60, 0.30, 0.50, "dark mustard"),
    (45, 65, 0.50, 1.0, 0.70, 0.85, "soft butter yellow"),
    (45, 65, 0.70, 1.0, 0.60, 0.75, "warm honey"),

    # === YELLOW-GREEN (hue 65-90) ===
    (65, 90, 0.40, 1.0, 0.40, 0.60, "fresh chartreuse"),
    (65, 90, 0.20, 0.50, 0.30, 0.50, "muted olive"),
    (65, 90, 0.40, 1.0, 0.60, 0.80, "soft pistachio"),

    # === GREENS (hue 90-165) ===
    (90, 140, 0.50, 1.0, 0.30, 0.50, "deep emerald green"),
    (90, 140, 0.60, 1.0, 0.50, 0.65, "bright kelly green"),
    (140, 165, 0.30, 0.70, 0.35, 0.55, "muted sage green"),
    (90, 140, 0.10, 0.30, 0.25, 0.45, "dark forest green"),
    (90, 140, 0.20, 0.50, 0.40, 0.60, "earthy moss green"),
    (140, 165, 0.40, 0.80, 0.55, 0.75, "soft mint green"),
    (90, 140, 0.40, 0.80, 0.65, 0.80, "pale sage"),
    (90, 140, 0.10, 0.30, 0.15, 0.30, "deep pine green"),

    # === TEALS / CYANS (hue 165-200) ===
    (165, 185, 0.50, 1.0, 0.35, 0.55, "rich teal"),
    (165, 185, 0.60, 1.0, 0.55, 0.70, "bright turquoise"),
    (185, 200, 0.50, 1.0, 0.40, 0.60, "deep cerulean"),
    (165, 200, 0.30, 0.60, 0.55, 0.75, "soft seafoam"),
    (165, 200, 0.40, 0.80, 0.70, 0.85, "pale aqua"),

    # === BLUES (hue 200-260) ===
    (200, 225, 0.70, 1.0, 0.40, 0.55, "bright cobalt blue"),
    (200, 225, 0.50, 0.80, 0.50, 0.65, "clear sky blue"),
    (225, 245, 0.60, 1.0, 0.35, 0.50, "deep royal blue"),
    (225, 245, 0.70, 1.0, 0.50, 0.65, "vivid sapphire blue"),
    (200, 225, 0.30, 0.60, 0.25, 0.40, "dark steel blue"),
    (225, 260, 0.40, 0.80, 0.15, 0.30, "deep navy blue"),
    (200, 260, 0.50, 1.0, 0.65, 0.80, "soft powder blue"),
    (200, 260, 0.20, 0.50, 0.40, 0.60, "muted denim blue"),
    (225, 260, 0.60, 1.0, 0.25, 0.40, "rich indigo"),

    # === PURPLES (hue 260-310) ===
    (260, 285, 0.50, 1.0, 0.35, 0.55, "deep amethyst purple"),
    (260, 285, 0.60, 1.0, 0.50, 0.65, "vivid violet"),
    (285, 310, 0.40, 0.80, 0.30, 0.50, "rich plum"),
    (260, 285, 0.30, 0.60, 0.60, 0.80, "soft lavender"),
    (285, 310, 0.30, 0.70, 0.55, 0.75, "gentle lilac"),
    (260, 310, 0.20, 0.40, 0.20, 0.35, "dark eggplant"),
    (285, 310, 0.50, 1.0, 0.50, 0.65, "bright orchid"),

    # === PINKS / MAGENTAS (hue 310-345) ===
    (310, 330, 0.70, 1.0, 0.45, 0.60, "vivid hot pink"),
    (330, 345, 0.50, 1.0, 0.40, 0.60, "rich raspberry"),
    (310, 345, 0.40, 0.70, 0.60, 0.80, "soft rose pink"),
    (310, 345, 0.60, 1.0, 0.70, 0.85, "pale cotton candy pink"),
    (310, 330, 0.30, 0.60, 0.30, 0.50, "deep mauve"),
    (330, 345, 0.20, 0.50, 0.50, 0.70, "muted dusty rose"),

    # === BROWNS (low saturation oranges/yellows) ===
    (15, 45, 0.30, 0.70, 0.15, 0.30, "rich chocolate brown"),
    (15, 45, 0.20, 0.50, 0.25, 0.40, "warm coffee brown"),
    (15, 45, 0.15, 0.40, 0.35, 0.50, "soft cinnamon"),
    (20, 50, 0.10, 0.30, 0.40, 0.55, "muted taupe"),
    (25, 50, 0.20, 0.50, 0.50, 0.65, "warm sand"),
    (15, 40, 0.30, 0.60, 0.20, 0.35, "deep sienna"),
    (30, 50, 0.40, 0.70, 0.30, 0.45, "warm caramel"),
]


def _hex_to_rgb(hex_color: str) -> tuple:
    """Converte hex para tupla RGB (0-255)."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple:
    """Converte RGB (0-255) para HSL (h: 0-360, s: 0-1, l: 0-1)."""
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return (h * 360, s, l)


def _match_memory_color(h: float, s: float, l: float) -> str | None:
    """Encontra o memory color que melhor corresponde ao HSL dado."""
    for h_min, h_max, s_min, s_max, l_min, l_max, name in MEMORY_COLORS:
        if h_min <= h <= h_max and s_min <= s <= s_max and l_min <= l <= l_max:
            return name
    return None


def _find_closest_memory_color(h: float, s: float, l: float) -> str:
    """Fallback: encontra o memory color mais próximo por distância HSL."""
    min_distance = float('inf')
    closest = "neutral gray"

    for h_min, h_max, s_min, s_max, l_min, l_max, name in MEMORY_COLORS:
        # Centro do range
        hc = (h_min + h_max) / 2
        sc = (s_min + s_max) / 2
        lc = (l_min + l_max) / 2

        # Distância circular para hue
        h_diff = min(abs(h - hc), 360 - abs(h - hc)) / 180.0
        s_diff = abs(s - sc)
        l_diff = abs(l - lc)

        # Peso: lightness e saturation importam mais que hue puro
        distance = (h_diff ** 2) + (s_diff ** 2) * 1.5 + (l_diff ** 2) * 2.0

        if distance < min_distance:
            min_distance = distance
            closest = name

    return closest


def hex_to_memory_color(hex_color: str) -> str:
    """
    Converte código HEX para memory color descritivo.

    Memory colors são nomes baseados em objetos do mundo real que IAs de imagem
    entendem melhor que códigos hex ou nomes CSS3 genéricos.

    Args:
        hex_color: Código HEX (ex: '#FF6B6B', '#4ECDC4')

    Returns:
        Memory color em inglês (ex: 'warm terracotta', 'bright turquoise')
    """
    if not hex_color:
        return 'neutral gray'

    try:
        if not hex_color.startswith('#'):
            hex_color = f'#{hex_color}'

        r, g, b = _hex_to_rgb(hex_color)
        h, s, l = _rgb_to_hsl(r, g, b)

        # Tenta match direto por range HSL
        result = _match_memory_color(h, s, l)
        if result:
            return result

        # Fallback: cor mais próxima por distância
        return _find_closest_memory_color(h, s, l)

    except Exception as e:
        logger.warning("Erro ao converter cor %s: %s", hex_color, e)
        return 'neutral gray'


def format_colors_for_prompt(color_palette: list) -> str:
    """
    Formata paleta de cores para uso em prompts de IA.

    Converte lista de HEX para memory colors descritivos.

    Args:
        color_palette: Lista de códigos HEX (ex: ['#FF6B6B', '#4ECDC4'])

    Returns:
        String formatada com memory colors (ex: '- soft coral red\\n- bright turquoise')
    """
    if not color_palette:
        return "- neutral colors"

    descriptions = []
    for hex_color in color_palette:
        if hex_color:
            name = hex_to_memory_color(hex_color)
            descriptions.append(f"- {name}")

    return "\n".join(descriptions) if descriptions else "- neutral colors"
