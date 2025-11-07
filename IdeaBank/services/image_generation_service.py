"""
Image Generation Service for AI-powered image creation.
"""

import logging
from typing import Dict

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory
from .credit_validation_service import CreditValidationService
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating AI-powered images."""

    def __init__(self):
        self.ai_service_factory = AIServiceFactory()
        self.credit_service = CreditValidationService()
        self.prompt_service = PromptService()
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'

    def generate_image(self, user: User, post_data: Dict, content: str,
                       custom_prompt: str = None, regenerate: bool = False) -> str:
        """
        Generate an image for the post using AI.

        Args:
            user: The user requesting the generation
            post_data: Dictionary containing post information
            content: The generated content for context
            custom_prompt: Optional custom prompt for image generation
            regenerate: Whether this is a regeneration request

        Returns:
            URL or base64 data of the generated image
        """
        model_name = self.default_model

        # Validate credits before generation
        if not self.credit_service.validate_image_credits(user, model_name, 1):
            raise ValueError("Créditos insuficientes para gerar imagem")

        # Use Google for image generation by default
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            raise ValueError(
                "Google service not available for image generation")

        # Set user on prompt service for profile access
        self.prompt_service.user = user

        # Build image prompt
        if regenerate:
            prompt = self.prompt_service.build_image_regeneration_prompt(
                custom_prompt or "")
        else:
            prompt = self.prompt_service.build_image_prompt(post_data, content)

        try:
            # Get current image for regeneration
            current_image = None
            if regenerate:
                current_image = self._get_current_image_for_regeneration(
                    post_data)

            # Generate image using the AI service
            if current_image:
                image_url = ai_service.generate_image(
                    prompt, current_image, user, post_data, content)
            else:
                image_url = ai_service.generate_image(
                    prompt, '', user, post_data, content)

            if not image_url:
                raise ValueError("Failed to generate image - no URL returned")

            # Credit deduction is handled inside ai_service.generate_image()
            # via AIModelService.deduct_image_credits

            logger.info(f"Image generated successfully for user {user.id}")

            return image_url

        except Exception as e:
            logger.error(
                f"Failed to generate image for user {user.id}: {str(e)}")
            raise ValueError(f"Failed to generate image: {str(e)}")

    def _get_current_image_for_regeneration(self, post_data: Dict) -> str:
        """
        Get the current image for regeneration from post data.

        Args:
            post_data: Dictionary containing post information

        Returns:
            Current image URL or empty string
        """
        try:
            # Try different ways to get the post idea with current image
            post_idea = None

            # Method 1: If post_data contains a post_idea_id
            if post_data.get('post_idea_id'):
                from IdeaBank.models import PostIdea
                post_idea = PostIdea.objects.filter(
                    id=post_data.get('post_idea_id')).first()

            # Method 2: If post_data contains a post_id, get the latest PostIdea for that post
            elif post_data.get('post_id'):
                from IdeaBank.models import Post, PostIdea
                post = Post.objects.filter(id=post_data.get('post_id')).first()
                if post:
                    post_idea = PostIdea.objects.filter(
                        post=post).order_by('-created_at').first()

            # Method 3: If we have a post object directly
            elif post_data.get('post'):
                from IdeaBank.models import PostIdea
                post_idea = PostIdea.objects.filter(
                    post=post_data.get('post')).order_by('-created_at').first()

            return post_idea.image_url if (post_idea and post_idea.image_url) else ""

        except Exception as e:
            logger.warning(
                f"Error getting current image for regeneration: {str(e)}")
            return ""
