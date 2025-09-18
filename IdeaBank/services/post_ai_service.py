"""
Post AI Service for generating post ideas using AI models.
"""

from typing import Dict

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory


class PostAIService:
    """Service for generating post ideas using AI models."""

    def __init__(self):
        self.default_provider = 'google'
        self.default_model = 'gemini-1.5-flash'

    def generate_post_content(
        self,
        user: User,
        post_data: Dict,
        ai_provider: str = None,
        ai_model: str = None
    ) -> Dict:
        """
        Generate AI content for a post based on the provided data.

        Args:
            user: The user requesting the generation
            post_data: Dictionary containing post information (name, objective, type, target audience)
            ai_provider: AI provider preference (google, openai, anthropic)
            ai_model: Specific AI model to use

        Returns:
            Dictionary containing the generated content
        """
        provider = ai_provider or self.default_provider
        model = ai_model or self.default_model

        # Store user for profile access
        self.user = user

        # Create AI service
        ai_service = AIServiceFactory.create_service(provider, model)
        if not ai_service:
            raise Exception(
                f"AI service not available for provider: {provider}")

        # Build the prompt for content generation
        prompt = self._build_content_prompt(post_data)

        # Generate content using the AI service
        try:
            # For now, we'll use a simple text generation method
            # This would be implemented in the base AI service
            content = self._generate_content_with_ai(ai_service, prompt)

            return {
                'content': content,
                'ai_provider': provider,
                'ai_model': model,
                'status': 'success'
            }
        except Exception as e:
            raise Exception(f"Failed to generate content: {str(e)}")

    def generate_image_for_post(
        self,
        user: User,
        post_data: Dict,
        content: str,
        custom_prompt: str = None
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
        # Use OpenAI for image generation by default
        ai_service = AIServiceFactory.create_service('openai', 'dall-e-3')
        if not ai_service:
            raise Exception(
                "OpenAI service not available for image generation")

        # Build image prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._build_image_prompt(post_data, content)

        try:
            image_url = ai_service.generate_image(prompt, user)
            if not image_url:
                raise Exception("Failed to generate image - no URL returned")
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

        # Create AI service
        ai_service = AIServiceFactory.create_service(provider, model)
        if not ai_service:
            raise Exception(
                f"AI service not available for provider: {provider}")

        # Build the regeneration prompt
        if user_prompt:
            prompt = self._build_regeneration_prompt(
                post_data, current_content, user_prompt)
        else:
            prompt = self._build_variation_prompt(post_data, current_content)

        try:
            content = self._generate_content_with_ai(ai_service, prompt)

            return {
                'content': content,
                'ai_provider': provider,
                'ai_model': model,
                'status': 'success'
            }
        except Exception as e:
            raise Exception(f"Failed to regenerate content: {str(e)}")

    def _build_content_prompt(self, post_data: Dict) -> str:
        """Build the prompt for content generation."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        post_type = post_data.get('type', '')

        # Target audience information
        target_info = []
        if post_data.get('target_gender'):
            target_info.append(f"Gênero: {post_data['target_gender']}")
        if post_data.get('target_age'):
            target_info.append(f"Idade: {post_data['target_age']}")
        if post_data.get('target_location'):
            target_info.append(f"Localização: {post_data['target_location']}")
        if post_data.get('target_salary'):
            target_info.append(f"Renda: {post_data['target_salary']}")
        if post_data.get('target_interests'):
            target_info.append(f"Interesses: {post_data['target_interests']}")

        target_section = f"\n\nPúblico-alvo:\n{chr(10).join(target_info)}" if target_info else ""

        # Creator profile information (if available)
        creator_profile_section = ""
        if hasattr(self, 'user') and self.user:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.filter(user=self.user).first()
            if profile:
                creator_info = []
                if profile.professional_name:
                    creator_info.append(
                        f"Nome Profissional: {profile.professional_name}")
                if profile.profession:
                    creator_info.append(f"Profissão: {profile.profession}")
                if profile.business_name:
                    creator_info.append(f"Negócio: {profile.business_name}")
                if profile.specialization:
                    creator_info.append(
                        f"Especialização: {profile.specialization}")
                if profile.voice_tone:
                    creator_info.append(
                        f"Tom de Voz Preferido: {profile.voice_tone}")

                if creator_info:
                    creator_profile_section = f"\n\nPerfil do Criador:\n{chr(10).join(creator_info)}"

        prompt = f"""Crie um conteúdo para uma publicação de redes sociais com as seguintes especificações:

Nome do post: {name}
Objetivo: {objective}
Tipo de conteúdo: {post_type}{target_section}{creator_profile_section}

O conteúdo deve ser formatado EXATAMENTE assim:

Título: [Título atrativo e chamativo]

Texto: [Texto principal do post, envolvente e adequado ao público-alvo]

Chamada para ação no post/carrossel: [CTA clara e direcionada ao objetivo]

Instruções:
- O conteúdo deve ser adequado para {post_type}
- Foque no objetivo de {objective}
- Use linguagem apropriada para o público-alvo especificado
- Seja criativo e autêntico
- Inclua emojis quando apropriado
- Mantenha o formato exato solicitado
- Use o tom de voz do perfil do criador se disponível
- Personalize o conteúdo baseado no contexto profissional do criador
"""

        return prompt

    def _build_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build the prompt for image generation."""
        post_type = post_data.get('type', '')
        objective = post_data.get('objective', '')

        # Extract title from content if available
        title = ""
        if "Título:" in content:
            title_line = content.split("Título:")[1].split("\n")[0].strip()
            title = title_line

        prompt = f"""Create a professional and engaging image for a social media {post_type} post.

Content context: {title}
Objective: {objective}
Post type: {post_type}

Style requirements:
- Professional and modern design
- Suitable for social media
- Eye-catching and engaging
- Clean and readable
- Appropriate for the content theme
- High quality and visually appealing

Avoid including text in the image itself."""

        return prompt

    def _build_regeneration_prompt(self, post_data: Dict, current_content: str, user_prompt: str) -> str:
        """Build the prompt for content regeneration with user feedback."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        post_type = post_data.get('type', '')

        prompt = f"""Você precisa melhorar o seguinte conteúdo de rede social baseado no feedback do usuário:

CONTEÚDO ATUAL:
{current_content}

FEEDBACK/SOLICITAÇÃO DO USUÁRIO:
{user_prompt}

ESPECIFICAÇÕES ORIGINAIS:
- Nome do post: {name}
- Objetivo: {objective}
- Tipo: {post_type}

Por favor, recrie o conteúdo incorporando o feedback do usuário, mantendo o formato:

Título: [Título melhorado]

Texto: [Texto melhorado]

Chamada para ação no post/carrossel: [CTA melhorada]

Certifique-se de que as melhorias atendam especificamente ao feedback fornecido.
"""

        return prompt

    def _build_variation_prompt(self, post_data: Dict, current_content: str) -> str:
        """Build the prompt for creating a variation of existing content."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        post_type = post_data.get('type', '')

        prompt = f"""Crie uma variação do seguinte conteúdo de rede social, mantendo o mesmo objetivo mas com abordagem diferente:

CONTEÚDO ORIGINAL:
{current_content}

ESPECIFICAÇÕES:
- Nome do post: {name}
- Objetivo: {objective}
- Tipo: {post_type}

Crie uma nova versão que:
- Mantenha o mesmo objetivo e propósito
- Use uma abordagem ou angle diferente
- Tenha um tom ligeiramente diferente
- Mantenha a qualidade e efetividade

Formato da resposta:

Título: [Novo título]

Texto: [Novo texto]

Chamada para ação no post/carrossel: [Nova CTA]
"""

        return prompt

    def _generate_content_with_ai(self, ai_service, prompt: str) -> str:
        """Generate content using the AI service."""
        # This is a simplified version. In a real implementation,
        # we would use the actual AI service methods
        # For now, we'll assume the AI service has a generate_text method

        # Try to use existing campaign generation logic adapted for posts
        try:
            # Create a mock config for the existing AI service
            mock_config = {
                'title': 'Post Generation',
                'objectives': ['engagement'],
                'platforms': ['instagram'],
                'content_types': {'instagram': ['post']},
                'voice_tone': 'professional',
                'product_description': prompt,
                'persona_interests': 'general audience'
            }

            # Use the existing generate_campaign_ideas_with_progress method
            # but extract just the content we need
            ideas_data, _ = ai_service.generate_campaign_ideas_with_progress(
                user=None,
                config=mock_config,
                progress_callback=None
            )

            if ideas_data and len(ideas_data) > 0:
                first_idea = ideas_data[0]
                content = first_idea.get('content', {})

                # Try to extract structured content
                if isinstance(content, dict) and 'variacao_a' in content:
                    var_a = content['variacao_a']
                    title = var_a.get('headline', '')
                    text = var_a.get('copy', '')
                    cta = var_a.get('cta', '')

                    formatted_content = f"""Título: {title}

Texto: {text}

Chamada para ação no post/carrossel: {cta}"""

                    return formatted_content
                elif isinstance(content, str):
                    return content
                else:
                    return str(content)
            else:
                raise Exception("No content generated by AI service")

        except Exception:
            # Fallback: return a simple response
            return """Título: Conteúdo Gerado por IA

Texto: Este é um conteúdo gerado automaticamente. Por favor, personalize conforme necessário.

Chamada para ação no post/carrossel: Saiba mais!"""
