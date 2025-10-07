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
        print(
            f"Gerando conteúdo com {provider} - {model} para usuário {user.id if user and user.is_authenticated else 'Anônimo'}")
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

            print(
                f"Conteúdo de tipo {post_data.get('type', 'desconhecido')} gerado com sucesso para usuário {user.id} - {user.first_name}"
            )
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

    def _get_creator_profile_data(self) -> dict:
        """Get creator profile data for prompt personalization."""
        profile_data = {
            'professional_name': 'Não informado',
            'profession': 'Não informado',
            'whatsapp_number': 'Não informado',
            'business_name': 'Não informado',
            'specialization': 'Não informado',
            'business_description': 'Não informado',
            'target_gender': 'Não informado',
            'target_age_range': 'Não informado',
            'target_interests': 'Não informado',
            'target_location': 'Não informado',
            'logo': 'Não fornecido',
            'color_palette': 'Não definida',
            'voice_tone': 'Profissional'
        }

        if hasattr(self, 'user') and self.user:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.filter(user=self.user).first()
            if profile:
                if profile.professional_name:
                    profile_data['professional_name'] = profile.professional_name
                if profile.profession:
                    profile_data['profession'] = profile.profession
                if profile.whatsapp_number:
                    profile_data['whatsapp_number'] = profile.whatsapp_number
                if profile.business_name:
                    profile_data['business_name'] = profile.business_name
                if profile.specialization:
                    profile_data['specialization'] = profile.specialization
                if profile.business_description:
                    profile_data['business_description'] = profile.business_description
                if profile.target_gender:
                    profile_data['target_gender'] = profile.target_gender
                if profile.target_age_range:
                    profile_data['target_age_range'] = profile.target_age_range
                if profile.target_interests:
                    profile_data['target_interests'] = profile.target_interests
                if profile.target_location:
                    profile_data['target_location'] = profile.target_location
                if profile.logo:
                    profile_data['logo'] = 'Logo disponível'
                if profile.voice_tone:
                    profile_data['voice_tone'] = profile.voice_tone

                # Color palette
                colors = [profile.color_1, profile.color_2,
                          profile.color_3, profile.color_4, profile.color_5]
                valid_colors = [
                    color for color in colors if color and color.strip()]
                if valid_colors:
                    profile_data['color_palette'] = ', '.join(valid_colors)

        return profile_data

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

        # Get dynamic data from creator profile and post
        creator_profile_data = self._get_creator_profile_data()

        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo, com foco em posts de Feed para redes sociais (Instagram, Facebook, LinkedIn, etc.).
Sua missão é gerar copies otimizadas e prompts de imagem complementares, com base nas informações do negócio do cliente e nos dados específicos do post.

Siga todas as instruções abaixo com atenção e precisão:

🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome profissional: {creator_profile_data.get('professional_name', 'Não informado')}

Profissão: {creator_profile_data.get('profession', 'Não informado')}

Número de celular: {creator_profile_data.get('whatsapp_number', 'Não informado')}

Nome do negócio: {creator_profile_data.get('business_name', 'Não informado')}

Setor/Nicho: {creator_profile_data.get('specialization', 'Não informado')}

Descrição do negócio: {creator_profile_data.get('business_description', 'Não informado')}

Gênero do público-alvo: {creator_profile_data.get('target_gender', 'Não informado')}

