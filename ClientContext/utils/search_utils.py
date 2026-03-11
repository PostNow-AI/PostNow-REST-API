"""
Utility functions for search and source enrichment.
Extracted from context_enrichment_service.py to keep files under 400 lines.

Search providers:
- Serper API (primary): Real Google results via commercial API
- Jina Reader: Extracts clean content from URLs (free tier: 1M tokens/month)
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from asgiref.sync import sync_to_async

from ClientContext.utils.source_quality import is_denied, score_source
from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.url_validation import validate_url_permissive_async
from services.jina_reader_service import JinaReaderService

logger = logging.getLogger(__name__)

# Search configuration
ENRICHMENT_SOURCES_PER_OPPORTUNITY = 3
MIN_SOURCES_REQUIRED = 3
SEARCH_RESULTS_TO_FETCH = 10

# Jina Reader instance (lazy initialized)
_jina_reader: Optional[JinaReaderService] = None

# Keywords by content type
TYPE_KEYWORDS = {
    'polemica': ['polêmica', 'debate', 'crítica', 'problema', 'controvérsia'],
    'educativo': ['como', 'guia', 'tutorial', 'passo a passo', 'dicas'],
    'newsjacking': ['novo', 'anuncia', 'lança', 'atualização', '2026'],
    'entretenimento': ['viral', 'meme', 'engraçado', 'trend', 'bomba'],
    'estudo_caso': ['case', 'sucesso', 'resultados', 'faturou', 'cresceu'],
    'futuro': ['tendência', 'futuro', 'previsão', 'vai mudar', '2026'],
}

TYPE_DISPLAY_TO_KEY = {
    'polêmica': 'polemica', 'polêmicas': 'polemica',
    'educativo': 'educativo', 'educativos': 'educativo',
    'newsjacking': 'newsjacking', 'entretenimento': 'entretenimento',
    'estudo de caso': 'estudo_caso', 'estudos de caso': 'estudo_caso',
    'futuro': 'futuro',
}

# Words to remove from queries (don't add search value)
QUERY_REMOVE_WORDS = {
    'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
    'no', 'na', 'nos', 'nas', 'em', 'por', 'para', 'com', 'sobre',
    'que', 'você', 'te', 'seu', 'sua', 'isso', 'este', 'esta', 'esse', 'essa',
    'ele', 'ela', 'eles', 'elas', 'eu', 'meu', 'minha',
    'segredo', 'verdade', 'ninguém', 'nunca', 'sempre', 'tudo', 'nada',
    'incrível', 'chocante', 'surpreendente', 'definitivo', 'absoluto',
    'realmente', 'verdadeiro', 'completo', 'único', 'novo', 'nova',
    'está', 'são', 'ser', 'ter', 'fazer', 'fazendo', 'sendo', 'tendo',
    'conta', 'fala', 'diz', 'muda', 'errado', 'certo', 'precisa',
    'porque', 'quando', 'onde', 'qual', 'quais',
}


def get_jina_reader() -> JinaReaderService:
    """Get or create Jina Reader service instance."""
    global _jina_reader
    if _jina_reader is None:
        _jina_reader = JinaReaderService()
    return _jina_reader


def build_search_query(
    opportunity: Dict[str, Any],
    category_key: str = '',
    for_news: bool = False
) -> str:
    """Build a search query optimized by content type."""
    titulo = opportunity.get('titulo_ideia', '')
    tipo = opportunity.get('tipo', '')

    # Clean emojis
    for emoji in ['🔥', '🧠', '📰', '😂', '💼', '🔮', '⚡']:
        tipo = tipo.replace(emoji, '').strip()

    if not category_key and tipo:
        category_key = TYPE_DISPLAY_TO_KEY.get(tipo.lower(), '')

    # News search uses simple query
    if for_news:
        return titulo

    query_parts = [titulo]
    if category_key in TYPE_KEYWORDS:
        query_parts.extend(TYPE_KEYWORDS[category_key][:2])

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
    Fetch sources with quality filtering and multi-strategy fallback.

    Uses 4 strategies to ensure minimum sources:
    1. Primary search (news for newsjacking)
    2. Alternate type (web ↔ news)
    3. Simplified query
    4. AI query reformulation
    """
    try:
        if not search_service.is_configured():
            logger.warning("[ENRICHMENT] Search service not configured")
            return []

        use_news = category_key == 'newsjacking'
        diagnosis = {'original_query': query, 'category': category_key, 'attempts': []}

        # Try all strategies until we have enough sources
        sources = await _try_all_strategies(
            search_service, query, section, used_url_keys,
            use_news, news_query, diagnosis
        )

        # Log failure if below minimum
        if len(sources) < MIN_SOURCES_REQUIRED:
            _log_search_failure(diagnosis, len(sources))

        # Optionally fetch full content
        if read_content and sources:
            sources = await _enrich_with_content(sources)

        logger.info(f"[ENRICHMENT] Final: {len(sources)} validated sources")
        return sources

    except Exception as e:
        logger.warning(f"Error fetching sources for '{query}': {e}")
        return []


