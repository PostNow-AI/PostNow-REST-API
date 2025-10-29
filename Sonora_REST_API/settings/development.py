"""
Development settings for Sonora REST API project.
Settings specific to development environment.
"""

import os
from pathlib import Path

# Load environment variables from .env file
import dotenv

from .base import *

dotenv.load_dotenv()

# Override BASE_DIR for development if needed
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DB_NAME = os.getenv('DB_NAME', 'sonora_db')
DB_USER = os.getenv('DB_USER', 'sonora_user')
DB_PASSWORD = os.getenv('DB_USER_PASSWORD', 'sonora_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Static files configuration
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Allowed hosts for development
ALLOWED_HOSTS = ['*']

# Email configuration for development (console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Session configuration for development
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_SAVE_EVERY_REQUEST = False

# CORS configuration for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React Create App default
    "http://localhost:5173",  # Vite default
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://sonora-ui.vercel.app",  # Vercel frontend
    "https://sonoria-posts.vercel.app",  # Production domain
    "https://postnow.com.br",  # Production domain
    "https://www.postnow.com.br",
]

# Add additional CORS origins from environment variable
ADDITIONAL_CORS_ORIGINS = os.getenv('ADDITIONAL_CORS_ORIGINS', '')
if ADDITIONAL_CORS_ORIGINS:
    CORS_ALLOWED_ORIGINS.extend(ADDITIONAL_CORS_ORIGINS.split(','))

# Allow credentials to be included in CORS requests
CORS_ALLOW_CREDENTIALS = True

# Allow common headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Allow common methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# For development only - remove in production
CORS_ALLOW_ALL_ORIGINS = True

# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'IdeaBank.services.daily_content_service': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Update REST Auth for development
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"

# Stripe configuration for development
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Google OAuth credentials
GOOGLE_OAUTH2_CLIENT_ID = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')

# Mailjet API Configuration (for direct API usage if needed)
MAILJET_API_KEY = os.getenv('MJ_APIKEY_PUBLIC')
MAILJET_SECRET_KEY = os.getenv('MJ_APIKEY_PRIVATE')
