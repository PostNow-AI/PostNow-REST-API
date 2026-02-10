"""
URL validation and recovery utilities for Weekly Context service.
"""
import requests
from typing import Any, List

from asgiref.sync import sync_to_async


def coerce_url_to_str(value: Any) -> str:
    """
    Normalize values from AI to URL string.
    AI occasionally returns objects/structures (dict/list) instead of string.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    # Common hallucination cases: {"url": "..."} / {"uri": "..."} / {"link": "..."}
    if isinstance(value, dict):
        for key in ("url", "uri", "link", "href", "original", "value"):
            v = value.get(key)
            if isinstance(v, str) and v.strip():
                return v
        return ""
    if isinstance(value, list):
        # Get first useful item
        for item in value:
            s = coerce_url_to_str(item)
            if s:
                return s
        return ""
    # Fallback: string representation (avoid crash)
    try:
        return str(value)
    except Exception:
        return ""


def recover_url(generated_url: Any, real_urls: List[str]) -> str:
    """
    Try to recover a hallucinated URL by finding the best match
    among the real URLs provided by Google Search.
    """
    generated_url = coerce_url_to_str(generated_url)
    if not generated_url:
        return ""

    generated_url = generated_url.strip().lower()
    # Normalize the list of real URLs (GoogleSearchService returns list of dicts)
    real_urls_norm = []
    for real in (real_urls or []):
        real_s = coerce_url_to_str(real)
        if real_s:
            real_urls_norm.append(real_s)

    # 1. Exact match (case insensitive)
    for real in real_urls_norm:
        if real.strip().lower() == generated_url:
            return real

    # 2. Partial match (Domain and Path)
    # If AI invented parameters but got the main path right
    # Ex: real: forbes.com/article | generated: forbes.com/article?utm=...
    for real in real_urls_norm:
        real_clean = real.split('?')[0].lower()
        gen_clean = generated_url.split('?')[0]
        if real_clean in gen_clean or gen_clean in real_clean:
            return real

    # 3. Safe Fallback: Return the AI's original URL
    # and let HTTP validation decide (if 404, it will be filtered out)
    return generated_url


def _is_soft_404(url_final: str, body_text: str) -> bool:
    """Check if a page is a soft 404 (returns 200 but shows 404 content)."""
    if not body_text:
        return False
    low = body_text.lower()

    # LinkedIn Pulse: often redirects to "article_not_found" with status 200
    if "linkedin.com" in (url_final or ""):
        if "trk=article_not_found" in (url_final or ""):
            return True
        if ("we can't find the page you're looking for" in low) or ("we can\u2019t find the page you\u2019re looking for" in low):
            return True

    # Generic soft-404 (try to avoid false positives)
    if "página não encontrada" in low or "pagina nao encontrada" in low:
        return True
    if "page not found" in low:
        return True

    return False


def validate_url_sync(url: str) -> bool:
    """
    Validate URL permissively.
    Returns True for anything that is NOT a confirmed 404.
    Timeouts and Connection Errors are considered valid URLs (presumption of innocence).
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Short timeout of 3s
        response = requests.head(url, headers=headers, timeout=3, allow_redirects=True)
        if response.status_code == 404:
            return False

        # Some sites return 200/302 on HEAD but are soft-404 on GET (e.g., LinkedIn)
        try:
            get_resp = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
            if get_resp.status_code == 404:
                return False
            if _is_soft_404(get_resp.url, get_resp.text or ""):
                return False
        except requests.exceptions.RequestException:
            # If GET fails (timeout/blocking), keep the presumption of innocence
            return True

        return True
    except requests.exceptions.RequestException:
        # If timeout or connection error, assume the link exists but the site is slow
        return True
    except Exception:
        # Any other error, assume valid
        return True


async def validate_url_permissive_async(url: str) -> bool:
    """Async wrapper for URL validation."""
    return await sync_to_async(validate_url_sync)(url)
