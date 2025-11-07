"""
Content Generation Service for AI-powered content creation.
"""

import logging
from typing import Dict

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory
from .credit_validation_service import CreditValidationService
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """Service for generating AI-powered content."""

    def __init__(self):
        self.ai_service_factory = AIServiceFactory()
        self.credit_service = CreditValidationService()
        self.prompt_service = PromptService()
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'

    def generate_content(self, user: User, post_data: Dict) -> Dict:
        """
        Generate AI content for a post.

        Args:
            user: The user requesting the generation
            post_data: Dictionary containing post information

        Returns:
            Dictionary containing the generated content
        """
        provider = self.default_provider
        model = self.default_model

        # Set user on prompt service for profile access
        self.prompt_service.user = user

        # Build the prompt for content generation
        prompt = self.prompt_service.build_content_prompt(post_data)

        # Validate credits before generating
        estimated_tokens = self.credit_service.estimate_tokens(prompt, model)
        if not self.credit_service.validate_credits(user, model, estimated_tokens):
            raise ValueError("Créditos insuficientes para gerar conteúdo")

        # Create AI service
        ai_service = self.ai_service_factory.create_service(provider, model)
        if not ai_service:
            raise ValueError(
                f"AI service not available for provider: {provider}")

        try:
            # Generate content using the AI service
            content = self._generate_content_with_ai(
                ai_service, prompt, post_data)

            # Deduct credits after successful generation
            actual_tokens = self.credit_service.estimate_tokens(
                prompt + content, model)
            self.credit_service.deduct_credits(
                user, model, actual_tokens, f"Geração de conteúdo - {post_data.get('name', 'Post')}")

            logger.info(f"Content generated successfully for user {user.id}")

            return {
                'content': content,
                'ai_provider': provider,
                'ai_model': model,
                'status': 'success'
            }

        except Exception as e:
            logger.error(
                f"Failed to generate content for user {user.id}: {str(e)}")
            raise ValueError(f"Failed to generate content: {str(e)}")

    def regenerate_content(self, user: User, post_data: Dict, current_content: str,
                           user_prompt: str = None, ai_provider: str = None,
                           ai_model: str = None) -> Dict:
        """
        Regenerate or edit existing post content.

        Args:
            user: The user requesting the regeneration
            post_data: Dictionary containing post information
            current_content: The current content to be improved
            user_prompt: Optional user prompt for specific changes
            ai_provider: AI provider preference
            ai_model: Specific AI model to use

        Returns:
            Dictionary containing the regenerated content
        """
        # Set provider and model with defaults
        provider = ai_provider or self.default_provider
        model = ai_model or self.default_model

        # Build the regeneration prompt
        if user_prompt:
            prompt = self.prompt_service.build_regeneration_prompt(
                current_content, user_prompt)
        else:
            prompt = self.prompt_service.build_variation_prompt(
                current_content)

        # Validate credits before regenerating
        estimated_tokens = self.credit_service.estimate_tokens(prompt, model)
        if not self.credit_service.validate_credits(user, model, estimated_tokens):
            raise ValueError("Créditos insuficientes para regenerar conteúdo")

        # Create AI service
        ai_service = self.ai_service_factory.create_service(provider, model)
        if not ai_service:
            raise ValueError(
                f"AI service not available for provider: {provider}")

        try:
            content = self._generate_content_with_ai(
                ai_service, prompt, post_data)

            # Clean and validate HTML content
            content = self._clean_and_validate_html(content)

            # Deduct credits after successful regeneration
            actual_tokens = self.credit_service.estimate_tokens(
                prompt + content, model)
            self.credit_service.deduct_credits(
                user, model, actual_tokens, f"Regeneração de conteúdo - {post_data.get('name', 'Post')}")

            logger.info(f"Content regenerated successfully for user {user.id}")

            return {
                'content': content,
                'ai_provider': provider,
                'ai_model': model,
                'status': 'success'
            }

        except Exception as e:
            logger.error(
                f"Failed to regenerate content for user {user.id}: {str(e)}")
            raise ValueError(f"Failed to regenerate content: {str(e)}")

    def _generate_content_with_ai(self, ai_service, prompt: str, post_data: dict = None) -> str:
        """Generate content using the AI service."""
        try:
            # Use the AI service's direct method
            response_text = ai_service._make_ai_request(
                prompt, ai_service.model_name, user=getattr(self, 'user', None), post_data=post_data)

            if response_text and response_text.strip():
                cleaned_content = response_text.strip()
                return cleaned_content
            else:
                raise ValueError("Empty response from AI service")

        except Exception as e:
            logger.error(f"Error generating content with AI service: {str(e)}")
            raise

    def _clean_and_validate_html(self, content: str) -> str:
        """
        Clean and validate HTML content to ensure it's browser-compatible.
        """
        import re

        try:
            # Check if content contains HTML
            if not re.search(r'<[^>]+>', content):
                return content  # Return as-is if no HTML tags found

            # Fix common HTML issues
            cleaned_content = content

            # 1. Ensure proper HTML structure - wrap content if it doesn't have a root element
            if not re.search(r'^\s*<(html|body|div|article|section)', cleaned_content, re.IGNORECASE):
                # Check if we have block-level elements that need wrapping
                if re.search(r'<(h[1-6]|p|div|ul|ol|li|blockquote)', cleaned_content, re.IGNORECASE):
                    cleaned_content = f'<div>{cleaned_content}</div>'

            # 2. Fix unclosed tags for common HTML elements
            # Match opening tags that might not be properly closed
            opening_tags = re.findall(
                r'<(\w+)(?:\s[^>]*)?>(?![^<]*</\1>)', cleaned_content, re.IGNORECASE)
            self_closing_tags = {'br', 'hr', 'img', 'input', 'meta', 'link',
                                 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}

            for tag in opening_tags:
                if tag.lower() not in self_closing_tags:
                    # Check if the tag is actually unclosed by counting occurrences
                    open_count = len(re.findall(
                        rf'<{tag}(?:\s[^>]*)?>(?!</)', cleaned_content, re.IGNORECASE))
                    close_count = len(re.findall(
                        rf'</{tag}>', cleaned_content, re.IGNORECASE))

                    if open_count > close_count:
                        # Add missing closing tags at the end
                        for _ in range(open_count - close_count):
                            cleaned_content += f'</{tag}>'

            # 3. Fix malformed attributes (remove quotes inside attribute values)
            cleaned_content = re.sub(
                r'(\w+="[^"]*)"([^"]*")', r'\1\2', cleaned_content)

            # 4. Ensure proper nesting - fix common nesting issues
            # Fix p tags containing block elements (browsers auto-close p tags before block elements)
            cleaned_content = re.sub(r'<p([^>]*)>([^<]*)<(div|h[1-6]|ul|ol|blockquote)',
                                     r'<p\1>\2</p><\3', cleaned_content, flags=re.IGNORECASE)

            # 5. Remove or escape potentially problematic characters
            # Replace smart quotes with regular quotes
            cleaned_content = cleaned_content.replace(
                '"', '"').replace('"', '"')
            cleaned_content = cleaned_content.replace(
                ''', "'").replace(''', "'")

            # 6. Validate and fix common HTML entities
            common_entities = {
                '&amp;': '&',
                '&lt;': '<',
                '&gt;': '>',
                '&quot;': '"',
                '&apos;': "'"
            }

            # First decode entities, then re-encode only the necessary ones
            for entity, char in common_entities.items():
                cleaned_content = cleaned_content.replace(entity, char)

            # Don't over-encode HTML content - browsers handle this well
            # Just ensure dangerous characters in text content are properly handled
            # Remove any double-encoded entities first
            cleaned_content = re.sub(r'&amp;(\w+);', r'&\1;', cleaned_content)
            cleaned_content = re.sub(
                r'&lt;(\w+)&gt;', r'<\1>', cleaned_content)

            # 7. Ensure proper line breaks for readability
            cleaned_content = re.sub(r'>\s*\n\s*<', '>\n<', cleaned_content)

            return cleaned_content.strip()

        except Exception:
            # If cleaning fails, return original content
            return content
