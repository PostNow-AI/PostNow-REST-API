import io
import os
import re
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont


class TextOverlayService:
    """Service for adding styled text overlays to images with bundled fonts for Vercel deployment."""

    def __init__(self):
        self.location_mapping = {
            'top-left': 'top_left',
            'top-center': 'top_center',
            'top-right': 'top_right',
            'center-left': 'center_left',
            'center-center': 'center_center',
            'center-right': 'center_right',
            'bottom-left': 'bottom_left',
            'bottom-center': 'bottom_center',
            'bottom-right': 'bottom_right'
        }

        # Base path for bundled fonts (adjust for your deployment structure)
        self.font_base_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'static', 'fonts')

    def add_text_overlay(self, image_bytes: bytes, text_config: Dict) -> bytes:
        """
        Add text overlays to image based on configuration.

        Args:
            image_bytes (bytes): Original image as bytes
            text_config (Dict): Configuration with titulo, sub-titulo, and cta sections

        Returns:
            bytes: Modified image with text overlays as bytes
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGBA for better text rendering
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Get image dimensions
            img_width, img_height = image.size

            # Calculate padding (5% of smallest dimension)
            padding = min(img_width, img_height) * 0.05

            # Create drawing context
            draw = ImageDraw.Draw(image)

            # Process each text element
            for text_type in ['titulo', 'sub-titulo', 'cta']:
                if text_type in text_config:
                    self._add_single_text(
                        draw, text_config[text_type],
                        img_width, img_height, padding
                    )

            # Convert back to bytes
            buffer = io.BytesIO()
            # Convert back to RGB for saving as JPEG/PNG
            if image.mode == 'RGBA':
                # Create white background for transparency
                background = Image.new('RGB', image.size, (255, 255, 255))
                # Use alpha channel as mask
                background.paste(image, mask=image.split()[-1])
                image = background

            image.save(buffer, format='PNG', quality=95, optimize=True)
            return buffer.getvalue()

        except Exception as e:
            print(f"❌ Error adding text overlay: {str(e)}")
            return image_bytes  # Return original if processing fails

    def _add_single_text(self, draw: ImageDraw.Draw, text_config: Dict,
                         img_width: int, img_height: int, padding: float):
        """Add a single text element to the image."""
        try:
            # Extract text content based on the key that exists
            content = (text_config.get('title-content') or
                       text_config.get('subtitle-content') or
                       text_config.get('cta-content') or '').strip()

            if not content:
                return

            # Get styling properties
            font_family = text_config.get('font-family', 'Arial')
            font_size = self._parse_font_size(
                text_config.get('font-size', '24px'), img_width)
            font_weight = text_config.get('font-weight', 'normal')
            color = self._parse_color(text_config.get('color', '#FFFFFF'))
            location = text_config.get('location', 'center-center')
            drop_shadow = text_config.get('drop-shadow', '')
            text_stroke = text_config.get('text-stroke', '')

            # Load font
            font = self._load_font(font_family, font_size, font_weight)

            # Calculate text dimensions and position
            text_bbox = draw.textbbox((0, 0), content, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            # Get position based on location
            x, y = self._calculate_position(
                location, img_width, img_height,
                text_width, text_height, padding
            )

            # Apply text stroke if specified
            if text_stroke:
                stroke_color, stroke_width = self._parse_text_stroke(
                    text_stroke)
                self._draw_text_with_stroke(
                    draw, content, (x,
                                    y), font, color, stroke_color, stroke_width
                )
            # Apply drop shadow if specified
            elif drop_shadow:
                shadow_color, shadow_offset = self._parse_drop_shadow(
                    drop_shadow)
                self._draw_text_with_shadow(
                    draw, content, (x,
                                    y), font, color, shadow_color, shadow_offset
                )
            else:
                # Simple text
                draw.text((x, y), content, font=font, fill=color)

        except Exception as e:
            print(f"⚠️ Error adding single text: {str(e)}")

    def _parse_font_size(self, font_size_str: str, img_width: int) -> int:
        """Parse font size string to integer pixels."""
        try:
            if isinstance(font_size_str, int):
                return font_size_str

            font_size_str = str(font_size_str).strip().lower()

            # Remove 'px' suffix if present
            if font_size_str.endswith('px'):
                return int(font_size_str[:-2])

            # Handle percentage (relative to image width)
            if font_size_str.endswith('%'):
                percentage = float(font_size_str[:-1])
                # Reasonable scaling
                return int(img_width * percentage / 100 / 20)

            # Handle em units (approximate)
            if font_size_str.endswith('em'):
                em_value = float(font_size_str[:-2])
                return int(em_value * 16)  # 1em ≈ 16px

            # Try to parse as plain number
            return int(float(font_size_str))

        except (ValueError, AttributeError):
            # Default size based on image width
            return max(24, img_width // 40)

    def _parse_color(self, color_str: str) -> Tuple[int, int, int, int]:
        """Parse color string to RGBA tuple."""
        try:
            color_str = str(color_str).strip()

            # Handle hex colors
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
                elif len(color_str) == 8:
                    r = int(color_str[0:2], 16)
                    g = int(color_str[2:4], 16)
                    b = int(color_str[4:6], 16)
                    a = int(color_str[6:8], 16)
                    return (r, g, b, a)

            # Handle rgb() and rgba() format
            rgb_match = re.match(
                r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', color_str)
            if rgb_match:
                r, g, b = int(rgb_match.group(1)), int(
                    rgb_match.group(2)), int(rgb_match.group(3))
                a = int(float(rgb_match.group(4)) *
                        255) if rgb_match.group(4) else 255
                return (r, g, b, a)

            # Handle named colors
            color_names = {
                'white': (255, 255, 255, 255),
                'black': (0, 0, 0, 255),
                'red': (255, 0, 0, 255),
                'green': (0, 128, 0, 255),
                'blue': (0, 0, 255, 255),
                'yellow': (255, 255, 0, 255),
                'cyan': (0, 255, 255, 255),
                'magenta': (255, 0, 255, 255),
                'orange': (255, 165, 0, 255),
                'purple': (128, 0, 128, 255),
                'gray': (128, 128, 128, 255),
                'grey': (128, 128, 128, 255),
            }

            if color_str.lower() in color_names:
                return color_names[color_str.lower()]

        except Exception as e:
            print(f"⚠️ Error parsing color '{color_str}': {str(e)}")

        # Default to white
        return (255, 255, 255, 255)

    def _load_font(self, font_family: str, font_size: int, font_weight: str) -> ImageFont.ImageFont:
        """Load font from bundled font files."""
        try:
            # Normalize font family name
            font_family = font_family.lower().replace(' ', '').replace('-', '')
            weight = 'bold' if font_weight.lower(
            ) in ['bold', '600', '700', '800', '900'] else 'normal'

            # Font file mapping for bundled fonts with fallbacks to system fonts
            font_files = {
                # Sans-serif fonts
                'poppins': {
                    'normal': 'Poppins-Regular.ttf',
                    'bold': 'Poppins-Bold.ttf'
                },
                'montserrat': {
                    'normal': 'Montserrat[wght].ttf',
                    # Variable font handles weights
                    'bold': 'Montserrat[wght].ttf'
                },
                'inter': {
                    'normal': 'Inter[opsz,wght].ttf',
                    # Variable font handles weights
                    'bold': 'Inter[opsz,wght].ttf'
                },
                'roboto': {
                    'normal': 'Roboto[wdth,wght].ttf',
                    # Variable font handles weights
                    'bold': 'Roboto[wdth,wght].ttf'
                },
                'opensans': {
                    'normal': 'OpenSans[wdth,wght].ttf',
                    # Variable font handles weights
                    'bold': 'OpenSans[wdth,wght].ttf'
                },
                'lato': {
                    'normal': 'Lato-Regular.ttf',
                    'bold': 'Lato-Bold.ttf'
                },
                'sourcesans': {
                    'normal': 'SourceSans3[wght].ttf',
                    # Variable font handles weights
                    'bold': 'SourceSans3[wght].ttf'
                },
                'sourcesans3': {
                    'normal': 'SourceSans3[wght].ttf',
                    # Variable font handles weights
                    'bold': 'SourceSans3[wght].ttf'
                },
                'nunito': {
                    'normal': 'Nunito[wght].ttf',
                    'bold': 'Nunito[wght].ttf'  # Variable font handles weights
                },
                'raleway': {
                    'normal': 'Raleway[wght].ttf',
                    # Variable font handles weights
                    'bold': 'Raleway[wght].ttf'
                },
                'quicksand': {
                    'normal': 'Quicksand[wght].ttf',
                    # Variable font handles weights
                    'bold': 'Quicksand[wght].ttf'
                },
                'comfortaa': {
                    'normal': 'Comfortaa[wght].ttf',
                    # Variable font handles weights
                    'bold': 'Comfortaa[wght].ttf'
                },
                'cabin': {
                    'normal': 'Cabin[wdth,wght].ttf',
                    # Variable font handles weights
                    'bold': 'Cabin[wdth,wght].ttf'
                },
                'exo': {
                    'normal': 'Exo2[wght].ttf',
                    'bold': 'Exo2[wght].ttf'  # Variable font handles weights
                },
                'exo2': {
                    'normal': 'Exo2[wght].ttf',
                    'bold': 'Exo2[wght].ttf'  # Variable font handles weights
                },
                'yanone': {
                    'normal': 'YanoneKaffeesatz[wght].ttf',
                    # Variable font handles weights
                    'bold': 'YanoneKaffeesatz[wght].ttf'
                },
                'yanonekaffeesatz': {
                    'normal': 'YanoneKaffeesatz[wght].ttf',
                    # Variable font handles weights
                    'bold': 'YanoneKaffeesatz[wght].ttf'
                },
                # Display and decorative fonts
                'oswald': {
                    'normal': 'Oswald[wght].ttf',
                    'bold': 'Oswald[wght].ttf'  # Variable font handles weights
                },
                'anton': {
                    'normal': 'Anton-Regular.ttf',
                    'bold': 'Anton-Regular.ttf'  # Same file for both
                },
                'bebas': {
                    'normal': 'BebasNeue-Regular.ttf',
                    'bold': 'BebasNeue-Regular.ttf'  # Same file for both
                },
                'bebasneue': {
                    'normal': 'BebasNeue-Regular.ttf',
                    'bold': 'BebasNeue-Regular.ttf'  # Same file for both
                },
                'fjalla': {
                    'normal': 'FjallaOne-Regular.ttf',
                    'bold': 'FjallaOne-Regular.ttf'  # Same file for both
                },
                'fjallaone': {
                    'normal': 'FjallaOne-Regular.ttf',
                    'bold': 'FjallaOne-Regular.ttf'  # Same file for both
                },
                'righteous': {
                    'normal': 'Righteous-Regular.ttf',
                    'bold': 'Righteous-Regular.ttf'  # Same file for both
                },
                # Serif fonts
                'playfair': {
                    'normal': 'PlayfairDisplay[wght].ttf',
                    # Variable font handles weights
                    'bold': 'PlayfairDisplay[wght].ttf'
                },
                'playfairdisplay': {
                    'normal': 'PlayfairDisplay[wght].ttf',
                    # Variable font handles weights
                    'bold': 'PlayfairDisplay[wght].ttf'
                },
                'merriweather': {
                    'normal': 'MerriweatherSans[wght].ttf',
                    # Variable font handles weights
                    'bold': 'MerriweatherSans[wght].ttf'
                },
                'merriweathersans': {
                    'normal': 'MerriweatherSans[wght].ttf',
                    # Variable font handles weights
                    'bold': 'MerriweatherSans[wght].ttf'
                },
                # Script and handwriting fonts
                'dancing': {
                    'normal': 'DancingScript[wght].ttf',
                    # Variable font handles weights
                    'bold': 'DancingScript[wght].ttf'
                },
                'dancingscript': {
                    'normal': 'DancingScript[wght].ttf',
                    # Variable font handles weights
                    'bold': 'DancingScript[wght].ttf'
                },
                'lobster': {
                    'normal': 'Lobster-Regular.ttf',
                    'bold': 'Lobster-Regular.ttf'  # Same file for both
                },
                'pacifico': {
                    'normal': 'Pacifico-Regular.ttf',
                    'bold': 'Pacifico-Regular.ttf'  # Same file for both
                }
            }

            # Find font family
            font_file = None
            for family_key in font_files:
                if family_key in font_family:
                    font_file = font_files[family_key].get(
                        weight, font_files[family_key]['normal'])
                    break

            # Default to Poppins if not found
            if not font_file:
                font_file = font_files['poppins']['normal']

            # Try bundled font first
            font_path = os.path.join(self.font_base_path, font_file)
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, font_size)

            # Fallback to system fonts for local development
            system_fonts = {
                'poppins': ['/home/matheussb/.local/share/fonts/google-fonts/poppins/Poppins-Regular.ttf',
                            '/home/matheussb/.local/share/fonts/google-fonts/poppins/Poppins-Bold.ttf'],
                'montserrat': ['/home/matheussb/.local/share/fonts/google-fonts/montserrat/Montserrat[wght].ttf'],
                'inter': ['/home/matheussb/.local/share/fonts/google-fonts/inter/Inter[opsz,wght].ttf'],
                'default': ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
            }

            # Try system fonts
            family_key = next(
                (k for k in system_fonts if k in font_family), 'default')
            for system_font in system_fonts[family_key]:
                try:
                    if os.path.exists(system_font):
                        return ImageFont.truetype(system_font, font_size)
                except Exception:
                    continue

            # Final fallback
            return ImageFont.load_default()

        except Exception as e:
            print(f"⚠️ Error loading font: {str(e)}")
            return ImageFont.load_default()

    def _calculate_position(self, location: str, img_width: int, img_height: int,
                            text_width: int, text_height: int, padding: float) -> Tuple[int, int]:
        """Calculate text position based on location string."""
        # Normalize location
        location = location.lower().replace('_', '-')

        # Define usable area (with padding)
        left = padding
        right = img_width - padding - text_width
        top = padding
        bottom = img_height - padding - text_height
        center_x = (img_width - text_width) // 2
        center_y = (img_height - text_height) // 2

        # Ensure positions don't go negative
        right = max(left, right)
        bottom = max(top, bottom)

        position_map = {
            'top-left': (left, top),
            'top-center': (center_x, top),
            'top-right': (right, top),
            'center-left': (left, center_y),
            'center-center': (center_x, center_y),
            'center-right': (right, center_y),
            'bottom-left': (left, bottom),
            'bottom-center': (center_x, bottom),
            'bottom-right': (right, bottom)
        }

        return position_map.get(location, (center_x, center_y))

    def _parse_drop_shadow(self, drop_shadow: str) -> Tuple[Tuple[int, int, int, int], Tuple[int, int]]:
        """Parse drop shadow string to color and offset."""
        try:
            # Example: "2px 2px 4px rgba(0,0,0,0.5)" or "2px 2px #000000"
            parts = drop_shadow.strip().split()

            if len(parts) >= 2:
                # Extract offset
                x_offset = int(parts[0].replace('px', ''))
                y_offset = int(parts[1].replace('px', ''))

                # Extract color (last part)
                color_part = parts[-1]
                shadow_color = self._parse_color(color_part)

                return shadow_color, (x_offset, y_offset)

        except Exception as e:
            print(f"⚠️ Error parsing drop shadow: {str(e)}")

        # Default shadow
        return (0, 0, 0, 128), (2, 2)

    def _parse_text_stroke(self, text_stroke: str) -> Tuple[Tuple[int, int, int, int], int]:
        """Parse text stroke string to color and width."""
        try:
            # Example: "2px #000000" or "1px rgba(0,0,0,1)"
            parts = text_stroke.strip().split()

            if len(parts) >= 2:
                width = int(parts[0].replace('px', ''))
                color = self._parse_color(parts[1])
                return color, width

        except Exception as e:
            print(f"⚠️ Error parsing text stroke: {str(e)}")

        # Default stroke
        return (0, 0, 0, 255), 1

    def _draw_text_with_shadow(self, draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
                               font: ImageFont.ImageFont, text_color: Tuple[int, int, int, int],
                               shadow_color: Tuple[int, int, int, int], shadow_offset: Tuple[int, int]):
        """Draw text with drop shadow effect."""
        x, y = position
        shadow_x, shadow_y = shadow_offset

        # Draw shadow first
        draw.text((x + shadow_x, y + shadow_y),
                  text, font=font, fill=shadow_color)

        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)

    def _draw_text_with_stroke(self, draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
                               font: ImageFont.ImageFont, text_color: Tuple[int, int, int, int],
                               stroke_color: Tuple[int, int, int, int], stroke_width: int):
        """Draw text with stroke/outline effect."""
        x, y = position

        # Draw stroke by drawing text in all directions
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text,
                              font=font, fill=stroke_color)

        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
