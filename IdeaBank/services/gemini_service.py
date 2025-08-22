import json
import os
from typing import Dict, List, Tuple

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from django.contrib.auth.models import User

from .base_ai_service import BaseAIService


class GeminiService(BaseAIService):
    """Service for interacting with Google Gemini AI."""

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai não está instalado. Execute: pip install google-generativeai")

        super().__init__(model_name)

        # Get default API key from environment
        self.default_api_key = os.getenv('GEMINI_API_KEY', '')

        # Initialize without API key - will be set per request
        genai.configure(api_key="")
        self.model = genai.GenerativeModel(model_name)

    def _validate_credits(self, user: User, estimated_tokens: int, model_name: str) -> bool:
        """Validate if user has sufficient credits for the AI operation."""
        try:
            from .ai_model_service import AIModelService
            if AIModelService:
                return AIModelService.validate_user_credits(user, model_name, estimated_tokens)
        except ImportError:
            pass
        return True  # Skip validation if service not available

    def _deduct_credits(self, user: User, actual_tokens: int, model_name: str, description: str) -> bool:
        """Deduct credits after AI operation."""
        try:
            from .ai_model_service import AIModelService
            if AIModelService:
                return AIModelService.deduct_credits(user, actual_tokens, model_name, description)
        except ImportError:
            pass
        return True  # Skip deduction if service not available

    def _estimate_tokens(self, prompt: str, model_name: str) -> int:
        """Estimate token count for a prompt."""
        try:
            from .ai_model_service import AIModelService
            if AIModelService:
                return AIModelService.estimate_tokens(prompt, model_name)
        except ImportError:
            pass

        # Fallback estimation: roughly 4 characters per token
        return len(prompt) // 4

    def _select_optimal_model(self, user: User, estimated_tokens: int, preferred_provider: str = None) -> str:
        """Select the optimal AI model for the operation."""
        try:
            from .ai_model_service import AIModelService
            if AIModelService:
                return AIModelService.select_optimal_model(user, estimated_tokens, preferred_provider)
        except ImportError:
            pass

        # Fallback to default model
        return self.model_name

    def _make_ai_request(self, prompt: str, model_name: str, api_key: str = None) -> str:
        """Make the actual AI API request to Gemini."""
        # Configure API key
        api_key = api_key or self.default_api_key
        if not api_key:
            raise ValueError("API key is required for Gemini requests")

        genai.configure(api_key=api_key)

        try:
            # Generate content
            response = self.model.generate_content(prompt)

            if response.text:
                return response.text
            else:
                raise Exception("Empty response from Gemini API")

        except Exception as e:
            print(f"Error making Gemini request: {e}")
            raise Exception(f"Falha na comunicação com Gemini: {str(e)}")

    def generate_single_idea_with_progress(self, user: User, campaign: Dict, idea_params: Dict, progress_callback=None) -> Tuple[Dict, Dict]:
        """Generate a single idea with progress tracking."""
        steps = [
            "Inicializando geração de ideia única...",
            "Validando créditos do usuário...",
            "Construindo prompt da ideia...",
            "Conectando com Gemini...",
            "Gerando ideia única...",
            "Processando resposta da IA...",
            "Validando dados da ideia...",
            "Estruturando ideia final...",
            "Finalizando geração..."
        ]

        self.progress_tracker.set_steps(steps)

        try:
            # Step 1: Initialize
            self.progress_tracker.next_step()
            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 2: Validate credits
            self.progress_tracker.next_step()
            prompt = self._build_single_idea_prompt(
                user, campaign, idea_params)
            estimated_tokens = self._estimate_tokens(prompt, self.model_name)
            if not self._validate_credits(user, estimated_tokens, self.model_name):
                raise Exception("Créditos insuficientes para gerar ideia")

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 3: Build prompt
            self.progress_tracker.next_step()

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 4: Connect to AI
            self.progress_tracker.next_step()
            api_key = campaign.get('gemini_api_key')
            response_text = self._make_ai_request(
                prompt, self.model_name, api_key)

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 5: Generate idea
            self.progress_tracker.next_step()

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 6: Process response
            self.progress_tracker.next_step()
            idea_data = self._parse_single_idea_response(
                response_text, campaign, idea_params)

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 7: Validate data
            self.progress_tracker.next_step()
            if not idea_data:
                raise Exception("Falha ao gerar ideia única")

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 8: Structure final idea
            self.progress_tracker.next_step()

            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Step 9: Finalize
            self.progress_tracker.next_step()
            if progress_callback:
                progress_callback(self.progress_tracker.get_progress())

            # Deduct credits
            actual_tokens = self._estimate_tokens(
                prompt + str(idea_data), self.model_name)
            self._deduct_credits(user, actual_tokens,
                                 self.model_name, "Geração de ideia única")

            return idea_data, self.progress_tracker.get_progress()

        except Exception as e:
            print(f"Error in generate_single_idea_with_progress: {e}")
            raise e

    def _build_single_idea_prompt(self, user: User, campaign: Dict, idea_params: Dict) -> str:
        """Build prompt for single idea generation."""
        from CreatorProfile.models import CreatorProfile

        profile = CreatorProfile.objects.filter(user=user).first()

        # Build persona section
        persona_section = self._build_persona_section(campaign)

        # Build social media section
        social_media_section = self._build_social_media_section(
            profile) if profile else ""

        prompt = f"""
Você é um especialista em marketing digital e criação de conteúdo para redes sociais.
Sua tarefa é gerar UMA ideia criativa e estratégica para uma campanha específica.

CONTEXTO DA CAMPANHA:
- Título: {campaign.get('title', 'Não especificado')}
- Descrição: {campaign.get('description', 'Não especificado')}
- Objetivos: {', '.join(campaign.get('objectives', []))}
- Plataformas: {', '.join(campaign.get('platforms', []))}
- Tom de Voz: {campaign.get('voice_tone', 'profissional')}

PARÂMETROS DA IDEIA:
- Título: {idea_params.get('title', 'Não especificado')}
- Descrição: {idea_params.get('description', 'Não especificado')}
- Conteúdo: {idea_params.get('content', 'Não especificado')}
- Plataforma: {idea_params.get('platform', 'Não especificado')}
- Tipo de Conteúdo: {idea_params.get('content_type', 'Não especificado')}

{persona_section}

{social_media_section}

INSTRUÇÕES:
1. Gere UMA ideia criativa e estratégica baseada nos parâmetros fornecidos
2. A ideia deve ser específica para a plataforma selecionada
3. Considere o tom de voz e objetivos da campanha
4. A ideia deve incluir:
   - Título atrativo e otimizado
   - Descrição clara e persuasiva
   - Conteúdo principal envolvente
   - Tipo de conteúdo apropriado para a plataforma
   - Plataforma específica
   - 3 variações (A, B, C) com:
     * Headline impactante
     * Copy persuasivo
     * CTA claro e acionável
     * Hashtags relevantes e estratégicos
     * Descrição visual detalhada
     * Composição de cores harmoniosa

FORMATO DE RESPOSTA:
Retorne APENAS um JSON válido com a seguinte estrutura:
{{
  "title": "Título da Ideia",
  "description": "Descrição da ideia",
  "content": "Conteúdo principal da ideia",
  "platform": "plataforma",
  "content_type": "tipo_de_conteudo",
  "variations": [
    {{
      "headline": "Headline da variação",
      "copy": "Copy da variação",
      "cta": "Call to action",
      "hashtags": ["hashtag1", "hashtag2"],
      "visual_description": "Descrição visual",
      "color_composition": "Composição de cores"
    }}
  ]
}}

IMPORTANTE:
- Retorne APENAS o JSON, sem texto adicional
- Use o idioma português brasileiro
- Seja criativo e estratégico
- Considere as melhores práticas da plataforma
- Foque na conversão e engajamento
- A ideia deve ser única e memorável
"""
        return prompt.strip()

    def _parse_single_idea_response(self, response_text: str, campaign: Dict, idea_params: Dict) -> Dict:
        """Parse AI response for single idea."""
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            if start_idx == -1:
                return None

            end_idx = response_text.rfind('}') + 1
            json_text = response_text[start_idx:end_idx]

            idea_data = json.loads(json_text)

            # Validate required fields
            required_fields = ['title', 'description',
                               'content', 'platform', 'content_type']
            for field in required_fields:
                if field not in idea_data:
                    return None

            return idea_data

        except Exception as e:
            print(f"Error parsing single idea response: {e}")
            return None

    # Legacy method compatibility
    def generate_campaign_ideas(self, user: User, config: Dict) -> List[Dict]:
        """Legacy method - now redirects to generate_campaign_ideas_with_progress."""
        ideas, _ = self.generate_campaign_ideas_with_progress(user, config)
        return ideas

    def generate_ideas(self, user: User, config: Dict) -> List[Dict]:
        """Legacy method - now redirects to generate_campaign_ideas_with_progress."""
        return self.generate_campaign_ideas(user, config)

    def improve_idea(self, user: User, current_idea, improvement_prompt: str, api_key: str = None) -> Dict:
        """Legacy method - now redirects to improve_idea_with_progress."""
        improved_data, _ = self.improve_idea_with_progress(
            user, current_idea, improvement_prompt, api_key)
        return improved_data

    def generate_single_idea(self, user: User, campaign: Dict, idea_params: Dict) -> Dict:
        """Legacy method - now redirects to generate_single_idea_with_progress."""
        idea_data, _ = self.generate_single_idea_with_progress(
            user, campaign, idea_params)
        return idea_data
