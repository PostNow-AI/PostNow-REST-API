"""Pytest configuration for CreditSystem tests."""

import os
import django

# Configure Django settings before importing any Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
