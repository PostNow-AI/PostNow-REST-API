"""
Tests for SocialMediaIntegration module.

Covers:
- Models (InstagramAccount, ScheduledPost, PublishingLog)
- Serializers (validation)
- Views (endpoints)
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    InstagramAccount,
    InstagramAccountStatus,
    MediaType,
    PublishingLog,
    PublishingLogStatus,
    ScheduledPost,
    ScheduledPostStatus,
)
from .serializers import (
    ScheduledPostCreateSerializer,
)


# =============================================================================
# Model Tests
# =============================================================================

class InstagramAccountModelTest(TestCase):
    """Tests for InstagramAccount model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = InstagramAccount.objects.create(
            user=self.user,
            instagram_user_id='12345678',
            instagram_username='testaccount',
            facebook_page_id='987654321',
            access_token='test_token_abc123',
            token_expires_at=timezone.now() + timedelta(days=60),
            status=InstagramAccountStatus.CONNECTED
        )

    def test_str_representation(self):
        """Test string representation."""
        expected = f"@testaccount ({self.user.email})"
        self.assertEqual(str(self.account), expected)

    def test_is_token_valid_with_valid_token(self):
        """Test is_token_valid returns True for valid token."""
        self.account.token_expires_at = timezone.now() + timedelta(days=30)
        self.account.save()
        self.assertTrue(self.account.is_token_valid)

    def test_is_token_valid_with_expired_token(self):
        """Test is_token_valid returns False for expired token."""
        self.account.token_expires_at = timezone.now() - timedelta(days=1)
        self.account.save()
        self.assertFalse(self.account.is_token_valid)

    def test_is_token_valid_with_expiring_soon(self):
        """Test is_token_valid returns False when expiring within 1 day buffer."""
        self.account.token_expires_at = timezone.now() + timedelta(hours=12)
        self.account.save()
        self.assertFalse(self.account.is_token_valid)

    def test_days_until_expiration(self):
        """Test days_until_expiration calculation."""
        self.account.token_expires_at = timezone.now() + timedelta(days=30)
        self.account.save()
        # Allow for rounding (29 or 30 depending on time of day)
        self.assertIn(self.account.days_until_expiration, [29, 30])

    def test_days_until_expiration_expired(self):
        """Test days_until_expiration returns 0 for expired token."""
        self.account.token_expires_at = timezone.now() - timedelta(days=5)
        self.account.save()
        self.assertEqual(self.account.days_until_expiration, 0)

    def test_unique_together_constraint(self):
        """Test unique_together constraint for user + instagram_user_id."""
        with self.assertRaises(Exception):
            InstagramAccount.objects.create(
                user=self.user,
                instagram_user_id='12345678',  # Same as existing
                instagram_username='anotheraccount',
                facebook_page_id='111111',
                access_token='another_token',
                token_expires_at=timezone.now() + timedelta(days=60)
            )


