"""
Django settings for Sonora_REST_API project.
This file imports settings based on the environment.
"""

import os

# Determine the environment
ENVIRONMENT = os.getenv('DJANGO_ENV', 'development')

if ENVIRONMENT == 'production':
    from .settings.production import *
elif ENVIRONMENT == 'staging':
    from .settings.staging import *
else:
    from .settings.development import *
