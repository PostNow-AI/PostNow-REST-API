import os

from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Debug Google OAuth configuration'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Google OAuth Debug Information ===')
        )

        # Check environment variables
        self.stdout.write('\n1. Environment Variables:')
        client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')

        self.stdout.write(
            f'   GOOGLE_OAUTH2_CLIENT_ID: {client_id[:20]}...' if client_id else '   GOOGLE_OAUTH2_CLIENT_ID: Not set')
        self.stdout.write(
            f'   GOOGLE_OAUTH2_CLIENT_SECRET: {"*" * 20}' if client_secret else '   GOOGLE_OAUTH2_CLIENT_SECRET: Not set')

        # Check Django settings
        self.stdout.write('\n2. Django Settings:')
        self.stdout.write(
            f'   SITE_ID: {getattr(settings, "SITE_ID", "Not set")}')
        self.stdout.write(f'   DEBUG: {getattr(settings, "DEBUG", "Not set")}')

        # Check Sites
        self.stdout.write('\n3. Sites Configuration:')
        sites = Site.objects.all()
        for site in sites:
            self.stdout.write(
                f'   Site {site.id}: {site.domain} ({site.name})')

        # Check SocialApps
        self.stdout.write('\n4. Social Applications:')
        social_apps = SocialApp.objects.all()
        if social_apps:
            for app in social_apps:
                self.stdout.write(f'   Provider: {app.provider}')
                self.stdout.write(f'   Name: {app.name}')
                self.stdout.write(f'   Client ID: {app.client_id}')
                self.stdout.write(f'   Secret: {"*" * len(app.secret)}')
                self.stdout.write(
                    f'   Sites: {[s.domain for s in app.sites.all()]}')
                self.stdout.write('   ---')
        else:
            self.stdout.write('   No social applications configured')

        # Check URLs that should be configured in Google Console
        self.stdout.write('\n5. URLs to Configure in Google Cloud Console:')
        self.stdout.write('   Authorized redirect URIs:')
        self.stdout.write(
            '   - http://localhost:8000/api/v1/auth/google/callback/')
        self.stdout.write(
            '   - http://127.0.0.1:8000/api/v1/auth/google/callback/')
        self.stdout.write('')
        self.stdout.write('   Authorized JavaScript origins:')
        self.stdout.write('   - http://localhost:5173')
        self.stdout.write('   - http://127.0.0.1:5173')
        self.stdout.write('   - http://localhost:8000')
        self.stdout.write('   - http://127.0.0.1:8000')

        self.stdout.write(
            self.style.SUCCESS('\n=== End Debug Information ===')
        )
