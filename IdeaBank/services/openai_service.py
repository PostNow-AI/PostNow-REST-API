
import os

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from django.contrib.auth.models import User

from .base_ai_service import BaseAIService


class OpenAIService(BaseAIService):
    def generate_image(self, prompt: str, user: User = None) -> str:
        """Generate an image using OpenAI's DALL·E API and return the image URL."""
        print("=== OPENAI IMAGE GENERATION START ===")

        if not OPENAI_AVAILABLE:
            print("❌ OpenAI not available - openai package not installed")
            return ""

        api_key = self.default_api_key
        if not api_key:
            print("❌ No API key available for OpenAI image generation")
            return ""

        # Validate credits before generation
        if user and user.is_authenticated:
            from .ai_model_service import AIModelService
            model_name = 'dall-e-3'
            if not AIModelService.validate_image_credits(user, model_name, 1):
                print("❌ Insufficient credits for image generation")
                raise ValueError("Créditos insuficientes para gerar imagem")

        print(f"✅ OpenAI API key available: {api_key[:10]}...")

        client = openai.OpenAI(api_key=api_key)
        try:
            print(
                f"🔄 Generating image with DALL-E-3, prompt: {prompt[:100]}...")

            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            if response.data and response.data[0].url:
                image_url = response.data[0].url

                # Download image and convert to base64
                try:
                    import base64

                    import requests
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        img_bytes = img_response.content
                        img_base64 = base64.b64encode(
                            img_bytes).decode('utf-8')
                        # Deduct credits for successful image generation
                        if user and user.is_authenticated:
                            from .ai_model_service import AIModelService
                            AIModelService.deduct_image_credits(
                                user, 'dall-e-3', 1, f"DALL-E-3 image generation - {prompt[:50]}...")
                        return 'data:image/png;base64,' + img_base64
                    else:
                        return ""
                except Exception:
                    import traceback
                    return str(traceback.format_exc())
            else:
                print("❌ Empty response from OpenAI Image API")
                return ""

        except Exception:
            import traceback
            return str(traceback.format_exc())
    """Service for interacting with OpenAI GPT models."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai não está instalado. Execute: pip install openai")

        super().__init__(model_name)

        # Set provider identifier
        self.provider = 'openai'

        # Set default API key from environment
        self.default_api_key = os.getenv('OPENAI_API_KEY', '')

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
                return AIModelService.deduct_credits(user, model_name, actual_tokens, description)
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
        """Make the actual AI API request to OpenAI."""
        # Configure API key
        api_key = api_key or self.default_api_key
        if not api_key:
            raise ValueError("API key is required for OpenAI requests")

        # Use the new OpenAI client (v1.0.0+)
        client = openai.OpenAI(api_key=api_key)

        try:
            # Generate content using OpenAI
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a marketing expert specializing in social media content creation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
            else:
                raise Exception("Empty response from OpenAI API")

        except Exception as e:
            print(f"Error making OpenAI request: {e}")
            raise Exception(f"Falha na comunicação com OpenAI: {str(e)}")

    # All other methods inherit from BaseAIService
    # The service automatically uses the base implementation for:
    # - generate_campaign_ideas_with_progress
    # - improve_idea_with_progress
    # - generate_single_idea_with_progress
    # - All prompt building and parsing methods
