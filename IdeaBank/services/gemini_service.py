import json
import os

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

import base64
import re
import time

from django.contrib.auth.models import User

from ..models import ChatHistory
from .base_ai_service import BaseAIService
from .prompt_service import PromptService

prompt_service = PromptService()


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
    def _convert_history_to_serializable(self, history):
        """Convert Gemini Content objects to serializable dictionaries."""
        serializable_history = []
        for content in history:
            # Convert Content object to dictionary
            content_dict = {
                'role': content.role,
                'parts': []
            }

            for part in content.parts:
                part_dict = {}

                # Handle text parts
                if hasattr(part, 'text') and part.text:
                    part_dict['text'] = part.text

                # Handle inline data (images)
                if hasattr(part, 'inline_data') and part.inline_data:
                    part_dict['inline_data'] = {
                        'mime_type': part.inline_data.mime_type,
                        'data': base64.b64encode(part.inline_data.data).decode('utf-8') if part.inline_data.data else None
                    }

                # Handle function calls
                if hasattr(part, 'function_call') and part.function_call:
                    part_dict['function_call'] = {
                        'name': part.function_call.name,
                        'args': dict(part.function_call.args) if part.function_call.args else {}
                    }

                # Handle function responses
                if hasattr(part, 'function_response') and part.function_response:
                    part_dict['function_response'] = {
                        'name': part.function_response.name,
                        'response': part.function_response.response
                    }

                content_dict['parts'].append(part_dict)

            serializable_history.append(content_dict)

        return serializable_history

    def generate_image(self, prompt: str, current_image: str, user: User = None, post_data: dict = None, idea_content: str = None, conversation_id: str = 'default') -> str:
        """Generate an image using Gemini's chat API with conversation history support."""
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
        if user and user.is_authenticated:
            from .ai_model_service import AIModelService
            model_name = 'gemini-imagen'
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
                        user, 'gemini-imagen', 1, f"Gemini image generation{description_suffix} - {prompt[:50]}...")
                except ImportError:
                    print("⚠️ Could not deduct credits - AIModelService not available")

        try:
            # Fetch existing conversation history from database for image generation
            chat_history_data = []
            if user:
                try:
                    chat_history_obj = ChatHistory.objects.get(
                        user=user, conversation_id=conversation_id)
                    chat_history_data = chat_history_obj.get_history()
                except ChatHistory.DoesNotExist:
                    # No existing history, start fresh
                    pass

            # Try different model names for image generation with fallbacks
            model_names = [
                'gemini-2.5-flash-image',
                'gemini-2.5-flash-image',
                'gemini-2.5-flash-image',
                'gemini-2.5-flash-image',
                'gemini-2.5-flash-image',
                'gemini-2.5-flash-image',
                'gemini-2.5-flash-image',
            ]

            for model_name in model_names:
                try:
                    # Create model and start chat session with history
                    model = genai.GenerativeModel(model_name)
                    chat = model.start_chat(history=chat_history_data)

                    # Prepare message content
                    message_parts = [enhanced_prompt]

                    creator_profile_data = prompt_service.get_creator_profile_data()
                    logo = creator_profile_data.get('logo_image', None)
                    if logo:
                        logo_bytes = extract_base64_image(logo)
                        message_parts.append({
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": logo_bytes
                            }
                        })

                    # Add current image if provided
                    if current_image:
                        image_bytes = extract_base64_image(current_image)
                        message_parts.append({
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_bytes
                            }
                        })
                    else:
                        # Create empty canvas image for context
                        if post_data and post_data.get('type') in ['story', 'reel']:
                            image_bytes = self._create_empty_vertical_image(
                                1080, 1920)
                        elif post_data and post_data.get('type') in ['post', 'campaign']:
                            image_bytes = self._create_empty_vertical_image(
                                1080, 1350)
                        else:
                            image_bytes = self._create_empty_vertical_image(
                                1080, 1080)

                        if image_bytes:
                            message_parts.append({
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": image_bytes
                                }
                            })

                    # Send message through chat session
                    response = chat.send_message(message_parts)

                    # Check if response has image data
                    compressed_data = self._handle_compression(
                        response, model_name, post_data)

                    # Final safety check
                    if compressed_data:
                        # Deduct credits for successful image generation
                        deduct_credits_for_image(" (chat session)")

                        # Save updated conversation history
                        if user:
                            updated_history = chat.history
                            serializable_history = self._convert_history_to_serializable(
                                updated_history)
                            chat_history_obj, created = ChatHistory.objects.get_or_create(
                                user=user, conversation_id=conversation_id)
                            chat_history_obj.set_history(serializable_history)
                            chat_history_obj.save()

                        return compressed_data
                    else:
                        print(
                            f"❌ Final compressed_data is empty for model: {model_name}")

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

                    continue

            # If we reach here, no models worked
            print("❌ All models failed to generate image")
            return ""

        except Exception as e:
            print(f"❌ General exception in generate_image: {str(e)}")
            return ""

    def _handle_compression(self, response, model_name: str, post_data: dict):
        print(
            f"🖼️ Model {model_name} returned {len(response.candidates)} candidates")
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Compress and optimize image data
                        compressed_data = self._compress_image_data(
                            part.inline_data.data, post_data)
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
            f"Gere uma imagem de alta qualidade com base nesta descrição: {base_prompt}"]

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
            enhanced_parts.append(
                f"Contexto do conteúdo: {idea_content}...")

        if post_data and post_data.get('type') in ['story', 'reel']:
            enhanced_parts.append(
                "Gere uma imagem criativa no formato vertical Tamanho: 1080 x 1920 px (Proporção: 9:16 (vertical – formato de Story/Reel), utilizando a imagem anexada como canvas base para a arte. Não deixe bordas brancas ao redor da imagem, preencha todo o espaço.")
        else:
            if post_data and post_data.get('type') in ['post', 'campaign']:
                enhanced_parts.append(
                    "Gere uma imagem criativa no formato vertical Tamanho: 1080 x 1350 px (Proporção: 4:5 (vertical – formato de post para Feed), utilizando a imagem anexada como canvas base para a arte. Não deixe bordas brancas ao redor da imagem, preencha todo o espaço.")

        enhanced_parts.append(
            "Crie uma imagem de marketing profissional e visualmente atraente, adequada para redes sociais. Não deixei bordas brancas ao redor da imagem. Use cores vibrantes e um design limpo, chamativo e original. NÃO DEIXE BORDAS BRANCAS AO REDOR DA IMAGEM, PREENCHA TODO O ESPAÇO, E NEM ADICIONE TEXTOS NA IMAGEM. NÃO QUEREMOS TEXTO, APENAS A IMAGEM SEM A BORDA BRANCA")
        return ". ".join(enhanced_parts)

    def _create_empty_vertical_image(self, width, height) -> bytes:
        """Create an empty white vertical image (9:16 aspect ratio) for stories/reels."""
        try:
            import io

            from PIL import Image

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

    def _make_ai_request(self, prompt: str, model_name: str, api_key: str = None, user: User = None, conversation_id: str = 'default', post_data: dict = None) -> str:
        """Make the actual AI API request to Gemini with conversation history support."""
        # Configure API key
        api_key = api_key or self.default_api_key
        if not api_key:
            raise ValueError("API key is required for Gemini requests")

        genai.configure(api_key=api_key)

        try:
            # Fetch existing conversation history from database
            chat_history_data = []
            if user:
                try:
                    chat_history_obj = ChatHistory.objects.get(
                        user=user, conversation_id=conversation_id)
                    chat_history_data = chat_history_obj.get_history()
                except ChatHistory.DoesNotExist:
                    # No existing history, start fresh
                    pass

            # Start a chat session with the fetched history
            chat = self.model.start_chat(history=chat_history_data)

            # Handle special conversation flows
            if conversation_id == "campaign_generation":
                return self._handle_campaign_generation_flow(chat, user, conversation_id, post_data)
            else:
                # Default flow - send the prompt as the message
                response = chat.send_message(prompt)

                if response.text:
                    # Save the updated history back to database
                    if user:
                        updated_history = chat.history
                        serializable_history = self._convert_history_to_serializable(
                            updated_history)
                        chat_history_obj, created = ChatHistory.objects.get_or_create(
                            user=user, conversation_id=conversation_id)
                        chat_history_obj.set_history(serializable_history)
                        chat_history_obj.save()

                    return response.text
                else:
                    raise Exception("Empty response from Gemini API")

        except Exception as e:
            raise Exception(f"Falha na comunicação com Gemini: {str(e)}")

    def _handle_campaign_generation_flow(self, chat, user: User, conversation_id: str, post_data: dict = None) -> str:
        """Handle campaign generation flow with historical analysis."""
        try:
            # Import prompt service

            # Call special prompt for historical analysis
            analysis_prompt = prompt_service.build_historical_analysis_prompt(
                post_data)
            response = chat.send_message(analysis_prompt)

            if response.text:
                # Parse the JSON response
                try:
                    analysis_data = response.text.strip('`')
                except json.JSONDecodeError as e:
                    raise Exception(f"Failed to parse analysis JSON: {str(e)}")

                updated_prompt = prompt_service.build_automatic_post_prompt(
                    analysis_data)
                content_gen_res = chat.send_message(updated_prompt)

                # Save the analysis interaction to chat history
                if user:
                    updated_history = chat.history
                    serializable_history = self._convert_history_to_serializable(
                        updated_history)
                    chat_history_obj, created = ChatHistory.objects.get_or_create(
                        user=user, conversation_id=conversation_id)
                    chat_history_obj.set_history(serializable_history)
                    chat_history_obj.save()

                return content_gen_res.text
            else:
                raise Exception("Empty response from historical analysis")

        except Exception as e:
            raise Exception(f"Failed in campaign generation flow: {str(e)}")
