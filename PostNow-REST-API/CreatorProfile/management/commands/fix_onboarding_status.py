from CreatorProfile.models import CreatorProfile
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fix onboarding status for existing creator profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY RUN MODE - No changes will be made'))

        profiles = CreatorProfile.objects.all()
        fixed_count = 0

        for profile in profiles:
            # Check if profile actually has data
            has_data = any([
                # Step 1 fields
                profile.professional_name and str(
                    profile.professional_name).strip(),
                profile.profession and str(profile.profession).strip(),
                profile.instagram_handle and str(
                    profile.instagram_handle).strip(),
                profile.whatsapp_number and str(
                    profile.whatsapp_number).strip(),

                # Step 2 fields
                profile.business_name and str(profile.business_name).strip(),
                profile.specialization and str(profile.specialization).strip(),
                profile.business_instagram_handle and str(
                    profile.business_instagram_handle).strip(),
                profile.business_website and str(
                    profile.business_website).strip(),
                profile.business_city and str(profile.business_city).strip(),
                profile.business_description and str(
                    profile.business_description).strip(),
                profile.target_gender and str(profile.target_gender).strip(),
                profile.target_age_range and str(
                    profile.target_age_range).strip(),
                profile.target_interests and str(
                    profile.target_interests).strip(),
                profile.target_location and str(
                    profile.target_location).strip(),

                # Step 3 fields
                profile.voice_tone and str(profile.voice_tone).strip(),
                profile.color_1 and str(profile.color_1).strip(),
                profile.color_2 and str(profile.color_2).strip(),
                profile.color_3 and str(profile.color_3).strip(),
                profile.color_4 and str(profile.color_4).strip(),
                profile.color_5 and str(profile.color_5).strip(),
            ])

            # Check if status needs fixing
            needs_fixing = False
            if has_data and not profile.onboarding_completed:
                needs_fixing = True
                if not dry_run:
                    profile.onboarding_completed = True
                    if not profile.onboarding_completed_at:
                        from django.utils import timezone
                        profile.onboarding_completed_at = timezone.now()
                    profile.save()
                    self.stdout.write(
                        f'Fixed profile {profile.id}: marked as completed')
                else:
                    self.stdout.write(
                        f'Would fix profile {profile.id}: mark as completed')

            elif not has_data and profile.onboarding_completed:
                needs_fixing = True
                if not dry_run:
                    profile.onboarding_completed = False
                    profile.onboarding_completed_at = None
                    profile.save()
                    self.stdout.write(
                        f'Fixed profile {profile.id}: marked as not completed')
                else:
                    self.stdout.write(
                        f'Would fix profile {profile.id}: mark as not completed')

            if needs_fixing:
                fixed_count += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would fix {fixed_count} profiles')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully fixed {fixed_count} profiles')
            )
