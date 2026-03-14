"""Servico de descoberta de tendencias por setor."""

import logging
import os
from typing import Dict, Any

import requests

logger = logging.getLogger(__name__)


class TrendsDiscoveryService:
    """Descobre tendencias reais para um setor usando busca web."""

    def __init__(self):
        self.api_key = os.getenv('SERPER_API_KEY')
        self.base_url = "https://google.serper.dev/search"

    def discover_trends_for_sector(
        self,
        sector: str,
        business_description: str = '',
        location: str = 'Brasil',
    ) -> Dict[str, Any]:
        """Busca tendencias reais para o setor do usuario.

        Returns:
            Dict com general_trends, sector_trends, rising_topics e validated_count.
        """
        if not self.api_key:
            logger.warning("SERPER_API_KEY nao configurada, pulando trend discovery")
            return self._empty_result('serper_not_configured')

        queries = [
            f"tendencias {sector} 2026",
            f"{sector} novidades mercado {location}",
        ]

        all_trends = []
        for query in queries:
            try:
                results = self._search(query)
                for item in results:
                    all_trends.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': item.get('domain', ''),
                        'query': query,
                    })
            except Exception as e:
                logger.error(f"Erro buscando tendencias para '{query}': {e}")

        sector_trends = all_trends[:5]
        general_trends = all_trends[5:10]

        return {
            'general_trends': general_trends,
            'sector_trends': sector_trends,
            'rising_topics': [],
            'validated_count': len(all_trends),
            'discovery_metadata': {
                'sector': sector,
                'location': location,
                'queries_used': len(queries),
            },
        }

    def _search(self, query: str, num_results: int = 5) -> list:
        """Executa busca via Serper."""
        payload = {
            'q': query,
            'num': num_results,
            'gl': 'br',
        }
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json',
        }
        response = requests.post(
            self.base_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get('organic', [])

    def _empty_result(self, error: str = '') -> Dict[str, Any]:
        return {
            'general_trends': [],
            'sector_trends': [],
            'rising_topics': [],
            'validated_count': 0,
            'discovery_metadata': {'error': error},
        }
