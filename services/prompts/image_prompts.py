"""
Prompts para análise semântica e geração de imagens.

Extraído de ai_prompt_service.py para separação de responsabilidades.
"""

import logging

from services.color_extraction import format_colors_for_prompt
from services.get_creator_profile_data import get_creator_profile_data
from services.prompt_logo import build_logo_section

logger = logging.getLogger(__name__)


def semantic_analysis_prompt(post_text: str) -> list[str]:
    """Prompt for semantic analysis of user input."""
    return [
        """
              Você é um analista de semântica e especialista em direção de arte para redes sociais. Sua função é interpretar textos publicitários e identificar seus elementos conceituais e visuais principais, transformando a mensagem escrita em diretrizes visuais e emocionais claras. Baseie suas respostas apenas no texto fornecido, sem adicionar interpretações não fundamentadas.
            """,
        f"""
              Analise o texto a seguir e extraia:

              1. Tema principal
              2. Conceitos visuais que o representam
              3. Emoções ou sensações associadas
              4. Elementos visuais sugeridos (objetos, cenários, cores)

              Texto: {post_text}

              A SAÍDA DEVE SER NO FORMATO:
              {{
                "analise_semantica":{{
                  "tema_principal": "",
                  "subtemas": [],
                  "conceitos_visuais": [],
                  "objetos_relevantes": [],
                  "contexto_visual_sugerido": "",
                  "emoções_associadas": [],
                  "tons_de_cor_sugeridos": [],
                  "ação_sugerida": "",
                  "sensação_geral": "",
                  "palavras_chave": [],
                  "titulo_imagem": ""
                }}
              }}

              REGRA PARA titulo_imagem:
              - Máximo 8 palavras, direto e impactante
              - Deve capturar a essência do tema em uma frase curta
              - NUNCA terminar em preposição ou conjunção (de, da, e, para, com, no, na, entre, sobre, como, sem)
              - Exemplos bons: "Erros fatais no primeiro ano da startup", "Precificação estratégica de SaaS B2B", "CLT ou empreendedorismo: a escolha real"
              - Exemplos ruins: "A importância da construção de um branding sólido, posicionamento e identidade visual para startups" (longo demais), "Vendas B2B para" (termina em preposição)
            """
    ]


def adapted_semantic_analysis_prompt(user, semantic_analysis: dict) -> list[str]:
    """Prompt for semantic analysis adapted to creator profile."""
    profile_data = get_creator_profile_data(user)
    colors_formatted = format_colors_for_prompt(profile_data.get('color_palette', []))

    return [
        """
              Você é um Diretor de Arte Sênior de Inteligência Artificial. Sua tarefa é fundir uma análise semântica de conteúdo com um perfil de marca específico, garantindo que o resultado seja uma diretriz visual coesa, priorizando **integralmente** a paleta de cores e a personalidade da marca, mesmo que os temas originais sejam de naturezas diferentes (ex: Café com marca Futurista).
            """,
        f"""
              ### DADOS DE ENTRADA ####

              1. PERSONALIDADE DA MARCA (Emoções)
              {profile_data['brand_personality']}

              2. ANÁLISE SEMÂNTICA (Conteúdo e Mensagem)
              {semantic_analysis}

              3. PERFIL DA MARCA (Identidade)

              - Cores da Marca (use estes nomes descritivos, não códigos hex):
{colors_formatted}
                Podem ser usadas variações mais escuras, mais claras e gradientes baseadas nestas cores.

              - Nicho: {profile_data.get('specialization', '')}
              - Tom de voz: {profile_data.get('voice_tone', '')}


              ### INSTRUÇÕES PARA ADAPTAÇÃO
              1. **Prioridade Absoluta:**
                O resultado final deve priorizar as **Cores da Marca** e a **Personalidade da Marca**.

              2. **Mapeamento Visual:**
                Adapte os `objetos_relevantes` e o `contexto_visual_sugerido` da análise semântica
                para serem coerentes com o nicho e personalidade da marca.

              3. **Mapeamento de Emoções:**
                Use a `Personalidade da Marca` para refinar a `ação_sugerida` e as `emoções_associadas`.
                Exemplo: uma marca *educadora* deve ter personagens em postura de clareza e acolhimento.

              4. **Paleta de Cores:**
                Substitua os `tons_de_cor_sugeridos` originais pelas **Cores da Marca** (nomes descritivos acima).
                Utilize as cores da marca para destaques, iluminação e elementos de fundo.
                NUNCA use códigos hex (#FFFFFF) — use apenas nomes descritivos de cor.

              5. **Geração:**
                Gere o novo JSON final com a estrutura abaixo,
                refletindo as adaptações e a priorização do `Perfil da Marca`.



              ### SAÍDA REQUERIDA (APENAS RETORNE O NOVO JSON ADAPTADO, NADA MAIS)
              {{
                "analise_semantica": {{
                    "tema_principal": "[Tema principal adaptado ao contexto da marca]",
                    "subtemas": [],
                    "titulo_imagem": "[Título curto para renderizar NA imagem, max 4 palavras, PT-BR, SEM acentos (ã, ç, é, ô, ü). Ex: 'Vendas Digital' ao invés de 'Ação Digital'. Deve ser impactante e relacionado ao tema.]",
                    "conceitos_visuais": ["[Conceitos reinterpretados para o nicho da marca]"],
                    "objetos_relevantes": ["[Objetos descritos de forma coerente com a marca]"],
                    "contexto_visual_sugerido": "[Cenário com a estética e paleta da marca]",
                    "emoções_associadas": ["[Emoções alinhadas à personalidade da marca]"],
                    "tons_de_cor_sugeridos": ["[Cores da marca em nomes descritivos e seus usos]"],
                    "ação_sugerida": "[Ação que reflete a personalidade da marca]",
                    "sensação_geral": "[Sensação geral de acordo com a estética da marca]",
                    "palavras_chave": ["[Keywords que fundem tema e marca]"]
                }}
              }}
            """
    ]


