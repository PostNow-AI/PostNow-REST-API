import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

from core.exceptions import BaseAPIException

logger = logging.getLogger(__name__)


def unified_exception_handler(exc, context):
    """
    Custom exception handler that provides unified error response format.

    Format: {
        "success": false,
        "code": "ERROR_CODE",
        "message": "Human readable error message",
        "errors": {}  # Detailed error information
    }
    """

    # Handle custom API exceptions first
    if isinstance(exc, BaseAPIException):
        return _handle_custom_api_exception(exc)

    # Get the standard DRF exception handler response
    response = exception_handler(exc, context)

    if response is not None:
        # DRF handled the exception, format it to our unified format
        return _format_drf_exception_response(exc, response)
    else:
        # DRF didn't handle the exception, handle it ourselves
        return _handle_unhandled_exception(exc, context)


def _handle_custom_api_exception(exc: BaseAPIException) -> JsonResponse:
    """
    Handle custom API exceptions with unified format.
    """
    response_data = {
        "success": False,
        "code": exc.error_code,
        "message": exc.message,
        "errors": exc.errors,
    }

    # Add any extra data from the exception
    if exc.extra_data:
        response_data.update(exc.extra_data)

    return JsonResponse(response_data, status=exc.status_code)


def _format_drf_exception_response(exc, response):
    """
    Format DRF exception responses to unified format
    """
    data = response.data
    status_code = response.status_code

    # Initialize unified response
    unified_response = {
        "success": False,
        "code": _get_error_code(exc, status_code),
        "message": _get_main_error_message(exc, data),
        "errors": _extract_error_details(data)
    }

    return JsonResponse(unified_response, status=status_code)


def _handle_unhandled_exception(exc, context):
    """
    Handle exceptions that DRF doesn't handle by default
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Default to internal server error
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "INTERNAL_SERVER_ERROR"
    message = "Um erro interno do servidor ocorreu, por favor tente novamente mais tarde."

    # Handle specific exception types
    if isinstance(exc, DjangoValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
        code = "VALIDATION_ERROR"
        message = "Falha na validação"
    elif isinstance(exc, ValueError):
        status_code = status.HTTP_400_BAD_REQUEST
        code = "VALUE_ERROR"
        message = str(exc)
    elif isinstance(exc, KeyError):
        status_code = status.HTTP_400_BAD_REQUEST
        code = "MISSING_KEY_ERROR"
        message = f"Campo obrigatório ausente: {str(exc)}"
    elif isinstance(exc, TypeError):
        status_code = status.HTTP_400_BAD_REQUEST
        code = "TYPE_ERROR"
        message = "Tipo de dados inválido fornecido"
    elif isinstance(exc, AttributeError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        code = "ATTRIBUTE_ERROR"
        message = "Erro interno do sistema"

    unified_response = {
        "success": False,
        "code": code,
        "message": message,
        "errors": [str(exc)] if str(exc) != message else []
    }

    return JsonResponse(unified_response, status=status_code)


def _get_error_code(exc, status_code):
    """
    Map status codes and exception types to error codes
    """
    # Map common HTTP status codes to error codes
    status_code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
        status.HTTP_502_BAD_GATEWAY: "BAD_GATEWAY",
        status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    }

    # Check for specific exception types
    if isinstance(exc, ValidationError):
        return "VALIDATION_ERROR"
    elif isinstance(exc, APIException):
        return getattr(exc, 'default_code', status_code_map.get(status_code, "API_ERROR"))

    return status_code_map.get(status_code, "UNKNOWN_ERROR")


def _get_main_error_message(exc, data):
    """
    Extract the main error message from DRF response data
    """
    # Try different keys that might contain the main message
    if isinstance(data, dict):
        # Check for common message keys
        for key in ['detail', 'message', 'error']:
            if key in data and isinstance(data[key], str):
                return data[key]

        # If it's a validation error dict, get the first error
        if 'non_field_errors' in data and data['non_field_errors']:
            return data['non_field_errors'][0]

        # Get first field error
        for field, errors in data.items():
            if isinstance(errors, list) and errors:
                return f"{field}: {errors[0]}"
            elif isinstance(errors, str):
                return f"{field}: {errors}"

    # Fallback to exception string representation
    return str(exc)


def _extract_error_details(data):
    """
    Extract detailed error information into a dict
    """
    errors = {}

    if isinstance(data, dict):
        # Handle non_field_errors
        if 'non_field_errors' in data:
            errors['non_field_errors'] = data['non_field_errors']

        # Handle field-specific errors
        for field, field_errors in data.items():
            if field == 'non_field_errors':
                continue

            if isinstance(field_errors, list):
                errors[field] = field_errors
            elif isinstance(field_errors, str):
                errors[field] = [field_errors]
            elif isinstance(field_errors, dict):
                # Nested errors (e.g., from nested serializers)
                nested_errors = {}
                for nested_field, nested_error_list in field_errors.items():
                    if isinstance(nested_error_list, list):
                        nested_errors[nested_field] = nested_error_list
                    else:
                        nested_errors[nested_field] = [str(nested_error_list)]
                errors[field] = nested_errors

    elif isinstance(data, list):
        errors['general'] = data

    elif isinstance(data, str):
        errors['general'] = [data]

    return errors
