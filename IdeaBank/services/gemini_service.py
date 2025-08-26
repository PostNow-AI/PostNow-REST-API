import os
from typing import Dict, List

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from django.contrib.auth.models import User

from .base_ai_service import BaseAIService


class GeminiService(BaseAIService):
    """Service for interacting with Google Gemini AI."""

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai não está instalado. Execute: pip install google-generativeai")

        super().__init__(model_name)

        # Set provider identifier
        self.provider = 'google'

        # Get default API key from environment
        self.default_api_key = os.getenv('GEMINI_API_KEY', '')

        # Initialize without API key - will be set per request
        genai.configure(api_key="")
        self.model = genai.GenerativeModel(model_name)

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
        """Make the actual AI API request to Gemini."""
        # Configure API key
        api_key = api_key or self.default_api_key
        if not api_key:
            raise ValueError("API key is required for Gemini requests")

        genai.configure(api_key=api_key)

        try:
            # Generate content
            response = self.model.generate_content(prompt)

            if response.text:
                return response.text
            else:
                raise Exception("Empty response from Gemini API")

        except Exception as e:
            print(f"Error making Gemini request: {e}")
            raise Exception(f"Falha na comunicação com Gemini: {str(e)}")

    # Legacy method compatibility

    def generate_campaign_ideas(self, user: User, config: Dict) -> List[Dict]:
        """Legacy method - now redirects to generate_campaign_ideas_with_progress."""
        ideas, _ = self.generate_campaign_ideas_with_progress(user, config)
        return ideas

    def generate_ideas(self, user: User, config: Dict) -> List[Dict]:
        """Legacy method - now redirects to generate_campaign_ideas_with_progress."""
        return self.generate_campaign_ideas(user, config)

    def improve_idea(self, user: User, current_idea, improvement_prompt: str, api_key: str = None) -> Dict:
        """Legacy method - now redirects to improve_idea_with_progress."""
        improved_data, _ = self.improve_idea_with_progress(
            user, current_idea, improvement_prompt, api_key)
        return improved_data

    def generate_single_idea(self, user: User, campaign: Dict, idea_params: Dict) -> Dict:
        """Legacy method - now redirects to generate_single_idea_with_progress."""
        idea_data, _ = self.generate_single_idea_with_progress(
            user, campaign, idea_params)
        return idea_data
