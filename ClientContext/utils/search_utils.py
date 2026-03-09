"""
Utility functions for search and source enrichment.
Extracted from context_enrichment_service.py to keep files under 400 lines.

Search providers:
- Serper API (primary): Real Google results via commercial API
- Jina Reader: Extracts clean content from URLs (free tier: 1M tokens/month)
"""
import logging
from typing import Any, Dict, List, Optional, Set

from asgiref.sync import sync_to_async

from ClientContext.utils.source_quality import is_denied, score_source
from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.url_validation import validate_url_permissive_async
from services.jina_reader_service import JinaReaderService

logger = logging.getLogger(__name__)

# Number of additional sources to fetch per opportunity (after filtering)
ENRICHMENT_SOURCES_PER_OPPORTUNITY = 3
# Minimum sources required (will retry with news search if below)
MIN_SOURCES_REQUIRED = 3
# Fetch more results to have margin after filtering (increased from 6)
SEARCH_RESULTS_TO_FETCH = 10

# Jina Reader instance (lazy initialized)
_jina_reader: Optional[JinaReaderService] = None


def get_jina_reader() -> JinaReaderService:
    """Get or create Jina Reader service instance."""
    global _jina_reader
    if _jina_reader is None:
        _jina_reader = JinaReaderService()
    return _jina_reader


# Palavras-chave por tipo de conteúdo para melhorar a busca
TYPE_KEYWORDS = {
    'polemica': ['polêmica', 'debate', 'crítica', 'problema', 'controvérsia'],
    'educativo': ['como', 'guia', 'tutorial', 'passo a passo', 'dicas'],
    'newsjacking': ['novo', 'anuncia', 'lança', 'atualização', '2026'],
    'entretenimento': ['viral', 'meme', 'engraçado', 'trend', 'bomba'],
    'estudo_caso': ['case', 'sucesso', 'resultados', 'faturou', 'cresceu'],
    'futuro': ['tendência', 'futuro', 'previsão', 'vai mudar', '2026'],
}

# Mapeamento de tipo exibido para chave interna
TYPE_DISPLAY_TO_KEY = {
    'polêmica': 'polemica',
    'polêmicas': 'polemica',
    'educativo': 'educativo',
    'educativos': 'educativo',
    'newsjacking': 'newsjacking',
    'entretenimento': 'entretenimento',
    'estudo de caso': 'estudo_caso',
    'estudos de caso': 'estudo_caso',
    'futuro': 'futuro',
}


def build_search_query(
    opportunity: Dict[str, Any],
    category_key: str = '',
    for_news: bool = False
) -> str:
    """
    Build a search query for the opportunity, optimized by content type.

    Args:
        opportunity: Opportunity dict with titulo_ideia and tipo
        category_key: Category key (polemica, educativo, etc.)
        for_news: If True, returns simpler query for news search

    Returns:
        Search query string optimized for the content type
    """
    titulo = opportunity.get('titulo_ideia', '')
    tipo = opportunity.get('tipo', '')

    # Clean up tipo (remove emojis)
    emojis_to_remove = ['🔥', '🧠', '📰', '😂', '💼', '🔮', '⚡']
    for emoji in emojis_to_remove:
        tipo = tipo.replace(emoji, '').strip()

    # Determine category key
    if not category_key and tipo:
        category_key = TYPE_DISPLAY_TO_KEY.get(tipo.lower(), '')

    # For news search, use simpler query (just the title)
    # Extra keywords can make news search too specific
    if for_news:
        return titulo

    # Build base query
    query_parts = [titulo]

    # Add type-specific keywords to improve search relevance
    if category_key and category_key in TYPE_KEYWORDS:
        # Add 2 most relevant keywords for the type
        keywords = TYPE_KEYWORDS[category_key][:2]
        query_parts.extend(keywords)

    return ' '.join(query_parts)


