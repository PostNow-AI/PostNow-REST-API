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
        # Validate credits before generation (skip for unauthenticated users)
        model_name = 'gemini-2.5-flash'  # Only supported model
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
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._build_image_prompt(post_data, content)

        try:
            image_url = ai_service.generate_image(
                prompt, user, post_data, content)
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
                post_data, current_content, user_prompt)
        else:
            prompt = self._build_variation_prompt(post_data, current_content)

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
        """Build the prompt for content generation using the same advanced copywriting prompt as base_ai_service."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        post_type = post_data.get('type', '')
        further_details = post_data.get('further_details', '')
        include_image = post_data.get('include_image', False)

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

        # Add further details if provided
        additional_context = f"\n\nDetalhes Adicionais: {further_details}" if further_details and further_details.strip(
        ) else ""

        # Add image generation context if requested
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
        """Build the prompt for image generation."""
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
                if profile.business_name:
                    brand_info.append(f"Empresa: {profile.business_name}")
                if profile.profession:
                    brand_info.append(f"Profissão: {profile.profession}")

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

        prompt = f"""Você é um especialista em criação visual para marketing digital e redes sociais.  
Sua missão é gerar imagens criativas, profissionais e impactantes que transmitam a mensagem central da campanha.  

### DADOS DE ENTRADA:  
- Tema da imagem: {tema}
- Objetivo da campanha: {objective}
- Tipo de conteúdo: {post_type} → pode ser Post, Reel (capa), Carousel, Story, Anúncio{context_adicional}
- Estilo visual desejado: MODERNO, PROFISSIONAL, REALISTA
- Cores/Identidade da marca: {identidade_marca}

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

        return prompt

    def _build_regeneration_prompt(self, post_data: Dict, current_content: str, user_prompt: str) -> str:
        """Build the prompt for content regeneration with user feedback."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        post_type = post_data.get('type', '')
        further_details = post_data.get('further_details', '')

        # Add further details context if available
        context_adicional = f"\n- Detalhes Adicionais: {further_details}" if further_details and further_details.strip(
        ) else ""

        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo, com domínio do método AIDA (Atenção, Interesse, Desejo, Ação) e das boas práticas de comunicação digital.  
Sua missão é gerar copies poderosas, relevantes e seguras para campanhas, sempre respeitando as políticas do Meta e Google Ads, evitando qualquer tipo de sensacionalismo, promessa exagerada ou afirmações que possam violar as diretrizes dessas plataformas.        
Você precisa melhorar o seguinte conteúdo de rede social baseado no feedback do usuário:

CONTEÚDO ATUAL:
{current_content}

FEEDBACK/SOLICITAÇÃO DO USUÁRIO:
{user_prompt}

ESPECIFICAÇÕES ORIGINAIS:
- Nome do post: {name}
- Objetivo: {objective}
- Tipo: {post_type}{context_adicional}

## REGRAS PARA CONSTRUÇÃO DA COPY:

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
- Linguagem alinhada ao perfil do criador e ao contexto fornecido.
- Respeito às boas práticas do Meta e Google Ads.  
- Emojis distribuídos de forma natural, sem excesso.  
- Parágrafos curtos, fáceis de ler e escaneáveis.  
- Uma única CTA ao final do texto.  

Por favor, recrie o conteúdo incorporando o feedback do usuário.

Certifique-se de que as melhorias atendam especificamente ao feedback fornecido.
"""

        return prompt

    def _build_variation_prompt(self, post_data: Dict, current_content: str) -> str:
        """Build the prompt for creating a variation of existing content."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        post_type = post_data.get('type', '')
        further_details = post_data.get('further_details', '')

        # Add further details context if available
        context_adicional = f"\n- Detalhes Adicionais: {further_details}" if further_details and further_details.strip(
        ) else ""

        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo, com domínio do método AIDA (Atenção, Interesse, Desejo, Ação) e das boas práticas de comunicação digital.  
Sua missão é gerar copies poderosas, relevantes e seguras para campanhas, sempre respeitando as políticas do Meta e Google Ads, evitando qualquer tipo de sensacionalismo, promessa exagerada ou afirmações que possam violar as diretrizes dessas plataformas.
Crie uma variação do seguinte conteúdo de rede social, mantendo o mesmo objetivo mas com abordagem diferente:

CONTEÚDO ORIGINAL:
{current_content}

ESPECIFICAÇÕES:
- Nome do post: {name}
- Objetivo: {objective}
- Tipo: {post_type}{context_adicional}

Crie uma nova versão que:
- Mantenha o mesmo objetivo e propósito
- Use uma abordagem ou angle diferente
- Tenha um tom ligeiramente diferente
- Mantenha a qualidade e efetividade


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
- Linguagem alinhada ao perfil do criador e ao contexto fornecido.
- Respeito às boas práticas do Meta e Google Ads.  
- Emojis distribuídos de forma natural, sem excesso.  
- Parágrafos curtos, fáceis de ler e escaneáveis.  
- Uma única CTA ao final do texto.  

Por favor, recrie o conteúdo como uma variação criativa do original.

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
