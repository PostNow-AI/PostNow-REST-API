"""
Instagram OAuth Service
Handles OAuth flow for Instagram Graph API authentication.
"""

import os
import secrets
from urllib.parse import urlencode

import requests
from AuditSystem.services import AuditService
from django.core.cache import cache


class InstagramOAuthService:
    """
    Service for handling Instagram OAuth 2.0 flow.
    Manages authorization URL generation, token exchange, and refresh.
    """

    def __init__(self):
        self.app_id = os.getenv('INSTAGRAM_APP_ID')
        self.app_secret = os.getenv('INSTAGRAM_APP_SECRET')
        self.redirect_uri = os.getenv(
            'INSTAGRAM_REDIRECT_URI',
            'http://localhost:8000/api/v1/social/instagram/callback/'
        )

        # Instagram Graph API URLs
        self.authorization_url = 'https://api.instagram.com/oauth/authorize'
        self.token_url = 'https://api.instagram.com/oauth/access_token'
        self.graph_api_url = 'https://graph.instagram.com'

        # Required scopes for Instagram Business accounts
        self.scopes = [
            'instagram_basic',
            'instagram_manage_insights',
            'pages_read_engagement',
        ]

    def get_authorization_url(self, user_id):
        """
        Generate Instagram OAuth authorization URL.

        Args:
            user_id: The user initiating the connection

        Returns:
            dict with authorization_url, state token, and expires_in
        """
        # Generate secure state token to prevent CSRF
        state = secrets.token_urlsafe(32)

        # Store state in cache for 10 minutes
        cache_key = f'instagram_oauth_state_{user_id}'
        cache.set(cache_key, state, timeout=600)

        # Build authorization URL
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'scope': ','.join(self.scopes),
            'response_type': 'code',
            'state': state,
        }

        auth_url = f"{self.authorization_url}?{urlencode(params)}"

        return {
            'authorization_url': auth_url,
            'state': state,
            'expires_in': 600,  # 10 minutes
        }

    def exchange_code_for_token(self, code, state, user):
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Instagram
            state: State token for CSRF protection
            user: Django User object

        Returns:
            dict with access_token, user_id, expires_in

        Raises:
            ValueError: If state token is invalid or exchange fails
        """
        # Validate state token
        cache_key = f'instagram_oauth_state_{user.id}'
        cached_state = cache.get(cache_key)

        if not cached_state or cached_state != state:
            AuditService.log_generic(
                user=user,
                action='instagram_oauth_invalid_state',
                status='error',
                details={'error': 'Invalid state token'}
            )
            raise ValueError(
                "Estado inválido. Por favor, tente conectar novamente.")

        # Clear state from cache
        cache.delete(cache_key)

        # Exchange code for short-lived token
        try:
            response = requests.post(
                self.token_url,
                data={
                    'client_id': self.app_id,
                    'client_secret': self.app_secret,
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.redirect_uri,
                    'code': code,
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            if 'error_type' in data:
                raise ValueError(
                    f"Erro do Instagram: {data.get('error_message', 'Unknown error')}")

            short_lived_token = data.get('access_token')
            instagram_user_id = data.get('user_id')

            # Exchange short-lived token for long-lived token (60 days)
            long_lived_data = self._get_long_lived_token(short_lived_token)

            AuditService.log_generic(
                user=user,
                action='instagram_oauth_success',
                status='success',
                details={'instagram_user_id': instagram_user_id}
            )

            return {
                'access_token': long_lived_data['access_token'],
                'token_type': long_lived_data.get('token_type', 'Bearer'),
                # 60 days
                'expires_in': long_lived_data.get('expires_in', 5184000),
                'instagram_user_id': instagram_user_id,
            }

        except requests.exceptions.RequestException as e:
            AuditService.log_generic(
                user=user,
                action='instagram_oauth_error',
                status='error',
                details={'error': str(e)}
            )
            raise ValueError(f"Erro ao conectar com Instagram: {str(e)}")

    def _get_long_lived_token(self, short_lived_token):
        """
        Exchange short-lived token for long-lived token (60 days).

        Args:
            short_lived_token: The short-lived access token

        Returns:
            dict with access_token, token_type, expires_in
        """
        url = f"{self.graph_api_url}/access_token"

        response = requests.get(
            url,
            params={
                'grant_type': 'ig_exchange_token',
                'client_secret': self.app_secret,
                'access_token': short_lived_token,
            },
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, current_token):
        """
        Refresh a long-lived token before it expires.

        Args:
            current_token: Current access token to refresh

        Returns:
            dict with new access_token, token_type, expires_in
        """
        url = f"{self.graph_api_url}/refresh_access_token"

        try:
            response = requests.get(
                url,
                params={
                    'grant_type': 'ig_refresh_token',
                    'access_token': current_token,
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            return {
                'access_token': data.get('access_token'),
                'token_type': data.get('token_type', 'Bearer'),
                'expires_in': data.get('expires_in', 5184000),  # 60 days
            }

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Erro ao renovar token: {str(e)}")

    def validate_business_account(self, access_token, instagram_user_id):
        """
        Validate that the Instagram account is a Business or Creator account.

        Args:
            access_token: Instagram access token
            instagram_user_id: Instagram user ID

        Returns:
            dict with account info (account_type, username, etc.)

        Raises:
            ValueError: If account is not Business/Creator
        """
        url = f"{self.graph_api_url}/{instagram_user_id}"

        try:
            response = requests.get(
                url,
                params={
                    'fields': 'id,username,account_type,profile_picture_url',
                    'access_token': access_token,
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            account_type = data.get('account_type', 'PERSONAL')

            if account_type == 'PERSONAL':
                raise ValueError(
                    "Sua conta Instagram precisa ser Business ou Creator. "
                    "Veja como converter: /docs/instagram-business-setup"
                )

            return {
                'account_type': account_type,
                'username': data.get('username'),
                'profile_picture_url': data.get('profile_picture_url'),
                'instagram_user_id': data.get('id'),
            }

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Erro ao validar conta: {str(e)}")
