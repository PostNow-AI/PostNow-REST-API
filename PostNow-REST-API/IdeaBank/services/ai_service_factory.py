from typing import Optional

from .base_ai_service import BaseAIService


class AIServiceFactory:
    """Factory for creating AI services based on provider preference."""

    @staticmethod
    def create_service(provider: str = 'google', model_name: str = 'gemini-2.5-flash') -> Optional[BaseAIService]:
        """
        Create an AI service

        Args:
            provider: AI provider (only 'google' is supported)
            model_name: AI model name (only 'gemini-2.5-flash' is supported)

        Returns:
            An instance of the AI service, or None if not available
        """
        # Only allow Google provider and Gemini 2.5 Flash model
        if provider.lower() != 'google':
            return None

        if model_name != 'gemini-2.5-flash':
            model_name = 'gemini-2.5-flash'  # Force to use only supported model

        from .gemini_service import GeminiService
        return GeminiService(model_name=model_name)
