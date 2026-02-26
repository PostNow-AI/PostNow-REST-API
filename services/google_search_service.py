"""
Google Custom Search API Service.
"""
import os
import logging
from typing import List, Dict, Any

import requests

logger = logging.getLogger(__name__)


class GoogleSearchService:
    """Service for performing Google Custom Search queries."""

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_CSE_API_KEY', '')
        self.search_engine_id = os.getenv('GOOGLE_CSE_ID', '')
        self.base_url = 'https://www.googleapis.com/customsearch/v1'

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
