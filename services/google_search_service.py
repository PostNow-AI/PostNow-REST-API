import logging
import os
import requests

logger = logging.getLogger(__name__)


class GoogleSearchService:
    """Busca via Serper.dev API (substitui Google Custom Search)."""

    def __init__(self):
        self.api_key = os.getenv('SERPER_API_KEY')
        self.base_url = "https://google.serper.dev/search"

    def search(self, query: str, num_results: int = 3, **kwargs) -> list:
        if not self.api_key:
            logger.error("SERPER_API_KEY não configurada.")
            return []

        payload = {
            'q': query,
            'num': min(num_results, 10),
            'gl': kwargs.get('gl', os.getenv('SERPER_GL', 'br')),
        }

        tbs = kwargs.get('dateRestrict')
        if tbs:
            payload['tbs'] = f"qdr:{tbs}"

        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                self.base_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get('organic', [])[:num_results]:
                results.append({
                    'title': item.get('title'),
                    'url': item.get('link'),
                    'snippet': item.get('snippet'),
                    'source': item.get('domain', ''),
                })

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na Serper API: {str(e)}")
            return []