async def fetch_and_filter_sources(
    search_service,
    query: str,
    section: str,
    used_url_keys: Set[str],
    read_content: bool = False,
    category_key: str = '',
    news_query: str = ''
) -> List[Dict[str, str]]:
    """
    Fetch additional sources from search with quality filtering.

    Uses source_quality.py for denylist/allowlist filtering and scoring.
    Uses url_validation.py for URL validation.
    Uses url_dedupe.py for deduplication.
    Optionally uses Jina Reader to extract page content.

    For 'newsjacking' category, uses Serper News API for better results.
    If less than MIN_SOURCES_REQUIRED are found, retries with multiple strategies.

    Args:
        search_service: SerperSearchService instance
        query: Search query (with keywords)
        section: Section name for source quality scoring
        used_url_keys: Set of already used URL keys for deduplication
        read_content: Whether to fetch full page content via Jina Reader
        category_key: Category key (polemica, educativo, newsjacking, etc.)
        news_query: Simplified query for news search (without extra keywords)

    Returns:
        List of validated, filtered source dicts with 'url', 'title', 'snippet'
        (and 'content' if read_content=True)
    """
    try:
        # Verificar se o serviço está configurado
        if not search_service.is_configured():
            logger.warning("[ENRICHMENT] Search service not configured, skipping source enrichment")
            return []

        # Para newsjacking, usar busca de notícias diretamente
        use_news_search = category_key == 'newsjacking'

        # Diagnóstico de busca
        search_diagnosis = {
            'original_query': query,
            'news_query': news_query,
            'category': category_key,
            'attempts': []
        }

        # Estratégia 1: Busca primária (news para newsjacking, regular para outros)
        validated_sources, diagnosis = await _fetch_with_diagnosis(
            search_service, query, section, used_url_keys, use_news_search,
            news_query=news_query, attempt_name="primary"
        )
        search_diagnosis['attempts'].append(diagnosis)

        # Estratégia 2: Se não conseguiu o mínimo, tentar busca oposta
        if len(validated_sources) < MIN_SOURCES_REQUIRED:
            logger.info(
                f"[ENRICHMENT] Strategy 1 got {len(validated_sources)} sources, "
                f"trying {'regular' if use_news_search else 'news'} search..."
            )
            additional_sources, diagnosis = await _fetch_with_diagnosis(
                search_service, query, section, used_url_keys, not use_news_search,
                news_query=news_query, attempt_name="alternate_type"
            )
            search_diagnosis['attempts'].append(diagnosis)
            validated_sources.extend(additional_sources)

        # Estratégia 3: Se ainda não tem o mínimo, tentar query simplificada
        if len(validated_sources) < MIN_SOURCES_REQUIRED and news_query and news_query != query:
            logger.info(
                f"[ENRICHMENT] Strategy 2 got {len(validated_sources)} sources, "
                f"trying simplified query..."
            )
            additional_sources, diagnosis = await _fetch_with_diagnosis(
                search_service, news_query, section, used_url_keys, False,
                news_query=news_query, attempt_name="simplified_query"
            )
            search_diagnosis['attempts'].append(diagnosis)
            validated_sources.extend(additional_sources)

        # Estratégia 4: Se ainda não tem o mínimo, usar IA para reformular query
        if len(validated_sources) < MIN_SOURCES_REQUIRED:
            logger.info(
                f"[ENRICHMENT] Strategy 3 got {len(validated_sources)} sources, "
                f"trying AI query reformulation..."
            )
            alternative_queries = await _generate_alternative_queries(news_query or query)

            for alt_query in alternative_queries:
                if len(validated_sources) >= MIN_SOURCES_REQUIRED:
                    break

                additional_sources, diagnosis = await _fetch_with_diagnosis(
                    search_service, alt_query, section, used_url_keys, False,
                    news_query=alt_query, attempt_name=f"ai_query:{alt_query[:30]}"
                )
                search_diagnosis['attempts'].append(diagnosis)
                validated_sources.extend(additional_sources)

        # Limitar ao máximo necessário
        validated_sources = validated_sources[:ENRICHMENT_SOURCES_PER_OPPORTUNITY]

        # Log diagnóstico se não conseguiu o mínimo
        if len(validated_sources) < MIN_SOURCES_REQUIRED:
            _log_search_failure(search_diagnosis, len(validated_sources))

        # Optionally fetch full content via Jina Reader
        if read_content and validated_sources:
            validated_sources = await _enrich_with_content(validated_sources)

        # Log sem expor dados sensíveis do usuário
        logger.info(
            f"[ENRICHMENT] Final result: {len(validated_sources)} validated sources"
        )

        return validated_sources

    except Exception as e:
        logger.warning(f"Error fetching additional sources for '{query}': {str(e)}")
        return []


