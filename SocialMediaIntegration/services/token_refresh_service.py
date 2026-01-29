"""
Token Refresh Service
Handles automatic token refresh for Instagram accounts before expiration.
"""

from datetime import timedelta
from functools import wraps

from AuditSystem.services import AuditService
from django.utils import timezone

from SocialMediaIntegration.models import InstagramAccount
from SocialMediaIntegration.services.instagram_oauth_service import (
    InstagramOAuthService,
)
from SocialMediaIntegration.services.notification_service import (
    InstagramNotificationService,
)
from SocialMediaIntegration.utils.encryption import decrypt_token, encrypt_token


class TokenRefreshService:
    """
    Service for managing Instagram token refresh.
    Ensures tokens are valid before API calls and auto-refreshes expiring tokens.
    """

    @staticmethod
    def refresh_token_if_needed(account):
        """
        Check if token needs refresh and refresh it if necessary.

        Args:
            account: InstagramAccount object

        Returns:
            bool: True if token was refreshed, False otherwise
        """
        # Check if token is expiring soon (< 7 days)
        if not account.is_token_expiring_soon(days=7):
            return False

        try:
            # Decrypt current token
            current_token = decrypt_token(account.access_token)

            # Refresh token
            oauth_service = InstagramOAuthService()
            token_data = oauth_service.refresh_access_token(current_token)

            # Update account with new token
            account.access_token = encrypt_token(token_data['access_token'])
            account.token_type = token_data.get('token_type', 'Bearer')

            # Set new expiration (60 days from now)
            expires_in_seconds = token_data.get('expires_in', 5184000)
            account.expires_at = timezone.now() + timedelta(seconds=expires_in_seconds)

            account.connection_status = 'connected'
            account.sync_error_message = None
            account.save(update_fields=[
                'access_token',
                'token_type',
                'expires_at',
                'connection_status',
                'sync_error_message',
                'updated_at'
            ])

            # Log success
            AuditService.log_generic(
                user=account.user,
                action='instagram_token_refreshed',
                status='success',
                details={'instagram_username': account.username}
            )

            return True

        except Exception as e:
            # Log error
            AuditService.log_generic(
                user=account.user,
                action='instagram_token_refresh_failed',
                status='error',
                details={
                    'instagram_username': account.username,
                    'error': str(e)
                }
            )

            # Update account status
            account.connection_status = 'error'
            account.sync_error_message = f"Erro ao renovar token: {str(e)}"
            account.save(update_fields=[
                         'connection_status', 'sync_error_message', 'updated_at'])

            # Notify user
            InstagramNotificationService.notify_sync_error(
                user=account.user,
                instagram_username=account.username,
                error_type='invalid_token'
            )

            return False

    @staticmethod
    def check_and_notify_expiring_tokens():
        """
        Check all accounts for expiring tokens and send notifications.
        This should be run daily as a background task.

        Returns:
            dict with counts of checked, refreshed, and notified accounts
        """
        # Get accounts expiring in 7 days or less
        threshold_date = timezone.now() + timedelta(days=7)
        expiring_accounts = InstagramAccount.objects.filter(
            is_active=True,
            expires_at__lte=threshold_date,
            expires_at__gt=timezone.now()
        )

        refreshed_count = 0
        notified_count = 0

        for account in expiring_accounts:
            # Try to refresh token
            was_refreshed = TokenRefreshService.refresh_token_if_needed(
                account)

            if was_refreshed:
                refreshed_count += 1
            else:
                # If refresh failed, notify user
                days_left = account.days_until_expiration()
                if days_left is not None and days_left <= 7:
                    InstagramNotificationService.notify_token_expiring(
                        user=account.user,
                        instagram_username=account.username,
                        days_left=days_left
                    )
                    notified_count += 1

        return {
            'checked': expiring_accounts.count(),
            'refreshed': refreshed_count,
            'notified': notified_count
        }

    @staticmethod
    def get_valid_token(account):
        """
        Get a valid token for an account, refreshing if necessary.

        Args:
            account: InstagramAccount object

        Returns:
            str: Decrypted access token

        Raises:
            ValueError: If token is invalid or refresh fails
        """
        # Check if token is expired
        if account.expires_at and account.expires_at <= timezone.now():
            account.connection_status = 'token_expired'
            account.save(update_fields=['connection_status'])
            raise ValueError(
                "Token expirado. Reconecte sua conta do Instagram.")

        # Try to refresh if expiring soon
        TokenRefreshService.refresh_token_if_needed(account)

        # Return decrypted token
        return decrypt_token(account.access_token)


def ensure_valid_token(func):
    """
    Decorator to ensure Instagram account has a valid token before making API calls.

    Usage:
        @ensure_valid_token
        def sync_account_data(account):
            token = decrypt_token(account.access_token)
            # Make API calls with token
    """
    @wraps(func)
    def wrapper(account, *args, **kwargs):
        try:
            # Ensure token is valid
            TokenRefreshService.get_valid_token(account)
            return func(account, *args, **kwargs)
        except ValueError as e:
            # Update account status
            account.connection_status = 'error'
            account.sync_error_message = str(e)
            account.save(update_fields=[
                         'connection_status', 'sync_error_message'])
            raise

    return wrapper
