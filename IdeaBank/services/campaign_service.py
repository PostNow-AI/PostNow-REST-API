"""
Campaign Service for managing AI-powered social media campaigns.
"""

import logging
from typing import Dict, List

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory
from .credit_validation_service import CreditValidationService
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing AI-powered social media campaigns."""

    def __init__(self):
        self.ai_service_factory = AIServiceFactory()
        self.credit_service = CreditValidationService()
        self.prompt_service = PromptService()
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'

    def generate_campaign(self, user: User, campaign_data: Dict) -> Dict:
        """
        Generate a complete social media campaign.

        Args:
            user: The user requesting the campaign
            campaign_data: Dictionary containing campaign information

        Returns:
            Dictionary with generated campaign content
        """
        model_name = self.default_model

        # Validate credits before generation
        if not self.credit_service.validate_credits(user, model_name, 1):
            raise ValueError("Créditos insuficientes para gerar campanha")

        # Use Google for campaign generation by default
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            raise ValueError(
                "Google service not available for campaign generation")

        # Set user on prompt service for profile access
        self.prompt_service.user = user

        try:
            # Build campaign prompt
            prompt = self.prompt_service.build_campaign_prompt(campaign_data)

            # Generate campaign content
            campaign_content = ai_service.generate_campaign(
                prompt, user, campaign_data)

            if not campaign_content:
                raise ValueError(
                    "Failed to generate campaign - no content returned")

            # Credit deduction is handled inside ai_service.generate_campaign()
            # via AIModelService.deduct_credits

            logger.info(f"Campaign generated successfully for user {user.id}")

            return campaign_content

        except Exception as e:
            logger.error(
                f"Failed to generate campaign for user {user.id}: {str(e)}")
            raise ValueError(f"Failed to generate campaign: {str(e)}")

    def generate_campaign_posts(self, user: User, campaign_data: Dict,
                                num_posts: int = 5) -> List[Dict]:
        """
        Generate multiple posts for a campaign.

        Args:
            user: The user requesting the posts
            campaign_data: Dictionary containing campaign information
            num_posts: Number of posts to generate

        Returns:
            List of dictionaries with generated post content
        """
        model_name = self.default_model

        # Validate credits before generation
        if not self.credit_service.validate_credits(user, model_name, num_posts):
            raise ValueError(
                f"Créditos insuficientes para gerar {num_posts} posts")

        # Use Google for post generation by default
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            raise ValueError(
                "Google service not available for post generation")

        # Set user on prompt service for profile access
        self.prompt_service.user = user

        try:
            # Build campaign posts prompt
            prompt = self.prompt_service.build_campaign_posts_prompt(
                campaign_data, num_posts)

            # Generate campaign posts
            posts_content = ai_service.generate_campaign_posts(
                prompt, user, campaign_data, num_posts)

            if not posts_content:
                raise ValueError(
                    "Failed to generate campaign posts - no content returned")

            # Credit deduction is handled inside ai_service.generate_campaign_posts()
            # via AIModelService.deduct_credits

            logger.info(
                f"Campaign posts generated successfully for user {user.id}")

            return posts_content

        except Exception as e:
            logger.error(
                f"Failed to generate campaign posts for user {user.id}: {str(e)}")
            raise ValueError(f"Failed to generate campaign posts: {str(e)}")

    def optimize_campaign_content(self, user: User, campaign_data: Dict,
                                  existing_content: str) -> Dict:
        """
        Optimize existing campaign content.

        Args:
            user: The user requesting optimization
            campaign_data: Dictionary containing campaign information
            existing_content: The existing content to optimize

        Returns:
            Dictionary with optimized campaign content
        """
        model_name = self.default_model

        # Validate credits before optimization
        if not self.credit_service.validate_credits(user, model_name, 1):
            raise ValueError("Créditos insuficientes para otimizar campanha")

        # Use Google for content optimization by default
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            raise ValueError(
                "Google service not available for content optimization")

        # Set user on prompt service for profile access
        self.prompt_service.user = user

        try:
            # Build optimization prompt
            prompt = self.prompt_service.build_campaign_optimization_prompt(
                campaign_data, existing_content)

            # Optimize campaign content
            optimized_content = ai_service.optimize_campaign_content(
                prompt, user, campaign_data, existing_content)

            if not optimized_content:
                raise ValueError(
                    "Failed to optimize campaign content - no content returned")

            # Credit deduction is handled inside ai_service.optimize_campaign_content()
            # via AIModelService.deduct_credits

            logger.info(
                f"Campaign content optimized successfully for user {user.id}")

            return optimized_content

        except Exception as e:
            logger.error(
                f"Failed to optimize campaign content for user {user.id}: {str(e)}")
            raise ValueError(f"Failed to optimize campaign content: {str(e)}")
