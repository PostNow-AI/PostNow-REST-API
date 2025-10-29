"""
Unified response utilities for consistent API responses.
"""

from typing import Any, Dict, Optional

from rest_framework import status
from rest_framework.response import Response


class APIResponse:
    """
    Utility class for creating consistent API responses.
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        **kwargs
    ) -> Response:
        """
        Create a success response.

        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            **kwargs: Additional response data

        Returns:
            Response: Success response
        """
        response_data = {
            "success": True,
            "message": message,
        }

        if data is not None:
            response_data["data"] = data

        # Add any additional fields
        response_data.update(kwargs)

        return Response(response_data, status=status_code)

    @staticmethod
    def error(
        message: str = "An error occurred",
        errors: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
        **kwargs
    ) -> Response:
        """
        Create an error response.

        Args:
            message: Error message
            errors: Detailed error information
            status_code: HTTP status code
            error_code: Custom error code
            **kwargs: Additional response data

        Returns:
            Response: Error response
        """
        response_data = {
            "success": False,
            "message": message,
        }

        if errors:
            response_data["errors"] = errors

        if error_code:
            response_data["error_code"] = error_code

        # Add any additional fields
        response_data.update(kwargs)

        return Response(response_data, status=status_code)

    @staticmethod
    def created(data: Any = None, message: str = "Resource created successfully") -> Response:
        """Create a 201 Created response."""
        return APIResponse.success(data, message, status.HTTP_201_CREATED)

    @staticmethod
    def no_content(message: str = "No content") -> Response:
        """Create a 204 No Content response."""
        return APIResponse.success(None, message, status.HTTP_204_NO_CONTENT)

    @staticmethod
    def bad_request(message: str = "Bad request", errors: Optional[Dict] = None) -> Response:
        """Create a 400 Bad Request response."""
        return APIResponse.error(message, errors, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> Response:
        """Create a 401 Unauthorized response."""
        return APIResponse.error(message, status_code=status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def forbidden(message: str = "Forbidden") -> Response:
        """Create a 403 Forbidden response."""
        return APIResponse.error(message, status_code=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def not_found(message: str = "Resource not found") -> Response:
        """Create a 404 Not Found response."""
        return APIResponse.error(message, status_code=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def conflict(message: str = "Conflict", errors: Optional[Dict] = None) -> Response:
        """Create a 409 Conflict response."""
        return APIResponse.error(message, errors, status.HTTP_409_CONFLICT)

    @staticmethod
    def unprocessable_entity(message: str = "Unprocessable entity", errors: Optional[Dict] = None) -> Response:
        """Create a 422 Unprocessable Entity response."""
        return APIResponse.error(message, errors, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @staticmethod
    def server_error(message: str = "Internal server error") -> Response:
        """Create a 500 Internal Server Error response."""
        return APIResponse.error(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResponseBuilder:
    """
    Builder pattern for creating complex responses.
    """

    def __init__(self):
        self._response_data = {}
        self._status_code = status.HTTP_200_OK
        self._success = True

    def success(self, success: bool = True) -> 'ResponseBuilder':
        """Set success flag."""
        self._success = success
        return self

    def message(self, message: str) -> 'ResponseBuilder':
        """Set response message."""
        self._response_data["message"] = message
        return self

    def data(self, data: Any) -> 'ResponseBuilder':
        """Set response data."""
        self._response_data["data"] = data
        return self

    def errors(self, errors: Dict[str, Any]) -> 'ResponseBuilder':
        """Set response errors."""
        self._response_data["errors"] = errors
        return self

    def error_code(self, code: str) -> 'ResponseBuilder':
        """Set error code."""
        self._response_data["error_code"] = code
        return self

    def status(self, status_code: int) -> 'ResponseBuilder':
        """Set HTTP status code."""
        self._status_code = status_code
        return self

    def add_field(self, key: str, value: Any) -> 'ResponseBuilder':
        """Add a custom field to the response."""
        self._response_data[key] = value
        return self

    def build(self) -> Response:
        """
        Build the final response.

        Returns:
            Response: The built response
        """
        response_data = dict(self._response_data)
        response_data["success"] = self._success

        return Response(response_data, status=self._status_code)
