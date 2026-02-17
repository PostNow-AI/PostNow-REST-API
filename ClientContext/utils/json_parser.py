"""Utilitarios para parsing de respostas AI."""

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def parse_ai_json_response(raw_response: str, key: str = 'contexto_pesquisado') -> Dict[str, Any]:
    """Remove markdown e extrai JSON da resposta AI.

    Args:
        raw_response: Resposta bruta da AI (pode conter markdown)
        key: Chave para extrair do JSON (default: 'contexto_pesquisado')

    Returns:
        Dicionario com os dados extraidos ou dicionario vazio se falhar
    """
    # Remove marcadores de codigo markdown de forma mais robusta
    cleaned = raw_response.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        return parsed.get(key, {})
    except json.JSONDecodeError as e:
        logger.warning(
            f"Failed to parse AI JSON response: {e}. "
            f"Raw response (first 200 chars): {raw_response[:200]}"
        )
        return {}


def extract_json_block(text: str) -> Optional[str]:
    """Extrai bloco JSON de texto usando contagem de chaves.

    Args:
        text: Texto contendo um bloco JSON

    Returns:
        String JSON extraida ou None se nao encontrar
    """
    # Remove markdown code blocks se presente
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text)

    # Encontra o inicio do JSON
    start_idx = text.find('{')
    if start_idx == -1:
        logger.debug("No JSON block found in text")
        return None

    brace_count = 0
    end_idx = start_idx

    for i, char in enumerate(text[start_idx:], start=start_idx):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break

    if brace_count != 0:
        logger.warning(
            f"Unbalanced braces in JSON block. "
            f"Text (first 200 chars): {text[:200]}"
        )
        return None

    return text[start_idx:end_idx + 1]


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Carrega JSON de forma segura, retornando default em caso de erro.

    Args:
        text: String JSON para parsear
        default: Valor a retornar em caso de erro (default: None)

    Returns:
        Objeto parseado ou default em caso de erro
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default
