"""
Jina Reader Service for extracting clean content from web pages.

Jina Reader converts any URL to clean, LLM-friendly markdown.

Pricing:
- Free tier: 1M tokens/month (very generous)
- No API key required for basic usage
- With API key: higher rate limits

For our use case:
- Average page: ~2000 tokens
- 1M tokens = ~500 pages/month for free
- More than enough for enrichment
"""
import os
import time
import logging
from typing import Optional, Dict, Any, List

import requests

logger = logging.getLogger(__name__)

# Rate limiting (conservative to avoid blocks)
RATE_LIMIT_REQUESTS_PER_SECOND = 2
RATE_LIMIT_INTERVAL = 1.0 / RATE_LIMIT_REQUESTS_PER_SECOND

# Request timeout
REQUEST_TIMEOUT = 30

# Jina Reader base URL
JINA_READER_URL = 'https://r.jina.ai/'


class JinaReaderService:
    """Service for extracting clean content from URLs via Jina Reader."""

    _last_request_time: float = 0.0

    def __init__(self):
        self.api_key = os.getenv('JINA_API_KEY', '')

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        now = time.time()
        elapsed = now - JinaReaderService._last_request_time
        if elapsed < RATE_LIMIT_INTERVAL:
            time.sleep(RATE_LIMIT_INTERVAL - elapsed)
        JinaReaderService._last_request_time = time.time()

    def _get_headers(
        self,
        output_format: str = 'markdown',
        include_links: bool = False
    ) -> Dict[str, str]:
        """Build request headers."""
        accept_type = 'text/html' if output_format == 'html' else f'text/{output_format}'
        headers = {'Accept': accept_type}

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        if not include_links:
            headers['X-No-Links'] = 'true'

        return headers

    def _check_response_status(self, response: requests.Response, url: str) -> bool:
        """Check response status. Returns True if OK, False if should skip."""
        if response.status_code == 404:
            logger.debug(f"Jina Reader: page not found for {url}")
            return False
        if response.status_code == 429:
            logger.warning("Jina Reader rate limit exceeded")
            return False
        if response.status_code == 503:
            logger.warning(f"Jina Reader: service unavailable for {url}")
            return False
        response.raise_for_status()
        return True

    def read_url(
        self,
        url: str,
        output_format: str = 'markdown',
        include_links: bool = False
    ) -> Optional[str]:
        """
        Read and extract clean content from a URL.

        Args:
            url: URL to read
            output_format: Output format ('markdown', 'text', 'html')
            include_links: Whether to include links in output

        Returns:
            Clean content string or None if failed
        """
        self._rate_limit()

        try:
            headers = self._get_headers(output_format, include_links)
            response = requests.get(
                f'{JINA_READER_URL}{url}', headers=headers, timeout=REQUEST_TIMEOUT
            )

            if not self._check_response_status(response, url):
                return None

            content = response.text
            if len(content) < 100:
                logger.debug(f"Jina Reader: content too short for {url}")
                return None

            logger.debug(f"Jina Reader: extracted {len(content)} chars from {url}")
            return content

        except requests.exceptions.Timeout:
            logger.warning(f"Jina Reader timeout for {url}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Jina Reader failed for {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Jina Reader: {str(e)}")
        return None

    def read_url_with_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Read URL and return content with metadata.

        Args:
            url: URL to read

        Returns:
            Dict with 'content', 'title', 'description' or None if failed
        """
        self._rate_limit()

        try:
            headers = {'Accept': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.get(
                f'{JINA_READER_URL}{url}', headers=headers, timeout=REQUEST_TIMEOUT
            )

            if response.status_code != 200:
                return None

            data = response.json()
            return {
                'content': data.get('content', ''),
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'url': data.get('url', url),
            }

        except Exception as e:
            logger.warning(f"Jina Reader metadata failed for {url}: {str(e)}")
            return None

    def is_configured(self) -> bool:
        """Jina Reader works without API key, so always available."""
        return True

    def batch_read_urls(self, urls: List[str]) -> Dict[str, Optional[str]]:
        """
        Read multiple URLs sequentially with rate limiting.

        Args:
            urls: List of URLs to read

        Returns:
            Dict mapping URL to content (or None if failed)
        """
        return {url: self.read_url(url) for url in urls}
