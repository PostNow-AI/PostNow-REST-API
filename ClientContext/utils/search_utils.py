"""
Utility functions for search and source enrichment.
Extracted from context_enrichment_service.py to keep files under 400 lines.
"""
import logging
from typing import Any, Dict, List, Set

from asgiref.sync import sync_to_async

from ClientContext.utils.source_quality import is_denied, score_source
from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.url_validation import validate_url_permissive_async

logger = logging.getLogger(__name__)

# Number of additional sources to fetch per opportunity (after filtering)
ENRICHMENT_SOURCES_PER_OPPORTUNITY = 3
# Fetch more from Google to have margin after filtering
GOOGLE_SEARCH_RESULTS = 6


def build_search_query(opportunity: Dict[str, Any]) -> str:
    """
    Build a search query for the opportunity.

    Args:
        opportunity: Opportunity dict with titulo_ideia and tipo

    Returns:
        Search query string
    """
    titulo = opportunity.get('titulo_ideia', '')
    tipo = opportunity.get('tipo', '')

    # Clean up tipo (remove emojis)
    emojis_to_remove = ['🔥', '🧠', '📰', '😂', '💼', '🔮', '⚡']
    for emoji in emojis_to_remove:
        tipo = tipo.replace(emoji, '').strip()

    # Build a focused search query
    query_parts = [titulo]
    if tipo and tipo.lower() not in titulo.lower():
        query_parts.append(tipo)

    return ' '.join(query_parts)


async def fetch_and_filter_sources(
    google_search_service,
    query: str,
    section: str,
    used_url_keys: Set[str]
) -> List[Dict[str, str]]:
    """
    Fetch additional sources from Google Search with quality filtering.

    Uses source_quality.py for denylist/allowlist filtering and scoring.
    Uses url_validation.py for URL validation.
    Uses url_dedupe.py for deduplication.

    Args:
        google_search_service: GoogleSearchService instance
        query: Search query
        section: Section name for source quality scoring
        used_url_keys: Set of already used URL keys for deduplication

    Returns:
        List of validated, filtered source dicts with 'url', 'title', 'snippet'
    """
    try:
        # Verificar se o serviço está configurado
        if not google_search_service.is_configured():
            logger.warning("[ENRICHMENT] Google CSE not configured, skipping source enrichment")
            return []

        # Fetch more results than needed to have margin after filtering
        results = await sync_to_async(google_search_service.search)(
            query=query,
            num_results=GOOGLE_SEARCH_RESULTS
        )

        if not results:
            return []

        # Score and filter sources
        scored_sources = _score_and_filter_sources(results, section, used_url_keys)

        # Sort by score (highest first)
        scored_sources.sort(key=lambda x: x['score'], reverse=True)

        # Validate and collect top sources
        validated_sources = await _validate_sources(scored_sources, used_url_keys)

        # Log sem expor dados sensíveis do usuário
        logger.info(
            f"[ENRICHMENT] Search completed -> "
            f"{len(results)} raw, {len(scored_sources)} scored, "
            f"{len(validated_sources)} validated"
        )

        return validated_sources

    except Exception as e:
        logger.warning(f"Error fetching additional sources for '{query}': {str(e)}")
        return []


def _score_and_filter_sources(
    results: List[Dict[str, Any]],
    section: str,
    used_url_keys: Set[str]
) -> List[Dict[str, Any]]:
    """
    Score and filter sources based on quality criteria.

    Args:
        results: Raw search results
        section: Section name for scoring
        used_url_keys: Set of already used URL keys

    Returns:
        List of scored source dicts
    """
    scored_sources = []

    for result in results:
        url = result.get('url', '')
        if not url:
            continue

        # Skip denied sources
        if is_denied(url):
            logger.debug(f"[ENRICHMENT] Denied URL: {url}")
            continue

        # Check for duplicates
        url_key = normalize_url_key(url)
        if url_key and url_key in used_url_keys:
            logger.debug(f"[ENRICHMENT] Duplicate URL skipped: {url}")
            continue

        # Score the source
        source_score = score_source(section, url)

        scored_sources.append({
            'url': url,
            'title': result.get('title', ''),
            'snippet': result.get('snippet', ''),
            'score': source_score,
            'url_key': url_key
        })

    return scored_sources


async def _validate_sources(
    scored_sources: List[Dict[str, Any]],
    used_url_keys: Set[str]
) -> List[Dict[str, str]]:
    """
    Validate sources and return the top valid ones.

    Args:
        scored_sources: List of scored source dicts
        used_url_keys: Set of already used URL keys

    Returns:
        List of validated source dicts
    """
    validated_sources = []

    for source in scored_sources:
        if len(validated_sources) >= ENRICHMENT_SOURCES_PER_OPPORTUNITY:
            break

        url = source['url']

        # Validate URL (check for 404, soft-404)
        is_valid = await validate_url_permissive_async(url)
        if not is_valid:
            logger.debug(f"[ENRICHMENT] Invalid URL (404/soft-404): {url}")
            continue

        # Mark URL as used
        if source['url_key']:
            used_url_keys.add(source['url_key'])

        validated_sources.append({
            'url': url,
            'title': source['title'],
            'snippet': source['snippet']
        })

    return validated_sources
