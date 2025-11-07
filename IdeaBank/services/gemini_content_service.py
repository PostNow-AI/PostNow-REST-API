"""
Gemini Content Service for AI-powered content generation.
"""

import logging
from typing import Dict

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory
from .credit_validation_service import CreditValidationService

logger = logging.getLogger(__name__)


class GeminiContentService:
    """Service for generating content using Gemini AI."""

    def __init__(self):
        self.ai_service_factory = AIServiceFactory()
        self.credit_service = CreditValidationService()
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'

    def generate_content(self, prompt: str, user: User = None, post_data: Dict = None) -> str:
        """
        Generate content using Gemini AI.

        Args:
            prompt: The content generation prompt
            user: The user requesting the generation
            post_data: Post data for context

        Returns:
            Generated content string
        """
        model_name = self.default_model

        # Estimate tokens and validate credits
        if user:
            estimated_tokens = self.credit_service.estimate_tokens(
                prompt, model_name)
            if not self.credit_service.validate_credits(user, model_name, estimated_tokens):
                raise ValueError("Créditos insuficientes para gerar conteúdo")

        # Get AI service
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            raise ValueError(
                "Gemini service not available for content generation")

        try:
            # Generate content using the AI service
            content = ai_service._make_ai_request(
                prompt, model_name, user=user, post_data=post_data)

            if not content:
                raise ValueError("Failed to generate content - empty response")

            # Deduct credits based on actual usage
            if user:
                actual_tokens = self.credit_service.estimate_tokens(
                    content, model_name)
                self.credit_service.deduct_credits(
                    user, model_name, actual_tokens, "Content generation")

            logger.info(
                f"Content generated successfully for user {user.id if user else 'anonymous'}")

            return content

        except Exception as e:
            logger.error(f"Failed to generate content: {str(e)}")
            raise ValueError(f"Failed to generate content: {str(e)}")

    def handle_campaign_generation_flow(self, chat, user: User, post_data: Dict = None) -> str:
        """
        Handle the campaign generation flow for complex multi-post campaigns.

        Args:
            chat: The chat session object
            user: The user requesting the campaign
            post_data: Post data for context

        Returns:
            Generated campaign content
        """
        try:
            # This would contain the logic for handling campaign generation
            # For now, delegate to the actual Gemini service
            ai_service = self.ai_service_factory.create_service(
                self.default_provider, self.default_model)
            if ai_service and hasattr(ai_service, '_handle_campaign_generation_flow'):
                return ai_service._handle_campaign_generation_flow(chat, user, post_data)

            logger.error("Campaign generation flow not available")
            return ""

        except Exception as e:
            logger.error(f"Error in campaign generation flow: {str(e)}")
            return ""

    def parse_campaign_response(self, full_content: str) -> Dict[str, str]:
        """
        Parse campaign response into structured data.

        Args:
            full_content: Raw campaign content from AI

        Returns:
            Dictionary with parsed campaign data
        """
        try:
            # This would contain the logic to parse campaign responses
            # For now, delegate to the actual Gemini service
            ai_service = self.ai_service_factory.create_service(
                self.default_provider, self.default_model)
            if ai_service and hasattr(ai_service, '_parse_campaign_response'):
                return ai_service._parse_campaign_response(full_content)

            logger.error("Campaign response parsing not available")
            return {}

        except Exception as e:
            logger.error(f"Error parsing campaign response: {str(e)}")
            return {}

    def clean_and_validate_html(self, content: str) -> str:
        """
        Clean and validate HTML content.

        Args:
            content: Raw content that may contain HTML

        Returns:
            Cleaned and validated content
        """
        try:
            # This would contain HTML cleaning and validation logic
            # For now, delegate to the actual Gemini service
            ai_service = self.ai_service_factory.create_service(
                self.default_provider, self.default_model)
            if ai_service and hasattr(ai_service, '_clean_and_validate_html'):
                return ai_service._clean_and_validate_html(content)

            # Basic HTML cleaning as fallback
            import re
            # Remove script and style tags
            content = re.sub(r'<script[^>]*>.*?</script>',
                             '', content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r'<style[^>]*>.*?</style>',
                             '', content, flags=re.DOTALL | re.IGNORECASE)
            # Remove other potentially dangerous tags
            dangerous_tags = ['iframe', 'object', 'embed', 'form', 'input']
            for tag in dangerous_tags:
                content = re.sub(
                    f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.DOTALL | re.IGNORECASE)

            return content.strip()

        except Exception as e:
            logger.error(f"Error cleaning HTML content: {str(e)}")
            return content  # Return original content on error