async def _fetch_with_strategy(
    search_service,
    query: str,
    section: str,
    used_url_keys: Set[str],
    use_news: bool,
    news_query: str = ''
) -> List[Dict[str, str]]:
    """
    Fetch sources using either regular or news search.

    Args:
        search_service: SerperSearchService instance
        query: Search query (optimized with keywords)
        section: Section name for scoring
        used_url_keys: Set of already used URL keys
        use_news: Whether to use news search
        news_query: Simplified query for news search (without extra keywords)

    Returns:
        List of validated source dicts
    """
    try:
        if use_news and hasattr(search_service, 'search_news'):
            # Use simplified query for news (extra keywords make it too specific)
            search_query = news_query if news_query else query
            results = await sync_to_async(search_service.search_news)(
                query=search_query,
                num_results=SEARCH_RESULTS_TO_FETCH
            )
            search_type = "news"
        else:
            results = await sync_to_async(search_service.search)(
                query=query,
                num_results=SEARCH_RESULTS_TO_FETCH
            )
            search_type = "regular"

        if not results:
            logger.debug(f"[ENRICHMENT] No {search_type} results for query")
            return []

        # Score and filter sources
        scored_sources = _score_and_filter_sources(results, section, used_url_keys)

        # Sort by score (highest first)
        scored_sources.sort(key=lambda x: x['score'], reverse=True)

        # Validate and collect top sources
        validated_sources = await _validate_sources(scored_sources, used_url_keys)

        logger.info(
            f"[ENRICHMENT] {search_type.capitalize()} search -> "
            f"{len(results)} raw, {len(scored_sources)} scored, "
            f"{len(validated_sources)} validated"
        )

        return validated_sources

    except Exception as e:
        logger.warning(f"Error in {use_news and 'news' or 'regular'} search: {str(e)}")
        return []


async def _fetch_with_diagnosis(
    search_service,
    query: str,
    section: str,
    used_url_keys: Set[str],
    use_news: bool,
    news_query: str = '',
    attempt_name: str = ''
) -> tuple:
    """
    Fetch sources with detailed diagnosis for debugging.

    Returns:
        Tuple of (validated_sources, diagnosis_dict)
    """
    diagnosis = {
        'attempt': attempt_name,
        'query': news_query if use_news and news_query else query,
        'search_type': 'news' if use_news else 'regular',
        'raw_count': 0,
        'blocked_count': 0,
        'blocked_domains': [],
        'scored_count': 0,
        'validated_count': 0,
    }

    try:
        if use_news and hasattr(search_service, 'search_news'):
            search_query = news_query if news_query else query
            results = await sync_to_async(search_service.search_news)(
                query=search_query,
                num_results=SEARCH_RESULTS_TO_FETCH
            )
        else:
            results = await sync_to_async(search_service.search)(
                query=query,
                num_results=SEARCH_RESULTS_TO_FETCH
            )

        diagnosis['raw_count'] = len(results) if results else 0

        if not results:
            return [], diagnosis

        # Score and filter with detailed tracking
        scored_sources = []
        for result in results:
            url = result.get('url', '')
            if not url:
                continue

            if is_denied(url):
                diagnosis['blocked_count'] += 1
                # Extract domain for diagnosis
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace('www.', '')
                if domain not in diagnosis['blocked_domains']:
                    diagnosis['blocked_domains'].append(domain)
                continue

            url_key = normalize_url_key(url)
            if url_key and url_key in used_url_keys:
                continue

            source_score = score_source(section, url)
            scored_sources.append({
                'url': url,
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'score': source_score,
                'url_key': url_key
            })

        diagnosis['scored_count'] = len(scored_sources)
        scored_sources.sort(key=lambda x: x['score'], reverse=True)

        # Validate
        validated_sources = await _validate_sources(scored_sources, used_url_keys)
        diagnosis['validated_count'] = len(validated_sources)

        return validated_sources, diagnosis

    except Exception as e:
        diagnosis['error'] = str(e)
        return [], diagnosis


