"""
Gemini Image Service for AI-powered image generation.
"""

import logging
from typing import Dict, Optional

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory
from .credit_validation_service import CreditValidationService

logger = logging.getLogger(__name__)


class GeminiImageService:
    """Service for generating images using Gemini AI."""

    def __init__(self):
        self.ai_service_factory = AIServiceFactory()
        self.credit_service = CreditValidationService()
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'

    def generate_image(self, prompt: str, current_image: str = "", user: User = None,
                       post_data: Dict = None, idea_content: str = "") -> str:
        """
        Generate an image using Gemini AI.

        Args:
            prompt: The image generation prompt
            current_image: Current image for regeneration (optional)
            user: The user requesting the generation
            post_data: Post data for context
            idea_content: Content for context

        Returns:
            Generated image URL or base64 data
        """
        model_name = self.default_model

        # Validate credits before generation
        if user and not self.credit_service.validate_image_credits(user, model_name, 1):
            raise ValueError("Créditos insuficientes para gerar imagem")

        # Get AI service
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            raise ValueError(
                "Gemini service not available for image generation")

        try:
            # Generate image using the AI service
            image_url = ai_service.generate_image(
                prompt, current_image, user, post_data, idea_content)

            if not image_url:
                raise ValueError("Failed to generate image - no URL returned")

            # Credit deduction is handled inside ai_service.generate_image()
            # via AIModelService.deduct_image_credits

            logger.info(
                f"Image generated successfully for user {user.id if user else 'anonymous'}")

            return image_url

        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            raise ValueError(f"Failed to generate image: {str(e)}")

    def enhance_image_prompt(self, base_prompt: str, post_data: Dict = None,
                             idea_content: str = "") -> str:
        """
        Enhance an image generation prompt with additional context.

        Args:
            base_prompt: The base prompt to enhance
            post_data: Post data for context
            idea_content: Content for context

        Returns:
            Enhanced prompt string
        """
        try:
            enhancements = []

            # Add post type specific enhancements
            if post_data:
                post_type = post_data.get('type', '').lower()
                if post_type == 'feed':
                    enhancements.append(
                        "Formato: imagem quadrada adequada para feed do Instagram/Facebook")
                elif post_type == 'story':
                    enhancements.append(
                        "Formato: imagem vertical adequada para stories do Instagram")
                elif post_type == 'reels':
                    enhancements.append(
                        "Formato: thumbnail atraente para vídeo curto")

            # Add content-based enhancements
            if idea_content:
                content_length = len(idea_content)
                if content_length < 100:
                    enhancements.append("Estilo: minimalista e direto")
                elif content_length < 500:
                    enhancements.append(
                        "Estilo: equilibrado com elementos visuais")
                else:
                    enhancements.append(
                        "Estilo: rico em detalhes e informação")

            # Add quality enhancements
            enhancements.extend([
                "Qualidade: alta resolução, profissional",
                "Cores: vibrantes mas não excessivas",
                "Composição: bem equilibrada e atraente"
            ])

            # Combine enhancements
            if enhancements:
                enhanced_prompt = base_prompt + "\n\nRequisitos adicionais:\n" + \
                    "\n".join(f"- {enh}" for enh in enhancements)
                return enhanced_prompt

            return base_prompt

        except Exception as e:
            logger.error(f"Error enhancing image prompt: {str(e)}")
            return base_prompt  # Return original prompt on error

    def extract_image_bytes(self, response, model_name: str, post_data: Dict = None) -> Optional[bytes]:
        """
        Extract image bytes from AI response.

        Args:
            response: AI response containing image data
            model_name: The model used for generation
            post_data: Post data for context

        Returns:
            Image bytes or None if extraction failed
        """
        try:
            # This would contain the logic to extract image bytes from Gemini response
            # For now, delegate to the actual Gemini service
            ai_service = self.ai_service_factory.create_service(
                self.default_provider, model_name)
            if ai_service and hasattr(ai_service, '_extract_image_bytes'):
                return ai_service._extract_image_bytes(response, model_name, post_data)

            logger.error("Image byte extraction not available")
            return None

        except Exception as e:
            logger.error(f"Error extracting image bytes: {str(e)}")
            return None

    def save_image_to_s3(self, image_bytes: bytes, user: User = None, post_data: Dict = None) -> str:
        """
        Save image bytes to S3 storage.

        Args:
            image_bytes: The image data to save
            user: The user who owns the image
            post_data: Post data for context

        Returns:
            S3 URL of the saved image
        """
        try:
            # This would contain the logic to save to S3
            # For now, delegate to the actual Gemini service
            ai_service = self.ai_service_factory.create_service(
                self.default_provider, self.default_model)
            if ai_service and hasattr(ai_service, '_save_image_to_s3'):
                return ai_service._save_image_to_s3(image_bytes, user, post_data)

            logger.error("S3 image saving not available")
            return ""

        except Exception as e:
            logger.error(f"Error saving image to S3: {str(e)}")
            return ""
