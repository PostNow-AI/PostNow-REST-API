"""
Scheduled Post Processor Service

Processes pending scheduled posts and handles retries.
Designed to be called by cron job (GitHub Actions).
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional

from django.db import models, transaction
from django.db.models import F, Q
from django.utils import timezone

from ..models import (
    InstagramAccount,
    PublishingLog,
    PublishingLogStatus,
    ScheduledPost,
    ScheduledPostStatus,
)
from .instagram_publish_service import InstagramPublishService, PublishResult

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of batch processing."""
    total_processed: int
    successful: int
    failed: int
    skipped: int
    results: List[dict]


class ScheduledPostProcessor:
    """
    Processor for scheduled Instagram posts.

    Handles:
    - Finding posts due for publishing
    - Processing posts in batches
    - Retry logic with exponential backoff
    - Token validation before publishing
    """

    def __init__(self, batch_size: int = 10):
        """
        Initialize processor.

        Args:
            batch_size: Maximum posts to process per run
        """
        self.batch_size = batch_size
        self.publish_service = InstagramPublishService()

    def process_pending_posts(self) -> ProcessingResult:
        """
        Process all pending scheduled posts that are due.

        Returns:
            ProcessingResult with summary of processing
        """
        logger.info("Iniciando processamento de posts agendados...")

        # Get posts due for publishing
        due_posts = self._get_due_posts()
        logger.info(f"Encontrados {len(due_posts)} posts para processar")

        results = []
        successful = 0
        failed = 0
        skipped = 0

        for post in due_posts:
            try:
                # Check if we should process this post
                if not self._should_process(post):
                    skipped += 1
                    results.append({
                        'post_id': post.id,
                        'status': 'skipped',
                        'reason': 'Token inválido ou conta desconectada'
                    })
                    continue

                # Process the post
                result = self._process_single_post(post)

                if result.success:
                    successful += 1
                    results.append({
                        'post_id': post.id,
                        'status': 'success',
                        'media_id': result.media_id,
                        'permalink': result.permalink
                    })
                else:
                    failed += 1
                    results.append({
                        'post_id': post.id,
                        'status': 'failed',
                        'error': result.error_message
                    })

            except Exception as e:
                logger.exception(f"Erro inesperado ao processar post {post.id}")
                failed += 1
                results.append({
                    'post_id': post.id,
                    'status': 'error',
                    'error': str(e)
                })

        total = successful + failed + skipped
        logger.info(
            f"Processamento concluído: "
            f"{successful} sucesso, {failed} falha, {skipped} ignorado"
        )

        return ProcessingResult(
            total_processed=total,
            successful=successful,
            failed=failed,
            skipped=skipped,
            results=results
        )

    def process_retries(self) -> ProcessingResult:
        """
        Process posts that are due for retry.

        Returns:
            ProcessingResult with summary
        """
        logger.info("Processando posts para retry...")

        retry_posts = self._get_retry_posts()
        logger.info(f"Encontrados {len(retry_posts)} posts para retry")

        results = []
        successful = 0
        failed = 0
        skipped = 0

        for post in retry_posts:
            try:
                if not self._should_process(post):
                    skipped += 1
                    continue

                # Reset status to scheduled for retry
                post.status = ScheduledPostStatus.SCHEDULED
                post.save(update_fields=['status', 'updated_at'])

                result = self._process_single_post(post)

                if result.success:
                    successful += 1
                    results.append({
                        'post_id': post.id,
                        'status': 'success',
                        'retry_count': post.retry_count
                    })
                else:
                    failed += 1
                    results.append({
                        'post_id': post.id,
                        'status': 'failed',
                        'retry_count': post.retry_count,
                        'error': result.error_message
                    })

            except Exception as e:
                logger.exception(f"Erro no retry do post {post.id}")
                failed += 1

        return ProcessingResult(
            total_processed=successful + failed + skipped,
            successful=successful,
            failed=failed,
            skipped=skipped,
            results=results
        )

    def _get_due_posts(self) -> List[ScheduledPost]:
        """
        Get posts that are due for publishing.

        Returns:
            List of ScheduledPost ready to publish
        """
        now = timezone.now()

        return list(ScheduledPost.objects.filter(
            status=ScheduledPostStatus.SCHEDULED,
            scheduled_for__lte=now,
            instagram_account__status='connected'
        ).select_related(
            'instagram_account',
            'user',
            'post_idea'
        ).order_by('scheduled_for')[:self.batch_size])

    def _get_retry_posts(self) -> List[ScheduledPost]:
        """
        Get posts that are due for retry.

        Returns:
            List of ScheduledPost ready for retry
        """
        now = timezone.now()

        return list(ScheduledPost.objects.filter(
            status=ScheduledPostStatus.FAILED,
            next_retry_at__lte=now,
            retry_count__lt=F('max_retries'),
            instagram_account__status='connected'
        ).select_related(
            'instagram_account',
            'user'
        ).order_by('next_retry_at')[:self.batch_size])

    def _should_process(self, post: ScheduledPost) -> bool:
        """
        Check if post should be processed.

        Args:
            post: ScheduledPost to check

        Returns:
            True if post should be processed
        """
        account = post.instagram_account

        # Check account is connected
        if account.status != 'connected':
            logger.warning(
                f"Conta {account.instagram_username} não está conectada"
            )
            self._mark_skipped(post, "Conta não conectada")
            return False

        # Check token is valid
        if not account.is_token_valid:
            logger.warning(
                f"Token expirado para @{account.instagram_username}"
            )
            self._mark_skipped(post, "Token expirado")
            self._notify_token_expired(account)
            return False

        # Check media URLs exist
        if not post.media_urls or len(post.media_urls) == 0:
            logger.warning(f"Post {post.id} não tem mídia")
            self._mark_skipped(post, "Sem mídia para publicar")
            return False

        return True

    def _process_single_post(self, post: ScheduledPost) -> PublishResult:
        """
        Process a single post.

        Args:
            post: ScheduledPost to process

        Returns:
            PublishResult from publishing service
        """
        logger.info(
            f"Processando post {post.id} para "
            f"@{post.instagram_account.instagram_username}"
        )

        return self.publish_service.publish_post(post)

    def _mark_skipped(self, post: ScheduledPost, reason: str):
        """Mark post as skipped with reason."""
        post.last_error = f"Ignorado: {reason}"
        post.save(update_fields=['last_error', 'updated_at'])

    def _notify_token_expired(self, account: InstagramAccount):
        """
        Notify user about expired token.

        TODO: Implement notification system
        """
        # Update account status
        account.status = 'token_expired'
        account.save(update_fields=['status', 'updated_at'])

        # TODO: Send notification to user
        logger.info(
            f"Token expirado notificado para "
            f"@{account.instagram_username}"
        )

    def get_pending_count(self) -> int:
        """Get count of pending posts."""
        return ScheduledPost.objects.filter(
            status=ScheduledPostStatus.SCHEDULED,
            scheduled_for__lte=timezone.now()
        ).count()

    def get_stats(self) -> dict:
        """
        Get publishing statistics.

        Returns:
            Dict with statistics
        """
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        return {
            'pending_now': self.get_pending_count(),
            'scheduled_future': ScheduledPost.objects.filter(
                status=ScheduledPostStatus.SCHEDULED,
                scheduled_for__gt=now
            ).count(),
            'published_today': ScheduledPost.objects.filter(
                status=ScheduledPostStatus.PUBLISHED,
                published_at__gte=today_start
            ).count(),
            'failed_today': ScheduledPost.objects.filter(
                status=ScheduledPostStatus.FAILED,
                updated_at__gte=today_start
            ).count(),
            'awaiting_retry': ScheduledPost.objects.filter(
                status=ScheduledPostStatus.FAILED,
                next_retry_at__isnull=False,
                retry_count__lt=models.F('max_retries')
            ).count(),
        }
