"""
Base classes for Django REST Framework views.
Provides common functionality and consistent response patterns.
"""

from typing import Any, Dict, Optional

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class BaseAPIView(APIView):
    """
    Base API view with common response methods and error handling.
    """

    def success_response(
        self,
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK
    ) -> Response:
        """
        Return a standardized success response.

        Args:
            data: The response data
            message: Success message
            status_code: HTTP status code

        Returns:
            Response: Standardized success response
        """
        response_data = {
            "success": True,
            "message": message,
        }

        if data is not None:
            response_data["data"] = data

        return Response(response_data, status=status_code)

    def error_response(
        self,
        message: str = "An error occurred",
        errors: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> Response:
        """
        Return a standardized error response.

        Args:
            message: Error message
            errors: Detailed error information
            status_code: HTTP status code

        Returns:
            Response: Standardized error response
        """
        response_data = {
            "success": False,
            "message": message,
        }

        if errors:
            response_data["errors"] = errors

        return Response(response_data, status=status_code)

    def not_found_response(self, message: str = "Resource not found") -> Response:
        """Return a 404 not found response."""
        return self.error_response(message, status_code=status.HTTP_404_NOT_FOUND)

    def unauthorized_response(self, message: str = "Unauthorized") -> Response:
        """Return a 401 unauthorized response."""
        return self.error_response(message, status_code=status.HTTP_401_UNAUTHORIZED)

    def forbidden_response(self, message: str = "Forbidden") -> Response:
        """Return a 403 forbidden response."""
        return self.error_response(message, status_code=status.HTTP_403_FORBIDDEN)

    def bad_request_response(self, message: str = "Bad request", errors: Optional[Dict] = None) -> Response:
        """Return a 400 bad request response."""
        return self.error_response(message, errors, status_code=status.HTTP_400_BAD_REQUEST)

    def server_error_response(self, message: str = "Internal server error") -> Response:
        """Return a 500 internal server error response."""
        return self.error_response(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
