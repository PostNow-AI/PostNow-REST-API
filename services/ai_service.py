import base64
import os
from time import sleep

from AuditSystem.services import AuditService
from CreditSystem.services.credit_service import CreditService
from django.contrib.auth.models import User
from google import genai
from google.genai import types


class AiService:
    def __init__(self):
        # Prioridade padrão (como antes): Gemini 3 preview primeiro.
        # Flash/lite ficam como fallback.
        self.flash_models = [
            'gemini-2.0-flash', # Atualizado para 2.0 Flash que é o mais recente/rápido
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash',
            'gemini-1.5-flash-8b'
        ]
        self.models = [
            'gemini-3-pro-preview',
            'gemini-3-pro-preview',
            'gemini-3-pro-preview',
            'gemini-3-pro-preview',
            'gemini-3-pro-preview',
            'gemini-3-pro-preview',
            'gemini-3-pro-preview',
            'gemini-3-pro-preview',]
        self.image_models = [
            'gemini-3-pro-image-preview',
            'gemini-3-pro-image-preview',
            'gemini-3-pro-image-preview',
            'gemini-3-pro-image-preview',
            'gemini-3-pro-image-preview',
            'gemini-3-pro-image-preview',
            'gemini-3-pro-image-preview',
            'gemini-3-pro-image-preview',]
        self.api_key = os.getenv('GEMINI_API_KEY', '')
        self.client = genai.Client(api_key=self.api_key)
        self.generate_text_config = types.GenerateContentConfig(
            response_modalities=[
                "TEXT",
            ],
            tools=[types.Tool(
                google_search=types.GoogleSearch()
            )],
        )
        self.generate_image_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
            ],
            image_config=types.ImageConfig(
                aspect_ratio="4:5",
                image_size="1K",
            ),
        )

    def generate_text(self, prompt_list: list[str], user: User, config: types.GenerateContentConfig = None, return_metadata: bool = False, preferred_model: str = None, response_mime_type: str = None) -> dict | str:
        """Generate text using Gemini AI.
        
        Args:
            prompt_list: List of prompts to send to the model
            user: User making the request
            config: Optional custom generation config
            return_metadata: If True, returns dict with 'text' and 'grounding_metadata'. 
                           If False, returns only the text string (default for backward compatibility)
            preferred_model: Optional. If 'flash', forces use of faster Flash models.
            response_mime_type: Optional. If set (e.g. 'application/json'), forces the model to return data in this format.
        
        Returns:
            str if return_metadata=False (default)
            dict if return_metadata=True: {
                'text': str,
                'grounding_metadata': dict or None
            }
        """
        try:
            effective_config = self.generate_text_config

            if config is not None:
                effective_config = config
            
            # Apply response_mime_type if provided
            if response_mime_type:
                # Create a new config object
                # We intentionally DO NOT copy 'tools' (like Google Search) when requesting JSON,
                # to prevent Grounding metadata/artifacts from polluting the structured output.
                effective_config = types.GenerateContentConfig(
                    response_modalities=effective_config.response_modalities,
                    response_mime_type=response_mime_type
                )

            user_has_credits = self._validate_credits(
                user=user, operation='text_generation')
            if not user_has_credits:
                raise Exception(
                    "Créditos insuficientes para gerar texto. Por favor, adquira mais créditos.")

            # Select models based on preference
            target_models = self.models
            if preferred_model == 'flash':
                target_models = self.flash_models
                # Fallback to regular models if flash models fail all retries? 
                # For now, let's stick to flash if requested for speed.

            model, result = self._try_model_with_retries(
                models=target_models,
                generate_function=lambda model: self._try_generate_text(
                    model, prompt_list, effective_config),
                max_retries=3
            )
            self._deduct_credits(
                user=user, model=model, operation='text_generation',
                description='Geração de texto via Gemini'
            )

            AuditService.log_content_generation(
                user=user,
                action='content_generated',
                status='success',
                details={'model': model}
            )

            # Return based on return_metadata flag
            if return_metadata:
                return result
            else:
                # Backward compatibility: return only text
                return result['text'] if isinstance(result, dict) else result

        except Exception as e:
            AuditService.log_content_generation(
                user=user,
                action='content_generation_failed',
                status='failure',
                details={'error': str(e)}
            )
            raise Exception(f"Error generating text: {str(e)}")

    def generate_image(self, prompt_list: list[str], image_attachment: str, user: User, config: types.GenerateContentConfig = None) -> str:
        try:
            effective_config = self.generate_image_config

            if config is not None:
                effective_config = config

            user_has_credits = self._validate_credits(
                user=user, operation='image_generation')
            if not user_has_credits:
                raise Exception(
                    "Créditos insuficientes para gerar texto. Por favor, adquira mais créditos.")

            model, result = self._try_model_with_retries(
                models=self.image_models,
                generate_function=lambda model: self._try_generate_image(
                    model, prompt_list, image_attachment, effective_config),
                max_retries=3
            )
            self._deduct_credits(
                user=user, model=model, operation='image_generation',
                description='Geração de imagem via Gemini'
            )
            AuditService.log_image_generation(
                user=user,
                action='image_generated',
                status='success',
                details={'model': model}
            )
            return result

        except Exception as e:
            AuditService.log_image_generation(
                user=user,
                action='image_generation_failed',
                status='failure',
                details={'error': str(e)}
            )
            raise Exception(f"Error generating image: {str(e)}")

    def _try_model_with_retries(self, models: list[str], generate_function: callable, max_retries: int = 3) -> tuple[str, str]:
        """Try making a request to the AI model with retries for retryable errors."""
        last_error = None
        for model in models:
            for attempt in range(max_retries):
                try:
                    # Pass the current model to the function
                    result = generate_function(model)
                    print(f"Model {model} succeeded on attempt {attempt + 1}")
                    return model, result
                except Exception as e:
                    print(
                        f"Error with model {model} on attempt {attempt + 1}: {str(e)}")
                    error_str = str(e)
                    last_error = e
                    if not self._is_retryable_error(error_str):
                        # Non-retryable error, don't retry
                        print(
                            f"Non-retryable error for {model}, trying next model...")
                        break  # Break inner loop to try next model
                    if attempt < max_retries - 1:
                        # Exponential backoff delay between retries
                        sleep(5 * (2 ** attempt))
                        print(
                            f"Attempt {attempt + 1} failed for {model}, retrying...")
                    else:
                        print(
                            f"All {max_retries} attempts for {model} failed")
        raise last_error

    def _is_retryable_error(self, error_str: str) -> bool:
        """Determine if an error is retryable based on its content."""
        retryable_indicators = [
            '503',
            '500',
            'internal',
            'unavailable',
            'overloaded',
            'timeout',
            'temporarily',
            '429',
            'No image data received from the model'
        ]
        return any(indicator in error_str.lower() for indicator in retryable_indicators)

    def _try_generate_text(self, model: str, prompt_list: list[str], config: types.GenerateContentConfig) -> dict:
        """Try generating text using the specified model.
        
        Returns:
            dict: {
                'text': str - The generated text
                'grounding_metadata': dict - Grounding metadata if Google Search is used
            }
        """
        response_text = ''
        grounding_metadata = None
        contents = types.Content(
            role='user',
            parts=[]
        )
        for prompt in prompt_list:
            contents.parts.append(types.Part.from_text(text=prompt))

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
            
            # Capture grounding metadata from the last chunk (it's cumulative)
            if hasattr(chunk.candidates[0], 'grounding_metadata') and chunk.candidates[0].grounding_metadata:
                grounding_metadata = chunk.candidates[0].grounding_metadata
        
        # Extract structured metadata if available
        metadata_dict = None
        if grounding_metadata:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[GROUNDING_DEBUG] Metadata object received: {type(grounding_metadata)}")
            
            metadata_dict = {
                'web_search_queries': [],
                'grounding_chunks': []
            }
            
            # Extract web search queries
            if hasattr(grounding_metadata, 'web_search_queries') and grounding_metadata.web_search_queries:
                metadata_dict['web_search_queries'] = list(grounding_metadata.web_search_queries)
                logger.info(f"[GROUNDING_DEBUG] Found {len(metadata_dict['web_search_queries'])} search queries")
            
            # Extract grounding chunks with URLs
            if hasattr(grounding_metadata, 'grounding_chunks') and grounding_metadata.grounding_chunks:
                logger.info(f"[GROUNDING_DEBUG] Found {len(grounding_metadata.grounding_chunks)} grounding chunks")
                for chunk in grounding_metadata.grounding_chunks:
                    chunk_data = {}
                    if hasattr(chunk, 'web') and chunk.web:
                        # Try to get direct URI first
                        if hasattr(chunk.web, 'uri') and chunk.web.uri:
                            chunk_data['uri'] = chunk.web.uri
                        if hasattr(chunk.web, 'title') and chunk.web.title:
                            chunk_data['title'] = chunk.web.title
                    
                    # Also check for retrieved_context which might have different URL format
                    elif hasattr(chunk, 'retrieved_context') and chunk.retrieved_context:
                        if hasattr(chunk.retrieved_context, 'uri') and chunk.retrieved_context.uri:
                            chunk_data['uri'] = chunk.retrieved_context.uri
                        if hasattr(chunk.retrieved_context, 'title') and chunk.retrieved_context.title:
                            chunk_data['title'] = chunk.retrieved_context.title
                    
                    # Log chunk structure for debugging
                    if not chunk_data and hasattr(chunk, '__dict__'):
                        logger.debug(f"[GROUNDING_DEBUG] Chunk structure: {chunk.__dict__}")
                    
                    if chunk_data:  # Only add if we have data
                        metadata_dict['grounding_chunks'].append(chunk_data)
                
                logger.info(f"[GROUNDING_DEBUG] Extracted {len(metadata_dict['grounding_chunks'])} URLs from chunks")
            else:
                logger.warning("[GROUNDING_DEBUG] NO grounding_chunks found in metadata!")
        
        return {
            'text': response_text,
            'grounding_metadata': metadata_dict
        }

    def _try_generate_image(self, model: str, prompt_list: list[str], image_attachment: str, config: types.GenerateContentConfig) -> bytes:
        """Try generating an image using the specified model."""
        image_bytes = None
        contents = types.Content(
            role='user',
            parts=[]
        )

        if image_attachment:
            contents.parts.append(types.Part.from_bytes(
                mime_type="image/png",
                data=base64.b64decode(
                    f"""{image_attachment}""",
                ))
            )

        for prompt in prompt_list:
            contents.parts.append(types.Part.from_text(text=prompt))

        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        ):
            if not self._check_for_content_parts(chunk):
                continue

            part = chunk.candidates[0].content.parts[0]

            if hasattr(part, 'inline_data') and part.inline_data and hasattr(part.inline_data, 'data') and part.inline_data.data:
                inline_data = part.inline_data
                image_bytes = inline_data.data
                break
            elif hasattr(part, 'text') and part.text:
                continue

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
