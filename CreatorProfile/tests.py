from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CreatorProfile, OnboardingStepTracking, OnboardingTempData
from .services import OnboardingDataService


class CreatorProfileOnboardingTest(TestCase):
    """
    Tests for CreatorProfile onboarding logic.

    Current model fields for step completion:
    - Step 1: business_name, specialization, business_description
    - Step 2: voice_tone + at least one color
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_empty_profile_onboarding_not_completed(self):
        """Test that empty profiles are not marked as onboarding completed."""
        profile = CreatorProfile.objects.create(user=self.user)

        # Initially should not be completed
        self.assertFalse(profile.onboarding_completed)
        self.assertIsNone(profile.onboarding_completed_at)

        # Save should not change status for empty profile
        profile.save()
        self.assertFalse(profile.onboarding_completed)
        self.assertIsNone(profile.onboarding_completed_at)

    def test_profile_with_data_onboarding_completed(self):
        """Test that profiles with data are marked as onboarding completed."""
        profile = CreatorProfile.objects.create(
            user=self.user,
            # Step 1 fields
            business_name="Test Business",
            specialization="Web Development",
            business_description="A test business description that is long enough to pass validation.",
            # Step 2 fields
            voice_tone="Profissional",
            color_1="#FF6B6B"
        )

        # Save should mark as completed
        profile.save()
        self.assertTrue(profile.onboarding_completed)
        self.assertIsNotNone(profile.onboarding_completed_at)

    def test_profile_with_empty_strings_onboarding_not_completed(self):
        """Test that profiles with empty strings are not marked as completed."""
        profile = CreatorProfile.objects.create(
            user=self.user,
            business_name="",
            specialization="   ",
            business_description=""
        )

        # Save should not mark as completed
        profile.save()
        self.assertFalse(profile.onboarding_completed)
        self.assertIsNone(profile.onboarding_completed_at)

    def test_onboarding_status_calculation(self):
        """Test that onboarding status is calculated correctly."""
        profile = CreatorProfile.objects.create(user=self.user)

        # Empty profile should not be completed
        self.assertFalse(profile.onboarding_completed)
        self.assertEqual(profile.current_step, 1)

        # Profile with step 1 data
        profile.business_name = "Test Business"
        profile.specialization = "Development"
        profile.business_description = "A description for the business"
        profile.save()

        # Should complete step 1 but not full onboarding
        self.assertTrue(profile.step_1_completed)
        self.assertFalse(profile.onboarding_completed)
        self.assertEqual(profile.current_step, 2)

    def test_profile_reset_onboarding_status(self):
        """Test that removing all data resets onboarding status."""
        # Create complete profile
        profile = CreatorProfile.objects.create(
            user=self.user,
            business_name="Test Business",
            specialization="Web Development",
            business_description="A complete business description that meets all requirements.",
            voice_tone="Profissional",
            color_1="#FF6B6B"
        )
        profile.save()

        # Should be completed
        self.assertTrue(profile.onboarding_completed)
        self.assertIsNotNone(profile.onboarding_completed_at)

        # Clear data
        profile.business_name = ""
        profile.specialization = ""
        profile.business_description = ""
        profile.voice_tone = ""
        profile.color_1 = None
        profile.color_2 = None
        profile.color_3 = None
        profile.color_4 = None
        profile.color_5 = None
        profile.save()

        # Should not be completed
        self.assertFalse(profile.onboarding_completed)
        self.assertIsNone(profile.onboarding_completed_at)

    def test_step_completion_logic(self):
        """Test that step completion logic works correctly."""
        profile = CreatorProfile.objects.create(user=self.user)

        # Step 1 completion requires: business_name, specialization, business_description
        profile.business_name = "Test Business"
        profile.specialization = "Web Development"
        profile.business_description = "A comprehensive business description."
        profile.save()

        self.assertTrue(profile.step_1_completed)
        self.assertFalse(profile.step_2_completed)
        self.assertEqual(profile.current_step, 2)

        # Step 2 completion requires: voice_tone + at least one color
        profile.voice_tone = "Profissional"
        profile.color_1 = "#FF6B6B"
        profile.save()

        self.assertTrue(profile.step_1_completed)
        self.assertTrue(profile.step_2_completed)
        self.assertTrue(profile.onboarding_completed)
        self.assertEqual(profile.current_step, 3)  # Completed

    def test_colors_auto_assigned_if_empty(self):
        """Test that random colors are assigned if none provided."""
        profile = CreatorProfile.objects.create(user=self.user)

        # Colors should be auto-assigned on save
        self.assertIsNotNone(profile.color_1)
        self.assertIsNotNone(profile.color_2)
        self.assertIsNotNone(profile.color_3)
        self.assertIsNotNone(profile.color_4)
        self.assertIsNotNone(profile.color_5)


class OnboardingTempDataTest(TestCase):
    """Tests for OnboardingTempData model."""

    def test_create_temp_data(self):
        """Test creating temporary onboarding data."""
        temp_data = OnboardingTempData.objects.create(
            session_id='test-session-123',
            business_data={'business_name': 'Test Business'},
            branding_data={'voice_tone': 'Professional'}
        )

        self.assertEqual(temp_data.session_id, 'test-session-123')
        self.assertEqual(temp_data.business_data['business_name'], 'Test Business')
        self.assertIsNotNone(temp_data.expires_at)

    def test_expiration_date_set_automatically(self):
        """Test that expiration date is set to 7 days from creation."""
        temp_data = OnboardingTempData.objects.create(
            session_id='test-session-456'
        )

        expected_expiry = timezone.now() + timedelta(days=7)
        # Allow 1 minute tolerance
        self.assertAlmostEqual(
            temp_data.expires_at.timestamp(),
            expected_expiry.timestamp(),
            delta=60
        )

    def test_get_all_data(self):
        """Test get_all_data method combines business and branding data."""
        temp_data = OnboardingTempData.objects.create(
            session_id='test-session-789',
            business_data={'business_name': 'Test', 'specialization': 'Tech'},
            branding_data={'voice_tone': 'Casual', 'color_1': '#FF0000'}
        )

        all_data = temp_data.get_all_data()

        self.assertEqual(all_data['business_name'], 'Test')
        self.assertEqual(all_data['specialization'], 'Tech')
        self.assertEqual(all_data['voice_tone'], 'Casual')
        self.assertEqual(all_data['color_1'], '#FF0000')


class OnboardingDataServiceTest(TestCase):
    """Tests for OnboardingDataService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_save_temp_data_creates_new(self):
        """Test saving temp data creates new record."""
        data = {
            'business_name': 'My Business',
            'specialization': 'Consulting',
            'voice_tone': 'Professional'
        }

        temp_data = OnboardingDataService.save_temp_data('session-new', data)

        self.assertEqual(temp_data.session_id, 'session-new')
        self.assertEqual(temp_data.business_data['business_name'], 'My Business')
        self.assertEqual(temp_data.branding_data['voice_tone'], 'Professional')

    def test_save_temp_data_updates_existing(self):
        """Test saving temp data updates existing record."""
        # Create initial data
        OnboardingDataService.save_temp_data('session-update', {
            'business_name': 'Initial Name'
        })

        # Update with new data
        temp_data = OnboardingDataService.save_temp_data('session-update', {
            'business_name': 'Updated Name',
            'specialization': 'New Spec'
        })

        self.assertEqual(temp_data.business_data['business_name'], 'Updated Name')
        self.assertEqual(temp_data.business_data['specialization'], 'New Spec')

    def test_get_temp_data_returns_valid(self):
        """Test get_temp_data returns valid data."""
        OnboardingDataService.save_temp_data('session-get', {
            'business_name': 'Test'
        })

        temp_data = OnboardingDataService.get_temp_data('session-get')

        self.assertIsNotNone(temp_data)
        self.assertEqual(temp_data.session_id, 'session-get')

    def test_get_temp_data_returns_none_for_expired(self):
        """Test get_temp_data returns None for expired data."""
        temp_data = OnboardingTempData.objects.create(
            session_id='session-expired',
            expires_at=timezone.now() - timedelta(days=1)
        )

        result = OnboardingDataService.get_temp_data('session-expired')

        self.assertIsNone(result)

    def test_get_temp_data_returns_none_for_missing(self):
        """Test get_temp_data returns None for missing session."""
        result = OnboardingDataService.get_temp_data('nonexistent-session')

        self.assertIsNone(result)

    def test_link_data_to_user_creates_profile(self):
        """Test linking data to user creates/updates profile."""
        # Create temp data
        OnboardingDataService.save_temp_data('session-link', {
            'business_name': 'Linked Business',
            'specialization': 'Tech',
            'business_description': 'A test business',
            'voice_tone': 'Professional'
        })

        # Create tracking records
        OnboardingStepTracking.objects.create(
            session_id='session-link',
            step_number=1,
            completed=True
        )

        # Link to user
        profile = OnboardingDataService.link_data_to_user(self.user, 'session-link')

        self.assertIsNotNone(profile)
        self.assertEqual(profile.business_name, 'Linked Business')
        self.assertEqual(profile.specialization, 'Tech')
        self.assertEqual(profile.voice_tone, 'Professional')

        # Verify tracking linked to user
        tracking = OnboardingStepTracking.objects.get(session_id='session-link')
        self.assertEqual(tracking.user, self.user)

        # Verify temp data deleted
        self.assertIsNone(OnboardingDataService.get_temp_data('session-link'))

    def test_link_data_to_user_returns_none_for_missing_session(self):
        """Test linking returns None when no session_id provided."""
        result = OnboardingDataService.link_data_to_user(self.user, None)
        self.assertIsNone(result)

    def test_link_data_to_user_returns_none_for_missing_data(self):
        """Test linking returns None when no temp data exists."""
        result = OnboardingDataService.link_data_to_user(self.user, 'nonexistent')
        self.assertIsNone(result)

    def test_cleanup_expired_data(self):
        """Test cleanup removes expired records."""
        # Create expired data
        OnboardingTempData.objects.create(
            session_id='expired-1',
            expires_at=timezone.now() - timedelta(days=1)
        )
        OnboardingTempData.objects.create(
            session_id='expired-2',
            expires_at=timezone.now() - timedelta(days=10)
        )
        # Create valid data
        OnboardingTempData.objects.create(
            session_id='valid-1',
            expires_at=timezone.now() + timedelta(days=5)
        )

        deleted_count = OnboardingDataService.cleanup_expired_data()

        self.assertEqual(deleted_count, 2)
        self.assertEqual(OnboardingTempData.objects.count(), 1)
        self.assertTrue(OnboardingTempData.objects.filter(session_id='valid-1').exists())


