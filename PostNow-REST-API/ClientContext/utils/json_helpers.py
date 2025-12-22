"""
Módulo de utilitários para manipulação e parsing de JSON.

Este módulo centraliza funções auxiliares para trabalhar com strings JSON,
especialmente para lidar com respostas de IA que podem conter JSON mal formatado
ou envolto em markdown/texto adicional.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


def extract_json_block(text: str) -> str:
    """
    Extrai o primeiro bloco JSON válido de uma string usando contagem de chaves.
    Suporta objetos {} e listas [].
    
    Args:
        text: String que pode conter JSON envolto em outro texto
        
    Returns:
        String contendo o bloco JSON extraído, ou "{}" se nenhum for encontrado
        
    Examples:
        >>> extract_json_block('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'
        
        >>> extract_json_block('[1, 2, 3]')
        '[1, 2, 3]'
    """
    if not text:
        return "{}"
        
    text = text.strip()
    
    # Encontrar o primeiro caractere de início
    start_idx = -1
    stack = []
    
    for i, char in enumerate(text):
        if char == '{':
            if start_idx == -1:
                start_idx = i
            stack.append('{')
        elif char == '}':
            if stack and stack[-1] == '{':
                stack.pop()
                if not stack and start_idx != -1:
                    return text[start_idx:i+1]
        elif char == '[':
            if start_idx == -1:
                start_idx = i
            stack.append('[')
        elif char == ']':
            if stack and stack[-1] == '[':
                stack.pop()
                if not stack and start_idx != -1:
                    return text[start_idx:i+1]
                    
    # Fallback: Tentar regex simples se a lógica de pilha falhar (ex: json malformado)
    match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
    if match:
        return match.group(0)
        
    return "{}"


def clean_json_string(json_str: str) -> str:
    """
    Remove prefixos comuns de markdown (como 'json' após triple backticks)
    e espaços em branco desnecessários de uma string JSON.
    
    Args:
        json_str: String JSON potencialmente com prefixos markdown
        
    Returns:
        String JSON limpa
        
    Examples:
        >>> clean_json_string('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'
    """
    if not json_str:
        return "{}"
    
    # Remove 'json' prefix comum em respostas de IA
    cleaned = json_str.replace('json', '', 1).strip()
    
    # Remove backticks do markdown
    cleaned = cleaned.strip('`').strip()
    
    return cleaned


def safe_json_loads(json_str: str, default=None) -> dict:
    """
    Tenta fazer parse de uma string JSON de forma segura, com fallbacks.
    
    Args:
        json_str: String para fazer parse
        default: Valor padrão a retornar em caso de erro (default: {})
        
    Returns:
        Dict parseado ou valor default em caso de erro
        
    Examples:
        >>> safe_json_loads('{"key": "value"}')
        {'key': 'value'}
        
        >>> safe_json_loads('invalid json', default={'error': True})
        {'error': True}
    """
    if default is None:
        default = {}
    
    if not json_str:
        return default
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.debug(f"JSON parse error, trying extraction: {e}")
        
        # Tentar extrair bloco JSON
        try:
            extracted = extract_json_block(json_str)
            return json.loads(extracted)
        except json.JSONDecodeError as e2:
            logger.warning(f"Failed to parse JSON even after extraction: {e2}")
            return default

