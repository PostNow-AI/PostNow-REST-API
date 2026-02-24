"""
ColorService - Serviço de manipulação de cores para prompts de IA.

Este módulo contém funções para converter códigos HEX em nomes de cores
que a IA de geração de imagens entende melhor.

Problema resolvido:
    Quando enviamos '#FF6B6B' para a IA, ela pode interpretar literalmente
    e renderizar o texto '#FF6B6B' na imagem. Usando 'salmon' (nome da cor),
    a IA entende que deve usar essa cor, não renderizá-la como texto.

Solução:
    Usa a biblioteca webcolors para converter qualquer código HEX
    para o nome CSS3 mais próximo (147 cores disponíveis).
"""

import logging
from typing import List, Tuple

import webcolors

logger = logging.getLogger(__name__)


# =============================================================================
# CACHE DE CORES CSS3
# =============================================================================

# Cache do mapeamento de cores CSS3 (criado uma vez na importação)
_CSS3_COLOR_MAP = None


def _get_css3_color_map() -> dict:
    """
    Retorna mapeamento de cores CSS3 (nome → rgb).

    Usa cache para evitar recálculo em chamadas subsequentes.
    O cache é criado na primeira chamada e reutilizado.

    Returns:
        Dict com {nome_cor: (r, g, b)} para todas as 147 cores CSS3
    """
    global _CSS3_COLOR_MAP
    if _CSS3_COLOR_MAP is None:
        _CSS3_COLOR_MAP = {}
        for name in webcolors.names():
            try:
                rgb = webcolors.name_to_rgb(name)
                _CSS3_COLOR_MAP[name] = rgb
            except ValueError as exc:
                logger.debug(
                    "Ignoring invalid CSS3 color name from webcolors: %s (%s)",
                    name, exc
                )
    return _CSS3_COLOR_MAP


# =============================================================================
# CONVERSÃO DE CORES
# =============================================================================

def find_closest_color(rgb: Tuple[int, int, int]) -> str:
    """
    Encontra o nome da cor CSS3 mais próxima usando distância Euclidiana.

    Algoritmo:
        Para cada cor CSS3, calcula a distância no espaço RGB:
        distance = (r1-r2)² + (g1-g2)² + (b1-b2)²
        Retorna a cor com menor distância.

    Args:
        rgb: Tupla (r, g, b) com valores 0-255

    Returns:
        Nome da cor CSS3 mais próxima (ex: 'coral', 'teal', 'salmon')

    Example:
        >>> find_closest_color((255, 107, 107))
        'salmon'
    """
    color_map = _get_css3_color_map()
    min_distance = float('inf')
    closest_name = 'gray'  # fallback

    for name, (r, g, b) in color_map.items():
        distance = (r - rgb[0])**2 + (g - rgb[1])**2 + (b - rgb[2])**2
        if distance < min_distance:
            min_distance = distance
            closest_name = name

    return closest_name


def hex_to_color_name(hex_color: str) -> str:
    """
    Converte qualquer código HEX para o nome de cor mais próximo.

    Usa a biblioteca webcolors para encontrar o nome CSS3 mais próximo,
    evitando que a IA de imagem interprete códigos HEX literalmente.

    Args:
        hex_color: Código HEX (ex: '#FF6B6B', '#4ECDC4', 'FF6B6B')

    Returns:
        Nome da cor em inglês (ex: 'coral', 'medium aquamarine')

    Examples:
        >>> hex_to_color_name('#FF6B6B')
        'salmon'
        >>> hex_to_color_name('#1A365D')
        'midnightblue'
        >>> hex_to_color_name('invalid')
        'gray'
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
            return find_closest_color(rgb)
    except Exception as e:
        logger.warning(f"Erro ao converter cor {hex_color}: {e}")
        return 'gray'


def format_colors_for_prompt(color_palette: List[str]) -> str:
    """
    Formata paleta de cores para uso em prompts de IA.

    Converte lista de HEX para nomes descritivos que a IA entende melhor.

    Args:
        color_palette: Lista de códigos HEX (ex: ['#FF6B6B', '#4ECDC4'])

    Returns:
        String formatada com nomes de cores, uma por linha

    Example:
        >>> format_colors_for_prompt(['#FF6B6B', '#4ECDC4'])
        '- salmon\\n- mediumturquoise'
    """
    if not color_palette:
        return "- neutral colors"

    descriptions = []
    for hex_color in color_palette:
        if hex_color:
            name = hex_to_color_name(hex_color)
            descriptions.append(f"- {name}")

    return "\n".join(descriptions) if descriptions else "- neutral colors"


# =============================================================================
# CONSTRUÇÃO DE SEÇÕES DE PROMPT
# =============================================================================

def build_logo_section(
    business_name: str,
    color_palette: List[str],
    position: str = "bottom-right corner"
) -> str:
    """
    Gera instruções detalhadas para preservação de logo em imagens.

    Esta função resolve o problema da IA não renderizar o logo corretamente,
    fornecendo instruções específicas sobre posição, tamanho e preservação.

    Problema original:
        A instrução "Renderize a logomarca quando anexada" era muito vaga.
        A IA às vezes ignorava o logo ou o distorcia.

    Solução:
        Instruções detalhadas sobre:
        - Posição exata (ex: bottom-right, 8% da largura)
        - O que preservar (geometria, texto, proporções)
        - O que pode alterar (cores para contraste)

    Args:
        business_name: Nome da marca (ex: 'PostNow')
        color_palette: Lista de cores HEX do perfil
        position: Posição do logo na imagem (default: 'bottom-right corner')

    Returns:
        String com instruções completas para preservação do logo

    Example:
        >>> build_logo_section('PostNow', ['#8B5CF6', '#FFFFFF'])
        '**LOGO (Preserved Element):**\\n\\nUsing the logo image...'
    """
    colors_formatted = format_colors_for_prompt(color_palette)

    return f"""
**LOGO (Preserved Element):**

Using the logo image of "{business_name}" attached, position it in the {position}
with approximately 8% of the image width, ensuring it remains clearly visible
but not dominant.

PRESERVE EXACTLY: the icon shape and geometry, the text "{business_name}"
(spelling and arrangement), and the overall logo proportions. The logo must
appear exactly as provided in the attachment.

ONLY ALTER the logo colors if necessary for contrast with the background.
Choose from the brand palette colors that provide maximum readability:
{colors_formatted}

Keep the logo unchanged in all other aspects. Ensure all parts of the logo
are fully visible and legible against any background color.
""".strip()
