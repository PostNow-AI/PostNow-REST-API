"""
Custom exception classes for better error handling and consistent error responses.
"""

from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """
    Base exception class for API errors.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        errors: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__.upper()
        self.errors = errors or {}
        self.extra_data = kwargs

        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """Exception for validation errors."""

    def __init__(self, message: str = "Validation failed", errors: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, 400, "VALIDATION_ERROR", errors, **kwargs)


class AuthenticationError(BaseAPIException):
    """Exception for authentication errors."""

    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(message, 401, "AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(BaseAPIException):
    """Exception for authorization errors."""

    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(message, 403, "AUTHORIZATION_ERROR", **kwargs)


class NotFoundError(BaseAPIException):
    """Exception for resource not found errors."""

    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message, 404, "NOT_FOUND_ERROR", **kwargs)


class ConflictError(BaseAPIException):
    """Exception for resource conflict errors."""

    def __init__(self, message: str = "Resource conflict", **kwargs):
        super().__init__(message, 409, "CONFLICT_ERROR", **kwargs)


class BusinessRuleError(BaseAPIException):
    """Exception for business rule violations."""

    def __init__(self, message: str = "Business rule violation", **kwargs):
        super().__init__(message, 422, "BUSINESS_RULE_ERROR", **kwargs)


class ExternalServiceError(BaseAPIException):
    """Exception for external service errors."""

    def __init__(self, message: str = "External service error", **kwargs):
        super().__init__(message, 502, "EXTERNAL_SERVICE_ERROR", **kwargs)


class CreditInsufficientError(BusinessRuleError):
    """Exception for insufficient credit errors."""

    def __init__(self, required_credits: float, current_balance: float, **kwargs):
        message = f"Créditos insuficientes. Necessário: {required_credits}, Saldo atual: {current_balance}"
        super().__init__(message, **kwargs)
        self.required_credits = required_credits
        self.current_balance = current_balance


class SubscriptionRequiredError(AuthorizationError):
    """Exception for subscription required errors."""

    def __init__(self, message: str = "Assinatura necessária para esta funcionalidade", **kwargs):
        super().__init__(message, **kwargs)


class RateLimitError(BaseAPIException):
    """Exception for rate limiting errors."""

    def __init__(self, message: str = "Muitas requisições. Tente novamente mais tarde.", **kwargs):
        super().__init__(message, 429, "RATE_LIMIT_ERROR", **kwargs)
