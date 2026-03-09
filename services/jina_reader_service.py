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
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)

# Rate limiting (conservative to avoid blocks)
RATE_LIMIT_REQUESTS_PER_SECOND = 2
RATE_LIMIT_INTERVAL = 1.0 / RATE_LIMIT_REQUESTS_PER_SECOND

# Request timeout
REQUEST_TIMEOUT = 30


class JinaReaderService:
    """Service for extracting clean content from URLs via Jina Reader."""

    _last_request_time: float = 0.0

    def __init__(self):
        self.api_key = os.getenv('JINA_API_KEY', '')  # Optional
        self.base_url = 'https://r.jina.ai/'

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        now = time.time()
        elapsed = now - JinaReaderService._last_request_time
        if elapsed < RATE_LIMIT_INTERVAL:
            sleep_time = RATE_LIMIT_INTERVAL - elapsed
            time.sleep(sleep_time)
        JinaReaderService._last_request_time = time.time()

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
            headers = {
                'Accept': f'text/{output_format}' if output_format != 'html' else 'text/html',
            }

            # Add API key if available (for higher rate limits)
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            # Add options via headers
            if not include_links:
                headers['X-No-Links'] = 'true'

            response = requests.get(
                f'{self.base_url}{url}',
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 404:
                logger.debug(f"Jina Reader: page not found for {url}")
                return None

            if response.status_code == 429:
                logger.warning("Jina Reader rate limit exceeded")
                return None

            if response.status_code == 503:
                logger.warning(f"Jina Reader: service unavailable for {url}")
                return None

            response.raise_for_status()

            content = response.text

            # Basic validation - content should have reasonable length
            if len(content) < 100:
                logger.debug(f"Jina Reader: content too short for {url}")
                return None

            logger.debug(f"Jina Reader: extracted {len(content)} chars from {url}")
            return content

        except requests.exceptions.Timeout:
            logger.warning(f"Jina Reader timeout for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Jina Reader failed for {url}: {str(e)}")
            return None
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
            headers = {
                'Accept': 'application/json',
            }

            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.get(
                f'{self.base_url}{url}',
                headers=headers,
                timeout=REQUEST_TIMEOUT
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
            logger.warning(f"Jina Reader metadata extraction failed for {url}: {str(e)}")
            return None

    def is_configured(self) -> bool:
        """
        Check if service is available.
        Jina Reader works without API key, so always returns True.
        """
        return True

    def batch_read_urls(
        self,
        urls: list[str],
        max_concurrent: int = 3
    ) -> Dict[str, Optional[str]]:
        """
        Read multiple URLs sequentially with rate limiting.

        Args:
            urls: List of URLs to read
            max_concurrent: Not used (sequential for simplicity)

        Returns:
            Dict mapping URL to content (or None if failed)
        """
        results = {}

        for url in urls:
            content = self.read_url(url)
            results[url] = content

        return results
