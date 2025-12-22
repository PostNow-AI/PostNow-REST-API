"""
Módulo de utilitários para validação e manipulação de URLs.

Este módulo centraliza funções auxiliares para validar, normalizar e processar URLs,
especialmente para lidar com respostas de IA que podem retornar URLs em formatos inesperados.
"""

import logging
import re
import requests
from typing import Any, List
from urllib.parse import urlparse

from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


def is_blocked_filetype(url: str) -> bool:
    """
    Verifica se a URL aponta para um tipo de arquivo que deve ser bloqueado.
    
    Args:
        url: URL a ser verificada
        
    Returns:
        True se o arquivo deve ser bloqueado, False caso contrário
        
    Examples:
        >>> is_blocked_filetype('https://example.com/document.pdf')
        True
        
        >>> is_blocked_filetype('https://example.com/article')
        False
    """
    if not url:
        return False
        
    u = url.lower()
    blocked_extensions = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx")
    return u.endswith(blocked_extensions)


def coerce_url_to_str(value: Any) -> str:
    """
    Normaliza valores vindos da IA para uma URL em string.
    A IA ocasionalmente retorna objetos/estruturas (dict/list) em vez de string.
    
    Args:
        value: Valor que pode ser uma URL em vários formatos
        
    Returns:
        String com a URL normalizada, ou string vazia se não puder ser normalizada
        
    Examples:
        >>> coerce_url_to_str("https://example.com")
        'https://example.com'
        
        >>> coerce_url_to_str({"url": "https://example.com"})
        'https://example.com'
        
        >>> coerce_url_to_str(["https://example.com", "other"])
        'https://example.com'
    """
    if value is None:
        return ""
        
    if isinstance(value, str):
        return value
        
    # Casos comuns de alucinação: {"url": "..."} / {"uri": "..."} / {"link": "..."}
    if isinstance(value, dict):
        for key in ("url", "uri", "link", "href", "original", "value"):
            v = value.get(key)
            if isinstance(v, str) and v.strip():
                return v
        return ""
        
    if isinstance(value, list):
        # Pega o primeiro item útil
        for item in value:
            s = coerce_url_to_str(item)
            if s:
                return s
        return ""
        
    # Fallback: representação em string (evitar crash)
    try:
        return str(value)
    except Exception:
        return ""


def recover_url(generated_url: Any, real_urls: List[str]) -> str:
    """
    Tenta recuperar uma URL alucinada encontrando a melhor correspondência
    entre as URLs reais fornecidas pelo Google Search.
    
    Args:
        generated_url: URL gerada pela IA (pode estar em formato inesperado)
        real_urls: Lista de URLs reais do Google Search
        
    Returns:
        URL recuperada ou a URL original se nenhuma correspondência for encontrada
        
    Examples:
        >>> real_urls = ['https://forbes.com/article']
        >>> recover_url('https://forbes.com/article?utm=fake', real_urls)
        'https://forbes.com/article'
    """
    generated_url = coerce_url_to_str(generated_url)
    if not generated_url:
        return ""
        
    generated_url = generated_url.strip().lower()
    
    # Normalizar a lista de URLs reais
    real_urls_norm = []
    for real in (real_urls or []):
        real_s = coerce_url_to_str(real)
        if real_s:
            real_urls_norm.append(real_s)
    
    # 1. Correspondência Exata (case insensitive)
    for real in real_urls_norm:
        if real.strip().lower() == generated_url:
            return real
            
    # 2. Correspondência Parcial (Domínio e Path)
    # Se a IA inventou parâmetros mas acertou o path principal
    for real in real_urls_norm:
        real_clean = real.split('?')[0].lower()
        gen_clean = generated_url.split('?')[0]
        if real_clean in gen_clean or gen_clean in real_clean:
            return real
            
    # 3. Retorna a URL original da IA e deixa a validação HTTP decidir
    return generated_url


async def validate_url_permissive_async(url: str) -> bool:
    """
    Valida uma URL de forma permissiva, verificando se ela está acessível.
    Usa HEAD/GET requests para detectar 404s e soft-404s.
    
    Args:
        url: URL a ser validada
        
    Returns:
        True se a URL parece válida, False se for 404 ou soft-404
        
    Note:
        Esta função é permissiva em casos de timeout ou erro de conexão,
        assumindo que o site existe mas pode estar lento/bloqueando requests.
    """
    if not url or not url.strip():
        return False
        
    def _is_soft_404(url_final: str, body_text: str) -> bool:
        """Detecta soft-404s (páginas que retornam 200 mas são 404)."""
        if not body_text:
            return False
            
        low = body_text.lower()

        # LinkedIn Pulse: frequentemente redireciona para "article_not_found" com status 200
        if "linkedin.com" in (url_final or ""):
            if "trk=article_not_found" in (url_final or ""):
                return True
            if ("we can't find the page you're looking for" in low) or \
               ("we can\u2019t find the page you\u2019re looking for" in low):
                return True

        # Soft-404 genérico (tenta evitar falsos positivos)
        if "página não encontrada" in low or "pagina nao encontrada" in low:
            return True
        if "page not found" in low:
            return True

        return False

    def _check():
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Timeout curto de 3s para HEAD
            response = requests.head(url, headers=headers, timeout=3, allow_redirects=True)
            if response.status_code == 404:
                return False

            # Alguns sites retornam 200/302 no HEAD mas são soft-404 no GET
            try:
                get_resp = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
                if get_resp.status_code == 404:
                    return False
                if _is_soft_404(get_resp.url, get_resp.text or ""):
                    return False
            except requests.exceptions.RequestException:
                # Se GET falhar (timeout/bloqueio), mantém presunção de validade
                return True

            return True
            
        except requests.exceptions.RequestException:
            # Se der timeout ou erro de conexão, assume que o link existe
            return True
        except Exception:
            # Qualquer outro erro, assume válido
            return True
    
    return await sync_to_async(_check)()


def sanitize_query_for_allowlist(query: str) -> str:
    """
    Remove operadores de site do query original (que pode conter site:-site:),
    para não conflitar com a injeção de allowlist.
    
    Args:
        query: Query de busca que pode conter operadores site:
        
    Returns:
        Query sanitizada sem operadores site: e limitada a 220 caracteres
        
    Examples:
        >>> sanitize_query_for_allowlist('python -site:spam.com')
        'python'
    """
    if not query:
        return ""
        
    q = re.sub(r"(?i)(-?site:[^\s]+)", " ", query)
    q = re.sub(r"\s+", " ", q).strip()
    
    # Evitar queries muito longas (CSE é sensível a tamanho)
    return q[:220]

