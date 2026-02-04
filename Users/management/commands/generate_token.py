from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import RefreshToken


class Command(BaseCommand):
    help = 'Generate JWT access and refresh tokens for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email address',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        user_id = options.get('user_id')

        if not email and not user_id:
            self.stdout.write(self.style.ERROR(
                'Please provide either --email or --user-id'
            ))
            return

        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(id=user_id)

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            self.stdout.write(self.style.SUCCESS(
                f'\nTokens generated for user: {user.email}\n'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'Access Token:\n{access_token}\n'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'Refresh Token:\n{refresh_token}\n'
            ))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'User not found with {"email" if email else "ID"}: {email or user_id}'
            ))
