import time
import uuid
from typing import Any, Dict, Optional

from django.contrib.auth.models import User
from django.http import HttpRequest

from .models import AuditLog


class AuditService:
    """Service for logging audit events throughout the system"""

    @staticmethod
    def log_operation(
        user: Optional[User],
        operation_category: str,
        action: str,
        status: str = 'success',
        resource_type: str = '',
        resource_id: str = '',
        details: Optional[Dict[str, Any]] = None,
        error_message: str = '',
        request: Optional[HttpRequest] = None,
        duration_ms: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit operation.

        Args:
            user: User who performed the action (can be None for anonymous)
            operation_category: Category of operation (auth, account, profile, etc.)
            action: Specific action performed
            status: Operation status (success, failure, error, pending)
            resource_type: Type of resource affected
            resource_id: ID of affected resource
            details: Additional operation details
            error_message: Error message if operation failed
            request: Django request object for IP/user agent extraction
            duration_ms: Operation duration in milliseconds
            request_id: Unique request identifier

        Returns:
            Created AuditLog instance
        """
        # Extract request information if available
        ip_address = None
        user_agent = ''

        if request:
            # Get IP address (handle X-Forwarded-For for proxies)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Generate request ID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())

        # Prepare details dict
        if details is None:
            details = {}

        # Create audit log entry
        audit_log = AuditLog.objects.create(
            user=user,
            operation_category=operation_category,
            action=action,
            status=status,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            error_message=error_message,
            duration_ms=duration_ms,
            request_id=request_id
        )

        return audit_log

    @staticmethod
    def log_system_operation(
        user: Optional[User],
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log system-related operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='system',
            action=action,
            status=status,
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_auth_operation(
        user: Optional[User],
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log authentication-related operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='auth',
            action=action,
            status=status,
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_account_operation(
        user: Optional[User],
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log account management operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='account',
            action=action,
            status=status,
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_profile_operation(
        user: User,
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log creator profile operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='profile',
            action=action,
            status=status,
            resource_type='CreatorProfile',
            resource_id=str(user.id),
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_post_operation(
        user: User,
        action: str,
        post_id: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log post operations (create, update, delete)"""
        return AuditService.log_operation(
            user=user,
            operation_category='post',
            action=action,
            status=status,
            resource_type='Post',
            resource_id=post_id,
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_content_generation(
        user: User,
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log content generation operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='content',
            action=action,
            status=status,
            resource_type='ContentGeneration',
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_daily_content_generation(
        user: User,
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log content generation operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='content',
            action=action,
            status=status,
            resource_type='DailyGeneration',
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_image_generation(
        user: User,
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log content generation operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='image',
            action=action,
            status=status,
            resource_type='ImageGeneration',
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_subscription_operation(
        user: User,
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log subscription system operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='subscription',
            action=action,
            status=status,
            resource_type='Subscription',
            request=request,
            error_message=error_message,
            **kwargs
        )

    @staticmethod
    def log_email_operation(
        user: Optional[User],
        action: str,
        status: str = 'success',
        request: Optional[HttpRequest] = None,
        error_message: str = '',
        **kwargs
    ) -> AuditLog:
        """Log email operations"""
        return AuditService.log_operation(
            user=user,
            operation_category='email',
            action=action,
            status=status,
            resource_type='Email',
            request=request,
            error_message=error_message,
            **kwargs
        )


class AuditTimer:
    """Context manager for timing operations and automatically logging them"""

    def __init__(self, audit_service_method, *args, **kwargs):
        self.audit_service_method = audit_service_method
        self.args = args
        self.kwargs = kwargs
        self.start_time = None
        self.audit_log = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration_ms = int((end_time - self.start_time) * 1000)

        # Update kwargs with duration
        self.kwargs['duration_ms'] = duration_ms

        # If there was an exception, log it as failure
        if exc_type is not None:
            self.kwargs['status'] = 'error'
            self.kwargs['error_message'] = str(
                exc_val) if exc_val else f"{exc_type.__name__} occurred"

        # Log the operation
        self.audit_log = self.audit_service_method(*self.args, **self.kwargs)

        return False  # Don't suppress the exception
