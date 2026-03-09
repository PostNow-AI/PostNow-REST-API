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

# Serper API endpoints
SERPER_SEARCH_URL = 'https://google.serper.dev/search'
SERPER_NEWS_URL = 'https://google.serper.dev/news'
SERPER_ACCOUNT_URL = 'https://google.serper.dev/account'


class SerperSearchService:
    """Service for performing Google searches via Serper API."""

    _last_request_time: float = 0.0

    def __init__(self):
        self.api_key = os.getenv('SERPER_API_KEY', '')

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        now = time.time()
        elapsed = now - SerperSearchService._last_request_time
        if elapsed < RATE_LIMIT_INTERVAL:
            time.sleep(RATE_LIMIT_INTERVAL - elapsed)
        SerperSearchService._last_request_time = time.time()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        return {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

    def _build_payload(
        self,
        query: str,
        num_results: int,
        date_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build request payload for Serper API."""
        payload = {
            'q': query,
            'gl': 'br',
            'hl': 'pt-br',
            'num': min(num_results, 100),
        }
        if date_filter:
            payload['tbs'] = f'qdr:{date_filter}'
        return payload

    def _handle_response_errors(self, response: requests.Response) -> bool:
        """Handle API response errors. Returns True if OK, False if error."""
        if response.status_code == 401:
            logger.error("Serper API authentication failed (invalid API key)")
            return False
        if response.status_code == 429:
            logger.error("Serper API rate limit exceeded")
            return False
        response.raise_for_status()
        return True

    def _parse_organic_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse organic search results from API response."""
        results = []
        for item in data.get('organic', []):
            results.append({
                'url': item.get('link', ''),
                'title': item.get('title', ''),
                'snippet': item.get('snippet', ''),
                'position': item.get('position', 0),
            })
        return results

    def _parse_news_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse news results from API response."""
        results = []
        for item in data.get('news', []):
            results.append({
                'url': item.get('link', ''),
                'title': item.get('title', ''),
                'snippet': item.get('snippet', ''),
                'source': item.get('source', ''),
                'date': item.get('date', ''),
            })
        return results

    def search(
        self,
        query: str,
        num_results: int = 5,
        search_type: str = 'search',
        date_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google search via Serper API.

        Args:
            query: Search query string
            num_results: Number of results to return (max 100)
            search_type: Type of search ('search', 'news')
            date_filter: Date filter ('d1'=day, 'w1'=week, 'm3'=3 months)

        Returns:
            List of search result dicts with 'url', 'title', 'snippet'
        """
        if not self.api_key:
            logger.warning("Serper API key not configured")
            return []

        self._rate_limit()

        try:
            payload = self._build_payload(query, num_results, date_filter)
            endpoint = SERPER_NEWS_URL if search_type == 'news' else SERPER_SEARCH_URL

            response = requests.post(
                endpoint, json=payload, headers=self._get_headers(), timeout=10
            )

            if not self._handle_response_errors(response):
                return []

            data = response.json()
            results = self._parse_organic_results(data)

            logger.info(f"Serper search for '{query[:30]}...' returned {len(results)} results")
            return results

        except requests.exceptions.Timeout:
            logger.error(f"Serper search timeout for '{query}'")
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper search failed for '{query}': {str(e)}")
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
            payload = self._build_payload(query, num_results)
            response = requests.post(
                SERPER_NEWS_URL, json=payload, headers=self._get_headers(), timeout=10
            )
            response.raise_for_status()

            return self._parse_news_results(response.json())

        except Exception as e:
            logger.error(f"Serper news search failed: {str(e)}")
            return []

    def is_configured(self) -> bool:
        """Check if Serper API is properly configured."""
        return bool(self.api_key)

    def get_credits_info(self) -> Optional[Dict[str, Any]]:
        """Get account credits information from Serper."""
        if not self.api_key:
            return None

        try:
            response = requests.get(
                SERPER_ACCOUNT_URL,
                headers={'X-API-KEY': self.api_key},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Serper credits info: {str(e)}")
            return None
