"""
Service for enriching context data with additional sources and analysis.
Phase 2 of the two-phase enrichment system.
"""
import logging
from typing import Any, Dict, List, Optional, Set

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from ClientContext.models import ClientContext
from ClientContext.utils.source_quality import is_denied, score_source
from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.url_validation import validate_url_permissive_async
from services.google_search_service import GoogleSearchService
from services.ai_service import AiService
from services.semaphore_service import SemaphoreService

logger = logging.getLogger(__name__)

# Number of additional sources to fetch per opportunity (after filtering)
ENRICHMENT_SOURCES_PER_OPPORTUNITY = 3
# Fetch more from Google to have margin after filtering
GOOGLE_SEARCH_RESULTS = 6

# Map opportunity categories to source_quality sections
CATEGORY_TO_SECTION = {
    'polemica': 'tendencias',
    'educativo': 'tendencias',
    'newsjacking': 'mercado',
    'entretenimento': 'tendencias',
    'estudo_caso': 'concorrencia',
    'futuro': 'tendencias',
    'outros': 'mercado',
}


class ContextEnrichmentService:
    """Service for enriching context opportunities with additional data."""

    def __init__(
        self,
        google_search_service: Optional[GoogleSearchService] = None,
        ai_service: Optional[AiService] = None,
        semaphore_service: Optional[SemaphoreService] = None,
    ):
        self.google_search_service = google_search_service or GoogleSearchService()
        self.ai_service = ai_service or AiService()
        self.semaphore_service = semaphore_service or SemaphoreService()

    async def enrich_all_users_context(
        self,
        batch_number: int = 1,
        batch_size: int = 2
    ) -> Dict[str, Any]:
        """
        Enrich context for all users with pending enrichment status.

        Args:
            batch_number: Current batch number for processing
            batch_size: Number of users to process per batch (default 2 to avoid timeouts)

        Returns:
            Dict with processing results
        """
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size if batch_size > 0 else None

        # Fetch contexts pending enrichment
        contexts = await self._get_pending_contexts(offset=offset, limit=limit)
        total = len(contexts)

        if total == 0:
            return {
                'status': 'completed',
                'processed': 0,
                'total_contexts': 0,
                'message': 'No contexts pending enrichment',
            }

        results = []
        processed = 0
        failed = 0

        for context in contexts:
            try:
                user = await sync_to_async(User.objects.get)(id=context['user_id'])
                result = await self.enrich_user_context(user, context)
                results.append(result)
                if result.get('status') == 'success':
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed to enrich context for user {context['user_id']}: {str(e)}")
                failed += 1
                results.append({
                    'user_id': context['user_id'],
                    'status': 'failed',
                    'error': str(e)
                })

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        return {
            'status': 'completed',
            'processed': processed,
            'failed': failed,
            'total_contexts': total,
            'duration_seconds': duration,
            'details': results,
        }

    async def enrich_user_context(
        self,
        user: User,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich context for a specific user.

        Args:
            user: User instance
            context_data: Dictionary with context data including tendencies_data

        Returns:
            Dict with enrichment result
        """
        try:
            client_context = await sync_to_async(ClientContext.objects.get)(user=user)
            tendencies_data = context_data.get('tendencies_data') or {}

            if not tendencies_data:
                # No opportunities to enrich
                await self._update_enrichment_status(
                    client_context, 'enriched', None
                )
                return {
                    'user_id': user.id,
                    'status': 'success',
                    'message': 'No opportunities to enrich'
                }

            # Track used URLs across all categories to avoid duplicates
            used_url_keys: Set[str] = set()

            # Enrich each category
            enriched_data = await self._enrich_all_categories(
                tendencies_data, user, used_url_keys
            )

            # Save enriched data
            client_context.tendencies_data = enriched_data
            await self._update_enrichment_status(client_context, 'enriched', None)

            logger.info(f"Successfully enriched context for user {user.id}")
            return {
                'user_id': user.id,
                'status': 'success',
                'categories_enriched': len(enriched_data)
            }

        except Exception as e:
            logger.error(f"Error enriching context for user {user.id}: {str(e)}")
            try:
                client_context = await sync_to_async(ClientContext.objects.get)(user=user)
                await self._update_enrichment_status(client_context, 'failed', str(e))
            except Exception:
                pass
            return {
                'user_id': user.id,
                'status': 'failed',
                'error': str(e)
            }

    async def _enrich_all_categories(
        self,
        tendencies_data: Dict[str, Any],
        user: User,
        used_url_keys: Set[str]
    ) -> Dict[str, Any]:
        """
        Enrich all categories in tendencies_data.

        Args:
            tendencies_data: Dict with categories like 'polemica', 'educativo', etc.
            user: User instance for AI service calls
            used_url_keys: Set of already used URL keys for deduplication

        Returns:
            Enriched tendencies_data
        """
        enriched_data = {}

        for category_key, category_data in tendencies_data.items():
            if not isinstance(category_data, dict):
                enriched_data[category_key] = category_data
                continue

            items = category_data.get('items', [])
            if not items:
                enriched_data[category_key] = category_data
                continue

            # Get the section for source quality scoring
            section = CATEGORY_TO_SECTION.get(category_key, 'mercado')

            enriched_items = []
            for item in items[:3]:  # Only process top 3 per category
                enriched_item = await self._enrich_opportunity(
                    item, user, section, used_url_keys
                )
                enriched_items.append(enriched_item)

            enriched_data[category_key] = {
                'titulo': category_data.get('titulo', ''),
                'items': enriched_items
            }

        return enriched_data

    async def _enrich_opportunity(
        self,
        opportunity: Dict[str, Any],
        user: User,
        section: str,
        used_url_keys: Set[str]
    ) -> Dict[str, Any]:
        """
        Enrich a single opportunity with additional sources and analysis.

        Args:
            opportunity: Dict with opportunity data (titulo_ideia, score, url_fonte, etc.)
            user: User instance for AI service calls
            section: Section name for source quality scoring
            used_url_keys: Set of already used URL keys for deduplication

        Returns:
            Enriched opportunity dict with enriched_sources and enriched_analysis
        """
        enriched_opportunity = opportunity.copy()

        titulo = opportunity.get('titulo_ideia', '')
        if not titulo:
            return enriched_opportunity

        try:
            # Step 1: Google search for additional sources
            search_query = self._build_search_query(opportunity)
            enriched_sources = await self._fetch_and_filter_sources(
                search_query, section, used_url_keys
            )
            enriched_opportunity['enriched_sources'] = enriched_sources

            # Step 2: Generate deeper analysis with Gemini (only if we have sources)
            if enriched_sources:
                enriched_analysis = await self._generate_enriched_analysis(
                    opportunity, enriched_sources, user
                )
                enriched_opportunity['enriched_analysis'] = enriched_analysis
            else:
                enriched_opportunity['enriched_analysis'] = ''

        except Exception as e:
            logger.warning(f"Failed to enrich opportunity '{titulo}': {str(e)}")
            enriched_opportunity['enriched_sources'] = []
            enriched_opportunity['enriched_analysis'] = ''

        return enriched_opportunity

    def _build_search_query(self, opportunity: Dict[str, Any]) -> str:
        """
        Build a search query for the opportunity.

        Args:
            opportunity: Opportunity dict

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

    async def _fetch_and_filter_sources(
        self,
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
            query: Search query
            section: Section name for source quality scoring
            used_url_keys: Set of already used URL keys for deduplication

        Returns:
            List of validated, filtered source dicts with 'url', 'title', 'snippet'
        """
        try:
            # Fetch more results than needed to have margin after filtering
            results = await sync_to_async(self.google_search_service.search)(
                query=query,
                num_results=GOOGLE_SEARCH_RESULTS
            )

            if not results:
                return []

            # Score and filter sources
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

            # Sort by score (highest first)
            scored_sources.sort(key=lambda x: x['score'], reverse=True)

            # Validate and collect top sources
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

            logger.info(
                f"[ENRICHMENT] Query '{query[:50]}...' -> "
                f"{len(results)} raw, {len(scored_sources)} scored, "
                f"{len(validated_sources)} validated"
            )

            return validated_sources

        except Exception as e:
            logger.warning(f"Error fetching additional sources for '{query}': {str(e)}")
            return []

    async def _generate_enriched_analysis(
        self,
        opportunity: Dict[str, Any],
        sources: List[Dict[str, str]],
        user: User
    ) -> str:
        """
        Generate enriched analysis using Gemini.

        Args:
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
            sources_text = ""
            for i, source in enumerate(sources, 1):
                sources_text += f"\n{i}. {source.get('title', 'Sem titulo')}\n"
                sources_text += f"   {source.get('snippet', '')}\n"

            prompt = f"""Analise a seguinte oportunidade de conteudo e forneca uma analise mais profunda:

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

            analysis = await sync_to_async(self.ai_service.generate_text)(
                [prompt], user
            )

            return analysis.strip()

        except Exception as e:
            logger.warning(f"Error generating enriched analysis: {str(e)}")
            return ''

    @sync_to_async
    def _get_pending_contexts(
        self,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch contexts pending enrichment.

        Args:
            offset: Offset for pagination
            limit: Limit for pagination

        Returns:
            List of context dicts
        """
        queryset = ClientContext.objects.filter(
            weekly_context_error__isnull=True,
        ).exclude(
            context_enrichment_status='enriched'
        ).select_related('user').values(
            'id', 'user_id', 'user__email', 'user__first_name',
            'tendencies_data', 'context_enrichment_status'
        )

        if limit is not None:
            return list(queryset[offset:offset + limit])
        return list(queryset[offset:])

    @sync_to_async
    def _update_enrichment_status(
        self,
        client_context: ClientContext,
        status: str,
        error: Optional[str]
    ) -> None:
        """
        Update enrichment status on the context.

        Args:
            client_context: ClientContext instance
            status: New status ('pending', 'enriched', 'failed')
            error: Error message if failed
        """
        client_context.context_enrichment_status = status
        client_context.context_enrichment_date = timezone.now()
        client_context.context_enrichment_error = error or ''
        client_context.save()
