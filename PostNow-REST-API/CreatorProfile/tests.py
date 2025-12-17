from django.contrib.auth.models import User
from django.test import TestCase

from .models import CreatorProfile


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
            profession="Developer",
            whatsapp_number="11999999999",  # Required for step 1
            business_name="Test Business",
            specialization="Web Development",
            business_city="São Paulo",
            business_description="A test business description that is long enough to pass validation.",
            target_gender="Todos",
            target_age_range="25-34 anos",
            target_location="São Paulo",
            voice_tone="Profissional"
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
            specialization=""
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

        # Profile with only step 1 data
        profile.professional_name = "Test User"
        profile.profession = "Developer"
        profile.whatsapp_number = "11999999999"
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
            professional_name="Test User",
            profession="Developer",
            whatsapp_number="11999999999",
            business_name="Test Business",
            specialization="Web Development",
            business_city="São Paulo",
            business_description="A complete business description that meets all requirements.",
            target_gender="Todos",
            target_age_range="25-34 anos",
            target_location="São Paulo",
            voice_tone="Profissional"
        )
        profile.save()

        # Should be completed
        self.assertTrue(profile.onboarding_completed)
        self.assertIsNotNone(profile.onboarding_completed_at)

        # Clear data
        profile.professional_name = ""
        profile.profession = ""
        profile.whatsapp_number = ""
        profile.business_name = ""
        profile.specialization = ""
        profile.business_city = ""
        profile.business_description = ""
        profile.target_gender = ""
        profile.target_age_range = ""
        profile.target_location = ""
        profile.voice_tone = ""
        profile.save()

        # Should not be completed
        self.assertFalse(profile.onboarding_completed)
        self.assertIsNone(profile.onboarding_completed_at)

    def test_step_completion_logic(self):
        """Test that step completion logic works correctly with target demographic fields."""
        profile = CreatorProfile.objects.create(user=self.user)

        # Step 1 completion
        profile.professional_name = "Test User"
        profile.profession = "Developer"
        profile.whatsapp_number = "11999999999"
        profile.save()
        self.assertTrue(profile.step_1_completed)
        self.assertFalse(profile.step_2_completed)
        self.assertEqual(profile.current_step, 2)

        # Step 2 completion with target demographics
        profile.business_name = "Test Business"
        profile.specialization = "Web Development"
        profile.business_city = "São Paulo"
        profile.business_description = "A comprehensive business description that meets the minimum length requirements."
        profile.target_gender = "Todos"
        profile.target_age_range = "25-34 anos"
        profile.target_location = "São Paulo"
        profile.save()
        self.assertTrue(profile.step_1_completed)
        self.assertTrue(profile.step_2_completed)
        self.assertFalse(profile.step_3_completed)
        self.assertEqual(profile.current_step, 3)

        # Step 3 completion
        profile.voice_tone = "Profissional"
        profile.save()
        self.assertTrue(profile.step_1_completed)
        self.assertTrue(profile.step_2_completed)
        self.assertTrue(profile.step_3_completed)
        self.assertTrue(profile.onboarding_completed)
        self.assertEqual(profile.current_step, 4)  # All steps completed

    def test_target_demographic_fields_validation(self):
        """Test that target demographic fields are properly validated."""
        profile = CreatorProfile.objects.create(
            user=self.user,
            professional_name="Test User",
            profession="Developer",
            whatsapp_number="11999999999",
            business_name="Test Business",
            specialization="Web Development",
            business_city="São Paulo",
            business_description="A comprehensive business description.",
            # Missing target demographic fields
            voice_tone="Profissional"
        )
        profile.save()

        # Should complete step 1 but not step 2 due to missing target demographics
        self.assertTrue(profile.step_1_completed)
        self.assertFalse(profile.step_2_completed)
        self.assertEqual(profile.current_step, 2)

        # Add target demographics
        profile.target_gender = "Feminino"
        profile.target_age_range = "25-34 anos"
        profile.target_location = "Rio de Janeiro"
        profile.save()

        # Now step 2 should be completed and onboarding should be complete
        self.assertTrue(profile.step_1_completed)
        self.assertTrue(profile.step_2_completed)
        self.assertTrue(profile.step_3_completed)
        self.assertTrue(profile.onboarding_completed)
        self.assertEqual(profile.current_step, 4)  # All steps completed
