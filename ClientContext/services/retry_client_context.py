import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from services.semaphore_service import SemaphoreService

from .weekly_context_service import WeeklyContextService

logger = logging.getLogger(__name__)


class RetryClientContext:
    def __init__(self):
        self.semaphore_service = SemaphoreService()
        self.weekly_context_service = WeeklyContextService()

    @sync_to_async
    def _get_eligible_users(self, offset: int, limit: int) -> list[User]:
        """Get a batch of users with weekly context errors"""
        if limit is None:
            return list(
                User.objects.filter(
                    usersubscription__status='active',
                    is_active=True,
                    client_context__weekly_context_error__isnull=False
                ).distinct().values('id', 'email', 'username')[offset:]
            )

        return list(
            User.objects.filter(
                usersubscription__status='active',
                is_active=True,
                client_context__weekly_context_error__isnull=False
            ).distinct().values('id', 'email', 'username')[offset:offset + limit]
        )

    async def process_all_users_context(self, batch_number: int = 1, batch_size: int = 0) -> Dict[str, Any]:
        """Process weekly context gen for all eligible users."""
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size

        if batch_size == 0:
            offset = 0
            limit = None  # Process all users with errors

        eligible_users = await self._get_eligible_users(offset, limit)
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
                function=self.weekly_context_service._process_single_user
            )

            processed_count = sum(
                1 for r in results if r.get('status') == 'success')
            failed_count = sum(
                1 for r in results if r.get('status') == 'failed')
            skipped_count = sum(
                1 for r in results if r.get('status') == 'skipped')

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'status': 'completed',
                'processed': processed_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'total_users': total,
                'duration_seconds': duration,
                'details': results,
            }

            return result

        except Exception as e:
            return {
                'status': 'error',
                'processed': 0,
                'total_users': total,
                'message': f'Error processing users: {str(e)}',
            }
