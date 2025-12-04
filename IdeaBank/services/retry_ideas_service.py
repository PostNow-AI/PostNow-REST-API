import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from services.semaphore_service import SemaphoreService

from .daily_ideas_service import DailyIdeasService

logger = logging.getLogger(__name__)


class RetryIdeasService:
    def __init__(self):
        self.semaphore_service = SemaphoreService()
        self.daily_ideas_service = DailyIdeasService()

    @sync_to_async
    def _get_users_with_errors(self, offset: int, limit: int) -> list[User]:
        """Get all users who have daily generation errors."""
        if limit is None:
            return list(
                User.objects.extra(
                    where=["daily_generation_error IS NOT NULL"]
                ).filter(
                    usersubscription__status='active',
                    is_active=True
                ).distinct().values('id', 'email', 'username', 'first_name')
            )

        return list(
            User.objects.extra(
                where=["daily_generation_error IS NOT NULL"]
            ).filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().values('id', 'email', 'username', 'first_name')[offset:offset + limit]
        )

    async def process_daily_ideas_for_failed_users(self, batch_number: int = None, batch_size: int = None) -> Dict[str, Any]:
        """Process daily ideas generation for a batch of users"""
        start_time = timezone.now()
        offset = (batch_number - 1) * \
            batch_size if batch_size is not None else 0
        limit = batch_size

        eligible_users = await self._get_users_with_errors(offset=offset, limit=limit)
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
                function=self.daily_ideas_service._process_single_user
            )

            processed_count = sum(
                1 for r in results if r.get('status') == 'success')
            failed_count = sum(
                1 for r in results if r.get('status') == 'failed')
            skipped_count = sum(
                1 for r in results if r.get('status') == 'skipped')
            created_posts_count = sum(
                len(r.get('created_posts', [])) for r in results if r.get('status') == 'success'
            )

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'status': 'completed',
                'processed': processed_count,
                'created_posts': created_posts_count,
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