def image_generation_prompt(user, semantic_analysis: dict, generated_style=None) -> list[str]:
    """Prompt for AI image generation based on semantic analysis and generated style."""
    profile_data = get_creator_profile_data(user)

    logo_section = build_logo_section(
        business_name=profile_data.get('business_name', ''),
        color_palette=profile_data.get('color_palette', [])
    )
    colors_formatted = format_colors_for_prompt(profile_data.get('color_palette', []))

    if generated_style and hasattr(generated_style, 'style_data'):
        style = dict(generated_style.style_data or {})
    else:
        style = _fallback_style(semantic_analysis, profile_data)

    _typo_keywords = ('typography', 'typographic', 'type-first', 'text-heavy', 'lettering')
    _aesthetic = (style.get('aesthetic', '') or '').lower()
    _composition = (style.get('composition', '') or '').lower()
    if any(kw in _aesthetic or kw in _composition for kw in _typo_keywords):
        style['composition'] = (
            'Title in the upper third using oversized bold font for visual impact. '
            'The remaining 60-70% of the canvas MUST be filled with visual elements '
            '(illustrations, photos, icons, textures) — NOT more text. '
            'Logo bottom-right 8%.'
        )
        aesthetic = style.get('aesthetic', '')
        for phrase in ['typographic poster', 'typography-first', 'type-first',
                       'Oversized bold', 'headline-driven']:
            aesthetic = aesthetic.replace(phrase, 'bold visual')
        style['aesthetic'] = aesthetic

    _raw_title = semantic_analysis.get('titulo_imagem', semantic_analysis.get('tema_principal', ''))
    _title_words = (_raw_title or '').split()
    if len(_title_words) > 10:
        _stop_words = {'e', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos',
                       'nas', 'para', 'com', 'por', 'um', 'uma', 'o', 'a', 'os', 'as',
                       'que', 'ao', 'aos', 'ou', 'se', 'seu', 'sua', 'desde', 'entre',
                       'sobre', 'como', 'mais', 'sem', 'até', 'nem', 'já', 'mas',
                       'pela', 'pelo', 'pelas', 'pelos', 'num', 'numa'}
        cut = 10
        while cut > 5 and _title_words[cut - 1].lower().rstrip('.,;:') in _stop_words:
            cut -= 1
        title_text = ' '.join(_title_words[:cut]) + '.'
    else:
        title_text = ' '.join(_title_words)

    style_colors = style.get('colors', {})
    references = style.get('references', [])
    references_text = ', '.join(references) if references else 'professional social media design'

    return [
        f"""Professional Instagram feed post (4:5 vertical format, 1080x1350px)
for a {profile_data.get('specialization', 'business')} business.

STYLE:
{style.get('aesthetic', 'Clean professional design')}.
{style.get('lighting', 'Soft natural daylight, diffused and even')}.
Aesthetic references: {references_text}.

SUBJECT AND CONTEXT:
Main visual: {semantic_analysis.get('contexto_visual_sugerido', '')}.
Key elements: {', '.join(semantic_analysis.get('objetos_relevantes', []))}.
Theme: {semantic_analysis.get('tema_principal', '')}.
Mood: {style.get('mood', semantic_analysis.get('sensação_geral', 'professional'))}.

COLORS:
- Background: {style_colors.get('background', 'warm ivory')}
- Primary elements: {style_colors.get('primary', 'deep cobalt blue')}
- Accent details: {style_colors.get('accent', 'vivid coral')}
- Text color: {style_colors.get('text', 'dark charcoal')}
- Brand palette (prefer these):
{colors_formatted}

COMPOSITION:
{style.get('composition', 'Title upper third centered, main visual centered, logo bottom-right 8%')}.
Typography: {style.get('typography', 'modern bold sans-serif')}.
Safe margin of 10% on all edges — no important elements near borders.
Title text: "{title_text}" — render this exact text, centered in the upper third, in bold {style.get('typography', 'sans-serif')} font, {style_colors.get('text', 'dark charcoal')} color. This title has at most 10 words — do NOT add more words.
All rendered text must be in Brazilian Portuguese (PT-BR). Do NOT add accented characters (ã, ç, é, ô, ü) unless they appear in the title above.
CRITICAL: This image must be PRIMARILY VISUAL, not textual. Maximum 10 words of rendered text total (the title + logo only). Do NOT generate any other text — no paragraphs, no captions, no labels, no descriptions, no quotes, no words on screens or dashboards, no scattered typography. If the composition needs filler, use abstract shapes, icons, or blurred content instead. ANY text beyond the title risks being misspelled and ruins the image.
IMPORTANT: Even if the style description mentions "typography-heavy", "bold typography", or "typographic" approaches, you MUST still limit rendered text to the title only (max 10 words). Express the typographic energy through font weight, size, and placement of the TITLE — never by adding more text. Typography-heavy means a BOLD title, not more words.

{logo_section}

QUALITY:
Professional social media quality, optimized for mobile viewing.
Sharp focus on text, smooth gradients, clean edges, no artifacts.

AVOID:
- Watermarks, stock photo badges
- Distorted or misspelled text
- Colors outside the specified palette
- Cluttered background, too many competing elements
- Hashtags or hex codes rendered in the image
- Text in any language other than Brazilian Portuguese
- If no logo is attached, do NOT generate or add any logo
- Do NOT add decorative text on screens, dashboards, charts, or UI elements unless explicitly requested. If the image shows a laptop/phone screen, keep it blurred or show abstract shapes instead of readable text. Any visible text risks being misspelled.
- Do NOT add generic icons (rockets, lightbulbs, gears, targets) unless the content specifically mentions them. Prefer concrete imagery related to the actual topic.
"""
    ]


def _fallback_style(semantic_analysis: dict, profile_data: dict = None) -> dict:
    """Estilo fallback quando GeneratedVisualStyle não está disponível."""
    return {
        "aesthetic": "Clean professional design suitable for social media",
        "colors": {
            "background": "warm ivory",
            "primary": "deep cobalt blue",
            "accent": "vivid coral",
            "text": "dark charcoal",
        },
        "lighting": "Soft natural daylight, diffused and even",
        "typography": "modern bold sans-serif",
        "composition": "Title upper third centered, main visual centered 40% of frame, logo bottom-right 8%",
        "mood": semantic_analysis.get('sensação_geral', 'professional'),
        "references": ["editorial magazine layout"],
    }