class ScheduledPostModelTest(TestCase):
    """Tests for ScheduledPost model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = InstagramAccount.objects.create(
            user=self.user,
            instagram_user_id='12345678',
            instagram_username='testaccount',
            facebook_page_id='987654321',
            access_token='test_token',
            token_expires_at=timezone.now() + timedelta(days=60),
            status=InstagramAccountStatus.CONNECTED
        )
        self.post = ScheduledPost.objects.create(
            user=self.user,
            instagram_account=self.account,
            caption='Test caption for Instagram post',
            media_type=MediaType.IMAGE,
            media_urls=['https://example.com/image.jpg'],
            scheduled_for=timezone.now() + timedelta(hours=1),
            status=ScheduledPostStatus.SCHEDULED
        )

    def test_str_representation(self):
        """Test string representation."""
        self.assertIn('@testaccount', str(self.post))

    def test_caption_preview_short(self):
        """Test caption_preview for short caption."""
        self.post.caption = 'Short caption'
        self.assertEqual(self.post.caption_preview, 'Short caption')

    def test_caption_preview_long(self):
        """Test caption_preview for long caption."""
        self.post.caption = 'A' * 150
        preview = self.post.caption_preview
        self.assertEqual(len(preview), 103)  # 100 + '...'
        self.assertTrue(preview.endswith('...'))

    def test_is_ready_to_publish_true(self):
        """Test is_ready_to_publish returns True when ready."""
        self.post.scheduled_for = timezone.now() - timedelta(minutes=5)
        self.post.save()
        self.assertTrue(self.post.is_ready_to_publish)

    def test_is_ready_to_publish_false_future(self):
        """Test is_ready_to_publish returns False for future post."""
        self.post.scheduled_for = timezone.now() + timedelta(hours=1)
        self.post.save()
        self.assertFalse(self.post.is_ready_to_publish)

    def test_is_ready_to_publish_false_invalid_token(self):
        """Test is_ready_to_publish returns False when token expired."""
        self.account.token_expires_at = timezone.now() - timedelta(days=1)
        self.account.save()
        self.post.scheduled_for = timezone.now() - timedelta(minutes=5)
        self.post.save()
        self.assertFalse(self.post.is_ready_to_publish)

    def test_can_retry_true(self):
        """Test can_retry returns True when retries available."""
        self.post.status = ScheduledPostStatus.FAILED
        self.post.retry_count = 1
        self.post.max_retries = 3
        self.assertTrue(self.post.can_retry)

    def test_can_retry_false_max_reached(self):
        """Test can_retry returns False when max retries reached."""
        self.post.status = ScheduledPostStatus.FAILED
        self.post.retry_count = 3
        self.post.max_retries = 3
        self.assertFalse(self.post.can_retry)

    def test_can_retry_false_not_failed(self):
        """Test can_retry returns False when status is not FAILED."""
        self.post.status = ScheduledPostStatus.SCHEDULED
        self.post.retry_count = 0
        self.assertFalse(self.post.can_retry)

    def test_schedule_retry(self):
        """Test schedule_retry sets next_retry_at with backoff."""
        self.post.retry_count = 0
        self.post.schedule_retry(delay_minutes=15)

        self.assertEqual(self.post.retry_count, 1)
        self.assertIsNotNone(self.post.next_retry_at)
        # First retry: 15 * (2^0) = 15 minutes
        expected_min = timezone.now() + timedelta(minutes=14)
        expected_max = timezone.now() + timedelta(minutes=16)
        self.assertTrue(expected_min <= self.post.next_retry_at <= expected_max)

    def test_schedule_retry_exponential_backoff(self):
        """Test schedule_retry uses exponential backoff."""
        self.post.retry_count = 2
        self.post.schedule_retry(delay_minutes=15)

        self.assertEqual(self.post.retry_count, 3)
        # Third retry: 15 * (2^2) = 60 minutes
        # Allow wider margin for test timing
        expected_min = timezone.now() + timedelta(minutes=58)
        expected_max = timezone.now() + timedelta(minutes=62)
        self.assertTrue(expected_min <= self.post.next_retry_at <= expected_max)


class PublishingLogModelTest(TestCase):
    """Tests for PublishingLog model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = InstagramAccount.objects.create(
            user=self.user,
            instagram_user_id='12345678',
            instagram_username='testaccount',
            facebook_page_id='987654321',
            access_token='test_token',
            token_expires_at=timezone.now() + timedelta(days=60)
        )
        self.post = ScheduledPost.objects.create(
            user=self.user,
            instagram_account=self.account,
            caption='Test caption',
            media_urls=['https://example.com/image.jpg'],
            scheduled_for=timezone.now() + timedelta(hours=1),
            status=ScheduledPostStatus.SCHEDULED
        )
        self.log = PublishingLog.objects.create(
            scheduled_post=self.post,
            attempt_number=1,
            status=PublishingLogStatus.STARTED
        )

    def test_str_representation(self):
        """Test string representation."""
        expected = f"Log #1 - started ({self.post.id})"
        self.assertEqual(str(self.log), expected)

    def test_complete_success(self):
        """Test complete method for success."""
        self.log.complete(
            status=PublishingLogStatus.SUCCESS,
            response_data={'media_id': '123456'}
        )

        self.assertEqual(self.log.status, PublishingLogStatus.SUCCESS)
        self.assertIsNotNone(self.log.completed_at)
        self.assertIsNotNone(self.log.duration_ms)
        self.assertEqual(self.log.response_data, {'media_id': '123456'})

    def test_complete_error(self):
        """Test complete method for error."""
        self.log.complete(
            status=PublishingLogStatus.ERROR,
            error_message='API rate limit exceeded'
        )

        self.assertEqual(self.log.status, PublishingLogStatus.ERROR)
        self.assertEqual(self.log.error_message, 'API rate limit exceeded')


