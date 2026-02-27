"""
Source quality scoring and filtering.
Used by search_utils.py to filter and rank search results.
"""
import re
from urllib.parse import urlparse

# Denied domains (low quality, paywalls, etc.)
DENIED_DOMAINS = {
    'pinterest.com',
    'pinterest.com.br',
    'facebook.com',
    'instagram.com',
    'twitter.com',
    'x.com',
    'tiktok.com',
    'linkedin.com',
    'reddit.com',
    'quora.com',
    'medium.com',  # Often paywalled
    'scribd.com',  # Paywalled
    'slideshare.net',
}

# Allowed high-quality domains by section
ALLOWED_DOMAINS = {
    'mercado': {
        'exame.com': 90,
        'infomoney.com.br': 90,
        'valor.globo.com': 95,
        'forbes.com.br': 90,
        'estadao.com.br': 85,
        'folha.uol.com.br': 85,
        'g1.globo.com': 80,
        'uol.com.br': 75,
        'terra.com.br': 70,
    },
    'tendencias': {
        'tecmundo.com.br': 85,
        'techtudo.com.br': 85,
        'canaltech.com.br': 85,
        'olhardigital.com.br': 80,
        'tecnoblog.net': 85,
        'meioemensagem.com.br': 90,
        'propmark.com.br': 85,
    },
    'concorrencia': {
        'socialblade.com': 80,
        'similarweb.com': 85,
        'semrush.com': 85,
        'ahrefs.com': 85,
    },
}

# Default score for unknown domains
DEFAULT_SCORE = 50


def is_denied(url: str) -> bool:
    """
    Check if a URL is from a denied domain.

    Args:
        url: URL to check

    Returns:
        True if denied, False otherwise
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Check exact match
        if domain in DENIED_DOMAINS:
            return True

        # Check if subdomain of denied domain
        for denied in DENIED_DOMAINS:
            if domain.endswith('.' + denied):
                return True

        return False
    except Exception:
        return False


def score_source(section: str, url: str) -> int:
    """
    Score a source URL based on domain quality for a given section.

    Args:
        section: Section name ('mercado', 'tendencias', 'concorrencia')
        url: URL to score

    Returns:
        Score from 0-100
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Check section-specific allowed domains
        section_domains = ALLOWED_DOMAINS.get(section, {})
        if domain in section_domains:
            return section_domains[domain]

        # Check all sections for the domain
        for sect, domains in ALLOWED_DOMAINS.items():
            if domain in domains:
                # Slightly lower score if not the primary section
                return max(0, domains[domain] - 10)

        # Check for known TLDs
        if domain.endswith('.gov.br'):
            return 85
        if domain.endswith('.edu.br'):
            return 80
        if domain.endswith('.org.br'):
            return 70

        return DEFAULT_SCORE
    except Exception:
        return DEFAULT_SCORE