async def _try_all_strategies(
    search_service, query: str, section: str, used_url_keys: Set[str],
    use_news: bool, news_query: str, diagnosis: dict
) -> List[Dict[str, str]]:
    """Try multiple search strategies until minimum sources found."""
    sources = []

    # Strategy 1: Primary search
    new_sources, diag = await _fetch_with_diagnosis(
        search_service, query, section, used_url_keys, use_news, news_query, "primary"
    )
    diagnosis['attempts'].append(diag)
    sources.extend(new_sources)

    # Strategy 2: Alternate type
    if len(sources) < MIN_SOURCES_REQUIRED:
        new_sources, diag = await _fetch_with_diagnosis(
            search_service, query, section, used_url_keys, not use_news, news_query, "alternate"
        )
        diagnosis['attempts'].append(diag)
        sources.extend(new_sources)

    # Strategy 3: Simplified query
    if len(sources) < MIN_SOURCES_REQUIRED and news_query and news_query != query:
        new_sources, diag = await _fetch_with_diagnosis(
            search_service, news_query, section, used_url_keys, False, news_query, "simplified"
        )
        diagnosis['attempts'].append(diag)
        sources.extend(new_sources)

    # Strategy 4: AI reformulation
    if len(sources) < MIN_SOURCES_REQUIRED:
        alt_queries = await _generate_alternative_queries(news_query or query)
        for alt_q in alt_queries:
            if len(sources) >= MIN_SOURCES_REQUIRED:
                break
            new_sources, diag = await _fetch_with_diagnosis(
                search_service, alt_q, section, used_url_keys, False, alt_q, f"ai:{alt_q[:20]}"
            )
            diagnosis['attempts'].append(diag)
            sources.extend(new_sources)

    return sources[:ENRICHMENT_SOURCES_PER_OPPORTUNITY]


async def _fetch_with_diagnosis(
    search_service, query: str, section: str, used_url_keys: Set[str],
    use_news: bool, news_query: str, attempt_name: str
) -> Tuple[List[Dict[str, str]], dict]:
    """Fetch sources with detailed diagnosis."""
    diagnosis = {
        'attempt': attempt_name,
        'query': news_query if use_news and news_query else query,
        'search_type': 'news' if use_news else 'regular',
        'raw_count': 0, 'blocked_count': 0, 'blocked_domains': [],
        'scored_count': 0, 'validated_count': 0,
    }

    try:
        results = await _execute_search(search_service, query, news_query, use_news)
        diagnosis['raw_count'] = len(results) if results else 0

        if not results:
            return [], diagnosis

        scored = _score_results_with_tracking(results, section, used_url_keys, diagnosis)
        diagnosis['scored_count'] = len(scored)

        validated = await _validate_sources(scored, used_url_keys)
        diagnosis['validated_count'] = len(validated)

        return validated, diagnosis

    except Exception as e:
        diagnosis['error'] = str(e)
        return [], diagnosis


async def _execute_search(search_service, query: str, news_query: str, use_news: bool) -> list:
    """Execute the appropriate search type."""
    if use_news and hasattr(search_service, 'search_news'):
        return await sync_to_async(search_service.search_news)(
            query=news_query or query, num_results=SEARCH_RESULTS_TO_FETCH
        )
    return await sync_to_async(search_service.search)(
        query=query, num_results=SEARCH_RESULTS_TO_FETCH
    )


def _score_results_with_tracking(
    results: list, section: str, used_url_keys: Set[str], diagnosis: dict
) -> List[Dict[str, Any]]:
    """Score results and track blocked domains for diagnosis."""
    scored = []
    for result in results:
        url = result.get('url', '')
        if not url:
            continue

        if is_denied(url):
            diagnosis['blocked_count'] += 1
            domain = urlparse(url).netloc.replace('www.', '')
            if domain not in diagnosis['blocked_domains']:
                diagnosis['blocked_domains'].append(domain)
            continue

        url_key = normalize_url_key(url)
        if url_key and url_key in used_url_keys:
            continue

        scored.append({
            'url': url,
            'title': result.get('title', ''),
            'snippet': result.get('snippet', ''),
            'score': score_source(section, url),
            'url_key': url_key
        })

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored


