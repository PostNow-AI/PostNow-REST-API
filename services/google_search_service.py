"""
Google Custom Search API Service.

Limits and Costs:
- Free tier: 100 queries/day
- Paid: $5 per 1000 queries (after free tier)
- Rate limit: 10 queries/second (Google's limit)

For our use case (enrichment):
- ~6 searches per user (one per category)
- With 100 free queries, we can enrich ~16 users/day for free
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)

# Rate limiting settings
RATE_LIMIT_QUERIES_PER_SECOND = 5  # Stay under Google's 10/sec limit
RATE_LIMIT_INTERVAL = 1.0 / RATE_LIMIT_QUERIES_PER_SECOND


class GoogleSearchService:
    """Service for performing Google Custom Search queries."""

    _last_request_time: float = 0.0

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_CSE_API_KEY', os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY', ''))
        self.search_engine_id = os.getenv('GOOGLE_CSE_ID', os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID', ''))
        self.base_url = 'https://www.googleapis.com/customsearch/v1'

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        now = time.time()
        elapsed = now - GoogleSearchService._last_request_time
        if elapsed < RATE_LIMIT_INTERVAL:
            sleep_time = RATE_LIMIT_INTERVAL - elapsed
            time.sleep(sleep_time)
        GoogleSearchService._last_request_time = time.time()

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a Google Custom Search.

        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per request)

        Returns:
            List of search result dicts with 'url', 'title', 'snippet'
        """
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google CSE credentials not configured")
            return []

        # Apply rate limiting
        self._rate_limit()

        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(num_results, 10),  # Google CSE max is 10
                'lr': 'lang_pt',  # Portuguese language
                'gl': 'br',  # Brazil geolocation
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )

            # Handle quota exceeded
            if response.status_code == 429:
                logger.error("Google CSE quota exceeded (429 Too Many Requests)")
                return []

            # Handle quota limit (403 with specific error)
            if response.status_code == 403:
                error_data = response.json().get('error', {})
                if 'quotaExceeded' in str(error_data):
                    logger.error("Google CSE daily quota exceeded")
                    return []

            response.raise_for_status()

            data = response.json()
            items = data.get('items', [])

            results = []
            for item in items:
                results.append({
                    'url': item.get('link', ''),
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                })

            logger.info(f"Google search for '{query[:30]}...' returned {len(results)} results")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Google search failed for '{query}': {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Google search: {str(e)}")
            return []

    def is_configured(self) -> bool:
        """Check if Google CSE is properly configured."""
        return bool(self.api_key and self.search_engine_id)
