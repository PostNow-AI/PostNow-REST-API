"""
Base classes for Django REST Framework serializers.
Provides common validation patterns and utilities.
"""

from typing import Any, Dict, List, Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class BaseSerializer(serializers.Serializer):
    """
    Base serializer with common validation utilities.
    """

    def validate_required_string(self, value: Any, field_name: str, min_length: int = 1) -> str:
        """
        Validate that a field is a non-empty string with minimum length.

        Args:
            value: The value to validate
            field_name: Name of the field for error messages
            min_length: Minimum required length

        Returns:
            str: The validated string

        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise ValidationError(f"{field_name} é obrigatório.")

        if not isinstance(value, str):
            raise ValidationError(f"{field_name} deve ser uma string.")

        value = value.strip()
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} deve ter pelo menos {min_length} caracteres."
            )

        return value

    def validate_email_format(self, value: str, field_name: str = "Email") -> str:
        """
        Validate email format.

        Args:
            value: Email string to validate
            field_name: Name of the field for error messages

        Returns:
            str: The validated email

        Raises:
            ValidationError: If validation fails
        """
        import re

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, value):
            raise ValidationError(f"{field_name} deve ter um formato válido.")

        return value

    def validate_phone_number(self, value: str, field_name: str = "Telefone") -> str:
        """
        Validate Brazilian phone number format.

        Args:
            value: Phone number string to validate
            field_name: Name of the field for error messages

        Returns:
            str: The validated phone number

        Raises:
            ValidationError: If validation fails
        """
        import re

        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', value)

        # Check if it's a valid Brazilian phone number
        if len(digits_only) < 10 or len(digits_only) > 11:
            raise ValidationError(
                f"{field_name} deve ter entre 10 e 11 dígitos."
            )

        # Check if it starts with a valid area code
        if len(digits_only) == 11 and not digits_only.startswith(('9',)):
            # For 11 digits, should be mobile starting with 9
            pass  # Allow for now, could be more strict

        return digits_only

    def validate_url_format(self, value: str, field_name: str = "URL") -> str:
        """
        Validate URL format.

        Args:
            value: URL string to validate
            field_name: Name of the field for error messages

        Returns:
            str: The validated URL

        Raises:
            ValidationError: If validation fails
        """
        from urllib.parse import urlparse

        try:
            result = urlparse(value)
            if not result.scheme or not result.netloc:
                raise ValidationError(f"{field_name} deve ser uma URL válida.")
        except Exception:
            raise ValidationError(f"{field_name} deve ser uma URL válida.")

        return value


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base model serializer with common functionality.
    """

    def validate_unique_field(self, value: Any, field_name: str, queryset: Any, exclude_pk: Optional[int] = None) -> Any:
        """
        Validate that a field value is unique.

        Args:
            value: The value to check for uniqueness
            field_name: Name of the field for error messages
            queryset: Queryset to check against
            exclude_pk: Primary key to exclude from uniqueness check (for updates)

        Returns:
            Any: The validated value

        Raises:
            ValidationError: If value is not unique
        """
        query = {field_name: value}

        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)

        if queryset.filter(**query).exists():
            raise ValidationError(
                f"Já existe um registro com este {field_name}.")

        return value

    def handle_validation_error(self, exc: ValidationError) -> Dict[str, List[str]]:
        """
        Handle validation errors and return formatted error dict.

        Args:
            exc: The validation exception

        Returns:
            Dict[str, List[str]]: Formatted error dictionary
        """
        errors = {}
        for field, messages in exc.detail.items():
            if isinstance(messages, list):
                errors[field] = messages
            else:
                errors[field] = [str(messages)]
        return errors
