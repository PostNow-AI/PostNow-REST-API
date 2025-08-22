
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

from django.contrib.auth.models import User

from .base_ai_service import BaseAIService


class AnthropicService(BaseAIService):
    """Service for interacting with Anthropic Claude AI."""

    def __init__(self, model_name: str = "claude-3-sonnet"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic não está instalado. Execute: pip install anthropic")

        super().__init__(model_name)

        # Set default API key from environment
        self.default_api_key = None  # Will be set per request

    def _validate_credits(self, user: User, estimated_tokens: int, model_name: str) -> bool:
        """Validate if user has sufficient credits for the AI operation."""
        try:
            from .ai_model_service import AIModelService
            if AIModelService:
                return AIModelService.validate_user_credits(user, model_name, estimated_tokens)
        except ImportError:
            pass
        return True  # Skip validation if service not available

    def _deduct_credits(self, user: User, actual_tokens: int, model_name: str, description: str) -> bool:
        """Deduct credits after AI operation."""
        try:
            from .ai_model_service import AIModelService
            if AIModelService:
                return AIModelService.deduct_credits(user, actual_tokens, model_name, description)
        except ImportError:
            pass
        return True  # Skip deduction if service not available

    def _estimate_tokens(self, prompt: str, model_name: str) -> int:
        """Estimate token count for a prompt."""
        try:
            from .ai_model_service import AIModelService
            if AIModelService:
                return AIModelService.estimate_tokens(prompt, model_name)
        except ImportError:
            pass

        # Fallback estimation: roughly 4 characters per token
        return len(prompt) // 4

    def _select_optimal_model(self, user: User, estimated_tokens: int, preferred_provider: str = None) -> str:
        """Select the optimal AI model for the operation."""
        try:
            from .ai_model_service import AIModelService
            if AIModelService:
                return AIModelService.select_optimal_model(user, estimated_tokens, preferred_provider)
        except ImportError:
            pass

        # Fallback to default model
        return self.model_name

    def _make_ai_request(self, prompt: str, model_name: str, api_key: str = None) -> str:
        """Make the actual AI API request to Anthropic Claude."""
        # Configure API key
        if not api_key:
            raise ValueError("API key is required for Anthropic requests")

        client = anthropic.Anthropic(api_key=api_key)

        try:
            # Generate content using Anthropic Claude
            response = client.messages.create(
                model=model_name,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            if response.content and response.content[0].text:
                return response.content[0].text
            else:
                raise Exception("Empty response from Anthropic API")

        except Exception as e:
            print(f"Error making Anthropic request: {e}")
            raise Exception(f"Falha na comunicação com Anthropic: {str(e)}")

    # All other methods inherit from BaseAIService
    # The service automatically uses the base implementation for:
    # - generate_campaign_ideas_with_progress
    # - improve_idea_with_progress
    # - generate_single_idea_with_progress
    # - All prompt building and parsing methods