# =============================================================================
# Serializer Tests
# =============================================================================

class ScheduledPostCreateSerializerTest(TestCase):
    """Tests for ScheduledPostCreateSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = InstagramAccount.objects.create(
            user=self.user,
            instagram_user_id='12345678',
            instagram_username='testaccount',
            facebook_page_id='987654321',
            access_token='test_token',
            token_expires_at=timezone.now() + timedelta(days=60),
            status=InstagramAccountStatus.CONNECTED
        )

    def _get_serializer(self, data):
        """Helper to create serializer with request context."""
        request = MagicMock()
        request.user = self.user
        return ScheduledPostCreateSerializer(
            data=data,
            context={'request': request}
        )

    def test_valid_data(self):
        """Test serializer with valid data."""
        data = {
            'instagram_account_id': self.account.id,
            'caption': 'Test caption',
            'media_type': 'IMAGE',
            'media_urls': ['https://example.com/image.jpg'],
            'scheduled_for': (timezone.now() + timedelta(hours=1)).isoformat(),
        }
        serializer = self._get_serializer(data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_caption_max_length(self):
        """Test caption validation for max length."""
        data = {
            'instagram_account_id': self.account.id,
            'caption': 'A' * 2201,  # Over 2200 limit
            'media_type': 'IMAGE',
            'media_urls': ['https://example.com/image.jpg'],
            'scheduled_for': (timezone.now() + timedelta(hours=1)).isoformat(),
        }
        serializer = self._get_serializer(data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('caption', serializer.errors)

    def test_media_urls_required(self):
        """Test media_urls is required."""
        data = {
            'instagram_account_id': self.account.id,
            'caption': 'Test caption',
            'media_type': 'IMAGE',
            'media_urls': [],  # Empty
            'scheduled_for': (timezone.now() + timedelta(hours=1)).isoformat(),
        }
        serializer = self._get_serializer(data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('media_urls', serializer.errors)

    def test_carousel_min_items(self):
        """Test carousel requires at least 2 items."""
        data = {
            'instagram_account_id': self.account.id,
            'caption': 'Test caption',
            'media_type': 'CAROUSEL',
            'media_urls': ['https://example.com/image.jpg'],  # Only 1
            'scheduled_for': (timezone.now() + timedelta(hours=1)).isoformat(),
        }
        serializer = self._get_serializer(data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('media_urls', serializer.errors)

    def test_scheduled_for_in_past(self):
        """Test scheduled_for rejects past dates."""
        data = {
            'instagram_account_id': self.account.id,
            'caption': 'Test caption',
            'media_type': 'IMAGE',
            'media_urls': ['https://example.com/image.jpg'],
            'scheduled_for': (timezone.now() - timedelta(hours=1)).isoformat(),
        }
        serializer = self._get_serializer(data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('scheduled_for', serializer.errors)

    def test_invalid_account(self):
        """Test validation fails for non-existent account."""
        data = {
            'instagram_account_id': 99999,  # Non-existent
            'caption': 'Test caption',
            'media_type': 'IMAGE',
            'media_urls': ['https://example.com/image.jpg'],
            'scheduled_for': (timezone.now() + timedelta(hours=1)).isoformat(),
        }
        serializer = self._get_serializer(data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('instagram_account_id', serializer.errors)

    def test_disconnected_account(self):
        """Test validation fails for disconnected account."""
        self.account.status = InstagramAccountStatus.DISCONNECTED
        self.account.save()

        data = {
            'instagram_account_id': self.account.id,
            'caption': 'Test caption',
            'media_type': 'IMAGE',
            'media_urls': ['https://example.com/image.jpg'],
            'scheduled_for': (timezone.now() + timedelta(hours=1)).isoformat(),
        }
        serializer = self._get_serializer(data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('instagram_account_id', serializer.errors)


# =============================================================================
# View Tests
# =============================================================================

class ScheduledPostViewTest(APITestCase):
    """Tests for ScheduledPost views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = InstagramAccount.objects.create(
            user=self.user,
            instagram_user_id='12345678',
            instagram_username='testaccount',
            facebook_page_id='987654321',
            access_token='test_token',
            token_expires_at=timezone.now() + timedelta(days=60),
            status=InstagramAccountStatus.CONNECTED
        )
        self.post = ScheduledPost.objects.create(
            user=self.user,
            instagram_account=self.account,
            caption='Test caption',
            media_urls=['https://example.com/image.jpg'],
            scheduled_for=timezone.now() + timedelta(hours=1),
            status=ScheduledPostStatus.SCHEDULED
        )
        self.client.force_authenticate(user=self.user)

    def test_list_scheduled_posts(self):
        """Test listing scheduled posts."""
        url = reverse('social:scheduled-post-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_filtered_by_status(self):
        """Test filtering by status."""
        # Create a published post
        ScheduledPost.objects.create(
            user=self.user,
            instagram_account=self.account,
            caption='Published post',
            media_urls=['https://example.com/image2.jpg'],
            scheduled_for=timezone.now() - timedelta(hours=1),
            status=ScheduledPostStatus.PUBLISHED
        )

        url = reverse('social:scheduled-post-list')
        response = self.client.get(url, {'status': 'scheduled'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'scheduled')

    def test_create_scheduled_post(self):
        """Test creating a scheduled post."""
        url = reverse('social:scheduled-post-list')
        data = {
            'instagram_account_id': self.account.id,
            'caption': 'New test caption',
            'media_type': 'IMAGE',
            'media_urls': ['https://example.com/new-image.jpg'],
            'scheduled_for': (timezone.now() + timedelta(hours=2)).isoformat(),
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ScheduledPost.objects.count(), 2)

    def test_retrieve_scheduled_post(self):
        """Test retrieving a single post."""
        url = reverse('social:scheduled-post-detail', kwargs={'pk': self.post.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['caption'], 'Test caption')

    def test_update_scheduled_post(self):
        """Test updating a scheduled post."""
        url = reverse('social:scheduled-post-detail', kwargs={'pk': self.post.pk})
        data = {'caption': 'Updated caption'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.caption, 'Updated caption')

    def test_delete_scheduled_post(self):
        """Test deleting a scheduled post."""
        url = reverse('social:scheduled-post-detail', kwargs={'pk': self.post.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ScheduledPost.objects.count(), 0)

    def test_cannot_delete_published_post(self):
        """Test that published posts cannot be deleted."""
        self.post.status = ScheduledPostStatus.PUBLISHED
        self.post.save()

        url = reverse('social:scheduled-post-detail', kwargs={'pk': self.post.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_scheduled_post(self):
        """Test canceling a scheduled post."""
        url = reverse('social:scheduled-post-cancel', kwargs={'pk': self.post.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, ScheduledPostStatus.CANCELLED)

    def test_stats_endpoint(self):
        """Test stats endpoint."""
        url = reverse('social:scheduled-post-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pending', response.data)
        self.assertIn('scheduled_future', response.data)
        self.assertIn('failed', response.data)

    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access."""
        self.client.force_authenticate(user=None)
        url = reverse('social:scheduled-post-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_isolation(self):
        """Test that users can only see their own posts."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_account = InstagramAccount.objects.create(
            user=other_user,
            instagram_user_id='99999999',
            instagram_username='otheraccount',
            facebook_page_id='888888888',
            access_token='other_token',
            token_expires_at=timezone.now() + timedelta(days=60)
        )
        ScheduledPost.objects.create(
            user=other_user,
            instagram_account=other_account,
            caption='Other user post',
            media_urls=['https://example.com/other.jpg'],
            scheduled_for=timezone.now() + timedelta(hours=1),
            status=ScheduledPostStatus.SCHEDULED
        )

        url = reverse('social:scheduled-post-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only sees own post
        # List serializer uses caption_preview instead of full caption
        self.assertEqual(response.data[0]['caption_preview'], 'Test caption')


class InstagramAccountViewTest(APITestCase):
    """Tests for InstagramAccount views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = InstagramAccount.objects.create(
            user=self.user,
            instagram_user_id='12345678',
            instagram_username='testaccount',
            facebook_page_id='987654321',
            access_token='test_token',
            token_expires_at=timezone.now() + timedelta(days=60),
            status=InstagramAccountStatus.CONNECTED
        )
        self.client.force_authenticate(user=self.user)

    def test_list_accounts(self):
        """Test listing Instagram accounts."""
        url = reverse('social:instagram-account-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['instagram_username'], 'testaccount')

    def test_disconnect_account(self):
        """Test disconnecting an account."""
        url = reverse('social:instagram-account-disconnect', kwargs={'pk': self.account.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertEqual(self.account.status, 'disconnected')
        self.assertEqual(self.account.access_token, '')

    def test_cannot_disconnect_with_pending_posts(self):
        """Test that account with pending posts cannot be disconnected."""
        ScheduledPost.objects.create(
            user=self.user,
            instagram_account=self.account,
            caption='Pending post',
            media_urls=['https://example.com/image.jpg'],
            scheduled_for=timezone.now() + timedelta(hours=1),
            status=ScheduledPostStatus.SCHEDULED
        )

        url = reverse('social:instagram-account-disconnect', kwargs={'pk': self.account.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('posts agendados', response.data['error'])


# =============================================================================
# Service Tests (Basic)
# =============================================================================

class InstagramPublishServiceTest(TestCase):
    """Basic tests for InstagramPublishService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = InstagramAccount.objects.create(
            user=self.user,
            instagram_user_id='12345678',
            instagram_username='testaccount',
            facebook_page_id='987654321',
            access_token='test_token',
            token_expires_at=timezone.now() + timedelta(days=60),
            status=InstagramAccountStatus.CONNECTED
        )
        self.post = ScheduledPost.objects.create(
            user=self.user,
            instagram_account=self.account,
            caption='Test caption',
            media_urls=['https://example.com/image.jpg'],
            scheduled_for=timezone.now() - timedelta(minutes=5),
            status=ScheduledPostStatus.SCHEDULED
        )

    def test_is_video_url_true(self):
        """Test _is_video_url returns True for video URLs."""
        from .services import InstagramPublishService

        service = InstagramPublishService()
        self.assertTrue(service._is_video_url('https://example.com/video.mp4'))
        self.assertTrue(service._is_video_url('https://example.com/video.mov'))
        self.assertTrue(service._is_video_url('https://example.com/video.webm'))

    def test_is_video_url_false(self):
        """Test _is_video_url returns False for image URLs."""
        from .services import InstagramPublishService

        service = InstagramPublishService()
        self.assertFalse(service._is_video_url('https://example.com/image.jpg'))
        self.assertFalse(service._is_video_url('https://example.com/image.png'))

    @patch('SocialMediaIntegration.services.instagram_publish_service.requests.post')
    @patch('SocialMediaIntegration.services.instagram_publish_service.requests.get')
    def test_publish_post_creates_log(self, mock_get, mock_post):
        """Test that publishing creates a log entry."""
        from .services import InstagramPublishService

        # Mock API responses
        mock_post.return_value.json.return_value = {'id': 'container_123'}
        mock_get.return_value.json.return_value = {'status_code': 'FINISHED'}

        # Override publish to avoid actual API call
        service = InstagramPublishService()

        # Just verify log is created when publish starts
        initial_log_count = PublishingLog.objects.count()

        # Call a partial test - we can't fully test without mocking everything
        log = service._create_log(self.post, PublishingLogStatus.STARTED)

        self.assertEqual(PublishingLog.objects.count(), initial_log_count + 1)
        self.assertEqual(log.attempt_number, 1)
        self.assertEqual(log.status, PublishingLogStatus.STARTED)
