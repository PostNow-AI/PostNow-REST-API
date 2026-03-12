"""Utility functions for extracting and transforming context data."""

from typing import Dict, Any, List, Tuple


def extract_from_opportunities(section_data: Dict[str, Any]) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Extrai textos legíveis do formato fontes_analisadas/oportunidades.

    Args:
        section_data: Dictionary containing 'fontes_analisadas' key

    Returns:
        Tuple of (fontes_analisadas, all_opportunities, all_titles)
    """
    fontes_analisadas = section_data.get('fontes_analisadas', [])
    all_opps = []
    all_titles = []

    for fonte in fontes_analisadas:
        all_titles.append(fonte.get('titulo_original', ''))
        for opp in fonte.get('oportunidades', []):
            all_opps.append(opp)

    return fontes_analisadas, all_opps, all_titles


def normalize_section_structure(context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Garantir que todas as seções críticas sejam dicionários.

    Args:
        context_data: Raw context data from AI

    Returns:
        Normalized context data with all sections as dictionaries
    """
    sections = ['mercado', 'concorrencia', 'publico', 'tendencias', 'sazonalidade', 'marca']

    for section in sections:
        if section in context_data:
            if isinstance(context_data[section], list):
                # Se for lista, tenta pegar o primeiro item se for dict
                if context_data[section] and isinstance(context_data[section][0], dict):
                    context_data[section] = context_data[section][0]
                else:
                    # Se for lista de strings ou vazia, transforma em dict vazio
                    context_data[section] = {}
            elif not isinstance(context_data[section], dict):
                context_data[section] = {}

    return context_data


def generate_hashtags_from_opportunities(opportunities: List[Dict], max_hashtags: int = 15) -> List[str]:
    """
    Gerar hashtags a partir dos títulos das oportunidades.

    Args:
        opportunities: List of opportunity dictionaries
        max_hashtags: Maximum number of hashtags to return

    Returns:
        Sorted list of hashtag strings
    """
    hashtags = set()

    for opp in opportunities:
        titulo = opp.get('titulo_ideia', '')
        # Extrair palavras significativas dos títulos para hashtags
        for word in titulo.split():
            clean = word.strip('?!.,;:()[]{}"\'-').capitalize()
            if len(clean) > 3 and clean.isalpha():
                hashtags.add(f"#{clean}")

        # Usar tipo como hashtag também
        tipo = opp.get('tipo', '')
        if tipo:
            hashtags.add(f"#{tipo.replace(' ', '')}")

    return sorted(list(hashtags))[:max_hashtags]


def generate_keywords_from_opportunities(opportunities: List[Dict], max_keywords: int = 10) -> List[str]:
    """
    Gerar keywords a partir dos títulos e gatilhos criativos.

    Args:
        opportunities: List of opportunity dictionaries
        max_keywords: Maximum number of keywords to return

    Returns:
        List of keyword strings
    """
    keywords = set()

    for opp in opportunities:
        titulo = opp.get('titulo_ideia', '')
        gatilho = opp.get('gatilho_criativo', '')

        if titulo:
            keywords.add(titulo)
        if gatilho:
            keywords.add(gatilho)

    return list(keywords)[:max_keywords]
