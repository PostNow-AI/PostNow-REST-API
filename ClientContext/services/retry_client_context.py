"""Servico para retry de geracao de contexto semanal com falha."""

import logging
from typing import Any, Dict, Optional

from django.utils import timezone

from services.semaphore_service import SemaphoreService
from .context_error_service import ContextErrorService
from .context_stats_service import ContextStatsService
from .weekly_context_service import WeeklyContextService

logger = logging.getLogger(__name__)


class RetryClientContext:
    """Service for retrying failed weekly context generation.

    Supports dependency injection for testing and flexibility (DIP).
    """

    def __init__(
        self,
        semaphore_service: Optional[SemaphoreService] = None,
        weekly_context_service: Optional[WeeklyContextService] = None,
        error_service: Optional[ContextErrorService] = None,
        stats_service: Optional[ContextStatsService] = None,
    ):
        self.semaphore_service = semaphore_service or SemaphoreService()
        self.weekly_context_service = weekly_context_service or WeeklyContextService()
        self.error_service = error_service or ContextErrorService()
        self.stats_service = stats_service or ContextStatsService()

    async def process_all_users_context(self, batch_number: int = 1, batch_size: int = 0) -> Dict[str, Any]:
        """Process weekly context gen for all users with errors."""
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size

        if batch_size == 0:
            offset = 0
            limit = None

        eligible_users = await self.error_service.get_users_with_errors(offset, limit)
        total = len(eligible_users)

        if total == 0:
            return {
                'status': 'completed',
                'processed': 0,
                'total_users': 0,
                'message': 'No users with error found',
            }

        try:
            results = await self.semaphore_service.process_concurrently(
                users=eligible_users,
                function=self.weekly_context_service.process_single_user
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
