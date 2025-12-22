from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Set up Google OAuth credentials in Django admin'

    def add_arguments(self, parser):
        parser.add_argument('client_id', type=str,
                            help='Google OAuth Client ID')
        parser.add_argument('client_secret', type=str,
                            help='Google OAuth Client Secret')

    def handle(self, *args, **options):
        client_id = options['client_id']
        client_secret = options['client_secret']

        # Get the default site
        site = Site.objects.get(pk=1)

        # Create or update Google OAuth app
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        if not created:
            google_app.client_id = client_id
            google_app.secret = client_secret
            google_app.save()
            self.stdout.write(
                self.style.SUCCESS('Updated existing Google OAuth app')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Created new Google OAuth app')
            )

        # Add site to the app
        google_app.sites.add(site)

        self.stdout.write(
            self.style.SUCCESS('Google OAuth app configured:')
        )
        self.stdout.write(f'- Provider: {google_app.provider}')
        self.stdout.write(f'- Client ID: {google_app.client_id}')
        self.stdout.write(f'- Secret: {"*" * len(google_app.secret)}')
        self.stdout.write(
            f'- Sites: {[s.domain for s in google_app.sites.all()]}')
