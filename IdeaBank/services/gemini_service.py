import os

try:
    import google.generativeai as genai
    from openai import OpenAI

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

import base64
import re
import time

from django.contrib.auth.models import User

from .base_ai_service import BaseAIService


def extract_base64_image(data_url: str) -> bytes:
    """
    Extracts and decodes base64 image data from a data URL.
    Returns image bytes suitable for Gemini.
    """
    # Example data_url: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
    match = re.match(r"^data:image/(png|jpeg);base64,(.*)$", data_url)
    if match:
        base64_str = match.group(2)
        return base64.b64decode(base64_str)
    # If not a data URL, assume it's plain base64
    return base64.b64decode(data_url)


class GeminiService(BaseAIService):
    def generate_image(self, prompt: str, current_image: str, user: User = None, post_data: dict = None, idea_content: str = None, text_config: dict = None) -> str:
        """Generate an image using Gemini's image generation API and return a data URL (base64)."""
        compressed_data = ""
        if not GEMINI_AVAILABLE:
            return ""

        api_key = self.default_api_key
        if not api_key:
            return ""

        # Enhance prompt with post data and idea content
        enhanced_prompt = self._enhance_image_prompt(
            prompt, post_data, idea_content)
        # Validate credits before generation
        model_name = 'gemini-2.5-flash-image'
        if user and user.is_authenticated:
            from .ai_model_service import AIModelService
            if not AIModelService.validate_image_credits(user, model_name, 1):
                raise ValueError("Créditos insuficientes para gerar imagem")

        # Flag to track if we should deduct credits
        should_deduct_credits = user and user.is_authenticated

        # Helper function to deduct credits after successful generation
        def deduct_credits_for_image(description_suffix=""):
            if should_deduct_credits:
                try:
                    from .ai_model_service import AIModelService
                    AIModelService.deduct_image_credits(
                        user, 'gemini-2.5-flash-image', 1, f"Gemini image generation{description_suffix} - {prompt[:50]}...")
                except ImportError:
                    print("⚠️ Could not deduct credits - AIModelService not available")

        try:
            model = genai.GenerativeModel('gemini-2.5-flash-image',
                                          )

            # Prepare image data for the request
            image_bytes = None

            if current_image:
                image_bytes = extract_base64_image(current_image)
            elif post_data and post_data.get('type') in ['story', 'reel']:
                # Create empty white vertical image for stories/reels
                print('passou aqui')
                image_bytes = self._create_empty_vertical_image()

            if image_bytes:
                response = model.generate_content([
                    enhanced_prompt,
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_bytes
                        }
                    },
                ])
            else:
                response = model.generate_content([enhanced_prompt])

            compressed_data = self._handle_compression(
                response, model_name, post_data, text_config)
            if compressed_data:
                # Convert PNG bytes to base64 data URL for return

                # Deduct credits for successful image generation
                deduct_credits_for_image("gemini-2.5-flash-image-preview")
                return compressed_data
            else:
                print(
                    f"❌ Failed to generate image for model: {model_name}")

        except Exception as e:
            error_str = str(e)
            print(f"❌ Exception in model {model_name}: {error_str}")

            # Check for specific quota exhaustion errors
            if '429' in error_str or 'quota' in error_str.lower() or 'exhausted' in error_str.lower():
                print(
                    f"⚠️ Quota exhausted for model {model_name}, waiting before trying next model...")
                # Wait 2 seconds before trying next model
                time.sleep(2)
            elif 'not found' in error_str.lower() or 'invalid' in error_str.lower():
                print(
                    f"⚠️ Model {model_name} not available, trying next model...")

    def _handle_compression(self, response, model_name: str, post_data: dict, text_config: dict = None):
        print(
            f"🖼️ Model {model_name} returned {len(response.candidates)} candidates")
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Save Gemini image bytes as gemini_output.png in the root folder
                        gemini_image_bytes = part.inline_data.data
                        try:
                            with open('gemini_output.png', 'wb') as f:
                                f.write(gemini_image_bytes)
                            print('✅ Saved Gemini image bytes as gemini_output.png')
                        except Exception as e:
                            print(f'❌ Failed to save gemini_output.png: {e}')

                        # Apply text overlay if text_config is provided
                        final_image_bytes = gemini_image_bytes
                        if text_config:
                            try:
                                from .text_overlay_service import TextOverlayService
                                overlay_service = TextOverlayService()
                                final_image_bytes = overlay_service.add_text_overlay(
                                    gemini_image_bytes, text_config
                                )
                                print('✅ Applied text overlay to image')
                            except Exception as e:
                                print(f'⚠️ Failed to apply text overlay: {e}')
                                # Continue with original image if text overlay fails

                        # Compress and optimize final image data
                        compressed_data = self._compress_image_data(
                            final_image_bytes, post_data)
                        if compressed_data:
                            return compressed_data
                        else:
                            print(
                                f"⚠️ Failed to compress image data from model: {model_name}")
                    # Also check for text that might contain image references
                    if hasattr(part, 'text') and part.text:
                        print(
                            f"📝 Model {model_name} returned text: {part.text[:100]}...")

        # Return empty string if no image data found
        print(f"❌ No image data found in response from model: {model_name}")
        return ""

    def _enhance_image_prompt(self, base_prompt: str, post_data: dict = None, idea_content: str = None) -> str:
        """Enhance the image generation prompt with post data and idea content."""
        enhanced_parts = [
            f"Gere uma imagem de alta qualidade com base nesta descrição: {base_prompt}."]

        if post_data:
            if post_data.get('objective'):
                enhanced_parts.append(
                    f"Objetivo do post: {post_data['objective']}")
            if post_data.get('type'):
                enhanced_parts.append(f"Tipo de conteúdo: {post_data['type']}")
            if post_data.get('further_details'):
                enhanced_parts.append(
                    f"Detalhes adicionais: {post_data['further_details']}")

        if idea_content:
            # Extract key themes from idea content for visual inspiration
            enhanced_parts.append(f"Contexto do conteúdo: {idea_content}...")

        enhanced_parts.append(
            "Crie uma imagem de marketing profissional e visualmente atraente, adequada para redes sociais.")

        return ". ".join(enhanced_parts)

    def _create_empty_vertical_image(self) -> bytes:
        """Create an empty white vertical image (9:16 aspect ratio) for stories/reels."""
        try:
            import io

            from PIL import Image

            # Create 9:16 aspect ratio image (1080x1920 for good quality)
            width, height = 1080, 1920

            # Create white image
            image = Image.new('RGB', (width, height), color='white')

            # Convert to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            return buffer.getvalue()

        except ImportError:
            # If PIL not available, create minimal white image data
            # This is a minimal 1x1 white PNG in base64
            import base64
            white_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            return base64.b64decode(white_png_b64)
        except Exception:
            # Fallback to minimal white image
            import base64
            white_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            return base64.b64decode(white_png_b64)

    def _compress_image_data(self, image_data: bytes, post_data: dict) -> str:
        """Compress image data to reduce size for database storage."""
        try:
            import base64
            import io

            from PIL import Image

            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')

            # Resize image to a higher resolution for better quality (max 800x800)
            if post_data and post_data.get('type') in ['story', 'reel']:
                # For stories/reels, maintain 9:16 aspect ratio
                max_size = (1080, 1920)
            else:
                max_size = (1080, 1080)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save as JPEG with high quality for better visual appeal
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85, optimize=True)
            compressed_data = buffer.getvalue()

            # Convert to base64
            b64_data = base64.b64encode(compressed_data).decode('utf-8')
            data_url = f"data:image/jpeg;base64,{b64_data}"

            # TextField can handle much larger data, but let's still be reasonable
            if len(data_url) > 300000:  # 300KB limit for high quality images

                # Medium size and good quality for large images
                image = Image.open(io.BytesIO(image_data))
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')

                if post_data and post_data.get('type') in ['story', 'reel']:
                    image.thumbnail((720, 1280), Image.Resampling.LANCZOS)
                else:
                    image.thumbnail((600, 600), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=75, optimize=True)
                compressed_data = buffer.getvalue()

                b64_data = base64.b64encode(compressed_data).decode('utf-8')
                data_url = f"data:image/jpeg;base64,{b64_data}"

            if len(data_url) > 500000:  # 500KB absolute limit for high quality
                return ""

            return data_url

        except ImportError:
            # Fallback to original base64 without compression
            import base64
            b64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{b64_data}"

        except Exception:
            return ""

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
            raise Exception(f"Falha na comunicação com Gemini: {str(e)}")
