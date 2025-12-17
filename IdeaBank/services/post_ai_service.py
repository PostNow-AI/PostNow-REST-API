"""
Post AI Service for generating post ideas using AI models.
"""

import os
from typing import Dict

from django.contrib.auth.models import User
from django.db import transaction
from IdeaBank.models import Post, PostIdea

from .ai_service_factory import AIServiceFactory
from .base_ai_service import BaseAIService
from .prompt_service import PromptService


class PostAIService(BaseAIService):
    """Service for generating post ideas using AI models."""

    def __init__(self):
        super().__init__("gemini-2.5-flash")  # Initialize parent with default model
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'
        self.prompt_service = PromptService()

    def _validate_credits(self, user: User, estimated_tokens: int, model_name: str) -> bool:
        """Validate if user has sufficient credits for the AI operation."""
        if not user.is_authenticated:
            return True

        try:
            from .ai_model_service import AIModelService
            return AIModelService.validate_user_credits(user, model_name, estimated_tokens)
        except ImportError:
            return True

    def _deduct_credits(self, user: User, actual_tokens: int, model_name: str, description: str) -> bool:
        """Deduct credits after AI operation."""
        if not user.is_authenticated:
            return True

        try:
            from .ai_model_service import AIModelService
            return AIModelService.deduct_credits(user, model_name, actual_tokens, description)
        except ImportError:
            return True

    def _estimate_tokens(self, prompt: str, model_name: str) -> int:
        """Estimate token count for a prompt."""
        try:
            from .ai_model_service import AIModelService
            return AIModelService.estimate_tokens(prompt, model_name)
        except ImportError:
            return len(prompt) // 4

    def _make_ai_request(self, prompt: str, model_name: str, api_key: str = None, user: User = None, post_data: dict = None) -> str:
        """Make AI request using the AI service factory."""
        # Force to use only supported model
        if model_name != 'gemini-2.5-flash':
            model_name = 'gemini-2.5-flash'

        # Create AI service
        ai_service = AIServiceFactory.create_service('google', model_name)
        if not ai_service:
            raise Exception(
                f"AI service not available for provider: {self.default_provider}")

        # Make the request
        return ai_service._make_ai_request(prompt, model_name, api_key, user, post_data)

    def generate_post_content(
        self,
        user: User,
        post_data: Dict,
    ) -> Dict:
        """
        Generate AI content for a post based on the provided data.

        Args:
            user: The user requesting the generation
            post_data: Dictionary containing post information (name, objective, type, further details, include_image)
            ai_provider: AI provider preference (google)
            ai_model: gemini-2.5-flash

        Returns:
            Dictionary containing the generated content
        """
        provider = 'google'
        model = 'gemini-2.5-flash'
        # Store user and post_data for profile access
        self.user = user
        self._current_post_data = post_data

        # Set user on prompt service for profile access
        self.prompt_service.user = user

        # Special handling for campaign type - generate 3 posts
        if post_data.get('type', '').lower() == 'campaign':
            return self._generate_campaign_content(user, post_data, provider, model)

        # Build the prompt for content generation
        prompt = self.prompt_service.build_content_prompt(post_data)

        # Validate credits before generating (skip for unauthenticated users)
        if user and user.is_authenticated:
            estimated_tokens = self._estimate_tokens(prompt, model)
            if not self._validate_credits(user, estimated_tokens, model):
                raise Exception("Créditos insuficientes para gerar conteúdo")

        # Create AI service
        ai_service = AIServiceFactory.create_service('google', model)
        if not ai_service:
            raise Exception(
                f"AI service not available for provider: {provider}")

        # Generate content using the AI service
        try:
            # Use the AI service's direct method
            content = self._generate_content_with_ai(
                ai_service, prompt, post_data)

            # Deduct credits after successful generation (skip for unauthenticated users)
            if user and user.is_authenticated:
                actual_tokens = self._estimate_tokens(prompt + content, model)
                self._deduct_credits(
                    user, actual_tokens, model, f"Geração de conteúdo - {post_data.get('name', 'Post')}")

            # Special handling for feed posts - generate image if description is found
            image_url = None
            if post_data.get('type', '').lower() == 'feed':
                image_description = self._extract_image_description_from_content(
                    content)
                if image_description:
                    try:
                        image_url = self._generate_image_from_description(
                            ai_service, image_description, user, post_data, content)
                        # Remove image description from content after successful generation
                        content = self._remove_image_description_from_content(
                            content, image_description)
                    except Exception as e:
                        # Log image generation error but don't fail the entire request
                        print(
                            f"Failed to generate image for feed post: {str(e)}")

            response = {
                'content': content,
                'ai_provider': provider,
                'ai_model': model,
                'status': 'success'
            }

            if image_url:
                response['image_url'] = image_url

            return response
        except Exception as e:
            raise Exception(f"Failed to generate content: {str(e)}")

    def _generate_campaign_content(self, user: User, post_data: Dict, provider: str, model: str) -> Dict:
        """
        Special handler for campaign type - generates 3 posts (feed, reels, stories) from single AI response.
        """
        # Set user on prompt service for profile access
        self.prompt_service.user = user

        # Build the prompt for campaign generation
        prompt = self.prompt_service.build_content_prompt(post_data)

        # Create AI service
        ai_service = AIServiceFactory.create_service('google', model)
        if not ai_service:
            raise Exception(
                f"AI service not available for provider: {provider}")

        try:
            # Generate content using the AI service
            full_content = self._generate_content_with_ai(
                ai_service, prompt,  post_data)

            # Deduct credits after successful generation (skip for unauthenticated users)
            if user and user.is_authenticated:
                actual_tokens = self._estimate_tokens(
                    prompt + full_content, model)
                self._deduct_credits(
                    user, actual_tokens, model, f"Geração de campanha - {post_data.get('name', 'Campaign')}")

            # Parse the AI response into 3 separate contents
            parsed_content = self._parse_campaign_response(
                full_content.strip('`').strip('json'))

            # Extract image description for feed post
            feed_image_description = parsed_content.get(
                "feed_image_description", "")

            # Create 3 Post objects with their respective PostIdea objects
            created_posts = []
            with transaction.atomic():
                for post_type, content in parsed_content.items():
                    # Skip the image description - it's not a post type
                    if post_type == "feed_image_description":
                        continue

                    # Skip if content is empty
                    if not content or not content.strip():
                        continue

                    # Initialize image_url for this post
                    image_url = None

                    # Generate image for feed post if description is available
                    if post_type == "feed" and feed_image_description:
                        try:
                            print(
                                f"Generating image for feed post with description: {feed_image_description[:100]}...")
                            image_url = self._generate_image_from_description(
                                ai_service, feed_image_description, user, post_data, content)
                        except Exception as e:
                            print(
                                f"Failed to generate image for campaign feed post: {str(e)}")
                            # For campaign generation, image generation failure is critical
                            # Raise exception to fail the entire campaign generation
                            raise Exception(
                                f"Image generation failed for campaign feed post: {str(e)}")

                    # Create Post object
                    post = Post.objects.create(
                        user=user,
                        name=f"{post_data.get('name', 'Campaign')} - {post_type.title()}",
                        objective=post_data.get('objective', ''),
                        type=post_type.lower().strip('_html'),
                        further_details=post_data.get('further_details', ''),
                        include_image=post_data.get('include_image', False),
                        is_automatically_generated=post_data.get(
                            'is_automatically_generated', False),
                        is_active=post_data.get('is_active', True)
                    )

                    # Create PostIdea object
                    post_idea = PostIdea.objects.create(
                        post=post,
                        content=content,
                        image_url=image_url or '',
                        image_description=feed_image_description if post_type == "feed" else None
                    )

                    post_result = {
                        'post_id': post.id,
                        'post_idea_id': post_idea.id,
                        'type': post_type,
                        'content': content
                    }

                    if image_url:
                        post_result['image_url'] = image_url

                    created_posts.append(post_result)

            return {
                'posts': created_posts,
                'ai_provider': provider,
                'ai_model': model,
                'status': 'success',
                'campaign_mode': True
            }

        except Exception as e:
            raise Exception(f"Failed to generate campaign content: {str(e)}")

    def _parse_campaign_response(self, full_content: str) -> Dict[str, str]:
        """
        Parse the AI response into separate contents for feed, reels, and stories.
        """
        parsed = {'feed': '', 'reels': '',
                  'story': '', "feed_image_description": ""}

        try:
            import json

            # Remove markdown code block markers if present
            content_str = full_content.strip()
            if content_str.startswith('```json'):
                content_str = content_str[7:]  # Remove ```json
            elif content_str.startswith('```'):
                content_str = content_str[3:]  # Remove ```

            if content_str.endswith('```'):
                content_str = content_str[:-3]  # Remove trailing ```

            content_str = content_str.strip()

            # Parse JSON
            content = json.loads(content_str)

            # Extract fields
            parsed['feed'] = content.get('feed_html', '')
            parsed['reels'] = content.get('reels_html', '')
            parsed['story'] = content.get('story_html', '')
            parsed["feed_image_description"] = content.get(
                'feed_image_description', '')

        except json.JSONDecodeError:
            # If parsing fails, return empty
            parsed = {
                'feed': '',
                'reels': '',
                'story': '',
                'feed_image_description': ''
            }
        except Exception as e:
            print(f"Error parsing campaign response: {str(e)}")
            # If parsing fails, return empty
            parsed = {
                'feed': '',
                'reels': '',
                'story': '',
                'feed_image_description': ''
            }

        return parsed

    def generate_image_for_post(
        self,
        user: User,
        post_data: Dict,
        content: str,
        custom_prompt: str = None,
        regenerate: bool = False
    ) -> str:
        """
        Generate an image for the post using DALL-E or other image generation models.

        Args:
            user: The user requesting the generation
            post_data: Dictionary containing post information
            content: The generated content for context
            custom_prompt: Optional custom prompt for image generation

        Returns:
            URL or base64 data of the generated image
        """
        model_name = 'gemini-2.5-flash'  # Only supported model

        current_image = None
        if user and user.is_authenticated:
            try:
                from .ai_model_service import AIModelService
                if not AIModelService.validate_image_credits(user, model_name, 1):
                    raise Exception("Créditos insuficientes para gerar imagem")
            except ImportError:
                pass

        # Use Google for image generation by default
        ai_service = AIServiceFactory.create_service(
            'google', 'gemini-2.5-flash')
        if not ai_service:
            raise Exception(
                "Google service not available for image generation")

        # Set user on prompt service for profile access
        self.prompt_service.user = user

        # Build image prompt
        if regenerate:
            from IdeaBank.models import PostIdea
            # Try different ways to get the post idea with current image
            post_idea = None
            # Method 1: If post_data contains a post_idea_id
            if post_data.get('post_idea_id'):
                post_idea = PostIdea.objects.filter(
                    id=post_data.get('post_idea_id')).first()

            # Method 2: If post_data contains a post_id, get the latest PostIdea for that post
            elif post_data.get('post_id'):
                from IdeaBank.models import Post
                post = Post.objects.filter(id=post_data.get('post_id')).first()
                if post:
                    post_idea = PostIdea.objects.filter(
                        post=post).order_by('-created_at').first()

            # Method 3: If we have a post object directly
            elif post_data.get('post'):
                post_idea = PostIdea.objects.filter(
                    post=post_data.get('post')).order_by('-created_at').first()

            current_image = post_idea.image_url if (
                post_idea and post_idea.image_url) else None
            prompt = self.prompt_service.build_image_regeneration_prompt(
                custom_prompt)
        else:
            prompt = self.prompt_service.build_image_prompt(post_data, content)

        try:
            if current_image is not None:
                image_url = ai_service.generate_image(
                    prompt, current_image, user, post_data, content)
            else:
                image_url = ai_service.generate_image(
                    prompt, '', user, post_data, content)
            if not image_url:
                raise Exception("Failed to generate image - no URL returned")

            # Note: Credit deduction for image generation is handled inside ai_service.generate_image()
            # via AIModelService.deduct_image_credits in GeminiService and OpenAIService

            return image_url
        except Exception as e:
            raise Exception(f"Failed to generate image: {str(e)}")

    def regenerate_post_content(
        self,
        user: User,
        post_data: Dict,
        current_content: str,
        user_prompt: str = None,
        ai_provider: str = None,
        ai_model: str = None
    ) -> Dict:
        """
        Regenerate or edit existing post content based on user feedback.

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
        # Store user and post_data for profile access
        self.user = user
        self._current_post_data = post_data

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

        # Validate credits before regenerating (skip for unauthenticated users)
        if user and user.is_authenticated:
            estimated_tokens = self._estimate_tokens(prompt, model)
            if not self._validate_credits(user, estimated_tokens, model):
                raise Exception(
                    "Créditos insuficientes para regenerar conteúdo")

        # Create AI service
        ai_service = AIServiceFactory.create_service(provider, model)
        if not ai_service:
            raise Exception(
                f"AI service not available for provider: {provider}")

        try:
            content = self._generate_content_with_ai(
                ai_service, prompt, post_data)

            # Clean and validate HTML content
            content = self._clean_and_validate_html(content)

            # Deduct credits after successful regeneration (skip for unauthenticated users)
            if user and user.is_authenticated:
                actual_tokens = self._estimate_tokens(prompt + content, model)
                self._deduct_credits(
                    user, actual_tokens, model, f"Regeneração de conteúdo - {post_data.get('name', 'Post')}")
            return {
                'content': content,
                'ai_provider': provider,
                'ai_model': model,
                'status': 'success'
            }
        except Exception as e:
            raise Exception(f"Failed to regenerate content: {str(e)}")

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

    def _generate_content_with_ai(self, ai_service, prompt: str, post_data: dict = None) -> str:
        """Generate content using the AI service with direct API request."""
        try:
            # Use the AI service's direct _make_ai_request method with our sophisticated prompt
            response_text = ai_service._make_ai_request(
                prompt, ai_service.model_name, user=self.user, post_data=post_data)

            if response_text and response_text.strip():
                cleaned_content = response_text.strip()
                return cleaned_content
            else:
                raise Exception("Empty response from AI service")

        except Exception as e:
            raise Exception(
                f"Error generating content with AI service: {type(e).__name__}: {str(e)}")

    def _extract_image_description_from_content(self, content: str) -> str:
        """
        Extract image description text from feed post content.
        Looks for various patterns and formats to identify image generation prompts.
        """
        try:
            if not content or not content.strip():
                return ""

            content_lower = content.lower()
            original_content = content

            # Look for common patterns in Portuguese and English feed content
            patterns = [
                # Portuguese patterns
                "descrição para gerar a imagem",
                "descrição da imagem",
                "descrição para imagem",
                "prompt para imagem",
                "prompt da imagem",
                "imagem:",
                "visual:",
                "arte:",
                "ilustração:",
                "foto:",
                "gráfico:",
                "design:",
                "crie uma imagem",
                "gere uma imagem",
                "descreva a imagem",
                "descrição visual",
                "descrição de imagem",
                # English patterns
                "image description",
                "image prompt",
                "visual description",
                "art description",
                "illustration:",
                "photo:",
                "graphic:",
                "design:",
                "create an image",
                "generate an image",
                "describe the image",
                # More specific patterns
                "descrição para gerar a imagem (sem texto):",
                "descrição para gerar imagem:",
                "prompt de imagem:",
                "descrição visual:",
                "imagem a ser gerada:",
                "arte a ser criada:",
            ]

            best_match = ""
            best_score = 0

            for pattern in patterns:
                pattern_start = content_lower.find(pattern)
                if pattern_start != -1:
                    # Find the start of the description text (after colon or pattern end)
                    colon_pos = content.find(":", pattern_start)
                    if colon_pos != -1:
                        desc_start = colon_pos + 1
                    else:
                        # If no colon, start after the pattern
                        desc_start = pattern_start + len(pattern)

                    # Skip whitespace
                    while desc_start < len(content) and content[desc_start].isspace():
                        desc_start += 1

                    if desc_start >= len(content):
                        continue

                    # Extract potential description
                    remaining_content = content[desc_start:]

                    # Find the end of the description section
                    end_pos = self._find_description_end(remaining_content)

                    description = remaining_content[:end_pos].strip()

                    # Score this match based on length and content quality
                    score = self._score_description(description)

                    if score > best_score:
                        best_match = description
                        best_score = score

            # If we found a good match, return it
            if best_score > 0.5:  # Threshold for acceptable match
                return best_match

            # Fallback: Look for quoted text that might be an image description
            import re
            # Look for quotes with substantial content
            quotes = re.findall(r'"([^"]{20,200})"', original_content)
            for quote in quotes:
                if self._is_likely_image_description(quote):
                    return quote.strip()

            # Another fallback: Look for text after "Crie", "Gere", "Descreva" that spans multiple lines
            fallback_patterns = [
                r"crie uma?\s+([^.!?\n]{50,300})",
                r"gere uma?\s+([^.!?\n]{50,300})",
                r"descreva\s+([^.!?\n]{50,300})",
                r"create an?\s+([^.!?\n]{50,300})",
                r"generate an?\s+([^.!?\n]{50,300})",
                r"describe\s+([^.!?\n]{50,300})"
            ]

            for pattern in fallback_patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    cleaned_match = match.strip()
                    if len(cleaned_match) > 30 and self._is_likely_image_description(cleaned_match):
                        return cleaned_match

            # Final fallback: Look for any substantial paragraph that contains visual keywords
            paragraphs = re.split(r'\n\s*\n', original_content)
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if len(paragraph) > 50 and len(paragraph) < 500:
                    if self._is_likely_image_description(paragraph):
                        return paragraph

            return ""

        except Exception as e:
            print(f"Error extracting image description: {str(e)}")
            return ""

    def _find_description_end(self, content: str) -> int:
        """
        Find the end position of an image description within content.
        """
        # Look for section endings
        end_markers = [
            "\n\n##", "\n\n###", "\n\n####", "\n\n#####", "\n\n######",
            "\n\n---", "\n\n***", "\n\n___",
            "\n\n1.", "\n\n2.", "\n\n3.", "\n\n4.", "\n\n5.",
            "\n\n•", "\n\n-", "\n\n*",
            "\n\nTexto:", "\n\nCopy:", "\n\nLegenda:",
            "\n\nHashtags:", "\n\n#", "\n\nLinks:",
            "\n\nCall to action:", "\n\nCTA:",
            "\n\nConclusão:", "\n\nFinal:",
        ]

        end_pos = len(content)

        # Find the earliest end marker
        for marker in end_markers:
            marker_pos = content.find(marker)
            if marker_pos != -1 and marker_pos < end_pos:
                end_pos = marker_pos

        # If no marker found, look for double line breaks
        if end_pos == len(content):
            double_break = content.find("\n\n")
            if double_break != -1:
                end_pos = double_break

        # If still no end found, limit to reasonable length (max 1000 chars)
        if end_pos > 1000:
            # Try to find a natural break point
            sentences = content.split('.')
            if len(sentences) > 3:
                # Take first 3 sentences
                end_pos = content.find(sentences[3]) + len(sentences[3])
            else:
                end_pos = min(1000, len(content))

        return end_pos

    def _score_description(self, description: str) -> float:
        """
        Score a potential image description based on various criteria.
        Returns a score between 0 and 1.
        """
        if not description or len(description) < 10:
            return 0.0

        score = 0.0
        desc_lower = description.lower()

        # Length score (sweet spot around 50-200 chars)
        length = len(description)
        if 50 <= length <= 200:
            score += 0.3
        elif 20 <= length <= 300:
            score += 0.2
        elif length < 20:
            score += 0.1

        # Visual keywords score
        visual_keywords = [
            'imagem', 'image', 'visual', 'foto', 'photo', 'ilustração', 'illustration',
            'arte', 'art', 'design', 'gráfico', 'graphic', 'pintura', 'painting',
            'desenho', 'drawing', 'retrato', 'portrait', 'paisagem', 'landscape',
            'cena', 'scene', 'estilo', 'style', 'cor', 'color', 'luz', 'light',
            'sombra', 'shadow', 'textura', 'texture', 'composição', 'composition'
        ]

        keyword_count = sum(
            1 for keyword in visual_keywords if keyword in desc_lower)
        score += min(keyword_count * 0.1, 0.4)  # Max 0.4 for keywords

        # Action verbs score
        action_verbs = [
            'mostrar', 'show', 'ilustrar', 'illustrate', 'representar', 'represent',
            'capturar', 'capture', 'refletir', 'reflect', 'expressar', 'express',
            'criar', 'create', 'gerar', 'generate', 'produzir', 'produce'
        ]

        action_count = sum(1 for verb in action_verbs if verb in desc_lower)
        score += min(action_count * 0.05, 0.2)  # Max 0.2 for action verbs

        # Quality indicators
        if any(word in desc_lower for word in ['detalhes', 'details', 'realista', 'realistic', 'profissional', 'professional']):
            score += 0.1

        # Penalty for non-visual content
        if any(word in desc_lower for word in ['hashtags', 'link', 'call to action', 'cta', 'compartilhar', 'share']):
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _is_likely_image_description(self, text: str) -> bool:
        """
        Determine if a text snippet is likely to be an image description.
        """
        if not text or len(text) < 20:
            return False

        text_lower = text.lower()

        # Must have some visual keywords
        visual_keywords = [
            'imagem', 'image', 'visual', 'foto', 'photo', 'ilustração', 'illustration',
            'arte', 'art', 'design', 'gráfico', 'graphic', 'pintura', 'painting',
            'desenho', 'drawing', 'retrato', 'portrait', 'paisagem', 'landscape',
            'cor', 'color', 'luz', 'light', 'estilo', 'style'
        ]

        has_visual_keyword = any(
            keyword in text_lower for keyword in visual_keywords)

        # Should not have too many non-visual elements
        non_visual_indicators = [
            'hashtags', '#', 'link', 'compartilhar', 'share', 'seguir', 'follow',
            'curtir', 'like', 'comentar', 'comment', 'salvar', 'save'
        ]

        non_visual_count = sum(
            1 for indicator in non_visual_indicators if indicator in text_lower)

        # Allow some non-visual content but not too much
        return has_visual_keyword and non_visual_count <= 2

    def _remove_image_description_from_content(self, content: str, image_description: str) -> str:
        """
        Remove the image description section from the content after successful image generation.
        Uses multiple strategies to identify and remove the description section.
        """
        try:
            if not content or not image_description or not image_description.strip():
                return content

            original_content = content
            content_lower = content.lower()
            image_desc_lower = image_description.lower().strip()

            # Strategy 1: Look for structured sections with headers
            section_headers = [
                "descrição para gerar a imagem",
                "descrição da imagem",
                "descrição para imagem",
                "prompt para imagem",
                "prompt da imagem",
                "imagem:",
                "visual:",
                "arte:",
                "ilustração:",
                "foto:",
                "gráfico:",
                "design:",
                "descrição visual",
                "descrição de imagem",
                "image description",
                "image prompt",
                "visual description",
                "art description",
            ]

            for header in section_headers:
                header_start = content_lower.find(header)
                if header_start != -1:
                    # Find the colon after the header
                    colon_pos = content.find(":", header_start)
                    if colon_pos != -1:
                        # Extract the section from header start to end
                        section_start = header_start

                        # Find where this section ends
                        section_end = self._find_section_end(
                            content, colon_pos + 1)

                        # Extract the description from this section
                        extracted_desc = content[colon_pos +
                                                 1:section_end].strip()

                        # Check if this matches our image description (with fuzzy matching)
                        if self._descriptions_match(extracted_desc, image_description):
                            # Remove the entire section
                            cleaned_content = (
                                content[:section_start] + content[section_end:]).strip()

                            # Clean up extra whitespace
                            cleaned_content = self._clean_whitespace(
                                cleaned_content)
                            return cleaned_content

            # Strategy 2: Direct text matching with context
            # Find the image description in the content
            desc_pos = content_lower.find(image_desc_lower)
            if desc_pos != -1:
                # Look for context around the description
                # Look back up to 100 chars
                context_start = max(0, desc_pos - 100)
                context_end = min(len(content), desc_pos +
                                  len(image_description) + 100)  # Look forward

                context = content[context_start:context_end]
                context_lower = context.lower()

                # Check if this is within a description section
                section_indicators = [
                    "descrição", "description", "prompt", "imagem", "image",
                    "visual", "arte", "art", "ilustração", "illustration"
                ]

                has_section_context = any(
                    indicator in context_lower for indicator in section_indicators)

                if has_section_context:
                    # Find the start of this section
                    section_start = context_start
                    # Look for section start indicators
                    for indicator in section_indicators:
                        indicator_pos = content_lower.rfind(
                            indicator, 0, desc_pos)
                        if indicator_pos != -1 and indicator_pos >= context_start - 50:
                            section_start = indicator_pos
                            break

                    # Find the end of this section
                    section_end = self._find_section_end(
                        content, desc_pos + len(image_description))

                    # Remove the section
                    cleaned_content = (
                        content[:section_start] + content[section_end:]).strip()
                    cleaned_content = self._clean_whitespace(cleaned_content)
                    return cleaned_content

            # Strategy 3: Remove exact matches or very similar text
            if image_description in content:
                # Find all occurrences and remove the most likely one
                desc_length = len(image_description)
                best_match_pos = -1
                best_match_score = 0

                start = 0
                while True:
                    pos = content.find(image_description, start)
                    if pos == -1:
                        break

                    # Score this occurrence based on context
                    context_score = self._score_removal_context(
                        content, pos, desc_length)
                    if context_score > best_match_score:
                        best_match_score = context_score
                        best_match_pos = pos

                    start = pos + 1

                if best_match_pos != -1 and best_match_score > 0.3:
                    # Remove this occurrence
                    cleaned_content = (content[:best_match_pos] +
                                       content[best_match_pos + desc_length:]).strip()
                    cleaned_content = self._clean_whitespace(cleaned_content)
                    return cleaned_content

            # Strategy 4: Fuzzy matching for similar descriptions
            # Split both texts into words and find the best matching segment
            content_words = content.split()
            desc_words = image_description.split()

            if len(desc_words) >= 3:  # Only for substantial descriptions
                best_match_start = -1
                best_match_end = -1
                best_overlap = 0

                # Slide through content looking for word overlaps
                for i in range(len(content_words) - len(desc_words) + 1):
                    window = content_words[i:i + len(desc_words)]
                    overlap = len(set(window) & set(desc_words))

                    # 60% overlap
                    if overlap > best_overlap and overlap >= len(desc_words) * 0.6:
                        best_overlap = overlap
                        best_match_start = i
                        best_match_end = i + len(desc_words)

                if best_match_start != -1:
                    # Convert word positions to character positions
                    char_start = len(
                        ' '.join(content_words[:best_match_start]))
                    if best_match_start > 0:
                        char_start += 1  # Add space

                    char_end = len(' '.join(content_words[:best_match_end]))
                    if best_match_end > 0:
                        char_end += 1  # Add space

                    # Remove this segment
                    cleaned_content = (
                        content[:char_start] + content[char_end:]).strip()
                    cleaned_content = self._clean_whitespace(cleaned_content)
                    return cleaned_content

            # If no removal was successful, return original content
            return original_content

        except Exception as e:
            print(f"Error removing image description: {str(e)}")
            return content

    def _find_section_end(self, content: str, start_pos: int) -> int:
        """
        Find the end of a content section starting from a given position.
        """
        # Look for section endings
        end_markers = [
            "\n\n##", "\n\n###", "\n\n####", "\n\n#####", "\n\n######",
            "\n\n---", "\n\n***", "\n\n___",
            "\n\n1.", "\n\n2.", "\n\n3.", "\n\n4.", "\n\n5.",
            "\n\n•", "\n\n-", "\n\n*",
            "\n\nTexto:", "\n\nCopy:", "\n\nLegenda:",
            "\n\nHashtags:", "\n\n#", "\n\nLinks:",
            "\n\nCall to action:", "\n\nCTA:",
            "\n\nConclusão:", "\n\nFinal:",
        ]

        end_pos = len(content)

        # Find the earliest end marker after start_pos
        for marker in end_markers:
            marker_pos = content.find(marker, start_pos)
            if marker_pos != -1 and marker_pos < end_pos:
                end_pos = marker_pos

        # If no marker found, look for double line breaks
        if end_pos == len(content):
            double_break = content.find("\n\n", start_pos)
            if double_break != -1:
                end_pos = double_break

        # If still no end found, limit to reasonable length from start
        if end_pos - start_pos > 1000:
            # Look for sentence endings
            search_text = content[start_pos:start_pos + 1000]
            sentences = search_text.split('.')
            if len(sentences) > 3:
                # Take first 3 sentences
                end_pos = start_pos + \
                    search_text.find(sentences[3]) + len(sentences[3])
            else:
                end_pos = start_pos + min(1000, len(content) - start_pos)

        return end_pos

    def _descriptions_match(self, extracted: str, target: str) -> bool:
        """
        Check if two descriptions match, allowing for some variation.
        """
        if not extracted or not target:
            return False

        extracted_lower = extracted.lower().strip()
        target_lower = target.lower().strip()

        # Exact match
        if extracted_lower == target_lower:
            return True

        # One contains the other
        if extracted_lower in target_lower or target_lower in extracted_lower:
            return True

        # Word overlap check (at least 70% of words in common)
        extracted_words = set(extracted_lower.split())
        target_words = set(target_lower.split())

        if not extracted_words or not target_words:
            return False

        overlap = len(extracted_words & target_words)
        min_words = min(len(extracted_words), len(target_words))

        return overlap >= min_words * 0.7

    def _score_removal_context(self, content: str, pos: int, length: int) -> float:
        """
        Score how likely a text segment is to be an image description that should be removed.
        """
        score = 0.0

        # Look at context before and after
        context_before = content[max(0, pos - 50):pos].lower()
        context_after = content[pos + length:pos + length + 50].lower()

        # Positive indicators (suggests this is a description section)
        positive_indicators = [
            "descrição", "description", "prompt", "imagem", "image",
            "visual", "arte", "art", "ilustração", "illustration",
            "gerar", "generate", "criar", "create"
        ]

        for indicator in positive_indicators:
            if indicator in context_before:
                score += 0.3

        # Negative indicators (suggests this is part of main content)
        negative_indicators = [
            "hashtags", "link", "compartilhar", "share", "seguir", "follow",
            "curtir", "like", "comentar", "comment", "salvar", "save",
            "call to action", "cta", "legenda", "caption"
        ]

        for indicator in negative_indicators:
            if indicator in context_after or indicator in context_before:
                score -= 0.4

        # Length consideration
        if 50 <= length <= 300:
            score += 0.2
        elif length < 30:
            score -= 0.3

        return max(0.0, min(1.0, score))

    def _clean_whitespace(self, content: str) -> str:
        """
        Clean up whitespace and formatting in content.
        """
        if not content:
            return content

        # Replace multiple line breaks with double line breaks
        import re
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

        # Remove excessive spaces
        content = re.sub(r' +', ' ', content)

        # Clean up line breaks around section markers
        content = re.sub(r'\n\s*(\n\s*)+(?=\n\s*#)', '\n\n', content)

        return content.strip()

    def _generate_image_from_description(self, ai_service, image_description: str, user, post_data: Dict, content: str) -> str:
        """
        Generate an image using the extracted description via Gemini service.
        """
        try:
            # Validate image credits if user is authenticated
            if user and user.is_authenticated:
                try:
                    from .ai_model_service import AIModelService
                    if not AIModelService.validate_image_credits(user, 'gemini-2.5-flash', 1):
                        raise Exception(
                            "Créditos insuficientes para gerar imagem")
                except ImportError:
                    pass

            # Generate image using the AI service
            image_url = ai_service.generate_image(
                image_description, '', user, post_data, content)

            if not image_url:
                raise Exception("Failed to generate image - no URL returned")

            return image_url

        except Exception as e:
            raise Exception(
                f"Failed to generate image from description: {str(e)}")
