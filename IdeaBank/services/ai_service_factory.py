from typing import Optional

from .base_ai_service import BaseAIService


class AIServiceFactory:
    """Factory for creating AI services based on provider preference."""

    @staticmethod
    def create_service(provider: str, model_name: str = None) -> Optional[BaseAIService]:
        """
        Create an AI service based on the provider.

        Args:
            provider: The AI provider ('google', 'openai', 'anthropic')
            model_name: Specific model name to use

        Returns:
            An instance of the appropriate AI service, or None if not available
        """
        provider_lower = provider.lower() if provider else 'google'

        if provider_lower in ['google', 'gemini']:
            try:
                from .gemini_service import GeminiService
                default_model = model_name or 'gemini-1.5-flash'
                return GeminiService(model_name=default_model)
            except ImportError:
                print("Gemini service not available")
                return None

        elif provider_lower in ['openai', 'gpt']:
            try:
                from .openai_service import OpenAIService
                default_model = model_name or 'gpt-3.5-turbo'
                return OpenAIService(model_name=default_model)
            except ImportError:
                print("OpenAI service not available")
                return None

        elif provider_lower in ['anthropic', 'claude']:
            try:
                from .anthropic_service import AnthropicService
                default_model = model_name or 'claude-3-sonnet'
                return AnthropicService(model_name=default_model)
            except ImportError:
                print("Anthropic service not available")
                return None

        else:
            print(f"Unknown provider: {provider}")
            return None

    @staticmethod
    def get_available_providers() -> list:
        """Get list of available AI providers."""
        providers = []

        try:
            from .gemini_service import GeminiService
            providers.append('google')
        except ImportError:
            pass

        try:
            from .openai_service import OpenAIService
            providers.append('openai')
        except ImportError:
            pass

        try:
            from .anthropic_service import AnthropicService
            providers.append('anthropic')
        except ImportError:
            pass

        return providers

    @staticmethod
    def get_default_service() -> Optional[BaseAIService]:
        """Get the default AI service (usually Gemini)."""
        return AIServiceFactory.create_service('google')
