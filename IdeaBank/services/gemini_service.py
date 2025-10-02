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
    def generate_image(self, prompt: str, current_image: str, user: User = None, post_data: dict = None, idea_content: str = None) -> str:
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
            # Try different model names for image generation with fallbacks
            model_names = [
                'gemini-2.5-flash-image-preview',
                # 'gemini-2.0-flash-exp',           # Latest experimental model
                # 'gemini-1.5-flash',               # Stable fallback
                # 'gemini-2.5-flash-image',         # Original model
                # 'gemini-1.5-pro',                 # Pro model fallback
            ]

            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)

                    # When calling model.generate_content, include image if provided

                    # Prepare image data for the request
                    image_bytes = None

                    if current_image:
                        image_bytes = extract_base64_image(current_image)
                    elif post_data and post_data.get('type') in ['story', 'reel']:
                        # Create empty white vertical image for stories/reels
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
                    # Check if response has image data
                    compressed_data = self._handle_compression(
                        response, model_name, post_data)

                    # Final safety check
                    if compressed_data:
                        # compressed_data_bytes = self._generate_text(
                        #     post_data, compressed_data, user)
                        # compressed_data = self._compress_image_data(
                        #     compressed_data_bytes, post_data)
                        # if not compressed_data:
                        #     print(
                        #         f"❌ Failed to compress image after adding text for model: {model_name}")
                        #     continue

                        # Deduct credits for successful image generation
                        deduct_credits_for_image(
                            " (inline data)")
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

    def _generate_text(self, post_data: dict, image: str, user: User = None) -> bytes:
        """Inserts text from post data into the image using Pillow and returns the modified image as bytes.

        Args:
            post_data (dict): Post data containing name, objective, and further_details.
            image (str): Base64 image data URL.
            user (User): User object to get color palette from creator profile.

        Returns:
            bytes: The modified image as bytes.
        """
        try:
            import io

            from PIL import Image

            # Extract text from post data
            overlay_text = self._extract_text_from_post_data(post_data)

            if not overlay_text:
                print("⚠️ No text found in post data")
                # Return original image as bytes
                return extract_base64_image(image)

            print(f"📝 Extracted text: {overlay_text}")

            # Get user's color palette
            text_color = self._get_user_text_color(user)
            print(f"🎨 Using text color: {text_color}")

            # Convert image from data URL to PIL Image
            image_bytes = extract_base64_image(image)
            pil_image = Image.open(io.BytesIO(image_bytes))

            # Add text to image
            modified_image = self._add_text_to_image(
                pil_image, overlay_text, text_color)

            # Convert back to bytes
            buffer = io.BytesIO()
            modified_image.save(buffer, format='PNG')
            return buffer.getvalue()

        except Exception as e:
            print(f"❌ Error in _generate_text: {str(e)}")
            # Return original image as fallback
            try:
                return extract_base64_image(image)
            except Exception:
                return b""

    def _extract_text_from_post_data(self, post_data: dict) -> str:
        """Extract text from post data (name, objective, further_details).

        Args:
            post_data (dict): Post data containing text fields.

        Returns:
            str: Combined text or empty string if none found.
        """
        if not post_data:
            return ""

        text_parts = []

        # Get name (title/heading)
        if post_data.get('name'):
            text_parts.append(post_data['name'].strip())

        # Get objective (main message)
        if post_data.get('objective'):
            text_parts.append(post_data['objective'].strip())

        # Get further details (additional info)
        if post_data.get('further_details'):
            text_parts.append(post_data['further_details'].strip())

        if not text_parts:
            return ""

        # Combine text parts with line breaks
        combined_text = '\n'.join(text_parts)

        # Clean up the text
        # Normalize whitespace but keep line breaks
        combined_text = re.sub(
            r'\s+', ' ', combined_text.replace('\n', ' \n '))

        print(f"📝 Text parts found: {len(text_parts)}")
        return combined_text

    def _get_user_text_color(self, user: User = None) -> tuple:
        """Get text color from user's creator profile color palette.

        Args:
            user (User): User object to get color palette from.

        Returns:
            tuple: RGB color tuple (r, g, b, a) for text.
        """
        if not user:
            return (255, 255, 255, 255)  # Default white

        try:
            # Try to import and get color palette from CreatorProfile
            from CreatorProfile.models import CreatorProfile

            profile = CreatorProfile.objects.filter(user=user).first()
            if not profile:
                print("⚠️ No creator profile found, using default white")
                return (255, 255, 255, 255)

            # Check for color palette fields (using current field names)
            color_1 = getattr(profile, 'color_1', None)
            color_2 = getattr(profile, 'color_2', None)
            color_3 = getattr(profile, 'color_3', None)
            color_4 = getattr(profile, 'color_4', None)
            color_5 = getattr(profile, 'color_5', None)

            # Use colors in priority order (color_1 is primary)
            if color_1:
                return self._parse_color(color_1)

            # Use color_2 as fallback
            if color_2:
                return self._parse_color(color_2)

            # Use color_3 as fallback
            if color_3:
                return self._parse_color(color_3)

            # Use color_4 as fallback
            if color_4:
                return self._parse_color(color_4)

            # Use color_5 as final fallback
            if color_5:
                return self._parse_color(color_5)

            print("⚠️ No colors found in creator profile, using default white")
            return (255, 255, 255, 255)

        except ImportError:
            print("⚠️ CreatorProfile model not available, using default white")
            return (255, 255, 255, 255)
        except Exception as e:
            print(
                f"⚠️ Error getting user color: {str(e)}, using default white")
            return (255, 255, 255, 255)

    def _parse_color(self, color_value) -> tuple:
        """Parse color value to RGB tuple.

        Args:
            color_value: Color value (hex string, rgb string, etc.)

        Returns:
            tuple: RGB color tuple (r, g, b, a).
        """
        if not color_value:
            return (255, 255, 255, 255)

        try:
            color_str = str(color_value).strip()

            # Handle hex colors (#RRGGBB or #RGB)
            if color_str.startswith('#'):
                color_str = color_str[1:]
                if len(color_str) == 3:
                    # Convert #RGB to #RRGGBB
                    color_str = ''.join([c*2 for c in color_str])
                if len(color_str) == 6:
                    r = int(color_str[0:2], 16)
                    g = int(color_str[2:4], 16)
                    b = int(color_str[4:6], 16)
                    return (r, g, b, 255)

            # Handle rgb(r,g,b) format
            if color_str.startswith('rgb(') and color_str.endswith(')'):
                rgb_values = color_str[4:-1].split(',')
                if len(rgb_values) == 3:
                    r = int(rgb_values[0].strip())
                    g = int(rgb_values[1].strip())
                    b = int(rgb_values[2].strip())
                    return (r, g, b, 255)

            # Handle named colors (basic ones)
            color_names = {
                'black': (0, 0, 0, 255),
                'white': (255, 255, 255, 255),
                'red': (255, 0, 0, 255),
                'green': (0, 255, 0, 255),
                'blue': (0, 0, 255, 255),
                'yellow': (255, 255, 0, 255),
                'cyan': (0, 255, 255, 255),
                'magenta': (255, 0, 255, 255),
            }

            if color_str.lower() in color_names:
                return color_names[color_str.lower()]

        except Exception as e:
            print(f"⚠️ Error parsing color '{color_value}': {str(e)}")

        # Default to white if parsing fails
        return (255, 255, 255, 255)

    def _parse_color_palette(self, palette) -> tuple:
        """Parse color palette to get a suitable text color.

        Args:
            palette: Color palette data (JSON, dict, or string).

        Returns:
            tuple: RGB color tuple (r, g, b, a).
        """
        try:
            import json

            if isinstance(palette, str):
                palette = json.loads(palette)

            if isinstance(palette, dict):
                # Look for common palette keys
                for key in ['primary', 'secondary', 'accent', 'text', 'foreground']:
                    if key in palette:
                        return self._parse_color(palette[key])

                # If palette has colors array
                if 'colors' in palette and isinstance(palette['colors'], list) and palette['colors']:
                    return self._parse_color(palette['colors'][0])

        except Exception as e:
            print(f"⚠️ Error parsing color palette: {str(e)}")

        return (255, 255, 255, 255)

    def _add_text_to_image(self, image, text: str, text_color: tuple = (255, 255, 255, 255)):
        """Add text to image using Pillow with non-serif font and no background.

        Args:
            image: PIL Image object.
            text (str): Text to add to the image.
            text_color (tuple): RGBA color tuple for text.

        Returns:
            PIL Image: Modified image with text overlay.
        """
        try:
            from PIL import ImageDraw

            # Create a copy to avoid modifying original
            img_copy = image.copy()
            draw = ImageDraw.Draw(img_copy)

            # Get image dimensions
            width, height = img_copy.size

            # Try to load non-serif fonts, fallback to system fonts
            font = self._load_font(width)

            # Split text into lines for multi-line support
            lines = text.split('\n')

            # Calculate total text dimensions
            line_heights = []
            line_widths = []

            for line in lines:
                if font:
                    bbox = draw.textbbox((0, 0), line.strip(), font=font)
                    line_width = bbox[2] - bbox[0]
                    line_height = bbox[3] - bbox[1]
                else:
                    # Estimate text size without font
                    line_width = len(line.strip()) * 8
                    line_height = 16

                line_widths.append(line_width)
                line_heights.append(line_height)

            # Get total height
            total_height = sum(line_heights) + \
                (len(lines) - 1) * 5  # 5px line spacing

            # Position text at bottom center with padding
            # Increased padding for cleaner look
            padding = max(30, height // 30)
            start_y = height - total_height - padding

            # Draw each line
            current_y = start_y
            for i, line in enumerate(lines):
                line_text = line.strip()
                if not line_text:
                    continue

                # Center each line individually
                line_width = line_widths[i]
                line_x = (width - line_width) // 2

                # Draw text without background (clean look)
                if font:
                    draw.text((line_x, current_y), line_text,
                              font=font, fill=text_color)
                else:
                    draw.text((line_x, current_y), line_text, fill=text_color)

                # Move to next line
                current_y += line_heights[i] + 5  # 5px line spacing

            return img_copy

        except ImportError:
            print("⚠️ PIL ImageDraw/ImageFont not available, returning original image")
            return image
        except Exception as e:
            print(f"❌ Error adding text to image: {str(e)}")
            return image

    def _load_font(self, image_width: int):
        """Load a non-serif font with dynamic sizing.

        Args:
            image_width (int): Width of the image for font sizing.

        Returns:
            PIL.ImageFont: Font object or None if not available.
        """
        try:
            from PIL import ImageFont

            # Dynamic font size based on image width
            # Larger base size for better readability
            font_size = max(28, image_width // 20)

            # Try different non-serif fonts in order of preference
            font_paths = [
                # Modern non-serif fonts
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Clean non-serif
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-Regular.ttf",

                # System fonts
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/Windows/Fonts/arial.ttf",  # Windows
                "/usr/share/fonts/truetype/fonts-go/Go-Regular.ttf",  # Go font

                # Fallback system fonts
                "/usr/share/fonts/TTF/arial.ttf",
                "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
            ]

            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    print(f"✅ Loaded font: {font_path} (size: {font_size})")
                    return font
                except Exception:
                    continue

            # Try to use default font as last resort
            try:
                font = ImageFont.load_default()
                print("⚠️ Using default PIL font")
                return font
            except Exception:
                print("❌ No fonts available")
                return None

        except ImportError:
            print("⚠️ PIL ImageFont not available")
            return None
        except Exception as e:
            print(f"❌ Error loading font: {str(e)}")
            return None

#     def _build_analisys_and_improvement_prompt(self) -> str:
#         prompt = """Você é um especialista em revisão ortográfica e design digital.
# Sua missão é analisar a IMAGEM_BASE fornecida, identificar todos os textos presentes nela e corrigir automaticamente qualquer erro de ortografia, gramática ou acentuação em *Português do Brasil (pt-BR)*.
# Depois da correção, o texto revisado deve ser aplicado na mesma imagem, sem alterar design, estilo ou layout.

# ### REGRAS DE EXECUÇÃO:

# 1. *Análise OCR*: identifique todos os textos contidos na imagem fornecida.

# 2. *Correção de texto*:
#    - Corrija automaticamente todos os erros de ortografia, acentuação e gramática segundo as normas do *Português do Brasil (Acordo Ortográfico)*.
#    - Nunca inventar palavras, nunca traduzir para outro idioma.
#    - Manter o texto simples, claro e natural, respeitando a ideia original.

# 3. *Aplicação no design*:
#    - Substitua apenas o texto incorreto pelos textos corrigidos.
#    - Não mude posição, tipografia, tamanho, cor ou estilo.
#    - Preserve 100% do layout e da identidade visual da imagem original.

# 4. *Idioma: todo texto final deve estar obrigatoriamente em **Português do Brasil (pt-BR)*, revisado e sem erros.

# 5. *Formato de saída*:
#    - Retorne *apenas 1 imagem final*, no mesmo formato da original (ex.: 1080x1920 px se for Story).
#    - A única diferença em relação à imagem original deve ser o texto corrigido.

# ---

# ### ENTRADA:
# - IMAGEM_BASE: [imagem gerada anteriormente]

# ---

# ### SAÍDA ESPERADA:
# - Uma única imagem final, idêntica à original em design, mas com todos os textos revisados e corrigidos para pt-BR perfeito.
# - Nenhum outro elemento deve ser alterado."""
#         return prompt

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
            f"Gere uma imagem de alta qualidade com base nesta descrição: {base_prompt}. Nao ADICIONE NENHUM TEXTO NA IMAGEM."]

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
