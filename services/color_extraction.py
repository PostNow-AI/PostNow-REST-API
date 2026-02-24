import logging

import webcolors

logger = logging.getLogger(__name__)

_CSS3_COLOR_MAP = None


def _get_css3_color_map() -> dict:
    """
    Retorna mapeamento de cores CSS3 (nome → rgb).
    Usa cache para evitar recálculo.
    """
    global _CSS3_COLOR_MAP
    if _CSS3_COLOR_MAP is None:
        _CSS3_COLOR_MAP = {}
        for name in webcolors.names():
            try:
                rgb = webcolors.name_to_rgb(name)
                _CSS3_COLOR_MAP[name] = rgb
            except ValueError as exc:
                logger.debug("Ignoring invalid CSS3 color name from webcolors: %s (%s)", name, exc)
    return _CSS3_COLOR_MAP


def _find_closest_color(rgb: tuple) -> str:
    """
    Encontra o nome da cor CSS3 mais próxima usando distância Euclidiana.

    Args:
        rgb: Tupla (r, g, b) com valores 0-255

    Returns:
        Nome da cor CSS3 mais próxima (ex: 'coral', 'teal', 'salmon')
    """
    color_map = _get_css3_color_map()
    min_distance = float('inf')
    closest_name = 'gray'  # fallback

    for name, (r, g, b) in color_map.items():
        distance = (r - rgb[0]) ** 2 + (g - rgb[1]) ** 2 + (b - rgb[2]) ** 2
        if distance < min_distance:
            min_distance = distance
            closest_name = name

    return closest_name


def _hex_to_color_name(hex_color: str) -> str:
    """
    Converte qualquer código HEX para o nome de cor mais próximo.

    Usa a biblioteca webcolors para encontrar o nome CSS3 mais próximo,
    evitando que a IA de imagem interprete códigos HEX literalmente.

    Args:
        hex_color: Código HEX (ex: '#FF6B6B', '#4ECDC4')

    Returns:
        Nome da cor em inglês (ex: 'coral', 'medium aquamarine')
    """
    if not hex_color:
        return 'gray'

    try:
        # Normaliza o hex (adiciona # se necessário)
        if not hex_color.startswith('#'):
            hex_color = f'#{hex_color}'

        rgb = webcolors.hex_to_rgb(hex_color)

        # Tenta match exato primeiro
        try:
            return webcolors.hex_to_name(hex_color)
        except ValueError:
            # Se não encontrar, busca a cor mais próxima
            return _find_closest_color(rgb)
    except Exception as e:
        logger.warning(f"Erro ao converter cor {hex_color}: {e}")
        return 'gray'


def format_colors_for_prompt(color_palette: list) -> str:
    """
    Formata paleta de cores para uso em prompts de IA.

    Converte lista de HEX para nomes descritivos que a IA entende melhor.

    Args:
        color_palette: Lista de códigos HEX (ex: ['#FF6B6B', '#4ECDC4'])

    Returns:
        String formatada com nomes de cores (ex: '- coral\n- medium aquamarine')
    """
    if not color_palette:
        return "- neutral colors"

    descriptions = []
    for hex_color in color_palette:
        if hex_color:
            name = _hex_to_color_name(hex_color)
            descriptions.append(f"- {name}")

    return "\n".join(descriptions) if descriptions else "- neutral colors"
