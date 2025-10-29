"""
Production settings for Sonora REST API project.
Settings specific to production environment.
"""

import dotenv
import os

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Load environment variables

dotenv.load_dotenv()

# Security settings for production
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        'SECRET_KEY environment variable must be set in production')

# Allowed hosts for production
ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS', 'postnow.com.br,www.postnow.com.br').split(',')

# Database configuration for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'ssl': {'ca': os.getenv('DB_SSL_CA')} if os.getenv('DB_SSL_CA') else None,
        },
    }
}

# Static files configuration for production
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security middleware for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'in-v3.mailjet.com'
EMAIL_HOST_USER = os.getenv('MJ_APIKEY_PUBLIC')
EMAIL_HOST_PASSWORD = os.getenv('MJ_APIKEY_PRIVATE')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

DEFAULT_FROM_EMAIL = os.getenv('SENDER_EMAIL', 'contato@postnow.com.br')
SERVER_EMAIL = os.getenv('SENDER_EMAIL', 'contato@postnow.com.br')
DEFAULT_FROM_NAME = os.getenv('SENDER_NAME', 'PostNow AI')

# CORS configuration for production
CORS_ALLOWED_ORIGINS = [
    "https://postnow.com.br",
    "https://www.postnow.com.br",
    "https://sonora-ui.vercel.app",
]

# Add additional CORS origins from environment variable
ADDITIONAL_CORS_ORIGINS = os.getenv('ADDITIONAL_CORS_ORIGINS', '')
if ADDITIONAL_CORS_ORIGINS:
    CORS_ALLOWED_ORIGINS.extend(ADDITIONAL_CORS_ORIGINS.split(','))

CORS_ALLOW_CREDENTIALS = True

# Stripe configuration for production
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Google OAuth credentials
GOOGLE_OAUTH2_CLIENT_ID = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')

# Mailjet API Configuration
MAILJET_API_KEY = os.getenv('MJ_APIKEY_PUBLIC')
MAILJET_SECRET_KEY = os.getenv('MJ_APIKEY_PRIVATE')

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_error.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
