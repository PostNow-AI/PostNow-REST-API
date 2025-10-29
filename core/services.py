"""
Base classes for service layer.
Provides common patterns for business logic implementation.
"""

from typing import Any, Dict, Generic, Optional, TypeVar

from django.db import transaction
from django.db.models import Model, QuerySet

T = TypeVar('T', bound=Model)


class BaseService(Generic[T]):
    """
    Base service class with common CRUD operations and utilities.
    """

    model: type[T]

    @classmethod
    def get_queryset(cls) -> QuerySet[T]:
        """
        Get the base queryset for the model.

        Returns:
            QuerySet: Base queryset for the model
        """
        return cls.model.objects.all()

    @classmethod
    def get_by_id(cls, pk: Any) -> Optional[T]:
        """
        Get an object by its primary key.

        Args:
            pk: Primary key value

        Returns:
            Optional[T]: The object if found, None otherwise
        """
        try:
            return cls.get_queryset().get(pk=pk)
        except cls.model.DoesNotExist:
            return None

    @classmethod
    def get_or_create(cls, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[T, bool]:
        """
        Get an object or create it if it doesn't exist.

        Args:
            defaults: Default values for creation
            **kwargs: Lookup parameters

        Returns:
            tuple[T, bool]: (object, created)
        """
        return cls.get_queryset().get_or_create(defaults=defaults or {}, **kwargs)

    @classmethod
    def create(cls, **kwargs) -> T:
        """
        Create a new object.

        Args:
            **kwargs: Object attributes

        Returns:
            T: The created object
        """
        return cls.model.objects.create(**kwargs)

    @classmethod
    def update(cls, instance: T, **kwargs) -> T:
        """
        Update an existing object.

        Args:
            instance: The object to update
            **kwargs: Attributes to update

        Returns:
            T: The updated object
        """
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    @classmethod
    def delete(cls, instance: T) -> None:
        """
        Delete an object.

        Args:
            instance: The object to delete
        """
        instance.delete()

    @classmethod
    @transaction.atomic
    def bulk_create(cls, objects: list[Dict[str, Any]]) -> list[T]:
        """
        Bulk create objects.

        Args:
            objects: List of object dictionaries

        Returns:
            list[T]: List of created objects
        """
        instances = [cls.model(**obj_data) for obj_data in objects]
        return cls.model.objects.bulk_create(instances)

    @classmethod
    @transaction.atomic
    def bulk_update(cls, updates: list[tuple[T, Dict[str, Any]]]) -> None:
        """
        Bulk update objects.

        Args:
            updates: List of (instance, update_data) tuples
        """
        for instance, update_data in updates:
            for key, value in update_data.items():
                setattr(instance, key, value)
            instance.save()


class BaseBusinessService(BaseService[T]):
    """
    Base service for business logic with validation and error handling.
    """

    @classmethod
    def validate_business_rules(cls, data: Dict[str, Any], instance: Optional[T] = None) -> Dict[str, Any]:
        """
        Validate business rules before creating/updating.

        Args:
            data: The data to validate
            instance: Existing instance for updates (None for creates)

        Returns:
            Dict[str, Any]: Validated and potentially modified data

        Raises:
            ValueError: If business rules are violated
        """
        # Override in subclasses to implement business rule validation
        return data

    @classmethod
    def pre_save(cls, instance: T, data: Dict[str, Any]) -> T:
        """
        Hook called before saving an object.

        Args:
            instance: The object being saved
            data: The data being saved

        Returns:
            T: The modified object
        """
        # Override in subclasses for pre-save logic
        return instance

    @classmethod
    def post_save(cls, instance: T, created: bool) -> None:
        """
        Hook called after saving an object.

        Args:
            instance: The saved object
            created: Whether the object was created or updated
        """
        # Override in subclasses for post-save logic
        pass

    @classmethod
    @transaction.atomic
    def create_with_validation(cls, **kwargs) -> T:
        """
        Create an object with business rule validation.

        Args:
            **kwargs: Object attributes

        Returns:
            T: The created object

        Raises:
            ValueError: If business rules are violated
        """
        validated_data = cls.validate_business_rules(kwargs)
        instance = cls.model(**validated_data)
        instance = cls.pre_save(instance, validated_data)
        instance.save()
        cls.post_save(instance, created=True)
        return instance

    @classmethod
    @transaction.atomic
    def update_with_validation(cls, instance: T, **kwargs) -> T:
        """
        Update an object with business rule validation.

        Args:
            instance: The object to update
            **kwargs: Attributes to update

        Returns:
            T: The updated object

        Raises:
            ValueError: If business rules are violated
        """
        validated_data = cls.validate_business_rules(kwargs, instance)
        instance = cls.pre_save(instance, validated_data)
        updated_instance = cls.update(instance, **validated_data)
        cls.post_save(updated_instance, created=False)
        return updated_instance
