"""
Serper API Search Service.

Serper provides real Google search results via a commercial API.

Pricing:
- Free tier: 2,500 queries/month
- Starter: $50/50K queries ($1/1K)
- Business: $200/250K queries ($0.80/1K)

For our use case (enrichment):
- ~24 searches per user (6 categories x 4 opportunities)
- 2,500 free queries = ~104 users/month for free
- Much better quality than SearXNG (real Google results)
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)

# Rate limiting (Serper allows 300/sec, but we keep it conservative)
RATE_LIMIT_QUERIES_PER_SECOND = 10
RATE_LIMIT_INTERVAL = 1.0 / RATE_LIMIT_QUERIES_PER_SECOND


class SerperSearchService:
    """Service for performing Google searches via Serper API."""

    _last_request_time: float = 0.0

    def __init__(self):
        self.api_key = os.getenv('SERPER_API_KEY', '')
        self.base_url = 'https://google.serper.dev/search'

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        now = time.time()
        elapsed = now - SerperSearchService._last_request_time
        if elapsed < RATE_LIMIT_INTERVAL:
            sleep_time = RATE_LIMIT_INTERVAL - elapsed
            time.sleep(sleep_time)
        SerperSearchService._last_request_time = time.time()

    def search(
        self,
        query: str,
        num_results: int = 5,
        search_type: str = 'search'
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google search via Serper API.

        Args:
            query: Search query string
            num_results: Number of results to return (max 100)
            search_type: Type of search ('search', 'news', 'images')

        Returns:
            List of search result dicts with 'url', 'title', 'snippet'
        """
        if not self.api_key:
            logger.warning("Serper API key not configured")
            return []

        self._rate_limit()

        try:
            payload = {
                'q': query,
                'gl': 'br',  # Brazil geolocation
                'hl': 'pt-br',  # Portuguese language
                'num': min(num_results, 100),
            }

            # Add date filter for recent results (last 3 months)
            if search_type == 'search':
                payload['tbs'] = 'qdr:m3'

            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            endpoint = self.base_url
            if search_type == 'news':
                endpoint = 'https://google.serper.dev/news'

            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 401:
                logger.error("Serper API authentication failed (invalid API key)")
                return []

            if response.status_code == 429:
                logger.error("Serper API rate limit exceeded")
                return []

            response.raise_for_status()

            data = response.json()

            # Extract organic results
            results = []
            organic = data.get('organic', [])

            for item in organic:
                results.append({
                    'url': item.get('link', ''),
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'position': item.get('position', 0),
                })

            logger.info(
                f"Serper search for '{query[:30]}...' returned {len(results)} results"
            )
            return results

        except requests.exceptions.Timeout:
            logger.error(f"Serper search timeout for '{query}'")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper search failed for '{query}': {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Serper search: {str(e)}")
            return []

    def search_news(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search Google News via Serper API.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of news result dicts
        """
        if not self.api_key:
            return []

        self._rate_limit()

        try:
            payload = {
                'q': query,
                'gl': 'br',
                'hl': 'pt-br',
                'num': min(num_results, 100),
            }

            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            response = requests.post(
                'https://google.serper.dev/news',
                json=payload,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            results = []
            news = data.get('news', [])

            for item in news:
                results.append({
                    'url': item.get('link', ''),
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'source': item.get('source', ''),
                    'date': item.get('date', ''),
                })

            return results

        except Exception as e:
            logger.error(f"Serper news search failed: {str(e)}")
            return []

    def is_configured(self) -> bool:
        """Check if Serper API is properly configured."""
        return bool(self.api_key)

    def get_credits_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account credits information from Serper.

        Returns:
            Dict with 'credits' and 'used' or None if failed
        """
        if not self.api_key:
            return None

        try:
            response = requests.get(
                'https://google.serper.dev/account',
                headers={'X-API-KEY': self.api_key},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Serper credits info: {str(e)}")
            return None
