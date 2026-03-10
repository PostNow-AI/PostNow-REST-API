"""
Utilitários de validação para endpoints de batch.

Extraídos de views.py seguindo padrões do CTO.
"""
import os
import secrets


# Token secreto para endpoints de batch (definido no GitHub Secrets como CRON_SECRET)
BATCH_API_TOKEN = os.getenv('CRON_SECRET', '')

# Rate limiting para geração de contexto individual
SINGLE_CONTEXT_RATE_LIMIT_SECONDS = 300  # 5 minutos

# Limites de validação
MAX_BATCH_NUMBER = 100
MIN_BATCH_NUMBER = 1


def validate_batch_token(request) -> bool:
    """
    Valida o token de autenticação para endpoints de batch.

    Args:
        request: Django request object

    Returns:
        bool: True se autenticado, False caso contrário
    """
    if not BATCH_API_TOKEN:
        # Se não há token configurado, permite (desenvolvimento)
        return True
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        # Usar compare_digest para evitar timing attacks
        return secrets.compare_digest(token, BATCH_API_TOKEN)
    return False


def validate_batch_number(batch_str: str) -> int:
    """
    Valida e retorna o número do batch.

    Args:
        batch_str: String com o número do batch

    Returns:
        int: Número do batch validado (entre MIN_BATCH_NUMBER e MAX_BATCH_NUMBER)
    """
    try:
        batch = int(batch_str)
        if batch < MIN_BATCH_NUMBER:
            return MIN_BATCH_NUMBER
        if batch > MAX_BATCH_NUMBER:
            return MAX_BATCH_NUMBER
        return batch
    except (ValueError, TypeError):
        return 1
