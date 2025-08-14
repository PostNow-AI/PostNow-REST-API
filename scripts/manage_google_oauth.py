#!/usr/bin/env python
"""
Script to set up Google OAuth credentials in Django admin
Run this after creating your Google OAuth app in Google Cloud Console
"""

import os
import sys

import django
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Setup Django BEFORE importing Django models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
django.setup()

# Import Django models AFTER setup


def setup_google_oauth(client_id, client_secret):
    """
    Set up Google OAuth application in Django
    """
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
        print("Updated existing Google OAuth app")
    else:
        print("Created new Google OAuth app")

    # Add site to the app
    google_app.sites.add(site)

    print("Google OAuth app configured:")
    print(f"- Provider: {google_app.provider}")
    print(f"- Client ID: {google_app.client_id}")
    print(f"- Secret: {'*' * len(google_app.secret)}")
    print(f"- Sites: {[s.domain for s in google_app.sites.all()]}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python manage_google_oauth.py <client_id> <client_secret>")
        print("\nTo get these credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google+ API")
        print("4. Go to Credentials > Create Credentials > OAuth 2.0")
        print("5. Add authorized redirect URIs:")
        print("   - http://localhost:8000/api/v1/auth/google/callback/")
        print("   - http://127.0.0.1:8000/api/v1/auth/google/callback/")
        sys.exit(1)

    client_id = sys.argv[1]
    client_secret = sys.argv[2]

    setup_google_oauth(client_id, client_secret)
