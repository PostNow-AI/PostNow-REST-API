import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.db import connection
from django.utils import timezone

from services.semaphore_service import SemaphoreService
from .daily_ideas_service import DailyIdeasService

logger = logging.getLogger(__name__)


class RetryIdeasService:
    def __init__(self):
        self.semaphore_service = SemaphoreService()
        self.daily_ideas_service = DailyIdeasService()

    @sync_to_async
    def _get_users_with_errors(
        self, offset: int, limit: int, target_week: str
    ) -> list[dict[str, Any]]:
        """Get users who have errors AND haven't completed all 7 iterations this week."""

        cursor = connection.cursor()

        # Build SQL query with subquery for active subscriptions
        base_query = """
            SELECT DISTINCT u.id, u.email, u.username, u.first_name,
                   u.weekly_generation_progress, u.weekly_generation_week
            FROM auth_user u
            INNER JOIN CreditSystem_usersubscription us ON us.user_id = u.id
            WHERE u.daily_generation_error IS NOT NULL
              AND u.is_active = 1
              AND us.status = 'active'
              AND (u.weekly_generation_week != %s 
                   OR u.weekly_generation_week IS NULL 
                   OR u.weekly_generation_progress < 7)
        """

        if limit is None:
            # MySQL requires LIMIT when using OFFSET, use very large number for "all"
            query = base_query + " LIMIT 999999 OFFSET %s"
            cursor.execute(query, [target_week, offset])
        else:
            query = base_query + " LIMIT %s OFFSET %s"
            cursor.execute(query, [target_week, limit, offset])

        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return results

    async def process_daily_ideas_for_failed_users(
        self, batch_number: int, batch_size: int
    ) -> Dict[str, Any]:
        """Process daily ideas generation for failed users, respecting weekly progress."""
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size

        # Calculate current week in format YYYY-Www (e.g., "2025-W50")
        target_week = start_time.strftime("%Y-W%W")

        eligible_users = await self._get_users_with_errors(
            offset=offset, limit=limit, target_week=target_week
        )
        total = len(eligible_users)

        if total > 0:
            # Telemetria de agendamento (base pronta p/ RL de retries)
            try:
                from Analytics.models import Decision

                await sync_to_async(Decision.objects.create)(
                    decision_type="scheduler_batch",
                    action="retry_failed_users",
                    policy_id="scheduler_fixed_v0",
                    user=None,
                    resource_type="Batch",
                    resource_id=f"retry:{target_week}:{batch_number}",
                    context={"batch_number": batch_number, "batch_size": batch_size, "users": total},
                    properties={},
                )
            except Exception:
                pass

        if total == 0:
            return {
                "status": "completed",
                "processed": 0,
                "total_users": 0,
                "message": "No eligible users found",
            }

        try:
            results = await self.semaphore_service.process_concurrently(
                users=eligible_users,
                function=self.daily_ideas_service.process_single_user,
            )

            processed_count = sum(1 for r in results if r.get("status") == "success")
            partial_count = sum(1 for r in results if r.get("status") == "partial")
            failed_count = sum(1 for r in results if r.get("status") == "failed")
            skipped_count = sum(1 for r in results if r.get("status") == "skipped")
            created_posts_count = sum(
                len(r.get("created_posts", []))
                for r in results
                if r.get("status") in ["success", "partial"]
            )

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "status": "completed",
                "processed": processed_count,
                "partial": partial_count,
                "created_posts": created_posts_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "total_users": total,
                "duration_seconds": duration,
                "details": results,
            }

            return result
        except Exception as e:
            return {
                "status": "error",
                "processed": 0,
                "total_users": total,
                "message": f"Error processing users: {str(e)}",
            }
