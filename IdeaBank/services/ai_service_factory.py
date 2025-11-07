"""
AI Service Factory for managing different AI service providers.
"""

import logging
from typing import Optional

from .base_ai_service import BaseAIService

logger = logging.getLogger(__name__)


class AIServiceFactory:
    """Factory for creating AI services based on provider preference."""

    @staticmethod
    def create_service(provider: str = 'google', model_name: str = 'gemini-2.5-flash') -> Optional[BaseAIService]:
        """
        Create an AI service instance.

        Args:
            provider: AI provider (currently only 'google' is supported)
            model_name: AI model name (currently only 'gemini-2.5-flash' is supported)

        Returns:
            An instance of the AI service, or None if not available
        """
        try:
            # Validate provider
            if provider.lower() != 'google':
                logger.warning(
                    f"Unsupported AI provider: {provider}. Only 'google' is currently supported.")
                return None

            # Validate and normalize model name
            supported_models = ['gemini-2.5-flash',
                                'gemini-pro', 'gemini-pro-vision']
            if model_name not in supported_models:
                logger.warning(
                    f"Unsupported model: {model_name}. Using default 'gemini-2.5-flash'.")
                model_name = 'gemini-2.5-flash'

            # Create and return the service
            from .gemini_service import GeminiService
            service = GeminiService(model_name=model_name)

            if service:
                logger.info(
                    f"Successfully created AI service: {provider}/{model_name}")
            else:
                logger.error(
                    f"Failed to create AI service: {provider}/{model_name}")

            return service

        except ImportError as e:
            logger.error(f"Failed to import GeminiService: {str(e)}")
            return None
        except Exception as e:
            logger.error(
                f"Error creating AI service for {provider}/{model_name}: {str(e)}")
            return None

    @staticmethod
    def get_available_providers() -> list:
        """Get list of available AI service providers."""
        return ['google']

    @staticmethod
    def get_available_models(provider: str = 'google') -> list:
        """Get list of available models for a specific provider."""
        if provider.lower() == 'google':
            return ['gemini-2.5-flash', 'gemini-pro', 'gemini-pro-vision']
        return []

    @staticmethod
    def is_provider_supported(provider: str) -> bool:
        """Check if a provider is supported."""
        return provider.lower() == 'google'

    @staticmethod
    def is_model_supported(provider: str, model_name: str) -> bool:
        """Check if a model is supported for a given provider."""
        provider = provider.lower()
        model_name = model_name.lower()

        if provider == 'google':
            return model_name in ['gemini-2.5-flash', 'gemini-pro', 'gemini-pro-vision']

        return False
