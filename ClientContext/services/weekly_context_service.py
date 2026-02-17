"""Servico de orquestracao para geracao de contexto semanal."""

import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from AuditSystem.services import AuditService
from ..models import ClientContext
from ..serializers.context_serializer import WeeklyContextDataSerializer
from ..utils.json_parser import parse_ai_json_response
from .context_error_service import ContextErrorService
from .context_stats_service import ContextStatsService
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.semaphore_service import SemaphoreService
from services.user_validation_service import UserValidationService

logger = logging.getLogger(__name__)


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
        error_service: Optional[ContextErrorService] = None,
        stats_service: Optional[ContextStatsService] = None,
    ):
        self.user_validation_service = user_validation_service or UserValidationService()
        self.semaphore_service = semaphore_service or SemaphoreService()
        self.ai_service = ai_service or AiService()
        self.prompt_service = prompt_service or AIPromptService()
        self.audit_service = audit_service or AuditService()
        self.error_service = error_service or ContextErrorService()
        self.stats_service = stats_service or ContextStatsService()

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
        user = await sync_to_async(User.objects.get)(id=user_id)

        try:
            user_data = await self.user_validation_service.get_user_data(user_id)
            if not user_data:
                return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

            await sync_to_async(self.audit_service.log_context_generation)(
                user=user,
                action='weekly_context_generation_started',
                status='info',
            )

            validation_result = await self.user_validation_service.validate_user_eligibility(user_data)

            if validation_result['status'] != 'eligible':
                return {
                    'user_id': user_id,
                    'status': 'skipped',
                    'reason': validation_result['reason']
                }

            context_result = await sync_to_async(self._generate_context_for_user)(user)
            context_data = parse_ai_json_response(context_result)

            client_context, _ = await sync_to_async(ClientContext.objects.get_or_create)(user=user)

            serializer = WeeklyContextDataSerializer(context_data)
            serializer.update_client_context(client_context)

            client_context.weekly_context_error = None
            client_context.weekly_context_error_date = None
            await sync_to_async(client_context.save)()

            await sync_to_async(self.audit_service.log_context_generation)(
                user=user,
                action='context_generated',
                status='success',
            )

            return {
                'user_id': user_id,
                'status': 'success',
            }

        except Exception as e:
            await self.error_service.store_error(user, str(e))
            await sync_to_async(self.audit_service.log_context_generation)(
                user=user,
                action='weekly_context_generation_failed',
                status='error',
                details=str(e)
            )

            return {
                'user_id': user_id,
                'status': 'failed',
                'error': str(e),
            }

    def _generate_context_for_user(self, user: User) -> str:
        """AI service call to generate weekly context for a user."""
        try:
            self.prompt_service.set_user(user)
            prompt = self.prompt_service.build_context_prompts()
            context_result = self.ai_service.generate_text(prompt, user)

            return context_result
        except Exception as e:
            raise Exception(
                f"Failed to generate context for user {user.id}: {str(e)}")
