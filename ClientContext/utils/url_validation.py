"""
URL validation utilities.
Checks if URLs are valid and accessible (not 404, soft-404, etc.)
"""
import logging
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger(__name__)

# Timeout for URL validation (seconds)
VALIDATION_TIMEOUT = 5

# Soft-404 indicators in page content
SOFT_404_PATTERNS = [
    r'página não encontrada',
    r'page not found',
    r'404',
    r'não existe',
    r'does not exist',
    r'conteúdo indisponível',
    r'content unavailable',
]

# User agent for requests
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)


async def validate_url_permissive_async(url: str) -> bool:
    """
    Validate a URL by checking if it's accessible.

    Uses a permissive approach - only rejects clear errors (404, 5xx).
    Does not check for soft-404s to avoid false negatives.

    Args:
        url: URL to validate

    Returns:
        True if URL is likely valid, False if clearly invalid
    """
    try:
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        if parsed.scheme not in ('http', 'https'):
            return False

        # Try HEAD request first (faster)
        # Nota: ssl=False é usado para evitar falsos negativos em sites com
        # certificados auto-assinados ou expirados. O risco é aceitável pois
        # apenas validamos acessibilidade, não transmitimos dados sensíveis.
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(
                    url,
                    timeout=aiohttp.ClientTimeout(total=VALIDATION_TIMEOUT),
                    headers={'User-Agent': USER_AGENT},
                    allow_redirects=True,
                    ssl=False  # Risco aceito: apenas validação de acessibilidade
                ) as response:
                    # Accept 2xx and 3xx status codes
                    if response.status < 400:
                        return True

                    # Reject 4xx (except 403 which might be rate limiting)
                    if 400 <= response.status < 500 and response.status != 403:
                        logger.debug(f"URL validation failed ({response.status}): {url}")
                        return False

                    # For 5xx or 403, try GET as fallback
                    if response.status >= 500 or response.status == 403:
                        return await _validate_with_get(session, url)

                    return True

            except aiohttp.ClientError:
                # Network error, try GET
                return await _validate_with_get(session, url)

    except Exception as e:
        logger.debug(f"URL validation error for {url}: {str(e)}")
        # On error, assume URL is invalid
        return False


async def _validate_with_get(session: aiohttp.ClientSession, url: str) -> bool:
    """
    Fallback validation using GET request.

    Args:
        session: aiohttp session
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=VALIDATION_TIMEOUT),
            headers={'User-Agent': USER_AGENT},
            allow_redirects=True,
            ssl=False
        ) as response:
            if response.status < 400:
                return True
            if response.status == 403:
                # Rate limited, assume valid
                return True
            return False
    except Exception:
        # On error, assume URL is invalid
        return False


def validate_url_sync(url: str) -> bool:
    """
    Synchronous URL validation (basic checks only).

    Args:
        url: URL to validate

    Returns:
        True if URL format is valid
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False
