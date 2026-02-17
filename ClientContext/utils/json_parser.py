"""Utilitarios para parsing de respostas AI."""

import json
import re
from typing import Any, Dict, Optional


def parse_ai_json_response(raw_response: str, key: str = 'contexto_pesquisado') -> Dict[str, Any]:
    """Remove markdown e extrai JSON da resposta AI.

    Args:
        raw_response: Resposta bruta da AI (pode conter markdown)
        key: Chave para extrair do JSON (default: 'contexto_pesquisado')

    Returns:
        Dicionario com os dados extraidos ou dicionario vazio se falhar
    """
    cleaned = raw_response.replace('json', '', 1).strip('`').strip()
    try:
        parsed = json.loads(cleaned)
        return parsed.get(key, {})
    except json.JSONDecodeError:
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
        return None

    return text[start_idx:end_idx + 1]
