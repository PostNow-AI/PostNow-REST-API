"""Servico para retry de geracao diaria de ideias com falha."""

import logging
from typing import Any, Dict, Optional

from django.utils import timezone

from ClientContext.services.context_stats_service import ContextStatsService
from services.semaphore_service import SemaphoreService
from .daily_error_service import DailyErrorService
from .daily_ideas_service import DailyIdeasService

logger = logging.getLogger(__name__)


class RetryIdeasService:
    """Service for retrying failed daily ideas generation.

    Supports dependency injection for testing and flexibility (DIP).
    """

    def __init__(
        self,
        semaphore_service: Optional[SemaphoreService] = None,
        daily_ideas_service: Optional[DailyIdeasService] = None,
        error_service: Optional[DailyErrorService] = None,
        stats_service: Optional[ContextStatsService] = None,
    ):
        self.semaphore_service = semaphore_service or SemaphoreService()
        self.daily_ideas_service = daily_ideas_service or DailyIdeasService()
        self.error_service = error_service or DailyErrorService()
        self.stats_service = stats_service or ContextStatsService()

    async def process_daily_ideas_for_failed_users(self, batch_number: int, batch_size: int) -> Dict[str, Any]:
        """Process daily ideas generation for users with errors."""
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size if batch_size > 0 else None
        if batch_size == 0:
            offset = 0

        eligible_users = await self.error_service.get_users_with_errors(offset=offset, limit=limit)
        total = len(eligible_users)

        if total == 0:
            return {
                'status': 'completed',
                'processed': 0,
                'total_users': 0,
                'message': 'No users with errors found',
            }

        try:
            results = await self.semaphore_service.process_concurrently(
                users=eligible_users,
                function=self.daily_ideas_service.process_single_user
            )

            end_time = timezone.now()
            stats = self.stats_service.calculate_batch_results(results, start_time, end_time)

            # Adiciona contagem de posts criados (especifico para daily ideas)
            created_posts_count = sum(
                len(r.get('created_posts', [])) for r in results if r.get('status') == 'success'
            )

            result = self.stats_service.build_completion_result(stats, total, details=results)
            result['created_posts'] = created_posts_count

            return result

        except Exception as e:
            return {
                'status': 'error',
                'processed': 0,
                'total_users': total,
                'message': f'Error processing users: {str(e)}',
            }