async def _generate_alternative_queries(original_query: str) -> List[str]:
    """
    Generate alternative search queries using AI or rules.

    When initial searches fail, this generates different phrasings
    that might find better results.

    Args:
        original_query: The original query that failed

    Returns:
        List of 2-3 alternative queries to try
    """
    # Try to use Anthropic API if available
    try:
        import os
        api_key = os.getenv('ANTHROPIC_API_KEY', '')

        if api_key:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            response = client.messages.create(
                model='claude-3-5-haiku-20241022',
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"""Gere 3 queries de busca alternativas para encontrar artigos sobre este tema:

"{original_query}"

Regras:
- Queries curtas (3-5 palavras)
- Use termos que as pessoas realmente buscam
- Varie os termos (sinônimos, ângulos diferentes)
- Foque no tema central, não em detalhes

Responda APENAS com as 3 queries, uma por linha, sem numeração."""
                }]
            )

            queries = response.content[0].text.strip().split('\n')
            queries = [q.strip() for q in queries if q.strip()][:3]

            if queries:
                logger.info(f"[ENRICHMENT] AI generated {len(queries)} alternative queries")
                return queries

    except Exception as e:
        logger.debug(f"[ENRICHMENT] AI query generation failed: {e}")

    # Fallback: rule-based alternatives
    return _generate_rule_based_queries(original_query)


def _generate_rule_based_queries(original_query: str) -> List[str]:
    """
    Generate alternative queries using simple rules when AI is not available.

    Focus on extracting the TOPIC (nouns) and removing fluff.
    """
    words = original_query.split()
    alternatives = []

    # Words to completely remove (don't add meaning to searches)
    remove_words = {
        # Articles and prepositions
        'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
        'no', 'na', 'nos', 'nas', 'em', 'por', 'para', 'com', 'sobre',
        # Pronouns
        'que', 'você', 'te', 'seu', 'sua', 'isso', 'este', 'esta', 'esse', 'essa',
        'ele', 'ela', 'eles', 'elas', 'eu', 'meu', 'minha',
        # Clickbait/fluff
        'segredo', 'verdade', 'ninguém', 'nunca', 'sempre', 'tudo', 'nada',
        'incrível', 'chocante', 'surpreendente', 'definitivo', 'absoluto',
        'realmente', 'verdadeiro', 'completo', 'único', 'novo', 'nova',
        # Verbs that don't help search
        'está', 'são', 'ser', 'ter', 'fazer', 'fazendo', 'sendo', 'tendo',
        'conta', 'fala', 'diz', 'muda', 'errado', 'certo', 'precisa',
        # Common question words (keep 'como' only when leading)
        'por', 'porque', 'quando', 'onde', 'qual', 'quais',
    }

    # Extract topic words (likely nouns and key terms)
    topic_words = [
        w for w in words
        if w.lower() not in remove_words and len(w) > 2
    ]

    # Check if original starts with "como" (how-to query)
    starts_with_como = words[0].lower() == 'como' if words else False

    # If we have good topic words, use them
    if len(topic_words) >= 2:
        topic = ' '.join(topic_words[:4])

        # Strategy 1: Just the topic
        alternatives.append(topic)

        # Strategy 2: "como" + topic (only if not already there)
        if not starts_with_como and topic_words[0].lower() != 'como':
            alternatives.append(f"como {' '.join(topic_words[:3])}")
        else:
            alternatives.append(f"{' '.join(topic_words[:3])} guia")

        # Strategy 3: Topic + "tendências 2026"
        alternatives.append(f"{' '.join(topic_words[:3])} tendências 2026")

    elif len(topic_words) == 1:
        # Only one good word - expand it
        word = topic_words[0]
        alternatives.append(f"{word} guia completo")
        alternatives.append(f"{word} dicas 2026")
        alternatives.append(f"estratégias {word}")

    else:
        # Couldn't extract anything useful - use original but simplified
        simple = ' '.join([w for w in words if len(w) > 3][:4])
        if simple:
            alternatives.append(simple)
            alternatives.append(f"{simple} dicas")

    # Remove duplicates and empty strings
    seen = set()
    unique = []
    for q in alternatives:
        q = q.strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            unique.append(q)

    return unique[:3]


