import logging
import os
import requests

logger = logging.getLogger(__name__)

class GoogleSearchService:
    def __init__(self):
        # Suporta múltiplos nomes de env var (legado / novo).
        # No projeto, o .env usa GOOGLE_CUSTOM_SEARCH_API_KEY e GOOGLE_CUSTOM_SEARCH_ENGINE_ID.
        self.api_key = (
            os.getenv('GOOGLE_SEARCH_API_KEY')
            or os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
        )
        self.cse_id = (
            os.getenv('GOOGLE_CSE_ID')
            or os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
        )
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, num_results: int = 3, **kwargs) -> list:
        """
        Executa uma busca no Google Custom Search API.
        
        Args:
            query (str): Termo de busca.
            num_results (int): Número de resultados desejados.
            **kwargs: Outros parâmetros da API (ex: dateRestrict, lr, gl).
            
        Returns:
            list: Lista de dicionários com 'title', 'link', 'snippet'.
        """
        if not self.api_key or not self.cse_id:
            logger.error("Google Search API Key ou CSE ID não configurados.")
            return []

        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': min(num_results, 10), # API limita a 10 por request
            **kwargs
        }
        
        # Defaults de qualidade (configuráveis por env). Podem ser sobrescritos via kwargs.
        # dateRestrict: w2 (2 semanas) ou m1 (1 mês) são valores comuns.
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
                
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na Google Search API: {str(e)}")
            return []

