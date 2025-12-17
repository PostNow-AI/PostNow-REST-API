import time

from allauth.account.signals import user_signed_up
from django.contrib.auth.models import User
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.deprecation import MiddlewareMixin

from .services import AuditService


class AuditMiddleware(MiddlewareMixin):
    """Middleware to automatically log important system operations"""

    def __init__(self, get_response):
        super().__init__(get_response)
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up signal handlers for automatic audit logging"""

        # Authentication signals
        user_logged_in.connect(self._handle_user_logged_in)
        user_logged_out.connect(self._handle_user_logged_out)
        user_login_failed.connect(self._handle_user_login_failed)
        user_signed_up.connect(self._handle_user_signed_up)

        # Model signals for key entities
        # Note: These will be connected when the models are ready
        # We'll handle them in the views/services instead for now

    def _handle_user_logged_in(self, sender, request, user, **kwargs):
        """Handle successful user login"""
        AuditService.log_auth_operation(
            user=user,
            action='login',
            status='success',
            request=request,
            details={'login_method': 'django_auth'}
        )

    def _handle_user_logged_out(self, sender, request, user, **kwargs):
        """Handle user logout"""
        AuditService.log_auth_operation(
            user=user,
            action='logout',
            status='success',
            request=request
        )

    def _handle_user_login_failed(self, sender, credentials, **kwargs):
        """Handle failed login attempts"""
        # Try to get username from credentials
        username = credentials.get('username', 'unknown')
        AuditService.log_auth_operation(
            user=None,
            action='login_failed',
            status='failure',
            details={'attempted_username': username},
            error_message='Invalid login credentials'
        )

    def _handle_user_signed_up(self, sender, request, user, **kwargs):
        """Handle user registration"""
        AuditService.log_account_operation(
            user=user,
            action='account_created',
            status='success',
            request=request,
            details={'signup_method': 'allauth'}
        )

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process view to capture timing and other metrics"""
        # Store start time for potential timing measurements
        request._audit_start_time = time.time()
        request._audit_request_id = None  # Will be set by individual views if needed

        return None

    def process_exception(self, request, exception):
        """Log exceptions that occur during request processing"""
        # Only log if we have a user (authenticated requests)
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            AuditService.log_system_operation(
                action='system_error',
                status='error',
                user=user,
                request=request,
                error_message=str(exception),
                details={
                    'view': request.resolver_match.view_name if request.resolver_match else 'unknown',
                    'method': request.method,
                    'path': request.path,
                    'exception_type': type(exception).__name__
                }
            )


# Signal handlers for model operations
# These will be imported and connected in the app's ready() method

@receiver(post_save, sender=User)
def audit_user_save(sender, instance, created, **kwargs):
    """Audit user model saves"""
    if created:
        # User creation is already handled by user_signed_up signal
        return

    # User updates - only log if important fields changed
    # This is a simplified version; in production you might want to track specific field changes
    AuditService.log_account_operation(
        user=instance,
        action='account_updated',
        status='success',
        details={'updated_fields': ['basic_info']}  # Simplified
    )
