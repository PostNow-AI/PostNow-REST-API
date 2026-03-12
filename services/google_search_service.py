import logging
import os
import time
from typing import List, Dict, Any

import requests

logger = logging.getLogger(__name__)

# Rate limiting settings
RATE_LIMIT_QUERIES_PER_SECOND = 5  # Stay under Google's 10/sec limit
RATE_LIMIT_INTERVAL = 1.0 / RATE_LIMIT_QUERIES_PER_SECOND


class GoogleSearchService:
    """Service for performing Google Custom Search queries.

    Limits and Costs:
    - Free tier: 100 queries/day
    - Paid: $5 per 1000 queries (after free tier)
    - Rate limit: 10 queries/second (Google's limit)
    """

    _last_request_time: float = 0.0

    def __init__(self):
        # Suporta múltiplos nomes de env var (legado / novo).
        self.api_key = (
            os.getenv('GOOGLE_CSE_API_KEY')
            or os.getenv('GOOGLE_SEARCH_API_KEY')
            or os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
            or ''
        )
        self.cse_id = (
            os.getenv('GOOGLE_CSE_ID')
            or os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
            or ''
        )
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        now = time.time()
        elapsed = now - GoogleSearchService._last_request_time
        if elapsed < RATE_LIMIT_INTERVAL:
            sleep_time = RATE_LIMIT_INTERVAL - elapsed
            time.sleep(sleep_time)
        GoogleSearchService._last_request_time = time.time()

    def search(self, query: str, num_results: int = 3, **kwargs) -> list:
        """
        Executa uma busca no Google Custom Search API.

        Args:
            query (str): Termo de busca.
            num_results (int): Número de resultados desejados.
            **kwargs: Outros parâmetros da API (ex: dateRestrict, lr, gl, start).

        Returns:
            list: Lista de dicionários com 'title', 'url', 'snippet', 'source'.
        """
        if not self.api_key or not self.cse_id:
            logger.warning("Google CSE credentials not configured")
            return []

        # Apply rate limiting
        self._rate_limit()

        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': min(num_results, 10),  # API limita a 10 por request
            **kwargs
        }

        # Defaults de qualidade (configuráveis por env). Podem ser sobrescritos via kwargs.
        default_date_restrict = os.getenv("GOOGLE_CSE_DATE_RESTRICT", "w2")
        default_gl = os.getenv("GOOGLE_CSE_GL", "br")
        default_lr = os.getenv("GOOGLE_CSE_LR", "")  # ex: lang_pt ou lang_en

        if 'dateRestrict' not in params and default_date_restrict:
            params['dateRestrict'] = default_date_restrict
        if 'gl' not in params and default_gl:
            params['gl'] = default_gl
        if 'lr' not in params and default_lr:
            params['lr'] = default_lr

        try:
            response = requests.get(self.base_url, params=params, timeout=10)

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
                    'title': item.get('title'),
                    'url': item.get('link'),
                    'snippet': item.get('snippet'),
                    'source': item.get('displayLink')
                })

            logger.info(f"Google search for '{query[:30]}...' returned {len(results)} results")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na Google Search API: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Google search: {str(e)}")
            return []

    def is_configured(self) -> bool:
        """Check if Google CSE is properly configured."""
        return bool(self.api_key and self.cse_id)
