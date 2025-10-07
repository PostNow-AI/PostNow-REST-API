"""
Post AI Service for generating post ideas using AI models.
"""

from typing import Dict

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory
from .base_ai_service import BaseAIService


class PostAIService(BaseAIService):
    """Service for generating post ideas using AI models."""

    def __init__(self):
        super().__init__("gemini-2.5-flash")  # Initialize parent with default model
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'

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
        ai_provider: str = None,
        ai_model: str = None
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

        # Build the prompt for content generation
        prompt = self._build_content_prompt(post_data)

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

        # Store user and post_data for profile access
        self.user = user
        self._current_post_data = post_data

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
            prompt = self._build_image_regeneration_prompt(
                custom_prompt)
        else:
            prompt = self._build_image_prompt(post_data, content)

        try:
            if current_image is not None:
                image_url = ai_service.generate_image(
                    prompt, current_image, user, post_data, content, {
                        "titulo": {
                            "title-content": "Special Offer!",
                            "font-family": "Poppins",
                            "font-size": "98px",
                            "font-weight": "bold",
                            "color": "#000000",
                            "drop-shadow": "2px 2px 4px rgba(0,0,0,0.8)",
                            "text-stroke": "",
                            "location": "top-center"
                        },
                        "sub-titulo": {
                            "subtitle-content": "Save up to 50% today",
                            "font-family": "Poppins",
                            "font-size": "98px",
                            "font-weight": "bold",
                            "color": "#FFD700",
                            "drop-shadow": "1px 1px 2px rgba(0,0,0,0.6)",
                            "text-stroke": "",
                            "location": "center-center"
                        },
                        "cta": {
                            "cta-content": "Shop Now →",
                            "font-family": "Poppins",
                            "font-size": "92px",
                            "font-weight": "bold",
                            "color": "#FF4444",
                            "drop-shadow": "",
                            "text-stroke": "2px #000000",
                            "location": "bottom-center"
                        }
                    })
            else:
                image_url = ai_service.generate_image(
                    prompt, '', user, post_data, content, {
                        "titulo": {
                            "title-content": "Special Offer!",
                            "font-family": "Montserrat",
                            "font-size": "48px",
                            "font-weight": "bold",
                            "color": "#FFFFFF",
                            "drop-shadow": "2px 2px 4px rgba(0,0,0,0.8)",
                            "text-stroke": "",
                            "location": "top-center"
                        },
                        "sub-titulo": {
                            "subtitle-content": "Save up to 50% today",
                            "font-family": "Montserrat",
                            "font-size": "28px",
                            "font-weight": "normal",
                            "color": "#FFD700",
                            "drop-shadow": "1px 1px 2px rgba(0,0,0,0.6)",
                            "text-stroke": "",
                            "location": "center-center"
                        },
                        "cta": {
                            "cta-content": "Shop Now →",
                            "font-family": "Montserrat",
                            "font-size": "32px",
                            "font-weight": "bold",
                            "color": "#FF4444",
                            "drop-shadow": "",
                            "text-stroke": "2px #000000",
                            "location": "bottom-center"
                        }
                    })
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

        # Store user and post_data for profile access
        self.user = user
        self._current_post_data = post_data

        # Build the regeneration prompt
        if user_prompt:
            prompt = self._build_regeneration_prompt(
                current_content, user_prompt)
        else:
            prompt = self._build_variation_prompt(current_content)

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

    def _build_content_prompt(self, post_data: Dict) -> str:
        """Build the prompt for content generation based on post type."""
        post_type = post_data.get('type', '').lower()

        # Route to specific prompt based on post type
        if post_type == 'post':
            return self._build_feed_post_prompt(post_data)
        elif post_type == 'reel':
            return self._build_reel_prompt(post_data)
        elif post_type == 'story':
            return self._build_story_prompt(post_data)
        else:
            # Default fallback for other types (carousel, live, etc.)
            return self._build_default_prompt(post_data)

    def _get_creator_profile_section(self) -> str:
        """Get creator profile information for prompt context."""
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

                # Color palette
                colors = [profile.color_1, profile.color_2,
                          profile.color_3, profile.color_4, profile.color_5]
                valid_colors = [
                    color for color in colors if color and color.strip()]
                if valid_colors:
                    creator_info.append(
                        f"Paleta de Cores da Marca: {', '.join(valid_colors)}")

                if creator_info:
                    creator_profile_section = f"\n\nPERFIL DO CRIADOR:\n{chr(10).join(f'- {info}' for info in creator_info)}"

        return creator_profile_section

    def _build_all_details(self, further_details: str) -> str:
        """Build the audience and tone section combining further details with creator profile data."""
        sections = []

        # Add further details if provided
        if further_details and further_details.strip():
            sections.append(further_details.strip())

        # # Get creator profile data for target audience and voice tone
        # if hasattr(self, 'user') and self.user:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.filter(user=self.user).first()
            if profile:
                audience_info = []
                brand_info = []
                if profile.business_name:
                    brand_info.append(f"Empresa: {profile.business_name}")
                if profile.profession:
                    brand_info.append(f"Profissão: {profile.profession}")
                if profile.specialization:
                    brand_info.append(
                        f"Especialização: {profile.specialization}")
                # Target audience information
                if profile.target_gender and profile.target_gender.strip():
                    audience_info.append(
                        f"Gênero do Público: {profile.target_gender}")

                if profile.target_age_range and profile.target_age_range.strip():
                    audience_info.append(
                        f"Faixa Etária: {profile.target_age_range}")

                if profile.target_location and profile.target_location.strip():
                    audience_info.append(
                        f"Localização: {profile.target_location}")

                if profile.target_interests and profile.target_interests.strip():
                    audience_info.append(
                        f"Interesses: {profile.target_interests}")

                if profile.voice_tone and profile.voice_tone.strip():
                    brand_info.append(
                        f"Tom de Voz da Marca: {profile.voice_tone}")

                colors = [profile.color_1, profile.color_2,
                          profile.color_3, profile.color_4, profile.color_5]
                valid_colors = [
                    color for color in colors if color and color.strip()]
                if valid_colors:
                    brand_info.append(
                        f"Cores da marca: {', '.join(valid_colors)}")

                if audience_info:
                    sections.append(
                        f"Dados do Público-Alvo: {' | '.join(audience_info)}")
                if brand_info:
                    sections.append(
                        f"Dados da Marca: {' | '.join(brand_info)}")
        return ' - '.join(sections) if sections else "Informações não fornecidas"

    def _build_feed_post_prompt(self, post_data: Dict) -> str:
        """Build prompt specifically for feed posts."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')

        details = self._build_all_details(further_details)

        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo.
Sua missão é gerar copies otimizadas para posts de Feed em redes sociais, com foco em clareza, engajamento e relevância, respeitando sempre as boas práticas do Meta e Google Ads.

### DADOS DE ENTRADA
- Assunto do post: {name}
- Objetivo do post: {objective}
- Tipo do post: Feed
- Mais detalhes: {details}

---

### REGRAS PARA A COPY:

1. Estruture internamente no método AIDA (Atenção, Interesse, Desejo, Ação), mas entregue a copy final **sem rótulos ou divisões visíveis**.

2. O texto deve ser fluido, natural e pronto para publicação no Feed.

3. Utilize **parágrafos curtos e bem separados**, que facilitem a leitura rápida e escaneável nas redes sociais.

4. Insira **emojis de forma moderada e estratégica**, para dar leveza e proximidade, mas nunca em excesso.

5. Respeite sempre o **tom de voz e estilo definidos nos detalhes** pelo profissional (ex.: técnico, acolhedor, inspirador, educativo, motivacional, etc.).

6. Não use linguagem sensacionalista, promessas exageradas ou afirmações que violem políticas do Meta e Google Ads.
   - Não fazer comparações negativas diretas.
   - Não prometer resultados absolutos.
   - Não atacar autoestima ou expor dados sensíveis de forma invasiva.
   - Priorizar comunicação positiva, inclusiva e motivadora.

7. Se possível, traga expressões ou referências atuais que estejam em tendência no tema do post.

8. Sempre finalize com **uma única CTA natural e clara**, coerente com o objetivo definido do post.

---

### SAÍDA ESPERADA:
- Uma copy pronta para Feed, já formatada com parágrafos curtos e emojis leves.
- Texto direto para copiar e colar no post.
- Apenas **uma CTA final**, integrada de forma natural ao texto.
- Copy envolvente, relevante e alinhada ao objetivo da campanha e ao tom da marca.
"""
        return prompt.strip()

    def _build_reel_prompt(self, post_data: Dict) -> str:
        """Build prompt specifically for reels."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')

        details = self._build_all_details(further_details)
        # TODO: Replace with your specific reel prompt
        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo.
Sua missão é gerar roteiros curtos, impactantes e envolventes para Reels, otimizados para gerar atenção e engajamento já nos primeiros segundos.
O conteúdo deve ser dinâmico, direto e fácil de acompanhar, respeitando as boas práticas do Meta e Google Ads.

### DADOS DE ENTRADA
- Assunto do post: {name}
- Objetivo do post: {objective}
- Tipo do post: Reel
- Mais detalhes: {details}

---

### REGRAS PARA A COPY:

1. Estruture o roteiro internamente no método AIDA, mas entregue o resultado final **sem rótulos ou divisões visíveis de Atenção, Interesse, etc.**.

2. O texto deve estar organizado em um **roteiro de até 15 segundos**, dividido por blocos de tempo, exemplo:
   - [0s – 3s]
   - [3s – 6s]
   - [6s – 12s]
   - [12s – 15s]

3. O gancho inicial deve ser **forte e impactante**, capaz de prender a atenção já nos 3 primeiros segundos.

4. A linguagem deve ser fluida, natural e alinhada ao **tom de voz definido no formulário da empresa** (ex.: motivacional, técnico, acolhedor, educativo, inspirador).

5. Use **frases curtas, fáceis de ler e de ouvir**, perfeitas para um vídeo rápido.

6. Utilize **emojis moderados e estratégicos**, mas nunca em excesso.

7. Sempre finalize com **uma única CTA clara e objetiva**, coerente com o objetivo da campanha (ex.: “Clique no link da bio”, “Marque alguém”, “Agende agora”).

8. Nunca use linguagem sensacionalista ou promessas exageradas. Sempre respeite as políticas do Meta e Google Ads.

---

### SAÍDA ESPERADA:
- Um roteiro curto para Reel, com blocos de tempo (até 15 segundos).
- Copy pronta para ser usada no vídeo, fluida e envolvente.
- Texto dividido de forma natural em parágrafos curtos.
- Emojis aplicados de forma leve e estratégica.
- Apenas **uma CTA final** integrada ao texto.



"""
        return prompt.strip()

    def _build_story_prompt(self, post_data: Dict) -> str:
        """Build prompt specifically for stories."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')
        details = self._build_all_details(further_details)
        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo.
Sua missão é gerar copies curtas, envolventes e interativas para Stories em redes sociais, com foco em atenção imediata, clareza e incentivo à ação.

### DADOS DE ENTRADA
- Assunto do post: {name}
- Objetivo do post: {objective}
- Tipo do post: Story
- Mais detalhes: {details}

---

### REGRAS PARA A COPY:

1. Estruture a copy em 1 tela, com mensagens simples, claras e fáceis de ler.  

2. Cada tela deve conter **uma frase curta e impactante**, que mantenha a atenção e conduza o público até a CTA final.  

3. O tom de voz deve seguir exatamente o definido nos detalhes do formulário (ex.: inspirador, educativo, acolhedor, motivacional).  

4. Use **emojis moderados e estratégicos** para dar proximidade, mas sem exageros.  

5. A primeira tela deve ser um **gancho forte** que capture a atenção imediatamente.  

6. A última tela deve sempre conter **uma única CTA clara e direta**, coerente com o objetivo do post (ex.: “Arraste pra cima 🚀”, “Clique no link da bio 👉”, “Responda essa enquete ✨”).  

7. Frases devem ser curtas, de leitura rápida, evitando blocos longos de texto.  

8. A copy deve ser positiva, inclusiva e motivadora, nunca sensacionalista ou proibida pelas diretrizes do Meta/Google Ads.  


---



### SAÍDA ESPERADA:
- Copy finalizada para Story, 1 tela.  
- Texto pronto para copiar e colar.  
- Frases curtas, impactantes e fáceis de ler.  
- Emojis usados de forma leve e natural.  
- Apenas **uma CTA final** integrada ao último Story.  




"""
        return prompt.strip()

    def _build_default_prompt(self, post_data: Dict) -> str:
        """Build default prompt for other content types (carousel, live, etc.)."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        post_type = post_data.get('type', '')
        further_details = post_data.get('further_details', '')
        include_image = post_data.get('include_image', False)

        creator_profile_section = self._get_creator_profile_section()
        additional_context = f"\n\nDetalhes Adicionais: {further_details}" if further_details and further_details.strip(
        ) else ""
        image_context = "\n\nNOTA: Uma imagem será gerada automaticamente para este post usando IA." if include_image else ""

        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo, com domínio do método AIDA (Atenção, Interesse, Desejo, Ação) e das boas práticas de comunicação digital.
Sua missão é gerar copies poderosas, relevantes e seguras para campanhas, sempre respeitando as políticas do Meta e Google Ads, evitando qualquer tipo de sensacionalismo, promessa exagerada ou afirmações que possam violar as diretrizes dessas plataformas.

### DADOS DE ENTRADA:
- Nome do Post (tema principal): {name}
- Objetivo da campanha: {objective}
- Tipo de conteúdo: {post_type} → pode ser Live, Reel, Post, Carousel ou Story
- Plataforma: instagram{creator_profile_section}{additional_context}{image_context}

### REGRAS PARA CONSTRUÇÃO DA COPY:

1. Estruture o texto internamente seguindo o método AIDA, mas **não mostre as etapas nem insira rótulos**.
   O resultado deve ser apenas o texto final, fluido e pronto para publicação.

2. A copy deve respeitar o tom de voz definido no perfil do criador (se disponível) ou usar tom profissional como padrão.

3. Respeite as políticas de publicidade do Meta e Google Ads, sem sensacionalismo, promessas exageradas ou afirmações proibidas.
   - Não usar comparações negativas diretas.
   - Não prometer resultados absolutos.
   - Não atacar autoestima ou expor dados sensíveis de forma invasiva.
   - Priorizar sempre uma comunicação positiva, inclusiva e motivadora.

4. Sempre que possível, conecte a copy com tendências e expressões atuais relacionadas ao tema.

5. **Adaptação ao Tipo de Conteúdo**
   - Se for **Post**: texto curto, envolvente e objetivo, pronto para feed.
   - Se for **Reel**: entregue um roteiro estruturado em até 15 segundos, dividido por blocos de tempo (ex.: [0s – 3s], [3s – 6s], etc.), para que a gravação siga o ritmo ideal de engajamento. A copy deve ser curta, dinâmica e clara, sempre com CTA no final.
   - Se for **Story**: copy leve, direta e conversacional, podendo ser dividida em 2 ou 3 telas curtas, incentivando interação (ex.: enquete, resposta rápida, link).
   - Se for **Carousel**: texto dividido em partes curtas que façam sentido em sequência, cada card reforçando um ponto até a CTA final.
   - Se for **Live**: copy no formato de convite, explicando tema, horário, benefício de participar e incentivo para salvar a data.

6. Ajuste o tamanho, tom e formatação da copy sempre de acordo com o tipo de conteúdo escolhido.

7. Utilize **emojis de forma estratégica e moderada** para dar leveza e proximidade ao texto, sem exageros ou excesso.

8. Faça a **separação de parágrafos de forma natural**, garantindo boa legibilidade em redes sociais e anúncios, evitando blocos de texto longos.

9. Entregue **apenas uma CTA final**, integrada ao texto, natural e clara, sem listas ou alternativas extras.

10. NÃO inclua textos explicativos, como por exemplo "Título:", "Texto:", "CTA:", ou qualquer outro rótulo.

---

### SAÍDA ESPERADA:
- Texto final pronto para ser copiado e colado.
- Copy fluida, envolvente e natural, sem divisões ou rótulos técnicos.
- Linguagem alinhada ao perfil do criador e ao tom cadastrado.
- Respeito às boas práticas do Meta e Google Ads.
- Emojis distribuídos de forma natural, sem excesso.
- Parágrafos curtos, fáceis de ler e escaneáveis.
- Uma única CTA ao final do texto.

"""
        return prompt.strip()

    def _build_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build the prompt for image generation based on post type."""
        post_type = post_data.get('type', '').lower()

        # Route to specific image prompt based on post type
        if post_type == 'post':
            return self._build_feed_image_prompt(post_data, content)
        elif post_type == 'reel':
            return self._build_reel_image_prompt(post_data, content)
        elif post_type == 'story':
            return self._build_story_image_prompt(post_data, content)
        else:
            # Default fallback for other types (carousel, live, etc.)
            return self._build_default_image_prompt(post_data, content)

    def _get_image_context_section(self, post_data: Dict, content: str) -> tuple:
        """Get common image context information for all image prompt types."""
        post_type = post_data.get('type', '')
        objective = post_data.get('objective', '')
        name = post_data.get('name', '')
        further_details = post_data.get('further_details', '')

        # Extract title from content if available
        title = ""
        if "Título:" in content:
            title_line = content.split("Título:")[1].split("\n")[0].strip()
            title = title_line

        # Use title from content if available, otherwise use name from post_data
        tema = title if title else name

        # Creator profile information for brand identity (if available)
        identidade_marca = "Estilo profissional e moderno"
        if hasattr(self, 'user') and self.user:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.filter(user=self.user).first()
            if profile:
                brand_info = []
                audience_info = []
                if profile.business_name:
                    brand_info.append(f"Empresa: {profile.business_name}")
                if profile.profession:
                    brand_info.append(f"Profissão: {profile.profession}")
                if profile.specialization:
                    brand_info.append(
                        f"Especialização: {profile.specialization}")

                # Target audience information
                if profile.target_gender and profile.target_gender.strip():
                    audience_info.append(
                        f"Gênero do Público: {profile.target_gender}")

                if profile.target_age_range and profile.target_age_range.strip():
                    audience_info.append(
                        f"Faixa Etária: {profile.target_age_range}")

                if profile.target_location and profile.target_location.strip():
                    audience_info.append(
                        f"Localização: {profile.target_location}")

                if profile.target_interests and profile.target_interests.strip():
                    audience_info.append(
                        f"Interesses: {profile.target_interests}")

                if profile.voice_tone and profile.voice_tone.strip():
                    audience_info.append(
                        f"Tom de Voz da Marca: {profile.voice_tone}")

                if audience_info:
                    brand_info.append(
                        f"Dados do Público-Alvo e Marca: {' | '.join(audience_info)}")

                # Color palette
                colors = [profile.color_1, profile.color_2,
                          profile.color_3, profile.color_4, profile.color_5]
                valid_colors = [
                    color for color in colors if color and color.strip()]
                if valid_colors:
                    brand_info.append(
                        f"Cores da marca: {', '.join(valid_colors)}")

                if brand_info:
                    identidade_marca = f"{', '.join(brand_info)}, estilo profissional"

        # Add further details context if available
        context_adicional = f" - Contexto adicional: {further_details}" if further_details and further_details.strip(
        ) else ""

        return tema, objective, post_type, identidade_marca, context_adicional

    def _build_feed_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for feed post images."""
        tema, objective, post_type, identidade_marca, context_adicional = self._get_image_context_section(
            post_data, content)

        # TODO: Replace with your specific feed image prompt
        prompt = f"""
Você é um especialista em design para marketing digital e redes sociais.  
Sua missão é gerar artes visuais profissionais e impactantes, otimizadas para posts de Feed no Instagram ou Facebook.  

### DADOS DE ENTRADA 
- Assunto do post: {tema}
- Objetivo do post: {objective}
- Tipo do post: Feed
- Mais detalhes: {context_adicional}

---

### REGRAS PARA A IMAGEM:

1. A imagem deve ser **clara, atrativa e diretamente relacionada ao tema do post**.  
2. Formato padrão de Feed: **quadrado 1080x1080 px**.  
3. Use **chamadas curtas e impactantes como título na imagem**, sem excesso de texto.  
   - Exemplo: “Mais energia no seu dia 💧”, “Transforme sua rotina com saúde ✨”.  
   - Nunca coloque blocos longos de texto.  
4. O design deve ser limpo, moderno e profissional, respeitando a identidade visual da marca (quando fornecida).  
5. As cores, tipografia e estilo devem transmitir **o tom da marca** descrito nos detalhes (ex.: acolhedor, sofisticado, jovem, minimalista).  
6. Usar elementos visuais que conectem com o **público-alvo e seus interesses**.  
7. Respeitar sempre comunicação ética e positiva, sem sensacionalismo ou imagens que possam gerar desconforto.  
8. Se apropriado, incluir ícones ou ilustrações sutis que reforcem a mensagem (ex.: gotas para hidratação, folha para saúde, raio de energia para disposição).  

---

### SAÍDA ESPERADA:
- **Uma imagem final, pronta para ser publicada no Feed.**  
- A arte deve conter apenas uma chamada curta e impactante como título.  
- O design deve estar finalizado de acordo com os dados fornecidos e pronto para uso imediato.  



"""
        return prompt.strip()

    def _build_reel_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for reel cover images."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')
        details = self._build_all_details(further_details)
        # TODO: Replace with your specific reel image prompt
        prompt = f"""
Você é um especialista em design para marketing digital e redes sociais.  
Sua missão é criar capas de Reels profissionais, modernas e impactantes, que chamem a atenção do público já no primeiro contato.  
A capa deve ser clara, objetiva e reforçar a ideia central do conteúdo, sem excesso de elementos ou textos longos.  

### DADOS DE ENTRADA:
- Assunto do post: {name}  
- Objetivo do post: {objective}  
- Tipo do post: Capa de Reel  
- Mais detalhes: {details}  

---

### REGRAS PARA A CAPA:

1. Formato: **vertical 1080x1920 px**, otimizado para Reels.  

2. A capa deve conter **uma chamada curta e impactante**, em forma de título, que incentive o clique no vídeo.  
   - Exemplo: “Energia no pós-bariátrico 💧”, “O segredo do emagrecimento saudável ✨”.  
   - Nunca usar blocos longos de texto.  

3. O design deve ser limpo, moderno e profissional, com hierarquia visual clara:  
   - Título curto em destaque.  
   - Elementos visuais que remetam ao tema.  

4. Usar **cores, tipografia e estilo compatíveis com a identidade visual da marca** (quando fornecida).  

5. Se apropriado, incluir elementos visuais sutis que conectem ao tema (ex.: gotas d’água para soroterapia, coração para saúde, ícones de energia, etc.).  

6. Evitar poluição visual e excesso de informações. A capa deve ser simples, mas altamente chamativa.  

7. Comunicação sempre ética e positiva, sem sensacionalismo ou exageros.  

8. Utilize a imagem anexada como um canvas para a geração de todas as imagens que eu te pedir. Elas devem ser criadas no formato 9:16 para serem postadas no instagram
---

### SAÍDA ESPERADA:
- **Uma imagem final no formato de capa para Reel (1080x1920 px)**.  
- O design deve conter apenas **um título curto e impactante**, sem blocos longos de texto.  
- A arte deve estar finalizada, pronta para uso como capa do Reel.  



"""
        return prompt.strip()

    def _build_story_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for story images."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')
        details = self._build_all_details(further_details)

        # TODO: Replace with your specific story image prompt
        prompt = f"""
Você é um designer digital profissional, especialista em criar artes comerciais, modernas e limpas para redes sociais.
Sua missão é gerar uma arte no formato Story (1080x1920 px), sofisticada, atual e que realmente ajude a vender.

--REGRA OBRIGATORIA--
Caso uma imagem branca seja anexada, utilize-a como base para a criação da arte, respeitando o formato 9:16 e integrando-a harmoniosamente ao design final.

📥 Entradas do Cliente:

Assunto: {name}

Objetivo da arte: {objective}

Mais detalhes: {details}

⚠️ Regras obrigatórias:

Respeitar área segura obrigatória:

Margem mínima de 250 px no topo e na base.

Margem mínima de 60 px nas laterais.

Nenhum texto deve ser adicionado.

Imagens de pessoas variadas e brasileiras (brancas e negras, diversidade autêntica, sempre realistas e naturais).

Nunca repetir selos/ícones/textos.

📋 Hierarquia visual obrigatória:

Imagem principal: produto em destaque OU pessoa brasileira que represente o tema.

🎨 Estilo esperado:

Clean e premium (sem excesso de elementos).

Fundo moderno: cor sólida, gradiente suave ou textura leve.

Ícones apenas se forem sutis e agregarem valor.

Estética de campanha publicitária profissional.

Design que transmita confiança, clareza e desejo de compra.
"""
        return prompt.strip()

    def _build_default_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build default prompt for other image types (carousel, live, etc.)."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')
        details = self._build_all_details(further_details)
        prompt = f"""Você é um especialista em criação visual para marketing digital e redes sociais.  
Sua missão é gerar imagens criativas, profissionais e impactantes que transmitam a mensagem central da campanha.  

### DADOS DE ENTRADA (serão fornecidos pelo sistema):
- Assunto do post: {name}
- Objetivo do post: {objective}
- Tipo do post: Story ou feed ou reels
- Mais detalhes: {details}

---

### REGRAS PARA GERAÇÃO DA IMAGEM:

1. A imagem deve ser **clara, atrativa e coerente** com o tema central e o objetivo da campanha.  
2. Ajustar o **formato da arte** conforme o tipo de conteúdo (ex.: Story 1080x1920, Post 1080x1080, Reel capa 1080x1920).  
3. Representar a mensagem de forma **ética e respeitosa**, sem estereótipos ou sensacionalismo.  
4. Usar elementos visuais que conectem com o **perfil do criador e sua área de atuação**.  
5. Se houver informações da empresa (logo, paleta de cores, estilo visual), elas devem ser integradas.  
6. Evite excesso de texto. Se for necessário, use frases curtas e legíveis.  
7. A imagem deve parecer **profissional e de alta qualidade**, pronta para publicação em redes sociais.  

---

### SAÍDA ESPERADA:
- A imagem, em alta qualidade, compreendendo todas as informações passadas"""

        return prompt.strip()

    def _build_regeneration_prompt(self, current_content: str, user_prompt: str) -> str:
        """Build the prompt for content regeneration with user feedback."""

        prompt = f"""
Você é um especialista em ajustes e refinamentos de conteúdo para marketing digital.  
Sua missão é editar o material já criado (copy) mantendo sua identidade visual, estilo e tom, alterando **apenas o que for solicitado**.  

### DADOS DE ENTRADA:
- Conteúdo original: {current_content}  
- Alterações solicitadas: {user_prompt}

---

### REGRAS PARA EDIÇÃO:

1. **Mantenha toda a identidade visual e estilística do conteúdo original**:  
   - Paleta de cores  
   - Tipografia  
   - Layout  
   - Tom de voz e estilo da copy  
   - Estrutura do design ou texto  

2. **Modifique somente o que foi solicitado** pelo profissional, sem alterar nada além disso.  

3. Ajuste apenas as frases, palavras ou CTA especificadas, mantendo a mesma estrutura, tom e parágrafos curtos.  

4. Nunca descaracterize o material já feito. A ideia é **refinar e ajustar**, não recriar.  

5. O resultado deve estar pronto para uso imediato, atualizado conforme solicitado e sem perda da identidade visual/marca.  

---

### SAÍDA ESPERADA:
- Versão revisada do conteúdo (copy), com **as alterações solicitadas aplicadas**.  
- Todo o restante deve permanecer idêntico ao original.  
- Material final pronto para publicação.  

"""

        return prompt

    def _build_variation_prompt(self, current_content: str) -> str:
        """Build the prompt for creating a variation of existing content."""
        prompt = f"""
Você é um especialista em ajustes e refinamentos de conteúdo para marketing digital.  
Sua missão é editar o material já criado (copy) mantendo sua identidade visual, estilo e tom, alterando **apenas o que for solicitado**.  

### DADOS DE ENTRADA:
- Conteúdo original: {current_content}  

---

### REGRAS PARA EDIÇÃO:

1. **Mantenha toda a identidade visual e estilística do conteúdo original**:  
   - Paleta de cores  
   - Tipografia  
   - Layout  
   - Tom de voz e estilo da copy  
   - Estrutura do design ou texto  

2. **Modifique somente o que foi solicitado** pelo profissional, sem alterar nada além disso.  

3. Ajuste apenas as frases, palavras ou CTA especificadas, mantendo a mesma estrutura, tom e parágrafos curtos.  

4. Nunca descaracterize o material já feito. A ideia é **refinar e ajustar**, não recriar.  

5. O resultado deve estar pronto para uso imediato, atualizado conforme solicitado e sem perda da identidade visual/marca.  

---

### SAÍDA ESPERADA:
- Versão revisada do conteúdo (copy), com **as alterações solicitadas aplicadas**.  
- Todo o restante deve permanecer idêntico ao original.  
- Material final pronto para publicação.  


"""

        return prompt

    def _build_image_regeneration_prompt(self, user_prompt: str) -> str:
        """Build the prompt for image regeneration with user feedback."""

        # If no current image is found, we need to create a new image based on the user's request
        prompt = f"""
Você é um especialista em design digital e edição de imagens para marketing.  
Sua missão é editar a imagem já criada, mantendo **100% da identidade visual, layout, estilo, cores e elementos originais**, alterando **apenas o que for solicitado**.  

### DADOS DE ENTRADA:
- Imagem original: [IMAGEM ANEXADA]
- Alterações solicitadas: {user_prompt if user_prompt else 'imagem parecida mas diferente, dê-me uma nova versão'}

---

### REGRAS PARA EDIÇÃO:

1. **Nunca recrie a imagem do zero.**  
   - O design, estilo, paleta de cores, tipografia, elementos gráficos e identidade visual devem permanecer exatamente iguais à arte original.  

2. **Aplique apenas as mudanças solicitadas.**  
   - Exemplo: se o pedido for “mudar o título para X”, altere somente o texto do título, mantendo a fonte, cor, tamanho e posicionamento original.  
   - Se o pedido for “trocar a cor do fundo”, altere apenas essa cor, mantendo todos os demais elementos intactos.  

3. **Não adicione novos elementos** que não foram solicitados.  
   - O layout deve permanecer idêntico.  

4. **Respeite sempre a logomarca oficial** caso já esteja aplicada na arte.  

5. O resultado deve parecer exatamente a mesma imagem original, com apenas os pontos ajustados conforme solicitado.  

---

### SAÍDA ESPERADA:
- **A mesma imagem original, com apenas as alterações solicitadas aplicadas.**  
- Nada além do que foi pedido deve ser modificado.  
- O design final deve estar pronto para uso, fiel ao original.  



"""

        return prompt

    def _generate_content_with_ai(self, ai_service, prompt: str) -> str:
        """Generate content using the AI service with direct API request."""
        try:
            # Use the AI service's direct _make_ai_request method with our sophisticated prompt
            response_text = ai_service._make_ai_request(
                prompt, ai_service.model_name)

            if response_text and response_text.strip():
                return response_text.strip()
            else:
                raise Exception("Empty response from AI service")

        except Exception:
            # Fallback: return a simple response
            return """Título: Conteúdo Gerado por IA

Texto: Este é um conteúdo gerado automaticamente. Por favor, personalize conforme necessário.

Chamada para ação no post/carrossel: Saiba mais!"""
