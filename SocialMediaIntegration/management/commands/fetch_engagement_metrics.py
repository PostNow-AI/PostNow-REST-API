"""
Management command to fetch Instagram engagement metrics for published posts.

Usage:
    python manage.py fetch_engagement_metrics [--days 7]
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from SocialMediaIntegration.models import (
    EngagementMetrics,
    ScheduledPost,
    ScheduledPostStatus,
)
from SocialMediaIntegration.services.instagram_insights_service import (
    InstagramInsightsService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch Instagram engagement metrics for recently published posts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Fetch metrics for posts published in the last N days (default: 7)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        since = timezone.now() - timezone.timedelta(days=days)

        published_posts = ScheduledPost.objects.filter(
            status=ScheduledPostStatus.PUBLISHED,
            published_at__gte=since,
            instagram_media_id__isnull=False,
        ).select_related("instagram_account", "post_idea")

        if not published_posts.exists():
            self.stdout.write("No published posts found in the last %d days." % days)
            return

        service = InstagramInsightsService()
        updated = 0
        errors = 0

        for sp in published_posts:
            account = sp.instagram_account
            if not account.is_token_valid:
                logger.warning(
                    "Skipping %s — token expired for @%s",
                    sp.instagram_media_id,
                    account.instagram_username,
                )
                continue

            # Decrypt token (same pattern as publish service)
            try:
                from SocialMediaIntegration.services.instagram_publish_service import (
                    InstagramPublishService,
                )
                pub_service = InstagramPublishService()
                access_token = pub_service._decrypt_token(account.access_token)
            except Exception:
                access_token = account.access_token

            result = service.fetch_media_insights(
                sp.instagram_media_id, access_token
            )

            if not result.success:
                errors += 1
                logger.warning(
                    "Failed to fetch metrics for %s: %s",
                    sp.instagram_media_id,
                    result.error_message,
                )
                continue

            metrics, _ = EngagementMetrics.objects.update_or_create(
                scheduled_post=sp,
                defaults={
                    "instagram_media_id": sp.instagram_media_id,
                    "impressions": result.impressions,
                    "reach": result.reach,
                    "engagement": result.engagement,
                    "saves": result.saves,
                    "shares": result.shares,
                    "engagement_rate": result.engagement_rate,
                    "raw_data": result.raw_data,
                },
            )

            # Update GeneratedVisualStyle engagement_score via FK chain
            if sp.post_idea and sp.post_idea.generated_style:
                style = sp.post_idea.generated_style
                style.engagement_score = result.engagement_rate
                style.save(update_fields=["engagement_score"])

            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Fetched metrics: %d updated, %d errors" % (updated, errors)
            )
        )
