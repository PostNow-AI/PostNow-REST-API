"""
URL deduplication utilities.
Used to prevent duplicate sources in enrichment results.
"""
import re
from urllib.parse import urlparse, parse_qs, urlencode


def normalize_url_key(url: str) -> str:
    """
    Normalize a URL to a consistent key for deduplication.

    Removes:
    - Protocol (http/https)
    - www. prefix
    - Trailing slashes
    - Common tracking parameters (utm_*, ref, etc.)
    - Fragment identifiers (#)

    Args:
        url: URL to normalize

    Returns:
        Normalized URL key, or empty string if invalid
    """
    try:
        if not url:
            return ''

        parsed = urlparse(url.lower().strip())

        # Get domain without www.
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]

        # Get path without trailing slash
        path = parsed.path.rstrip('/')
        if not path:
            path = '/'

        # Filter out tracking parameters
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'ref', 'source', 'fbclid', 'gclid', 'mc_cid', 'mc_eid',
            '_ga', '_gl', 'affiliate', 'partner'
        }

        query_params = parse_qs(parsed.query, keep_blank_values=False)
        filtered_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in tracking_params
        }

        # Rebuild query string
        if filtered_params:
            # Sort for consistency
            query = urlencode(filtered_params, doseq=True)
            return f"{domain}{path}?{query}"

        return f"{domain}{path}"

    except Exception:
        return ''


def urls_are_same(url1: str, url2: str) -> bool:
    """
    Check if two URLs point to the same content.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        True if URLs are effectively the same
    """
    key1 = normalize_url_key(url1)
    key2 = normalize_url_key(url2)

    if not key1 or not key2:
        return False

    return key1 == key2
