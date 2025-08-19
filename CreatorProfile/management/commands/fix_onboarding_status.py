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
                profile.professional_name and str(
                    profile.professional_name).strip(),
                profile.profession and str(profile.profession).strip(),
                profile.specialization and str(profile.specialization).strip(),
                profile.linkedin_url and str(profile.linkedin_url).strip(),
                profile.instagram_username and str(
                    profile.instagram_username).strip(),
                profile.youtube_channel and str(
                    profile.youtube_channel).strip(),
                profile.tiktok_username and str(
                    profile.tiktok_username).strip(),
                profile.primary_color and str(profile.primary_color).strip(),
                profile.secondary_color and str(
                    profile.secondary_color).strip(),
                profile.accent_color_1 and str(profile.accent_color_1).strip(),
                profile.accent_color_2 and str(profile.accent_color_2).strip(),
                profile.accent_color_3 and str(profile.accent_color_3).strip(),
                profile.primary_font and str(profile.primary_font).strip(),
                profile.secondary_font and str(profile.secondary_font).strip(),
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
