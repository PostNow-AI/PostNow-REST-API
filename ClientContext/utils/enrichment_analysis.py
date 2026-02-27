"""
Utility functions for generating enriched analysis with AI.
Extracted from context_enrichment_service.py to keep files under 400 lines.
"""
import logging
from typing import Any, Dict, List

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


async def generate_enriched_analysis(
    ai_service,
    opportunity: Dict[str, Any],
    sources: List[Dict[str, str]],
    user: User
) -> str:
    """
    Generate enriched analysis using Gemini.

    Args:
        ai_service: AiService instance
        opportunity: Original opportunity data
        sources: Additional sources fetched
        user: User instance

    Returns:
        Enriched analysis text
    """
    try:
        titulo = opportunity.get('titulo_ideia', '')
        descricao = opportunity.get('descricao', '')
        tipo = opportunity.get('tipo', '')

        # Build sources context
        sources_text = _format_sources_for_prompt(sources)

        prompt = _build_analysis_prompt(titulo, tipo, descricao, sources_text)

        analysis = await sync_to_async(ai_service.generate_text)(
            [prompt], user
        )

        return analysis.strip()

    except Exception as e:
        logger.warning(f"Error generating enriched analysis: {str(e)}")
        return ''


def _format_sources_for_prompt(sources: List[Dict[str, str]]) -> str:
    """
    Format sources list for inclusion in AI prompt.

    Args:
        sources: List of source dicts with title and snippet

    Returns:
        Formatted string with numbered sources
    """
    sources_text = ""
    for i, source in enumerate(sources, 1):
        sources_text += f"\n{i}. {source.get('title', 'Sem titulo')}\n"
        sources_text += f"   {source.get('snippet', '')}\n"
    return sources_text


def _build_analysis_prompt(
    titulo: str,
    tipo: str,
    descricao: str,
    sources_text: str
) -> str:
    """
    Build the prompt for AI analysis generation.

    Args:
        titulo: Opportunity title
        tipo: Opportunity type
        descricao: Opportunity description
        sources_text: Formatted sources text

    Returns:
        Complete prompt string
    """
    return f"""Analise a seguinte oportunidade de conteudo e forneca uma analise mais profunda:

OPORTUNIDADE:
- Titulo: {titulo}
- Tipo: {tipo}
- Descricao: {descricao}

FONTES ADICIONAIS ENCONTRADAS:
{sources_text}

Com base nas fontes adicionais, forneca:
1. Contexto expandido sobre o tema (2-3 frases)
2. Angulos de abordagem recomendados (2-3 sugestoes)
3. Pontos de atencao ou controversias relevantes

Responda de forma concisa e objetiva, em portugues brasileiro.
Maximo de 200 palavras no total."""