def _log_search_failure(diagnosis: dict, final_count: int) -> None:
    """
    Log detailed diagnosis when search fails to find minimum sources.
    This helps identify patterns and fix query/filter issues.
    """
    logger.warning(
        f"[ENRICHMENT FAILURE] Could not find {MIN_SOURCES_REQUIRED} sources "
        f"(got {final_count}) for query: {diagnosis.get('original_query', 'N/A')}"
    )

    for attempt in diagnosis.get('attempts', []):
        blocked_info = ""
        if attempt.get('blocked_count', 0) > 0:
            blocked_info = f", blocked: {attempt['blocked_count']} ({', '.join(attempt.get('blocked_domains', [])[:3])})"

        logger.warning(
            f"[ENRICHMENT FAILURE] Attempt '{attempt.get('attempt', 'N/A')}': "
            f"raw={attempt.get('raw_count', 0)}, "
            f"scored={attempt.get('scored_count', 0)}, "
            f"validated={attempt.get('validated_count', 0)}"
            f"{blocked_info}"
        )

    # Log recommendation
    if all(a.get('raw_count', 0) == 0 for a in diagnosis.get('attempts', [])):
        logger.warning(
            f"[ENRICHMENT FAILURE] RECOMMENDATION: Query may be too specific or "
            f"in wrong language. Try broader terms."
        )
    elif sum(a.get('blocked_count', 0) for a in diagnosis.get('attempts', [])) > 10:
        logger.warning(
            f"[ENRICHMENT FAILURE] RECOMMENDATION: Too many results blocked. "
            f"Review blocked domains list."
        )


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


async def _enrich_with_content(
    sources: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Enrich sources with full page content via Jina Reader.

    Args:
        sources: List of validated source dicts

    Returns:
        Sources with 'content' field added (empty string if failed)
    """
    jina = get_jina_reader()

    for source in sources:
        try:
            content = await sync_to_async(jina.read_url)(source['url'])
            source['content'] = content or ''
        except Exception as e:
            logger.debug(f"[ENRICHMENT] Failed to read content from {source['url']}: {e}")
            source['content'] = ''

    return sources


async def fetch_url_content(url: str) -> Optional[str]:
    """
    Fetch content from a single URL via Jina Reader.

    Args:
        url: URL to read

    Returns:
        Clean markdown content or None if failed
    """
    jina = get_jina_reader()
    try:
        return await sync_to_async(jina.read_url)(url)
    except Exception as e:
        logger.warning(f"[ENRICHMENT] Failed to fetch content from {url}: {e}")
        return None
