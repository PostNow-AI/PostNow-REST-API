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
from ClientContext.utils.search_utils import build_search_query, fetch_and_filter_sources
from ClientContext.utils.enrichment_analysis import generate_enriched_analysis
from services.google_search_service import GoogleSearchService
from services.ai_service import AiService
from services.semaphore_service import SemaphoreService

logger = logging.getLogger(__name__)

# Limite máximo de retries para contextos com falha
MAX_ENRICHMENT_RETRIES = 3

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
            batch_size: Number of users to process per batch

        Returns:
            Dict with processing results
        """
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size if batch_size > 0 else None

        contexts = await self._get_pending_contexts(offset=offset, limit=limit)
        total = len(contexts)

        if total == 0:
            return {
                'status': 'completed',
                'processed': 0,
                'total_contexts': 0,
                'message': 'No contexts pending enrichment',
            }

        # Pre-fetch all users in a single query to avoid N+1
        user_ids = [ctx['user_id'] for ctx in contexts]
        users_queryset = await sync_to_async(list)(
            User.objects.filter(id__in=user_ids)
        )
        users_by_id = {user.id: user for user in users_queryset}

        results = []
        processed = 0
        failed = 0

        for context in contexts:
            try:
                user = users_by_id.get(context['user_id'])
                if not user:
                    logger.error(f"User {context['user_id']} not found")
                    failed += 1
                    continue
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
                await self._update_enrichment_status(client_context, 'enriched', None)
                return {
                    'user_id': user.id,
                    'status': 'success',
                    'message': 'No opportunities to enrich'
                }

            used_url_keys: Set[str] = set()

            enriched_data = await self._enrich_all_categories(
                tendencies_data, user, used_url_keys
            )

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

            section = CATEGORY_TO_SECTION.get(category_key, 'mercado')

            enriched_items = []
            for item in items[:3]:
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
            opportunity: Dict with opportunity data
            user: User instance for AI service calls
            section: Section name for source quality scoring
            used_url_keys: Set of already used URL keys for deduplication

        Returns:
            Enriched opportunity dict
        """
        enriched_opportunity = opportunity.copy()

        titulo = opportunity.get('titulo_ideia', '')
        if not titulo:
            return enriched_opportunity

        try:
            search_query = build_search_query(opportunity)
            enriched_sources = await fetch_and_filter_sources(
                self.google_search_service, search_query, section, used_url_keys
            )
            enriched_opportunity['enriched_sources'] = enriched_sources

            if enriched_sources:
                enriched_analysis = await generate_enriched_analysis(
                    self.ai_service, opportunity, enriched_sources, user
                )
                enriched_opportunity['enriched_analysis'] = enriched_analysis
            else:
                enriched_opportunity['enriched_analysis'] = ''

        except Exception as e:
            logger.warning(f"Failed to enrich opportunity '{titulo}': {str(e)}")
            enriched_opportunity['enriched_sources'] = []
            enriched_opportunity['enriched_analysis'] = ''

        return enriched_opportunity

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
            context_enrichment_status__in=['pending', 'failed'],
        ).exclude(
            # Exclui contextos que falharam mais de MAX_ENRICHMENT_RETRIES vezes
            # Usando o campo context_enrichment_error para contar tentativas
            context_enrichment_status='failed',
            context_enrichment_error__contains=f'[retry:{MAX_ENRICHMENT_RETRIES}]'
        ).select_related('user').values(
            'id', 'user_id', 'user__email', 'user__first_name',
            'tendencies_data', 'context_enrichment_status',
            'context_enrichment_error'
        ).order_by('id')  # Ordenação determinística para paginação

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

        if status == 'failed' and error:
            # Incrementar contador de retries
            current_error = client_context.context_enrichment_error or ''
            retry_count = 1
            if '[retry:' in current_error:
                try:
                    start = current_error.index('[retry:') + 7
                    end = current_error.index(']', start)
                    retry_count = int(current_error[start:end]) + 1
                except (ValueError, IndexError):
                    retry_count = 1
            client_context.context_enrichment_error = f'[retry:{retry_count}] {error}'
        else:
            client_context.context_enrichment_error = error or ''

        client_context.save()
