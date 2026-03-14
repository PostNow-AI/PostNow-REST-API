"""Servico de orquestracao para geracao de contexto semanal."""

import json
import logging
import os
from typing import Dict, Any, Optional

from google.genai import types
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from AuditSystem.services import AuditService
from ..utils.policy_resolver import resolve_policy
from ..utils.text_utils import extract_json_block
from ..utils.history_utils import get_recent_topics, get_recent_url_keys
from ..utils.data_extraction import normalize_section_structure
from .opportunity_ranking_service import OpportunityRankingService
from .context_error_service import ContextErrorService
from .context_stats_service import ContextStatsService
from .context_persistence_service import ContextPersistenceService
from .source_fetching_service import SourceFetchingService
from services.get_creator_profile_data import get_creator_profile_data
from services.prompt_utils import build_optimized_search_queries
from services.user_validation_service import UserValidationService
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.search_service import SearchService
from services.semaphore_service import SemaphoreService
from services.trends_discovery_service import TrendsDiscoveryService

logger = logging.getLogger(__name__)

# DRY: Mapeamento centralizado JSON -> Model fields
CONTEXT_FIELD_MAPPING = {
    'mercado': {
        'panorama': ('market_panorama', ''),
        'tendencias': ('market_tendencies', []),
        'desafios': ('market_challenges', []),
        'fontes': ('market_sources', []),
    },
    'concorrencia': {
        'principais': ('competition_main', []),
        'estrategias': ('competition_strategies', ''),
        'oportunidades': ('competition_opportunities', ''),
        'fontes': ('competition_sources', []),
    },
    'publico': {
        'perfil': ('target_audience_profile', ''),
        'comportamento_online': ('target_audience_behaviors', ''),
        'interesses': ('target_audience_interests', []),
        'fontes': ('target_audience_sources', []),
    },
    'tendencias': {
        'temas_populares': ('tendencies_popular_themes', []),
        'hashtags': ('tendencies_hashtags', []),
        'keywords': ('tendencies_keywords', []),
        'fontes': ('tendencies_sources', []),
    },
    'sazonalidade': {
        'datas_relevantes': ('seasonal_relevant_dates', []),
        'eventos_locais': ('seasonal_local_events', []),
        'fontes': ('seasonal_sources', []),
    },
    'marca': {
        'presenca_online': ('brand_online_presence', ''),
        'reputacao': ('brand_reputation', ''),
        'tom_comunicacao_atual': ('brand_communication_style', ''),
        'fontes': ('brand_sources', []),
    },
}

SECTIONS = ['mercado', 'concorrencia', 'publico', 'tendencias', 'sazonalidade', 'marca']


