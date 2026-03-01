"""
Instagram Publish Service

Implements the Instagram Graph API Content Publishing flow:
1. Create media container
2. Wait for processing
3. Publish container

API Documentation: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/content-publishing
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings
from django.utils import timezone

from ..models import (
    InstagramAccount,
    MediaType,
    PublishingLog,
    PublishingLogStatus,
    ScheduledPost,
    ScheduledPostStatus,
)

logger = logging.getLogger(__name__)

# Instagram Graph API base URL
GRAPH_API_BASE = "https://graph.instagram.com"
GRAPH_API_VERSION = "v21.0"


@dataclass
class PublishResult:
    """Result of a publishing attempt."""
    success: bool
    media_id: Optional[str] = None
    permalink: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class InstagramPublishError(Exception):
    """Custom exception for Instagram publishing errors."""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class InstagramPublishService:
    """
    Service for publishing content to Instagram via Graph API.

    The publishing process follows Instagram's 3-step flow:
    1. Create a media container (upload media)
    2. Wait for Instagram to process the media
    3. Publish the container

    Rate Limits:
    - 200 API requests per hour per account
    - 25 posts per 24 hours via API
    """

    def __init__(self):
        self.api_base = f"{GRAPH_API_BASE}/{GRAPH_API_VERSION}"
        self.max_processing_checks = 30  # Max polling attempts
        self.processing_check_interval = 2  # Seconds between checks

    def publish_post(self, scheduled_post: ScheduledPost) -> PublishResult:
        """
        Publish a scheduled post to Instagram.

        Args:
            scheduled_post: The ScheduledPost to publish

        Returns:
            PublishResult with success status and media info
        """
        account = scheduled_post.instagram_account
        log = self._create_log(scheduled_post, PublishingLogStatus.STARTED)

        try:
            # Validate account and token
            if not account.is_token_valid:
                raise InstagramPublishError(
                    "Token expirado ou inválido",
                    error_code="TOKEN_EXPIRED"
                )

            # Get decrypted access token
            access_token = self._get_access_token(account)

            # Step 1: Create media container
            log.step = "create_container"
            log.save()

            container_id = self._create_container(
                scheduled_post=scheduled_post,
                access_token=access_token,
                log=log
            )

            scheduled_post.instagram_container_id = container_id
            scheduled_post.status = ScheduledPostStatus.PUBLISHING
            scheduled_post.save(update_fields=['instagram_container_id', 'status', 'updated_at'])

            log.status = PublishingLogStatus.CONTAINER_CREATED
            log.save()

            # Step 2: Wait for processing
            log.step = "check_status"
            log.status = PublishingLogStatus.PROCESSING
            log.save()

            self._wait_for_processing(container_id, access_token)

            # Step 3: Publish container
            log.step = "publish"
            log.save()

            media_id = self._publish_container(
                ig_user_id=account.instagram_user_id,
                container_id=container_id,
                access_token=access_token,
                log=log
            )

            # Get permalink
            permalink = self._get_media_permalink(media_id, access_token)

            # Update scheduled post
            scheduled_post.instagram_media_id = media_id
            scheduled_post.instagram_permalink = permalink
            scheduled_post.published_at = timezone.now()
            scheduled_post.status = ScheduledPostStatus.PUBLISHED
            scheduled_post.save()

            # Complete log
            log.complete(
                status=PublishingLogStatus.SUCCESS,
                response_data={
                    'media_id': media_id,
                    'permalink': permalink
                }
            )

            logger.info(
                f"Post publicado com sucesso: {media_id} "
                f"(@{account.instagram_username})"
            )

            return PublishResult(
                success=True,
                media_id=media_id,
                permalink=permalink
            )

        except InstagramPublishError as e:
            return self._handle_error(scheduled_post, log, e)
        except requests.RequestException as e:
            error = InstagramPublishError(
                f"Erro de conexão: {str(e)}",
                error_code="CONNECTION_ERROR"
            )
            return self._handle_error(scheduled_post, log, error)
        except Exception as e:
            error = InstagramPublishError(
                f"Erro inesperado: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
            return self._handle_error(scheduled_post, log, error)

    def _create_container(
        self,
        scheduled_post: ScheduledPost,
        access_token: str,
        log: PublishingLog
    ) -> str:
        """
        Create a media container for the post.

        Args:
            scheduled_post: The post to create container for
            access_token: Instagram access token
            log: Publishing log for tracking

        Returns:
            Container ID from Instagram
        """
        ig_user_id = scheduled_post.instagram_account.instagram_user_id
        endpoint = f"{self.api_base}/{ig_user_id}/media"

        # Build params based on media type
        params = {
            "access_token": access_token,
            "caption": scheduled_post.caption,
        }

        media_urls = scheduled_post.media_urls
        media_type = scheduled_post.media_type

        if media_type == MediaType.IMAGE:
            params["image_url"] = media_urls[0]
        elif media_type == MediaType.VIDEO:
            params["media_type"] = "VIDEO"
            params["video_url"] = media_urls[0]
        elif media_type == MediaType.REELS:
            params["media_type"] = "REELS"
            params["video_url"] = media_urls[0]
        elif media_type == MediaType.STORY:
            # Stories require different handling
            if self._is_video_url(media_urls[0]):
                params["media_type"] = "STORIES"
                params["video_url"] = media_urls[0]
            else:
                params["media_type"] = "STORIES"
                params["image_url"] = media_urls[0]
        elif media_type == MediaType.CAROUSEL:
            # Carousel requires creating child containers first
            children_ids = self._create_carousel_children(
                ig_user_id=ig_user_id,
                media_urls=media_urls,
                access_token=access_token
            )
            params["media_type"] = "CAROUSEL"
            params["children"] = ",".join(children_ids)
            # Remove image_url for carousel
            params.pop("image_url", None)

        # Log request (without token)
        log.api_endpoint = endpoint
        log.request_data = {k: v for k, v in params.items() if k != "access_token"}
        log.save()

        # Make request
        response = requests.post(endpoint, params=params, timeout=60)
        response_data = response.json()

        if "error" in response_data:
            error = response_data["error"]
            raise InstagramPublishError(
                message=error.get("message", "Erro ao criar container"),
                error_code=error.get("code"),
                details=error
            )

        container_id = response_data.get("id")
        if not container_id:
            raise InstagramPublishError(
                "Container ID não retornado pela API",
                error_code="MISSING_CONTAINER_ID"
            )

        log.response_data = {"container_id": container_id}
        log.save()

        return container_id

    def _create_carousel_children(
        self,
        ig_user_id: str,
        media_urls: list,
        access_token: str
    ) -> list:
        """
        Create child containers for carousel post.

        Args:
            ig_user_id: Instagram user ID
            media_urls: List of media URLs
            access_token: Access token

        Returns:
            List of child container IDs
        """
        endpoint = f"{self.api_base}/{ig_user_id}/media"
        children_ids = []

        for url in media_urls[:10]:  # Max 10 items in carousel
            params = {
                "access_token": access_token,
                "is_carousel_item": "true",
            }

            if self._is_video_url(url):
                params["media_type"] = "VIDEO"
                params["video_url"] = url
            else:
                params["image_url"] = url

            response = requests.post(endpoint, params=params, timeout=60)
            response_data = response.json()

            if "error" in response_data:
                error = response_data["error"]
                raise InstagramPublishError(
                    message=f"Erro ao criar item do carrossel: {error.get('message')}",
                    error_code=error.get("code"),
                    details=error
                )

            child_id = response_data.get("id")
            if child_id:
                children_ids.append(child_id)

            # Small delay between children
            time.sleep(0.5)

        return children_ids

    def _wait_for_processing(self, container_id: str, access_token: str):
        """
        Wait for Instagram to finish processing the media.

        Args:
            container_id: The container ID to check
            access_token: Access token

        Raises:
            InstagramPublishError: If processing fails or times out
        """
        endpoint = f"{self.api_base}/{container_id}"
        params = {
            "fields": "status_code,status",
            "access_token": access_token
        }

        for attempt in range(self.max_processing_checks):
            response = requests.get(endpoint, params=params, timeout=30)
            response_data = response.json()

            if "error" in response_data:
                error = response_data["error"]
                raise InstagramPublishError(
                    message=f"Erro ao verificar status: {error.get('message')}",
                    error_code=error.get("code"),
                    details=error
                )

            status_code = response_data.get("status_code")

            if status_code == "FINISHED":
                logger.debug(f"Container {container_id} pronto para publicar")
                return
            elif status_code == "ERROR":
                status = response_data.get("status", "Unknown error")
                raise InstagramPublishError(
                    message=f"Erro no processamento: {status}",
                    error_code="PROCESSING_ERROR"
                )
            elif status_code == "EXPIRED":
                raise InstagramPublishError(
                    message="Container expirou durante processamento",
                    error_code="CONTAINER_EXPIRED"
                )
            elif status_code == "IN_PROGRESS":
                logger.debug(
                    f"Container {container_id} processando... "
                    f"(tentativa {attempt + 1}/{self.max_processing_checks})"
                )
                time.sleep(self.processing_check_interval)
            else:
                logger.warning(f"Status desconhecido: {status_code}")
                time.sleep(self.processing_check_interval)

        raise InstagramPublishError(
            message="Timeout aguardando processamento",
            error_code="PROCESSING_TIMEOUT"
        )

    def _publish_container(
        self,
        ig_user_id: str,
        container_id: str,
        access_token: str,
        log: PublishingLog
    ) -> str:
        """
        Publish a processed media container.

        Args:
            ig_user_id: Instagram user ID
            container_id: Container ID to publish
            access_token: Access token
            log: Publishing log

        Returns:
            Published media ID
        """
        endpoint = f"{self.api_base}/{ig_user_id}/media_publish"
        params = {
            "creation_id": container_id,
            "access_token": access_token
        }

        log.api_endpoint = endpoint
        log.request_data = {"creation_id": container_id}
        log.save()

        response = requests.post(endpoint, params=params, timeout=60)
        response_data = response.json()

        if "error" in response_data:
            error = response_data["error"]
            raise InstagramPublishError(
                message=f"Erro ao publicar: {error.get('message')}",
                error_code=error.get("code"),
                details=error
            )

        media_id = response_data.get("id")
        if not media_id:
            raise InstagramPublishError(
                "Media ID não retornado pela API",
                error_code="MISSING_MEDIA_ID"
            )

        return media_id

    def _get_media_permalink(self, media_id: str, access_token: str) -> Optional[str]:
        """
        Get the permanent link to a published media.

        Args:
            media_id: Published media ID
            access_token: Access token

        Returns:
            Permalink URL or None
        """
        endpoint = f"{self.api_base}/{media_id}"
        params = {
            "fields": "permalink",
            "access_token": access_token
        }

        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response_data = response.json()
            return response_data.get("permalink")
        except Exception as e:
            logger.warning(f"Erro ao obter permalink: {e}")
            return None

    def _get_access_token(self, account: InstagramAccount) -> str:
        """
        Get decrypted access token for account.

        In production, this should decrypt the token using Fernet.
        For now, returns the stored token directly.

        Args:
            account: Instagram account

        Returns:
            Decrypted access token
        """
        # TODO: Implement token decryption with Fernet
        # from cryptography.fernet import Fernet
        # cipher = Fernet(settings.FERNET_KEY)
        # return cipher.decrypt(account.access_token.encode()).decode()
        return account.access_token

    def _create_log(
        self,
        scheduled_post: ScheduledPost,
        status: PublishingLogStatus
    ) -> PublishingLog:
        """Create a publishing log entry."""
        return PublishingLog.objects.create(
            scheduled_post=scheduled_post,
            attempt_number=scheduled_post.retry_count + 1,
            status=status
        )

    def _handle_error(
        self,
        scheduled_post: ScheduledPost,
        log: PublishingLog,
        error: InstagramPublishError
    ) -> PublishResult:
        """Handle publishing error."""
        # Update log
        log.error_code = error.error_code
        log.error_message = str(error)
        log.error_details = error.details
        log.complete(
            status=PublishingLogStatus.ERROR,
            error_message=str(error)
        )

        # Update scheduled post
        scheduled_post.last_error = str(error)
        scheduled_post.status = ScheduledPostStatus.FAILED
        scheduled_post.save(update_fields=['last_error', 'status', 'updated_at'])

        # Schedule retry if possible
        if scheduled_post.can_retry:
            scheduled_post.schedule_retry()
            log.status = PublishingLogStatus.RETRY
            log.save()
            logger.info(
                f"Post agendado para retry em "
                f"{scheduled_post.next_retry_at}"
            )

        logger.error(
            f"Erro ao publicar post {scheduled_post.id}: "
            f"{error.error_code} - {error}"
        )

        return PublishResult(
            success=False,
            error_code=error.error_code,
            error_message=str(error)
        )

    @staticmethod
    def _is_video_url(url: str) -> bool:
        """Check if URL points to a video file."""
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        return any(url.lower().endswith(ext) for ext in video_extensions)
