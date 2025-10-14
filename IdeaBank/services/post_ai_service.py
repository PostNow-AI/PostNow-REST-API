"""
Post AI Service for generating post ideas using AI models.
"""

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

    def _make_ai_request(self, prompt: str, model_name: str, api_key: str = None) -> str:
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
        return ai_service._make_ai_request(prompt, model_name, api_key)

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
            content = self._generate_content_with_ai(ai_service, prompt)

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

        try:
            # Generate content using the AI service
            full_content = self._generate_content_with_ai(ai_service, prompt)

            # Deduct credits after successful generation (skip for unauthenticated users)
            if user and user.is_authenticated:
                actual_tokens = self._estimate_tokens(
                    prompt + full_content, model)
                self._deduct_credits(
                    user, actual_tokens, model, f"Geração de campanha - {post_data.get('name', 'Campaign')}")

            # Parse the AI response into 3 separate contents
            parsed_content = self._parse_campaign_response(full_content)

            # Create 3 Post objects with their respective PostIdea objects
            created_posts = []
            with transaction.atomic():
                for post_type, content in parsed_content.items():
                    # Clean and validate HTML for each content section
                    content = self._clean_and_validate_html(content)
                    # Create Post object
                    post = Post.objects.create(
                        user=user,
                        name=f"{post_data.get('name', 'Campaign')} - {post_type.title()}",
                        objective=post_data.get('objective', ''),
                        type=post_type,
                        further_details=post_data.get('further_details', ''),
                        include_image=post_data.get('include_image', False),
                        is_automatically_generated=post_data.get(
                            'is_automatically_generated', False),
                        is_active=post_data.get('is_active', True)
                    )

                    # Generate image for feed posts
                    image_url = None
                    if post_type == 'feed':
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
                                    f"Failed to generate image for campaign feed post: {str(e)}")

                    # Create PostIdea object
                    post_idea = PostIdea.objects.create(
                        post=post,
                        content=content,
                        image_url=image_url or ''
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
        parsed = {'feed': '', 'reels': '', 'story': ''}

        try:
            # Split content by sections
            content = full_content.strip()

            # Look for Feed content (section 1)
            feed_start = content.find('🧩 1. Conteúdo de Feed')
            stories_start = content.find('🎥 2. Ideias de Stories')
            reels_start = content.find('🎬 3. Ideia de Roteiro para Reels')

            if feed_start != -1:
                feed_end = stories_start if stories_start != - \
                    1 else len(content)
                parsed['feed'] = content[feed_start:feed_end].strip()

            # Look for Stories content (section 2)
            if stories_start != -1:
                stories_end = reels_start if reels_start != - \
                    1 else len(content)
                parsed['story'] = content[stories_start:stories_end].strip()

            # Look for Reels content (section 3)
            if reels_start != -1:
                parsed['reels'] = content[reels_start:].strip()

            # Fallback: if sections not found, try to split by numbered sections
            if not any(parsed.values()):
                lines = content.split('\n')
                current_section = None
                current_content = []

                for line in lines:
                    line = line.strip()
                    if '1.' in line and 'feed' in line.lower():
                        current_section = 'feed'
                        current_content = [line]
                    elif '2.' in line and ('stories' in line.lower() or 'story' in line.lower()):
                        if current_section == 'feed':
                            parsed['feed'] = '\n'.join(current_content)
                        current_section = 'story'
                        current_content = [line]
                    elif '3.' in line and 'reel' in line.lower():
                        if current_section == 'story':
                            parsed['story'] = '\n'.join(current_content)
                        current_section = 'reels'
                        current_content = [line]
                    elif current_section:
                        current_content.append(line)

                # Add the last section
                if current_section == 'reels' and current_content:
                    parsed['reels'] = '\n'.join(current_content)
                elif current_section == 'story' and current_content:
                    parsed['story'] = '\n'.join(current_content)
                elif current_section == 'feed' and current_content:
                    parsed['feed'] = '\n'.join(current_content)

            # Ensure all sections have content, use full content as fallback
            for key in parsed:
                if not parsed[key].strip():
                    parsed[key] = full_content
                else:
                    # Clean and validate HTML for each section
                    parsed[key] = self._clean_and_validate_html(parsed[key])

        except Exception:
            # If parsing fails, return the full content for all types
            cleaned_full_content = self._clean_and_validate_html(full_content)
            parsed = {
                'feed': cleaned_full_content,
                'reels': cleaned_full_content,
                'story': cleaned_full_content
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
        provider = ai_provider or self.default_provider
        model = ai_model or self.default_model

        # Set user on prompt service for profile access
        self.prompt_service.user = user

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
            content = self._generate_content_with_ai(ai_service, prompt)

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

        except Exception as e:
            print(f"HTML cleaning error: {str(e)}")
            # If cleaning fails, return original content
            return content

    def _generate_content_with_ai(self, ai_service, prompt: str) -> str:
        """Generate content using the AI service with direct API request."""
        try:
            # Use the AI service's direct _make_ai_request method with our sophisticated prompt
            response_text = ai_service._make_ai_request(
                prompt, ai_service.model_name)

            if response_text and response_text.strip():
                cleaned_content = self._clean_and_validate_html(
                    response_text.strip())
                return cleaned_content
            else:
                raise Exception("Empty response from AI service")

        except Exception:
            # Fallback: return a simple response
            return """Título: Conteúdo Gerado por IA

Texto: Este é um conteúdo gerado automaticamente. Por favor, personalize conforme necessário.

Chamada para ação no post/carrossel: Saiba mais!"""

    def _extract_image_description_from_content(self, content: str) -> str:
        """
        Extract image description text from feed post content.
        Looks for patterns like "Descrição para gerar a imagem" or similar.
        """
        try:
            content_lower = content.lower()

            # Look for common patterns in Portuguese feed content
            patterns = [
                "descrição para gerar a imagem",
                "descrição da imagem",
                "imagem:",
                "visual:",
                "arte:"
            ]

            for pattern in patterns:
                pattern_start = content_lower.find(pattern)
                if pattern_start != -1:
                    # Find the start of the description text
                    desc_start = content.find(":", pattern_start) + 1
                    if desc_start > 0:
                        # Find the end (next section or end of content)
                        remaining_content = content[desc_start:]

                        # Look for common section endings
                        end_markers = ["\n\n", "###", "##", "---", "***"]
                        end_pos = len(remaining_content)

                        for marker in end_markers:
                            marker_pos = remaining_content.find(marker)
                            if marker_pos != -1 and marker_pos < end_pos:
                                end_pos = marker_pos

                        description = remaining_content[:end_pos].strip()
                        if len(description) > 20:  # Ensure it's substantial
                            return description

            # Fallback: look for any text after "Crie" or "Descreva"
            fallback_patterns = ["crie uma", "descreva", "gere uma imagem"]
            for pattern in fallback_patterns:
                pattern_start = content_lower.find(pattern)
                if pattern_start != -1:
                    # Take up to 500 chars
                    remaining = content[pattern_start:pattern_start + 500]
                    lines = remaining.split('\n')
                    if len(lines) > 0 and len(lines[0]) > 30:
                        return lines[0].strip()

            return ""

        except Exception:
            return ""

    def _remove_image_description_from_content(self, content: str, image_description: str) -> str:
        """
        Remove the image description section from the content after successful image generation.
        """
        try:
            if not image_description or not image_description.strip():
                return content

            content_lower = content.lower()
            image_desc_lower = image_description.lower()

            # Look for common patterns that precede the image description
            patterns = [
                "descrição para gerar a imagem",
                "descrição da imagem",
                "imagem:",
                "visual:",
                "arte:"
            ]

            for pattern in patterns:
                pattern_start = content_lower.find(pattern)
                if pattern_start != -1:
                    # Find where the image description starts in the original content
                    desc_section_start = content.find(":", pattern_start)
                    if desc_section_start != -1:
                        # Find the end of the description section
                        remaining_content = content[desc_section_start + 1:]

                        # Look for section endings
                        end_markers = ["\n\n", "###", "##", "---", "***"]
                        end_pos = len(remaining_content)

                        for marker in end_markers:
                            marker_pos = remaining_content.find(marker)
                            if marker_pos != -1 and marker_pos < end_pos:
                                end_pos = marker_pos

                        # Extract the description section
                        extracted_description = remaining_content[:end_pos].strip(
                        )

                        # Check if this matches our image description (fuzzy match)
                        if (extracted_description.lower() in image_desc_lower or
                            image_desc_lower in extracted_description.lower() or
                                len(set(extracted_description.lower().split()) & set(image_desc_lower.split())) > 3):

                            # Remove the entire section from pattern to end
                            section_end = desc_section_start + 1 + end_pos
                            # Also remove the pattern label
                            pattern_actual_start = content.find(
                                pattern, pattern_start - 20, pattern_start + 20)
                            if pattern_actual_start == -1:
                                pattern_actual_start = pattern_start

                            # Remove from pattern start to section end, including trailing whitespace
                            cleaned_content = (content[:pattern_actual_start] +
                                               content[section_end:]).strip()

                            # Clean up any double line breaks
                            cleaned_content = cleaned_content.replace(
                                '\n\n\n', '\n\n')

                            return cleaned_content

            # Fallback: try to remove the exact description text
            if image_description in content:
                cleaned_content = content.replace(
                    image_description, "").strip()
                # Clean up any remaining artifacts
                cleaned_content = cleaned_content.replace('\n\n\n', '\n\n')
                return cleaned_content

            # If no pattern matches, return original content
            return content

        except Exception as e:
            print(f"Error removing image description: {str(e)}")
            return content

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