class WeeklyContextService:
    """Service for generating weekly context for users.

    Supports dependency injection for testing and flexibility (DIP).
    """

    def __init__(
        self,
        user_validation_service: Optional[UserValidationService] = None,
        semaphore_service: Optional[SemaphoreService] = None,
        ai_service: Optional[AiService] = None,
        prompt_service: Optional[AIPromptService] = None,
        audit_service: Optional[AuditService] = None,
        search_service: Optional[SearchService] = None,
        opportunity_ranking_service: Optional[OpportunityRankingService] = None,
        error_service: Optional[ContextErrorService] = None,
        stats_service: Optional[ContextStatsService] = None,
        persistence_service: Optional[ContextPersistenceService] = None,
        trends_discovery_service: Optional[TrendsDiscoveryService] = None,
        source_fetching_service: Optional[SourceFetchingService] = None,
    ):
        self.user_validation_service = user_validation_service or UserValidationService()
        self.semaphore_service = semaphore_service or SemaphoreService()
        self.ai_service = ai_service or AiService()
        self.prompt_service = prompt_service or AIPromptService()
        self.audit_service = audit_service or AuditService()
        search_svc = search_service or SearchService()
        self.search_service = search_svc
        self.opportunity_ranking_service = opportunity_ranking_service or OpportunityRankingService()
        self.error_service = error_service or ContextErrorService()
        self.stats_service = stats_service or ContextStatsService()
        self.persistence_service = persistence_service or ContextPersistenceService()
        self.trends_discovery_service = trends_discovery_service or TrendsDiscoveryService()
        self.source_fetching_service = source_fetching_service or SourceFetchingService(search_svc)
        self.dedupe_lookback_weeks = 4

    @sync_to_async
    def _get_eligible_users(self, offset: int, limit: int) -> list[dict[str, Any]]:
        """Get a batch of users eligible for weekly context generation."""
        queryset = User.objects.filter(
            usersubscription__status='active',
            is_active=True
        ).distinct().values('id', 'email', 'username')

        if limit is None:
            return list(queryset[offset:])
        return list(queryset[offset:offset + limit])

    async def process_single_user(self, user_data: dict) -> Dict[str, Any]:
        """Wrapper method to process a single user from the user data."""
        user_id = user_data.get('id') or user_data.get('user_id')
        if not user_data:
            return {'status': 'failed', 'reason': 'no_user_data'}
        if not user_id:
            return {'status': 'failed', 'reason': 'no_user_id', 'user_data': user_data}

        return await self._process_user_context(user_id)

    async def process_all_users_context(self, batch_number: int, batch_size: int) -> Dict[str, Any]:
        """Process weekly context gen for all eligible users."""
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size

        if batch_size == 0:
            offset = 0
            limit = None

        eligible_users = await self._get_eligible_users(offset=offset, limit=limit)
        total = len(eligible_users)

        if total == 0:
            return {
                'status': 'completed',
                'processed': 0,
                'total_users': 0,
                'message': 'No eligible users found',
            }

        try:
            results = await self.semaphore_service.process_concurrently(
                users=eligible_users,
                function=self.process_single_user
            )

            end_time = timezone.now()
            stats = self.stats_service.calculate_batch_results(results, start_time, end_time)

            return self.stats_service.build_completion_result(stats, total, details=results)

        except Exception as e:
            return {
                'status': 'error',
                'processed': 0,
                'total_users': total,
                'message': f'Error processing users: {str(e)}',
            }

    async def _process_user_context(self, user_id: int) -> Dict[str, Any]:
        """Process weekly context generation for a single user."""
        try:
            user = await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

        try:
            user_data = await self.user_validation_service.get_user_data(user_id)
            if not user_data:
                return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

            await sync_to_async(self.audit_service.log_context_generation)(
                user=user, action='weekly_context_generation_started', status='info')

            validation_result = await self.user_validation_service.validate_user_eligibility(user_data)
            if validation_result['status'] != 'eligible':
                return {'user_id': user_id, 'status': 'skipped', 'reason': validation_result['reason']}

            # Fase 0: Descobrir tendencias reais para o setor
            discovered_trends = await self._discover_trends_for_user(user)

            json_str, search_results_map = await self._generate_context_for_user(user)

            context_data = self._parse_context_json(json_str)
            context_data = normalize_section_structure(context_data)

            recent_used_url_keys = await get_recent_url_keys(user, self.dedupe_lookback_weeks)
            ranked_opportunities = await self.opportunity_ranking_service.aggregate_and_rank_opportunities(
                context_data, search_results_map, recent_used_url_keys=recent_used_url_keys)
            context_data['ranked_opportunities'] = ranked_opportunities

            client_context = await self.persistence_service.save_context(
                user=user, context_data=context_data, ranked_opportunities=ranked_opportunities)
            await self.persistence_service.save_context_history(user, client_context)

            await sync_to_async(self.audit_service.log_context_generation)(
                user=user, action='context_generated', status='success',
                details={'discovered_trends_count': discovered_trends.get('validated_count', 0)})

            return {
                'user_id': user_id,
                'status': 'success',
                'discovered_trends_count': discovered_trends.get('validated_count', 0),
            }

        except Exception as e:
            await self.error_service.store_error(user, str(e))
            await sync_to_async(self.audit_service.log_context_generation)(
                user=user, action='weekly_context_generation_failed',
                status='error', details=str(e))
            return {'user_id': user_id, 'status': 'failed', 'error': str(e)}

    def _parse_context_json(self, json_str: str) -> dict:
        """Parse JSON from AI response with fallback."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            clean_context = extract_json_block(json_str)
            try:
                return json.loads(clean_context)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format from AI synthesis")

    async def _generate_context_for_user(self, user: User) -> tuple:
        """Generate context for a specific user.

        Returns: (json_string, search_results_by_section)
        """
        self.prompt_service.set_user(user)

        profile_data = await sync_to_async(get_creator_profile_data)(user)
        queries = build_optimized_search_queries(profile_data)

        decision = resolve_policy(profile_data)
        policy = decision.policy
        logger.info(
            "[POLICY] key=%s source=%s languages=%s",
            policy.key, decision.source, ",".join(policy.languages))

        excluded_topics = await get_recent_topics(user, self.dedupe_lookback_weeks)
        used_url_keys_recent = await get_recent_url_keys(user, self.dedupe_lookback_weeks)
        used_url_keys_this_run: set[str] = set()

        # Buscar fontes por secao (delegado ao SourceFetchingService)
        search_results = {}
        for section in SECTIONS:
            search_results[section] = await self.source_fetching_service.fetch_and_filter_section(
                section=section,
                query=queries.get(section, ''),
                profile_data=profile_data,
                policy=policy,
                used_url_keys_recent=used_url_keys_recent,
                used_url_keys_this_run=used_url_keys_this_run,
            )

        context_borrowed_for_audience = (
            search_results.get('mercado', []) + search_results.get('tendencias', []))

        # Sintetizar com IA por secao
        final_json_parts = []
        for section in SECTIONS:
            borrowed = context_borrowed_for_audience if section == 'publico' else None
            json_part = await self._synthesize_section(
                section, queries.get(section, ''),
                search_results.get(section, []),
                profile_data, excluded_topics, borrowed)
            final_json_parts.append(f'"{section}": {json_part}')

        full_json_str = "{" + ", ".join(final_json_parts) + "}"
        return full_json_str, search_results

    async def _synthesize_section(
        self, section: str, query: str, urls: list,
        profile_data: dict, excluded_topics: list, borrowed=None,
    ) -> str:
        """Synthesize a single section with AI."""
        prompt_list = self.prompt_service._build_synthesis_prompt(
            section_name=section,
            query=query,
            urls=urls,
            profile_data=profile_data,
            excluded_topics=excluded_topics,
            context_borrowed=borrowed,
        )

        synthesis_config = types.GenerateContentConfig(
            response_modalities=["TEXT"],
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=4096,
            response_mime_type="application/json",
        )

        try:
            ai_response = await sync_to_async(self.ai_service.generate_text)(
                prompt_list, None, config=synthesis_config)
            if isinstance(ai_response, dict):
                ai_text = ai_response.get('text', '')
            else:
                ai_text = str(ai_response)
            return extract_json_block(ai_text)
        except Exception as e:
            logger.error(f"Error generating section {section}: {e}")
            return '{}'

    async def _discover_trends_for_user(self, user: User) -> Dict[str, Any]:
        """Fase 0: Descobre tendencias REAIS para o setor do usuario."""
        try:
            profile_data = await sync_to_async(get_creator_profile_data)(user)
            sector = profile_data.get('specialization', '')
            business_description = profile_data.get('business_description', '')
            location = profile_data.get('business_location', 'Brasil')

            if not sector:
                logger.warning(f"User {user.id} has no sector defined, skipping trend discovery")
                return {'general_trends': [], 'sector_trends': [], 'rising_topics': [],
                        'validated_count': 0, 'discovery_metadata': {'error': 'no_sector_defined'}}

            discovered_trends = await sync_to_async(
                self.trends_discovery_service.discover_trends_for_sector
            )(sector=sector, business_description=business_description, location=location)

            logger.info(
                f"Discovered {discovered_trends.get('validated_count', 0)} trends "
                f"for user {user.id} (sector: {sector})")
            return discovered_trends

        except Exception as e:
            logger.error(f"Error discovering trends for user {user.id}: {e}")
            return {'general_trends': [], 'sector_trends': [], 'rising_topics': [],
                    'validated_count': 0, 'discovery_metadata': {'error': str(e)}}

    def _map_context_fields(self, client_context, context_data: dict) -> None:
        """DRY: Map JSON context data to ClientContext model fields."""
        for section_key, fields in CONTEXT_FIELD_MAPPING.items():
            section_data = context_data.get(section_key, {})
            for json_key, (model_field, default) in fields.items():
                value = section_data.get(json_key, default)
                setattr(client_context, model_field, value)
