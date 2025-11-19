import os
from time import time

from AuditSystem.services import AuditService
from CreditSystem.services.credit_service import CreditService
from django.contrib.auth.models import User
from google import genai
from google.genai import types


class AiService:
    def __init__(self):
        self.main_model = 'gemini-2.5-flash'
        self.main_image_model = 'gemini-2.5-flash-image'
        self.secondary_model = 'gemini-2.5-flash-lite'
        self.secondary_image_model = 'gemini-2.5-flash-image-lite'
        self.api_key = os.getenv('GEMINI_API_KEY', '')
        self.client = genai.Client(api_key=self.api_key)
        self.contents = types.Content(
            role='user',
            parts=[]
        )
        self.generate_text_config = types.GenerateContentConfig(
            response_modalities=[
                "TEXT",
            ],
        )
        self.generate_image_config = types.GenerateContentConfig(
            image_config=types.ImageConfig(
                image_size="1K",
            ),
            response_modalities=[
                "IMAGE",
            ],
        )

    def generate_text(self, prompt_list: list[str], user: User) -> str:
        try:
            user_has_credits = self._validate_credits(
                user=user, operation='text_generation')
            if not user_has_credits:
                raise Exception(
                    "Créditos insuficientes para gerar texto. Por favor, adquira mais créditos.")

            for prompt in prompt_list:
                self.contents.parts.append(types.Part.from_text(text=prompt))

            try:
                result = self._try_model_with_retries(
                    model=self.main_model,
                    generate_function=lambda: self._try_generate_text(
                        self.main_model, self.contents, self.generate_text_config),
                    max_retries=3
                )
                self._deduct_credits(
                    user=user, model=self.main_model, operation='text_generation',
                    description='Geração de texto via Gemini'
                )

                AuditService.log_content_generation(
                    user=user,
                    action='content_generated',
                    status='success',
                    details={'model': self.main_model}
                )

                return result
            except Exception as main_error:
                if self._is_retryable_error(str(main_error)):
                    print(
                        f"Main image model failed: {main_error}. Trying secondary model...")
                    try:
                        result = self._try_model_with_retries(
                            model=self.secondary_model,
                            generate_function=lambda: self._try_generate_image(
                                self.secondary_model, self.contents, self.generate_image_config),
                            max_retries=3,
                            is_main_model=False
                        )
                        self._deduct_credits(
                            user=user, model=self.secondary_model, operation='text_generation',
                            description='Geração de texto via Gemini (fallback model)'
                        )

                        AuditService.log_content_generation(
                            user=user,
                            action='content_generated',
                            status='success',
                            details={'model': self.secondary_model}
                        )

                        return result
                    except Exception as secondary_error:
                        raise Exception(
                            f"Both image models failed after retries. Main: {main_error}, Secondary: {secondary_error}")
                else:
                    raise main_error

        except Exception as e:
            AuditService.log_content_generation(
                user=user,
                action='content_generation_failed',
                status='failure',
                details={'error': str(e)}
            )
            raise Exception(f"Error generating text: {str(e)}")

    def generate_image(self, prompt_list: list[str], user: User) -> str:
        try:
            user_has_credits = self._validate_credits(
                user=user, operation='image_generation')
            if not user_has_credits:
                raise Exception(
                    "Créditos insuficientes para gerar texto. Por favor, adquira mais créditos.")

            for prompt in prompt_list:
                self.contents.parts.append(types.Part.from_text(text=prompt))

            try:
                result = self._try_model_with_retries(
                    model=self.main_image_model,
                    generate_function=lambda: self._try_generate_image(
                        self.main_image_model, self.contents, self.generate_image_config),
                    max_retries=3,
                    is_main_model=True
                )
                self._deduct_credits(
                    user=user, model=self.main_image_model, operation='image_generation',
                    description='Geração de imagem via Gemini'
                )
                AuditService.log_image_generation(
                    user=user,
                    action='image_generated',
                    status='success',
                    details={'model': self.main_image_model}
                )
                return result
            except Exception as main_error:
                if self._is_retryable_error(str(main_error)):
                    print(
                        f"Main image model failed: {main_error}. Trying secondary model...")
                    try:
                        result = self._try_model_with_retries(
                            model=self.secondary_image_model,
                            generate_function=lambda: self._try_generate_image(
                                self.secondary_image_model, self.contents, self.generate_image_config),
                            max_retries=3,
                            is_main_model=False
                        )
                        self._deduct_credits(
                            user=user, model=self.secondary_image_model, operation='image_generation',
                            description='Geração de imagem via Gemini (fallback model)'
                        )
                        AuditService.log_image_generation(
                            user=user,
                            action='image_generated',
                            status='success',
                            details={'model': self.secondary_image_model}
                        )
                        return result
                    except Exception as secondary_error:
                        raise Exception(
                            f"Both image models failed after retries. Main: {main_error}, Secondary: {secondary_error}")
                else:
                    # Non-retryable error, don't try secondary
                    raise main_error

        except Exception as e:
            AuditService.log_image_generation(
                user=user,
                action='image_generation_failed',
                status='failure',
                details={'error': str(e)}
            )
            raise Exception(f"Error generating image: {str(e)}")

    def _try_model_with_retries(self, model: str, generate_function: callable, max_retries: int = 3) -> str:
        """Try making a request to the AI model with retries for retryable errors."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return generate_function()
            except Exception as e:
                error_str = str(e)
                last_error = e
                if not self._is_retryable_error(error_str):
                    # Non-retryable error, don't retry
                    raise e
                if attempt < max_retries - 1:
                    # Wait a bit before retrying (exponential backoff could be added here)
                    # Exponential backoff delay between retries
                    time.sleep(10 * (2 ** attempt))
                    print(
                        f"Attempt {attempt + 1} failed for {model}, retrying...")
                else:
                    print(f"All {max_retries} attempts failed for {model}")
        raise last_error

    def _is_retryable_error(self, error_str: str) -> bool:
        """Determine if an error is retryable based on its content."""
        retryable_indicators = [
            '503',
            'unavailable',
            'overloaded',
            'timeout',
            'temporarily',
            '429'
        ]
        return any(indicator in error_str.lower() for indicator in retryable_indicators)

    def _try_generate_text(self, model: str, contents: types.Content, config: types.GenerateContentConfig) -> str:
        """Try generating text using the specified model."""
        response_text = ''
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        ):
            if not self._check_for_content_parts(chunk):
                continue

            part = chunk.candidates[0].content.parts[0]
            if hasattr(part, 'text') and part.text:
                response_text += part.text
        return response_text

    def _try_generate_image(self, model: str, contents: types.Content, config: types.GenerateContentConfig) -> str:
        """Try generating an image using the specified model."""
        image_bytes = None
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        ):
            if not self._check_for_content_parts(chunk):
                continue

            part = chunk.candidates[0].content.parts[0]
            if hasattr(part, 'inline_data') and part.inline_data and hasattr(part.inline_data, 'data') and part.inline_data.data:
                image_bytes = part.inline_data
                # Use the image bytes directly
        return image_bytes

    def _check_for_content_parts(self, chunk: types.Content) -> bool:
        if not hasattr(chunk, 'candidates') or chunk.candidates is None:
            return False
        if (
            len(chunk.candidates) == 0
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
            or len(chunk.candidates[0].content.parts) == 0
        ):
            return False
        return True

    def _get_block_reason_error_message(self, error_str: str) -> str:
        """Generate user-friendly error message for Gemini block reasons."""
        if 'block_reason: OTHER' in error_str:
            return "O conteúdo solicitado foi bloqueado pelos filtros de segurança do Gemini. Isso pode acontecer com certos tipos de conteúdo. Tente reformular sua solicitação ou usar termos mais neutros."
        elif 'block_reason: SAFETY' in error_str:
            return "O conteúdo solicitado foi considerado inseguro pelos filtros de segurança do Gemini. Por favor, revise sua solicitação para evitar conteúdo potencialmente prejudicial."
        elif 'block_reason:' in error_str:
            return "O conteúdo solicitado foi bloqueado pelos filtros de segurança do Gemini. Tente uma abordagem diferente ou reformule sua solicitação."
        else:
            return "Erro de segurança na geração de conteúdo. Tente reformular sua solicitação."

    def _get_quota_error_message(self, error_str: str) -> str:
        """Generate user-friendly error message for quota/rate limit errors."""
        if '429' in error_str:
            return "Limite de taxa da API atingido. Tente novamente em alguns minutos."
        elif 'quota' in error_str.lower() or 'exhausted' in error_str.lower():
            return "Quota da API esgotada. Verifique seu plano de uso ou tente novamente mais tarde."
        else:
            return "Erro de limite da API. Tente novamente em alguns minutos."

    def _get_overload_error_message(self, error_str: str) -> str:
        """Generate user-friendly error message for server overload (503) errors."""
        if '503' in error_str or 'unavailable' in error_str.lower():
            return "O modelo de IA está temporariamente sobrecarregado. Tente novamente em alguns minutos."
        elif 'overloaded' in error_str.lower():
            return "O serviço de IA está sobrecarregado no momento. Aguarde alguns minutos e tente novamente."
        else:
            return "Serviço temporariamente indisponível. Tente novamente em alguns minutos."

    def _validate_credits(self, user: User, operation: str) -> bool:
        """Validate if user has sufficient credits."""
        try:
            return CreditService.validate_operation(user=user, operation_type=operation)
        except Exception:
            return False

    def _deduct_credits(self, user: User, model: str, operation: str, description: str) -> bool:
        """Deduct credits after AI operation."""
        try:
            return CreditService.deduct_credits_for_operation(
                user=user, operation_type=operation, ai_model=model, description=description)
        except Exception:
            return False