async def _validate_sources(
    scored_sources: List[Dict[str, Any]], used_url_keys: Set[str]
) -> List[Dict[str, str]]:
    """Validate URLs and return top valid sources."""
    validated = []
    for source in scored_sources:
        if len(validated) >= ENRICHMENT_SOURCES_PER_OPPORTUNITY:
            break

        if not await validate_url_permissive_async(source['url']):
            continue

        if source['url_key']:
            used_url_keys.add(source['url_key'])

        validated.append({
            'url': source['url'],
            'title': source['title'],
            'snippet': source['snippet']
        })

    return validated


async def _generate_alternative_queries(original_query: str) -> List[str]:
    """Generate alternative queries using AI or rules."""
    try:
        import os
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if api_key:
            return await _generate_ai_queries(original_query, api_key)
    except Exception as e:
        logger.debug(f"[ENRICHMENT] AI query generation failed: {e}")

    return _generate_rule_based_queries(original_query)


async def _generate_ai_queries(query: str, api_key: str) -> List[str]:
    """Generate queries using Claude."""
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model='claude-3-5-haiku-20241022',
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Gere 3 queries de busca alternativas para:
"{query}"

Regras: queries curtas (3-5 palavras), termos comuns, foque no tema central.
Responda APENAS com as 3 queries, uma por linha."""
        }]
    )

    queries = [q.strip() for q in response.content[0].text.strip().split('\n') if q.strip()]
    if queries:
        logger.info(f"[ENRICHMENT] AI generated {len(queries[:3])} queries")
    return queries[:3]


def _generate_rule_based_queries(original_query: str) -> List[str]:
    """Generate queries using simple rules."""
    words = original_query.split()
    topic_words = [w for w in words if w.lower() not in QUERY_REMOVE_WORDS and len(w) > 2]

    if len(topic_words) >= 2:
        return _build_multi_word_queries(topic_words)
    elif len(topic_words) == 1:
        return _build_single_word_queries(topic_words[0])
    else:
        simple = ' '.join([w for w in words if len(w) > 3][:4])
        return [simple, f"{simple} dicas"] if simple else []


def _build_multi_word_queries(words: List[str]) -> List[str]:
    """Build queries from multiple topic words."""
    topic = ' '.join(words[:4])
    queries = [topic]

    if words[0].lower() != 'como':
        queries.append(f"como {' '.join(words[:3])}")
    else:
        queries.append(f"{' '.join(words[:3])} guia")

    queries.append(f"{' '.join(words[:3])} tendências 2026")
    return _dedupe_queries(queries)


def _build_single_word_queries(word: str) -> List[str]:
    """Build queries from single topic word."""
    return [
        f"{word} guia completo",
        f"{word} dicas 2026",
        f"estratégias {word}"
    ]


def _dedupe_queries(queries: List[str]) -> List[str]:
    """Remove duplicate queries."""
    seen = set()
    unique = []
    for q in queries:
        q = q.strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            unique.append(q)
    return unique[:3]


def _log_search_failure(diagnosis: dict, final_count: int) -> None:
    """Log detailed failure diagnosis."""
    logger.warning(
        f"[ENRICHMENT FAILURE] Got {final_count}/{MIN_SOURCES_REQUIRED} sources "
        f"for: {diagnosis.get('original_query', 'N/A')}"
    )

    for attempt in diagnosis.get('attempts', []):
        blocked = ""
        if attempt.get('blocked_count', 0) > 0:
            domains = ', '.join(attempt.get('blocked_domains', [])[:3])
            blocked = f", blocked: {attempt['blocked_count']} ({domains})"

        logger.warning(
            f"[ENRICHMENT FAILURE] {attempt.get('attempt')}: "
            f"raw={attempt.get('raw_count', 0)}, validated={attempt.get('validated_count', 0)}{blocked}"
        )


async def _enrich_with_content(sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Add full page content via Jina Reader, falling back to Serper snippet."""
    jina = get_jina_reader()
    for source in sources:
        try:
            content = await sync_to_async(jina.read_url)(source['url'])
            # Fall back to Serper snippet so the AI always has some context
            source['content'] = content or source.get('snippet', '')
        except Exception as e:
            logger.debug(f"[ENRICHMENT] Content read failed: {e}")
            source['content'] = source.get('snippet', '')
    return sources


async def fetch_url_content(url: str) -> Optional[str]:
    """Fetch content from a single URL."""
    jina = get_jina_reader()
    try:
        return await sync_to_async(jina.read_url)(url)
    except Exception as e:
        logger.warning(f"[ENRICHMENT] Content fetch failed: {e}")
        return None
