"""
Management command to refresh expiring Instagram tokens.
Should be run daily via cron job.

Usage:
    python manage.py refresh_instagram_tokens
"""

from AuditSystem.services import AuditService
from django.core.management.base import BaseCommand

from SocialMediaIntegration.services.token_refresh_service import TokenRefreshService


class Command(BaseCommand):
    help = 'Refresh expiring Instagram access tokens and notify users'

    def handle(self, *args, **options):
        """Execute the command"""
        self.stdout.write(self.style.WARNING(
            'Starting Instagram token refresh...'))

        try:
            # Run token refresh check
            results = TokenRefreshService.check_and_notify_expiring_tokens()

            # Log results
            self.stdout.write(self.style.SUCCESS(
                f"✓ Checked: {results['checked']} accounts"
            ))
            self.stdout.write(self.style.SUCCESS(
                f"✓ Refreshed: {results['refreshed']} tokens"
            ))
            self.stdout.write(self.style.WARNING(
                f"⚠ Notified: {results['notified']} users about expiring tokens"
            ))

            # Audit log
            AuditService.log_generic(
                user=None,
                action='instagram_token_refresh_cron',
                status='success',
                details=results
            )

            self.stdout.write(self.style.SUCCESS(
                'Instagram token refresh completed'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

            # Audit log error
            AuditService.log_generic(
                user=None,
                action='instagram_token_refresh_cron',
                status='error',
                details={'error': str(e)}
            )

            return