Faixa etária do público-alvo: {creator_profile_data.get('target_age_range', 'Não informado')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', 'Não informado')}

Localização do público-alvo: {creator_profile_data.get('target_location', 'Não informado')}

Logo: {creator_profile_data.get('logo', 'Não fornecido')}

Paleta de cores: {creator_profile_data.get('color_palette', 'Não definida')}

Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

🧠 DADOS DO POST:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {details}

🪶 REGRAS PARA A COPY:

Siga o método AIDA (Atenção, Interesse, Desejo, Ação):

Comece com uma frase ou pergunta envolvente que capture a atenção.

Desenvolva o tema de forma fluida e relevante, despertando curiosidade e identificação.

Crie conexão emocional e mostre benefícios reais.

Finalize com uma única CTA natural e coerente com o objetivo do post.

Estilo e tom:

Use parágrafos curtos e bem espaçados, facilitando a leitura rápida e escaneável.

Respeite o tom de voz informado ({creator_profile_data.get('voice_tone', 'Profissional')}).

Evite sensacionalismo, exageros ou promessas irreais.

Adapte o vocabulário ao público-alvo, nicho e faixa etária.

Traga expressões, temas ou referências atuais que estejam em alta no contexto do post.

Uso de emojis:

Utilize em média 5 emojis por copy principal, aplicados de forma natural, coerente e distribuída ao longo do texto.

Os emojis devem reforçar o tom e o sentimento do conteúdo, nunca poluir visualmente.

Não use emojis no título, subtítulo ou CTA da imagem.

Personalização obrigatória:

Considere o nicho, público, localização e interesses para contextualizar a linguagem e o estilo.

Faça alusões sutis ao negócio do cliente ({creator_profile_data.get('business_name', 'seu negócio')}) quando fizer sentido, sem autopromoção direta.

📦 FORMATO DE SAÍDA:

Gere a resposta exatamente neste formato:

[TEXTO COMPLETO DA COPY — fluido, natural e pronto para publicação no Feed, com média de 5 emojis inseridos de forma estratégica.]

Como sugestão para escrever na imagem:

Título: [Frase curta e chamativa (até 8 palavras)]

Subtítulo: [Frase complementar breve, despertando curiosidade ou contexto]

CTA: [Uma chamada clara e coerente com o objetivo do post]

Descrição para gerar a imagem (sem texto):
Crie uma descrição detalhada da imagem ideal para acompanhar o post, considerando:

Identidade visual (use a paleta de cores {creator_profile_data.get('color_palette')})

Nicho e público-alvo ({creator_profile_data.get('specialization')}, {creator_profile_data.get('target_gender')}, {creator_profile_data.get('target_age_range')}, {creator_profile_data.get('target_location')})

Tom de voz e emoção transmitida pela copy ({creator_profile_data.get('voice_tone')})

Cores, estilo, iluminação e ambientação condizentes com o negócio ({creator_profile_data.get('business_name')})

Elementos visuais que comuniquem a mensagem principal da copy sem incluir textos.
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
Você é um especialista em design digital e marketing visual.



Sua missão é gerar uma arte de Story altamente criativa, moderna e impactante, que vá além do simples.

O resultado deve ser um design sofisticado, envolvente e visualmente atrativo, pronto para ser publicado como Story.



### DADOS DE ENTRADA (serão fornecidos pelo sistema):

- Assunto do post: {name}

- Objetivo do post: {objective}

- Tipo do post: Story

- Mais detalhes: {details}



---



### REGRAS PARA A IMAGEM:



1. Gere **apenas 1 imagem final** no formato vertical **1080x1920 px (proporção 9:16)**, otimizada para Instagram Stories.



2. Utilize a **imagem anexada como canvas base** para a geração da arte.

- As alterações devem ser feitas sobre essa base, preservando estilo, layout e identidade, a menos que outra mudança seja explicitamente pedida.



3. **Estética PREMIUM e de Vanguarda:** O design deve ter uma estética moderna, minimalista e elegante. **Implemente o 'Princípio do Espaço Negativo' (Less is More)**, utilizando hierarquia de forma sofisticada e focando na qualidade dos assets, não na quantidade. Crie profundidade com sombras suaves, gradientes bem trabalhados ou elementos 3D quando apropriado. Busque um acabamento que se assemelhe a um material de agência de alto nível (ex: FutureBrand, Pentagram).



4. **Título como ÂNCORA Visual:** Crie um título **extremamente curto** (máx. 5 palavras) e impactante, integrado ao design de forma harmoniosa, com tipografia que reflita a identidade da marca e garanta impacto imediato (tamanho e peso contrastantes).



5. **Hierarquia visual clara**:

- Título principal chamando a atenção.

- Espaço de respiro para facilitar a leitura.

- Elementos gráficos ou ilustrações de apoio que reforcem o tema (mas sem poluição visual).



6. **Coerência de Marca (Brand Guidelines):** O design deve seguir diretrizes de marca imaginárias, incluindo a paleta de cores primária e secundária, e tipografia, para garantir coesão em todas as peças. **O resultado não pode parecer genérico.**



7. **LOGOMARCA**:

- Se o cliente anexar a logomarca, **use obrigatoriamente a logo original** no design.

- Se não houver logomarca anexada, **não crie logomarca fictícia em hipótese alguma**.



8. **Imagens de pessoas reais** podem ser usadas no design para transmitir mais **profissionalismo, proximidade e autenticidade**, desde que respeitem a proposta visual da marca.



9. **Elementos Visuais de Alto Nível:** Utilize apenas **ativos visuais de alta resolução e qualidade inquestionável**. Priorize renderizações 3D abstratas, fotografia com tratamento cinematográfico, ou ilustrações vetoriais minimalistas e originais. **Evite fotos de banco de imagens genéricas.**



10. **Área de segurança (safe zone):** mantenha pelo menos 10% de margem sem textos próximos às bordas, para evitar cortes em diferentes telas.



11. Toda a comunicação visual deve ser **positiva, ética e inspiradora**, sem sensacionalismo ou exageros.



12. **Regras de texto em PT-BR (Blindagem Total Contra Erros):**



12.1. Criação e Validação por Redundância:

- A IA deve criar a copy curta e impactante **exclusivamente em Português do Brasil (pt-BR)**.

- **PROTOCOLO DE REVISÃO DUPLA:** 1º - Rascunho: Gere a copy inicial. 2º - Validação Rigorosa: Submeta esta copy a uma revisão gramatical e ortográfica automática de nível avançado. O resultado **FINAL** deve ser zero erros de ortografia, acentuação ou concordância.



12.2. Lista de Checagem (Checklist) Ortográfica e Gramatical Essencial:

- A IA deve confirmar o seguinte com **extremo rigor** antes de finalizar a imagem:

- **100% de Correção Ortográfica:** Cada palavra individualmente deve ser verificada para garantir sua grafia exata e correta em PT-BR. **Nenhum erro de digitação (typo), troca de letras, inversão, omissão ou adição de letras é permitido em hipótese alguma** (ex: "Garanitad" é proibido, deve ser "Garantida").

- **Acentos:** Todas as palavras essenciais (ex: saúde, médico, física) e de regra geral estão acentuadas corretamente.

- **Crase:** O uso de crase foi validado.

- **Concordância:** A concordância nominal e verbal está perfeita.

- **Validação Lexical:** Cada palavra utilizada deve ser **validada ativamente por sua existência e grafia correta em um dicionário de Português do Brasil padrão**, assegurando que não há palavras inventadas ou corrompidas.



12.3. Aplicação Técnica:

- Renderizar os textos como camadas de texto editável (live text) usando tipografia que suporte totalmente os caracteres pt-BR (ex.: Inter, Montserrat, Poppins, Nunito, Roboto).

- Garantir alta legibilidade: contraste adequado, sem distorção, sem warp, espaçamento e acentuação preservados.

- Validação Final: A IA deve validar internamente que todas as palavras estão corretas em pt-BR antes da renderização final.



---



### SAÍDA ESPERADA:

- **Uma única imagem final premium em formato 1080x1920 px (9:16)**.

- Arte com acabamento visual sofisticado, criativo e impactante, pronta para Story.

- Design moderno, com chamada curta em destaque e alinhado ao tema do post.

- Estética de alto nível, como um material produzido em agência de design profissional.

- Logomarca usada apenas se fornecida, nunca criada artificialmente.

- Possibilidade de incluir **pessoas reais** no design para transmitir mais profissionalismo e autenticidade.

- Texto criado pela IA em **pt-BR perfeito**, sem erros de português, pronto para publicação.
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