class OnboardingTempDataAPITest(APITestCase):
    """API tests for temporary onboarding data endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_save_temp_data_endpoint(self):
        """Test POST /onboarding/temp-data/ saves data."""
        response = self.client.post('/api/v1/creator-profile/onboarding/temp-data/', {
            'session_id': 'api-test-session',
            'business_name': 'API Test Business',
            'specialization': 'API Testing'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['session_id'], 'api-test-session')

        # Verify data was saved
        temp_data = OnboardingTempData.objects.get(session_id='api-test-session')
        self.assertEqual(temp_data.business_data['business_name'], 'API Test Business')

    def test_save_temp_data_requires_session_id(self):
        """Test POST /onboarding/temp-data/ requires session_id."""
        response = self.client.post('/api/v1/creator-profile/onboarding/temp-data/', {
            'business_name': 'Test'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_temp_data_endpoint(self):
        """Test GET /onboarding/temp-data/ retrieves data."""
        OnboardingDataService.save_temp_data('get-test-session', {
            'business_name': 'Get Test'
        })

        response = self.client.get(
            '/api/v1/creator-profile/onboarding/temp-data/',
            {'session_id': 'get-test-session'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_id'], 'get-test-session')
        self.assertEqual(response.data['business_data']['business_name'], 'Get Test')

    def test_get_temp_data_requires_session_id(self):
        """Test GET /onboarding/temp-data/ requires session_id param."""
        response = self.client.get('/api/v1/creator-profile/onboarding/temp-data/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_temp_data_returns_404_for_missing(self):
        """Test GET /onboarding/temp-data/ returns 404 for missing data."""
        response = self.client.get(
            '/api/v1/creator-profile/onboarding/temp-data/',
            {'session_id': 'nonexistent'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_link_data_endpoint_requires_auth(self):
        """Test POST /onboarding/link-data/ requires authentication."""
        response = self.client.post('/api/v1/creator-profile/onboarding/link-data/', {
            'session_id': 'test-session'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_link_data_endpoint_authenticated(self):
        """Test POST /onboarding/link-data/ works when authenticated."""
        # Create temp data
        OnboardingDataService.save_temp_data('auth-test-session', {
            'business_name': 'Auth Test',
            'specialization': 'Testing',
            'business_description': 'Test description'
        })

        # Authenticate
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/v1/creator-profile/onboarding/link-data/', {
            'session_id': 'auth-test-session'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

        # Verify profile was created
        profile = CreatorProfile.objects.get(user=self.user)
        self.assertEqual(profile.business_name, 'Auth Test')

    def test_link_data_endpoint_requires_session_id(self):
        """Test POST /onboarding/link-data/ requires session_id."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/v1/creator-profile/onboarding/link-data/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
