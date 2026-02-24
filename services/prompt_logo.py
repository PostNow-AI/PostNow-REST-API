from services.color_extraction import format_colors_for_prompt


def build_logo_section(business_name: str, color_palette: list, position: str = "bottom-right corner") -> str:
    """
    Gera instruções detalhadas para preservação de logo em imagens.

    Esta função resolve o problema da IA não renderizar o logo corretamente,
    fornecendo instruções específicas sobre posição, tamanho e preservação.

    Args:
        business_name: Nome da marca (ex: 'PostNow')
        color_palette: Lista de cores HEX do perfil
        position: Posição do logo na imagem (default: 'bottom-right corner')

    Returns:
        String com instruções completas para preservação do logo
    """
    colors_formatted = format_colors_for_prompt(color_palette)

    return f"""
**LOGO (Preserved Element):**

Using the attached logo image of "{business_name}", place it in the {position}
at approximately 8% of the image width, ensuring it remains clearly visible
but not dominant.

PRESERVE EXACTLY: the icon shape and geometry, the text "{business_name}"
spelling and arrangement, and the overall logo proportions. The logo must
appear exactly as provided in the attachment.

Change ONLY the logo colors if needed for contrast against the background.
Choose from the brand palette colors that provide maximum readability:
{colors_formatted}

Keep the logo unchanged in every other aspect: same icon geometry, same text
content, same layout structure. Ensure all parts of the logo are fully visible
and legible against any background color.
""".strip()
