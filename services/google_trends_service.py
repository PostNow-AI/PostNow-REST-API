"""
Google Trends Service.

Integração com Google Trends via pytrends para descoberta de tendências reais.

Rate Limiting:
- Google Trends tem rate limiting agressivo
- Recomendado: 60 segundos entre requests após atingir limite
- Para processamento batch (domingo): OK, temos tempo

Uso:
- Não requer API key (pytrends usa scraping simulado)
- Dados de tendências REAIS e verificáveis
- Sem custo adicional
"""
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError

logger = logging.getLogger(__name__)

# Rate limiting settings
RATE_LIMIT_SECONDS = 2  # Intervalo mínimo entre requests
RETRY_DELAY_SECONDS = 60  # Delay após 429 (Too Many Requests)
MAX_RETRIES = 3


class GoogleTrendsService:
    """
    Serviço para buscar tendências do Google Trends.

    Usa pytrends para acessar dados de trending searches,
    tópicos relacionados e interesse ao longo do tempo.
    """

    _last_request_time: float = 0.0

    def __init__(self, language: str = 'pt-BR', timezone_offset: int = 180):
        """
        Inicializa o serviço de Google Trends.

        Args:
            language: Código do idioma (default: pt-BR para português brasileiro)
            timezone_offset: Offset do timezone em minutos (default: 180 para Brasil)
        """
        self.language = language
        self.timezone_offset = timezone_offset
        self._pytrends: Optional[TrendReq] = None

    @property
    def pytrends(self) -> TrendReq:
        """Lazy initialization do cliente pytrends."""
        if self._pytrends is None:
            # Nota: Não usar retries/backoff_factor pois causam incompatibilidade
            # com versões mais recentes do urllib3 (method_whitelist deprecated)
            self._pytrends = TrendReq(
                hl=self.language,
                tz=self.timezone_offset,
                timeout=(10, 25),  # (connect, read) timeout
            )
        return self._pytrends

    def _rate_limit(self) -> None:
        """Aplica rate limiting entre requests."""
        now = time.time()
        elapsed = now - GoogleTrendsService._last_request_time
        if elapsed < RATE_LIMIT_SECONDS:
            sleep_time = RATE_LIMIT_SECONDS - elapsed
            time.sleep(sleep_time)
        GoogleTrendsService._last_request_time = time.time()

    def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executa uma função com retry em caso de rate limiting.

        Args:
            func: Função a executar
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            Resultado da função

        Raises:
            Exception: Após MAX_RETRIES tentativas falhas
        """
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                self._rate_limit()
                return func(*args, **kwargs)
            except TooManyRequestsError as e:
                last_error = e
                logger.warning(
                    f"Google Trends rate limited (attempt {attempt + 1}/{MAX_RETRIES}). "
                    f"Waiting {RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(RETRY_DELAY_SECONDS)
            except Exception as e:
                last_error = e
                logger.error(f"Google Trends error: {e}")
                # Non-rate-limit errors (e.g. 404, parse errors) will not recover
                # from retrying — fail immediately.
                break

        logger.error(f"Google Trends failed: {last_error}")
        raise last_error if last_error else Exception("Unknown error in Google Trends")

    def get_trending_searches(self, country: str = 'brazil') -> List[str]:
        """
        Busca trending searches de um país.

        Args:
            country: Nome do país em inglês (default: brazil)

        Returns:
            Lista de termos em alta (até 20 itens)
        """
        try:
            def _fetch():
                df = self.pytrends.trending_searches(pn=country)
                return df[0].tolist() if not df.empty else []

            result = self._execute_with_retry(_fetch)
            logger.info(f"Fetched {len(result)} trending searches for {country}")
            return result

        except Exception as e:
            logger.error(f"Failed to get trending searches for {country}: {e}")
            return []

    def get_realtime_trends(self, country: str = 'BR', category: str = 'all') -> List[Dict[str, Any]]:
        """
        Busca tendências em tempo real.

        Args:
            country: Código do país (default: BR)
            category: Categoria (all, entertainment, business, tech, sports, health)

        Returns:
            Lista de tendências com título e tráfego aproximado
        """
        try:
            def _fetch():
                df = self.pytrends.realtime_trending_searches(pn=country)
                if df.empty:
                    return []

                trends = []
                for _, row in df.iterrows():
                    trends.append({
                        'title': row.get('title', ''),
                        'traffic': row.get('formattedTraffic', 'N/A'),
                        'news_url': row.get('newsUrl', ''),
                    })
                return trends

            result = self._execute_with_retry(_fetch)
            logger.info(f"Fetched {len(result)} realtime trends for {country}")
            return result

        except Exception as e:
            logger.error(f"Failed to get realtime trends for {country}: {e}")
            return []

    def get_related_topics(self, keyword: str, timeframe: str = 'today 3-m', geo: str = 'BR') -> Dict[str, List[Dict]]:
        """
        Busca tópicos relacionados a uma palavra-chave.

        Args:
            keyword: Palavra-chave para pesquisar
            timeframe: Período de tempo (default: últimos 3 meses)
            geo: Código geográfico (default: BR)

        Returns:
            Dict com 'rising' (em crescimento) e 'top' (mais populares)
        """
        try:
            def _fetch():
                self.pytrends.build_payload(
                    [keyword],
                    timeframe=timeframe,
                    geo=geo,
                )
                data = self.pytrends.related_topics()

                result = {'rising': [], 'top': []}

                if keyword in data:
                    keyword_data = data[keyword]

                    # Tópicos em crescimento
                    if 'rising' in keyword_data and keyword_data['rising'] is not None:
                        rising_df = keyword_data['rising']
                        if not rising_df.empty:
                            for _, row in rising_df.head(10).iterrows():
                                result['rising'].append({
                                    'topic': row.get('topic_title', ''),
                                    'value': row.get('value', 0),
                                })

                    # Tópicos mais populares
                    if 'top' in keyword_data and keyword_data['top'] is not None:
                        top_df = keyword_data['top']
                        if not top_df.empty:
                            for _, row in top_df.head(10).iterrows():
                                result['top'].append({
                                    'topic': row.get('topic_title', ''),
                                    'value': row.get('value', 0),
                                })

                return result

            result = self._execute_with_retry(_fetch)
            total = len(result.get('rising', [])) + len(result.get('top', []))
            logger.info(f"Fetched {total} related topics for '{keyword}'")
            return result

        except Exception as e:
            logger.error(f"Failed to get related topics for '{keyword}': {e}")
            return {'rising': [], 'top': []}

    def get_related_queries(self, keyword: str, timeframe: str = 'today 3-m', geo: str = 'BR') -> Dict[str, List[Dict]]:
        """
        Busca queries relacionadas a uma palavra-chave.

        Args:
            keyword: Palavra-chave para pesquisar
            timeframe: Período de tempo (default: últimos 3 meses)
            geo: Código geográfico (default: BR)

        Returns:
            Dict com 'rising' (em crescimento) e 'top' (mais populares)
        """
        try:
            def _fetch():
                self.pytrends.build_payload(
                    [keyword],
                    timeframe=timeframe,
                    geo=geo,
                )
                data = self.pytrends.related_queries()

                result = {'rising': [], 'top': []}

                if keyword in data:
                    keyword_data = data[keyword]

                    # Queries em crescimento
                    if 'rising' in keyword_data and keyword_data['rising'] is not None:
                        rising_df = keyword_data['rising']
                        if not rising_df.empty:
                            for _, row in rising_df.head(10).iterrows():
                                result['rising'].append({
                                    'query': row.get('query', ''),
                                    'value': row.get('value', 0),
                                })

                    # Queries mais populares
                    if 'top' in keyword_data and keyword_data['top'] is not None:
                        top_df = keyword_data['top']
                        if not top_df.empty:
                            for _, row in top_df.head(10).iterrows():
                                result['top'].append({
                                    'query': row.get('query', ''),
                                    'value': row.get('value', 0),
                                })

                return result

            result = self._execute_with_retry(_fetch)
            total = len(result.get('rising', [])) + len(result.get('top', []))
            logger.info(f"Fetched {total} related queries for '{keyword}'")
            return result

        except Exception as e:
            logger.error(f"Failed to get related queries for '{keyword}': {e}")
            return {'rising': [], 'top': []}

    def get_interest_over_time(
        self,
        keywords: List[str],
        timeframe: str = 'today 3-m',
        geo: str = 'BR'
    ) -> Dict[str, Any]:
        """
        Busca interesse ao longo do tempo para palavras-chave.

        Args:
            keywords: Lista de palavras-chave (máximo 5)
            timeframe: Período de tempo
            geo: Código geográfico

        Returns:
            Dict com dados de interesse ao longo do tempo
        """
        if not keywords:
            return {}

        # Google Trends limita a 5 keywords
        keywords = keywords[:5]

        try:
            def _fetch():
                self.pytrends.build_payload(
                    keywords,
                    timeframe=timeframe,
                    geo=geo,
                )
                df = self.pytrends.interest_over_time()

                if df.empty:
                    return {}

                # Calcular média de interesse para cada keyword
                result = {}
                for kw in keywords:
                    if kw in df.columns:
                        result[kw] = {
                            'average': float(df[kw].mean()),
                            'max': float(df[kw].max()),
                            'min': float(df[kw].min()),
                            'trend': 'rising' if df[kw].iloc[-1] > df[kw].iloc[0] else 'falling',
                        }

                return result

            result = self._execute_with_retry(_fetch)
            logger.info(f"Fetched interest over time for {len(keywords)} keywords")
            return result

        except Exception as e:
            logger.error(f"Failed to get interest over time for keywords: {e}")
            return {}

    def get_suggestions(self, keyword: str) -> List[Dict[str, str]]:
        """
        Busca sugestões de keywords relacionadas.

        Args:
            keyword: Palavra-chave base

        Returns:
            Lista de sugestões com título e tipo
        """
        try:
            def _fetch():
                suggestions = self.pytrends.suggestions(keyword)
                return [
                    {
                        'title': s.get('title', ''),
                        'type': s.get('type', ''),
                    }
                    for s in suggestions[:10]
                ]

            result = self._execute_with_retry(_fetch)
            logger.info(f"Fetched {len(result)} suggestions for '{keyword}'")
            return result

        except Exception as e:
            logger.error(f"Failed to get suggestions for '{keyword}': {e}")
            return []
