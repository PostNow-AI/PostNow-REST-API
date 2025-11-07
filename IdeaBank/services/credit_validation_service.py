"""
Credit Validation Service for managing AI operation credits.
"""

import logging

from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class CreditValidationService:
    """Service for validating and managing user credits for AI operations."""

    def __init__(self):
        self.ai_model_service = None
        self._load_ai_model_service()

    def _load_ai_model_service(self):
        """Load AI model service if available."""
        try:
            from .ai_model_service import AIModelService
            self.ai_model_service = AIModelService
        except ImportError:
            logger.warning(
                "AIModelService not available - credit validation disabled")
            self.ai_model_service = None

    def validate_credits(self, user: User, model_name: str, estimated_tokens: int) -> bool:
        """
        Validate if user has sufficient credits for an AI operation.

        Args:
            user: The user requesting the operation
            model_name: Name of the AI model
            estimated_tokens: Estimated token count for the operation

        Returns:
            True if user has sufficient credits, False otherwise
        """
        if not user or not user.is_authenticated:
            return True  # Skip validation for unauthenticated users

        if not self.ai_model_service:
            logger.warning(
                "Credit validation skipped - AIModelService not available")
            return True

        try:
            return self.ai_model_service.validate_user_credits(user, model_name, estimated_tokens)
        except Exception as e:
            logger.error(
                f"Error validating credits for user {user.id}: {str(e)}")
            return False

    def validate_image_credits(self, user: User, model_name: str, image_count: int = 1) -> bool:
        """
        Validate if user has sufficient credits for image generation.

        Args:
            user: The user requesting image generation
            model_name: Name of the AI model
            image_count: Number of images to generate

        Returns:
            True if user has sufficient credits, False otherwise
        """
        if not user or not user.is_authenticated:
            return True  # Skip validation for unauthenticated users

        if not self.ai_model_service:
            logger.warning(
                "Image credit validation skipped - AIModelService not available")
            return True

        try:
            return self.ai_model_service.validate_image_credits(user, model_name, image_count)
        except Exception as e:
            logger.error(
                f"Error validating image credits for user {user.id}: {str(e)}")
            return False

    def deduct_credits(self, user: User, model_name: str, actual_tokens: int, description: str) -> bool:
        """
        Deduct credits after successful AI operation.

        Args:
            user: The user who performed the operation
            model_name: Name of the AI model used
            actual_tokens: Actual token count used
            description: Description of the operation

        Returns:
            True if credits were deducted successfully, False otherwise
        """
        if not user or not user.is_authenticated:
            return True  # Skip deduction for unauthenticated users

        if not self.ai_model_service:
            logger.warning(
                "Credit deduction skipped - AIModelService not available")
            return True

        try:
            return self.ai_model_service.deduct_credits(user, model_name, actual_tokens, description)
        except Exception as e:
            logger.error(
                f"Error deducting credits for user {user.id}: {str(e)}")
            return False

    def deduct_image_credits(self, user: User, model_name: str, image_count: int, description: str) -> bool:
        """
        Deduct credits after successful image generation.

        Args:
            user: The user who performed the operation
            model_name: Name of the AI model used
            image_count: Number of images generated
            description: Description of the operation

        Returns:
            True if credits were deducted successfully, False otherwise
        """
        if not user or not user.is_authenticated:
            return True  # Skip deduction for unauthenticated users

        if not self.ai_model_service:
            logger.warning(
                "Image credit deduction skipped - AIModelService not available")
            return True

        try:
            return self.ai_model_service.deduct_image_credits(user, model_name, image_count, description)
        except Exception as e:
            logger.error(
                f"Error deducting image credits for user {user.id}: {str(e)}")
            return False

    def estimate_tokens(self, prompt: str, model_name: str) -> int:
        """
        Estimate token count for a prompt.

        Args:
            prompt: The prompt text
            model_name: Name of the AI model

        Returns:
            Estimated token count
        """
        if not self.ai_model_service:
            # Fallback estimation: roughly 4 characters per token
            return len(prompt) // 4

        try:
            return self.ai_model_service.estimate_tokens(prompt, model_name)
        except Exception as e:
            logger.warning(f"Error estimating tokens: {str(e)}")
            # Fallback estimation
            return len(prompt) // 4
