from django.contrib.auth.models import User
from django.test import TestCase

from .models import CreatorProfile
from .services import CreatorProfileService


class CreatorProfileOnboardingTest(TestCase):
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
            professional_name="Test Professional",
            profession="Developer"
        )

        # Save should mark as completed
        profile.save()
        self.assertTrue(profile.onboarding_completed)
        self.assertIsNotNone(profile.onboarding_completed_at)

    def test_profile_with_empty_strings_onboarding_not_completed(self):
        """Test that profiles with empty strings are not marked as completed."""
        profile = CreatorProfile.objects.create(
            user=self.user,
            professional_name="",
            profession="   ",
            specialization=None
        )

        # Save should not mark as completed
        profile.save()
        self.assertFalse(profile.onboarding_completed)
        self.assertIsNone(profile.onboarding_completed_at)

    def test_onboarding_status_calculation(self):
        """Test that onboarding status is calculated correctly."""
        profile = CreatorProfile.objects.create(user=self.user)

        # Empty profile
        status = CreatorProfileService.calculate_onboarding_status(profile)
        self.assertFalse(status['onboarding_completed'])
        self.assertEqual(status['filled_fields_count'], 0)
        self.assertFalse(status['has_data'])

        # Profile with data
        profile.professional_name = "Test User"
        profile.profession = "Developer"
        profile.save()

        status = CreatorProfileService.calculate_onboarding_status(profile)
        self.assertTrue(status['onboarding_completed'])
        self.assertEqual(status['filled_fields_count'], 2)
        self.assertTrue(status['has_data'])

    def test_profile_reset_onboarding_status(self):
        """Test that removing all data resets onboarding status."""
        profile = CreatorProfile.objects.create(
            user=self.user,
            professional_name="Test User",
            profession="Developer"
        )
        profile.save()

        # Should be completed
        self.assertTrue(profile.onboarding_completed)
        self.assertIsNotNone(profile.onboarding_completed_at)

        # Clear data
        profile.professional_name = ""
        profile.profession = ""
        profile.save()

        # Should not be completed
        self.assertFalse(profile.onboarding_completed)
        self.assertIsNone(profile.onboarding_completed_at)
