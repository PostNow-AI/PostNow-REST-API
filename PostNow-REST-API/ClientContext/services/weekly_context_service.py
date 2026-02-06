"""
Weekly Context Service - Orchestrates weekly context generation.
Refactored to follow SOLID principles (especially SRP and DIP).
"""
import json
import logging
import os
from typing import Dict, Any

from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from google.genai import types

from ClientContext.models import ClientContext
from ClientContext.utils.policy_resolver import resolve_policy
from ClientContext.utils.json_helpers import extract_json_block
from ClientContext.utils.weekly_context import generate_weekly_context_email_template

# Refactored services (SRP)
from ClientContext.services.url_processing_service import UrlProcessingService
from ClientContext.services.search_pool_processor import SearchPoolProcessor
from ClientContext.services.opportunity_aggregator import OpportunityAggregator
from ClientContext.services.context_persistence_service import ContextPersistenceService

# External services
from services.user_validation_service import UserValidationService
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from AuditSystem.services import AuditService
from services.google_search_service import GoogleSearchService
from services.mailjet_service import MailjetService

logger = logging.getLogger(__name__)

# Section names used throughout the service
SECTIONS = ['mercado', 'concorrencia', 'publico', 'tendencias', 'sazonalidade', 'marca']


class WeeklyContextService:
    """
    Orchestrates weekly context generation.

    Responsibilities:
    - Coordinate the workflow between specialized services
    - Handle user validation and auditing
    - Generate AI synthesis for each section
    """

    def __init__(self):
        # External services
        self.ai_service = AiService()
        self.prompt_service = AIPromptService()
        self.google_search_service = GoogleSearchService()
        self.mailjet_service = MailjetService()
        self.user_validation_service = UserValidationService()
        self.audit_service = AuditService()

        # Internal specialized services (DIP - could be injected)
        self.url_processor = UrlProcessingService()
        self.search_processor = SearchPoolProcessor(
            self.google_search_service,
            self.url_processor
        )
        self.opportunity_aggregator = OpportunityAggregator(self.url_processor)
        self.persistence_service = ContextPersistenceService()

        # Configuration
        self.dedupe_lookback_weeks = int(
            os.getenv("WEEKLY_CONTEXT_DEDUPE_WEEKS", "4")
        )

    async def _process_user_context(
        self,
        user_id: int,
        bcc: list[str] = None
    ) -> Dict[str, Any]:
        """Process weekly context generation for a single user."""
        user = await sync_to_async(User.objects.get)(id=user_id)

        try:
            # 1. Validate user eligibility
            validation_result = await self._validate_user(user, user_id)
            if validation_result:
                return validation_result

            # 2. Log start
            await self._log_audit(user, 'weekly_context_generation_started', 'info')

            # 3. Generate context
            context_result = await self._generate_context_for_user(user)
            json_str, search_results_map = self._parse_context_result(context_result)

            # 4. Parse and fix JSON structure
            context_data = self._parse_and_fix_json(json_str)

            # 5. Aggregate and rank opportunities
            recent_url_keys = await self._get_recent_url_keys(user)
            ranked_opportunities = await self.opportunity_aggregator.aggregate_and_rank(
                context_data,
                search_results_map,
                recent_used_url_keys=recent_url_keys
            )
            context_data['ranked_opportunities'] = ranked_opportunities

            # 6. Persist to database
            client_context = await self.persistence_service.save_context(
                user, context_data, ranked_opportunities
            )
            await self.persistence_service.save_to_history(user, client_context)

            # 7. Log success and send email
            await self._log_audit(user, 'context_generated', 'success')
            await self._send_email_async(user, context_data, bcc=bcc)

            return {'user_id': user_id, 'status': 'success'}

        except Exception as e:
            return await self._handle_error(user, user_id, e)

    async def _validate_user(self, user: User, user_id: int) -> Dict[str, Any] | None:
        """Validate user eligibility. Returns error dict if invalid, None if valid."""
        user_data = await self.user_validation_service.get_user_data(user_id)
        if not user_data:
            return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

        validation_result = await self.user_validation_service.validate_user_eligibility(
            user_data
        )
        if validation_result['status'] != 'eligible':
            return {
                'user_id': user_id,
                'status': 'skipped',
                'reason': validation_result['reason']
            }
        return None

    async def _handle_error(
        self,
        user: User,
        user_id: int,
        error: Exception
    ) -> Dict[str, Any]:
        """Handle and log errors during context generation."""
        await self.persistence_service.store_error(user, str(error))
        await self._log_audit(
            user,
            'weekly_context_generation_failed',
            'error',
            details=str(error)
        )
        return {'user_id': user_id, 'status': 'failed', 'error': str(error)}

    async def _log_audit(
        self,
        user: User,
        action: str,
        status: str,
        details: str = None
    ):
        """Log audit event."""
        kwargs = {'user': user, 'action': action, 'status': status}
        if details:
            kwargs['details'] = details
        await sync_to_async(self.audit_service.log_context_generation)(**kwargs)

    def _parse_context_result(self, context_result) -> tuple[str, dict]:
        """Parse the context generation result."""
        logger.info(f"Context Result Type: {type(context_result)}")

        if isinstance(context_result, tuple):
            return context_result[0], context_result[1]
        return context_result, {}

    def _parse_and_fix_json(self, json_str: str) -> dict:
        """Parse JSON string and fix structure issues."""
        try:
            context_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error Main: {e}")
            clean_context = extract_json_block(json_str)
            try:
                context_data = json.loads(clean_context)
            except json.JSONDecodeError as e2:
                logger.error(f"Failed to parse extracted JSON Main: {e2}")
                raise ValueError("Invalid JSON format from AI synthesis")

        # Fix structure: ensure all sections are dicts
        for section in SECTIONS:
            if section in context_data:
                context_data[section] = self._ensure_dict(context_data[section])

        return context_data

    def _ensure_dict(self, value) -> dict:
        """Ensure a value is a dictionary."""
        if isinstance(value, list):
            if value and isinstance(value[0], dict):
                return value[0]
            return {}
        if not isinstance(value, dict):
            return {}
        return value

    async def _send_email_async(
        self,
        user: User,
        context_data: dict,
        bcc: list[str] = None
    ):
        """Send the weekly context email."""
        user_tuple = await self.user_validation_service.get_user_data(user.id)
        if not user_tuple:
            logger.error(f"User data not found for email sending: {user.id}")
            return

        user_obj, profile_obj = user_tuple
        user_data = {
            'business_name': profile_obj.business_name,
            'user_name': user_obj.first_name,
            'user__first_name': user_obj.first_name
        }

        # Remove recipient from BCC to avoid duplicate
        if bcc and user.email in bcc:
            bcc = [email for email in bcc if email != user.email]

        html_content = generate_weekly_context_email_template(context_data, user_data)

        await self.mailjet_service.send_email(
            to_email=user.email,
            subject="Seu Contexto Semanal de Mercado",
            body=html_content,
            bcc=bcc
        )

    async def _generate_context_for_user(self, user: User) -> tuple:
        """Generate context for a specific user."""
        self.prompt_service.set_user(user)

        # 1. Prepare queries and policy
        profile_data = await sync_to_async(
            self.prompt_service._get_creator_profile_data
        )()
        queries = self.prompt_service._build_optimized_search_queries(profile_data)
        policy = self._get_policy(profile_data)

        # 2. Get historical data for deduplication
        excluded_topics = await self._get_recent_topics(user)
        used_url_keys_recent = await self._get_recent_url_keys(user)
        used_url_keys_this_run: set[str] = set()

        # 3. Execute searches for all sections
        search_results = {}
        for section in SECTIONS:
            query = queries.get(section, '')
            if query:
                items, used_url_keys_this_run, _ = await self.search_processor.fetch_and_filter_section(
                    section=section,
                    query=query,
                    profile_data=profile_data,
                    policy=policy,
                    used_keys_recent=used_url_keys_recent,
                    used_keys_this_run=used_url_keys_this_run
                )
                search_results[section] = items
            else:
                search_results[section] = []

        # 4. Generate AI synthesis for each section
        context_borrowed = search_results.get('mercado', []) + search_results.get('tendencias', [])
        final_json_parts = await self._synthesize_sections(
            queries, search_results, profile_data,
            excluded_topics, context_borrowed, user
        )

        # 5. Build final JSON
        full_json_str = "{" + ", ".join(final_json_parts) + "}"
        return full_json_str, search_results

    def _get_policy(self, profile_data: dict):
        """Get policy configuration."""
        decision = resolve_policy(profile_data)
        policy = decision.policy
        logger.info(
            "[POLICY] key=%s source=%s override=%s reason=%s languages=%s",
            policy.key, decision.source,
            decision.override_value or "",
            decision.reason,
            ",".join(policy.languages),
        )
        return policy

    async def _synthesize_sections(
        self,
        queries: dict,
        search_results: dict,
        profile_data: dict,
        excluded_topics: list,
        context_borrowed: list,
        user: User
    ) -> list[str]:
        """Generate AI synthesis for all sections."""
        final_json_parts = []

        synthesis_config = types.GenerateContentConfig(
            response_modalities=["TEXT"],
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=2000,
            response_mime_type="application/json"
        )

        for section in SECTIONS:
            borrowed = context_borrowed if section == 'publico' else None

            prompt_list = self.prompt_service._build_synthesis_prompt(
                section_name=section,
                query=queries.get(section, ''),
                urls=search_results.get(section, []),
                profile_data=profile_data,
                excluded_topics=excluded_topics,
                context_borrowed=borrowed
            )

            try:
                ai_response = await sync_to_async(self.ai_service.generate_text)(
                    prompt_list,
                    user,
                    config=synthesis_config,
                    response_mime_type="application/json"
                )

                ai_text = ai_response.get('text', '') if isinstance(ai_response, dict) else str(ai_response)
                clean_json = extract_json_block(ai_text)
                final_json_parts.append(f'"{section}": {clean_json}')

            except Exception as e:
                logger.error(f"Error generating section {section}: {e}")
                final_json_parts.append(f'"{section}": {{}}')

        return final_json_parts

    async def _get_recent_topics(self, user: User) -> list:
        """Get topics from recent weeks to avoid repetition."""
        from ClientContext.models import ClientContextHistory
        from datetime import timedelta
        from django.utils import timezone

        one_month_ago = timezone.now() - timedelta(weeks=4)

        history = await sync_to_async(lambda: list(
            ClientContextHistory.objects.filter(
                user=user,
                created_at__gte=one_month_ago
            ).values_list('tendencies_popular_themes', flat=True)
        ))()

        topics = []
        for item in history:
            if item:
                if isinstance(item, list):
                    topics.extend(item)
                elif isinstance(item, str):
                    try:
                        topics.extend(json.loads(item))
                    except:
                        pass
        return list(set(topics))

    async def _get_recent_url_keys(self, user: User) -> set[str]:
        """Get URL keys used recently for deduplication."""
        from ClientContext.models import ClientContextHistory
        from ClientContext.utils.url_dedupe import normalize_url_key
        from datetime import timedelta
        from django.utils import timezone

        since = timezone.now() - timedelta(days=max(self.dedupe_lookback_weeks, 1) * 7)

        histories = await sync_to_async(lambda: list(
            ClientContextHistory.objects.filter(
                user=user,
                created_at__gte=since
            ).order_by("-created_at").values("tendencies_data")
        ))()

        used: set[str] = set()
        for h in histories:
            data = h.get("tendencies_data") or {}
            if not isinstance(data, dict):
                continue
            for group in data.values():
                if not isinstance(group, dict):
                    continue
                for item in (group.get("items") or []):
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url_fonte")
                    if isinstance(url, str) and url.startswith("http"):
                        k = normalize_url_key(url)
                        if k:
                            used.add(k)

        return used
