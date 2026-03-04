"""
Trends Discovery Service.

Orquestra a descoberta de tendências reais antes da geração de oportunidades.

Fluxo:
    1. Busca trending searches gerais (Google Trends)
    2. Busca tópicos relacionados ao setor do usuário
    3. Valida cada tendência buscando artigos recentes (Google Search)
    4. Retorna apenas tendências com fontes verificáveis

Este serviço resolve o problema de "inverter o fluxo":
    ANTES: Gemini "inventa" → tentamos validar → falha
    AGORA: Descobrimos tendências reais → Gemini adapta → sempre tem fontes
"""
import logging
from typing import Any, Dict, List, Optional

from services.google_trends_service import GoogleTrendsService
from services.google_search_service import GoogleSearchService

logger = logging.getLogger(__name__)

# Configurações
MIN_SOURCES_FOR_VALID_TREND = 2  # Mínimo de fontes para considerar tendência válida
MAX_TRENDS_PER_CATEGORY = 5  # Máximo de tendências por categoria
MAX_GENERAL_TRENDS = 10  # Máximo de tendências gerais a processar


class TrendsDiscoveryService:
    """
    Serviço para descoberta de tendências reais e validadas.

    Combina Google Trends (descoberta) com Google Search (validação)
    para garantir que apenas tendências com fontes verificáveis
    sejam usadas na geração de oportunidades.
    """

    def __init__(
        self,
        google_trends_service: Optional[GoogleTrendsService] = None,
        google_search_service: Optional[GoogleSearchService] = None,
    ):
        """
        Inicializa o serviço de descoberta de tendências.

        Args:
            google_trends_service: Serviço de Google Trends (injetável para testes)
            google_search_service: Serviço de Google Search (injetável para testes)
        """
        self.google_trends = google_trends_service or GoogleTrendsService()
        self.google_search = google_search_service or GoogleSearchService()

    def discover_trends_for_sector(
        self,
        sector: str,
        business_description: str = '',
        location: str = 'Brasil',
    ) -> Dict[str, Any]:
        """
        Descobre tendências relevantes para um setor específico.

        Args:
            sector: Setor/nicho de atuação do usuário
            business_description: Descrição do negócio (para contexto adicional)
            location: Localização geográfica

        Returns:
            Dict com tendências validadas organizadas por categoria:
            {
                'general_trends': [...],  # Tendências gerais do país
                'sector_trends': [...],   # Tendências específicas do setor
                'rising_topics': [...],   # Tópicos em crescimento
                'validated_count': int,   # Total de tendências validadas
                'discovery_metadata': {...}  # Metadados da descoberta
            }
        """
        logger.info(f"Discovering trends for sector: {sector}")

        result = {
            'general_trends': [],
            'sector_trends': [],
            'rising_topics': [],
            'validated_count': 0,
            'discovery_metadata': {
                'sector': sector,
                'location': location,
            }
        }

        # 1. Buscar tendências gerais do Brasil
        general_trends = self._discover_general_trends()
        result['general_trends'] = general_trends

        # 2. Buscar tendências específicas do setor
        sector_trends = self._discover_sector_trends(sector, business_description)
        result['sector_trends'] = sector_trends

        # 3. Buscar tópicos em crescimento relacionados ao setor
        rising_topics = self._discover_rising_topics(sector)
        result['rising_topics'] = rising_topics

        # Calcular total de tendências validadas
        result['validated_count'] = (
            len(result['general_trends']) +
            len(result['sector_trends']) +
            len(result['rising_topics'])
        )

        logger.info(f"Discovered {result['validated_count']} validated trends for sector '{sector}'")
        return result

    def _discover_general_trends(self) -> List[Dict[str, Any]]:
        """
        Descobre tendências gerais do Brasil e valida com fontes.

        Returns:
            Lista de tendências gerais validadas
        """
        validated_trends = []

        try:
            # Buscar trending searches
            trending = self.google_trends.get_trending_searches(country='brazil')

            if not trending:
                logger.warning("No trending searches found")
                return []

            # Processar apenas os top N
            for trend_topic in trending[:MAX_GENERAL_TRENDS]:
                validated = self._validate_trend_with_sources(trend_topic)
                if validated:
                    validated_trends.append(validated)

                # Parar se já temos tendências suficientes
                if len(validated_trends) >= MAX_TRENDS_PER_CATEGORY:
                    break

        except Exception as e:
            logger.error(f"Error discovering general trends: {e}")

        return validated_trends

    def _discover_sector_trends(self, sector: str, business_description: str = '') -> List[Dict[str, Any]]:
        """
        Descobre tendências específicas do setor.

        Args:
            sector: Setor de atuação
            business_description: Descrição do negócio

        Returns:
            Lista de tendências do setor validadas
        """
        validated_trends = []

        try:
            # Buscar queries relacionadas ao setor
            related_queries = self.google_trends.get_related_queries(
                keyword=sector,
                timeframe='today 3-m',
                geo='BR'
            )

            # Processar queries em crescimento (mais relevantes)
            rising_queries = related_queries.get('rising', [])
            for query_data in rising_queries[:MAX_TRENDS_PER_CATEGORY]:
                query = query_data.get('query', '')
                if not query:
                    continue

                validated = self._validate_trend_with_sources(
                    topic=query,
                    context_keywords=[sector],
                    growth_score=query_data.get('value', 0)
                )
                if validated:
                    validated_trends.append(validated)

            # Se não temos suficientes, pegar das top queries também
            if len(validated_trends) < MAX_TRENDS_PER_CATEGORY:
                top_queries = related_queries.get('top', [])
                for query_data in top_queries:
                    if len(validated_trends) >= MAX_TRENDS_PER_CATEGORY:
                        break

                    query = query_data.get('query', '')
                    if not query:
                        continue

                    # Verificar se já não está na lista
                    if any(t.get('topic') == query for t in validated_trends):
                        continue

                    validated = self._validate_trend_with_sources(
                        topic=query,
                        context_keywords=[sector],
                        growth_score=query_data.get('value', 0)
                    )
                    if validated:
                        validated_trends.append(validated)

        except Exception as e:
            logger.error(f"Error discovering sector trends for '{sector}': {e}")

        return validated_trends

    def _discover_rising_topics(self, sector: str) -> List[Dict[str, Any]]:
        """
        Descobre tópicos em crescimento relacionados ao setor.

        Args:
            sector: Setor de atuação

        Returns:
            Lista de tópicos em crescimento validados
        """
        validated_trends = []

        try:
            # Buscar tópicos relacionados
            related_topics = self.google_trends.get_related_topics(
                keyword=sector,
                timeframe='today 3-m',
                geo='BR'
            )

            # Processar tópicos em crescimento
            rising_topics = related_topics.get('rising', [])
            for topic_data in rising_topics[:MAX_TRENDS_PER_CATEGORY]:
                topic = topic_data.get('topic', '')
                if not topic:
                    continue

                validated = self._validate_trend_with_sources(
                    topic=topic,
                    context_keywords=[sector],
                    growth_score=topic_data.get('value', 0)
                )
                if validated:
                    validated['is_rising'] = True
                    validated_trends.append(validated)

        except Exception as e:
            logger.error(f"Error discovering rising topics for '{sector}': {e}")

        return validated_trends

    def _validate_trend_with_sources(
        self,
        topic: str,
        context_keywords: List[str] = None,
        growth_score: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Valida uma tendência buscando fontes reais.

        Args:
            topic: Tópico/tendência a validar
            context_keywords: Palavras-chave adicionais para contexto
            growth_score: Score de crescimento do Google Trends

        Returns:
            Dict com tendência validada ou None se não tiver fontes suficientes
        """
        if not topic:
            return None

        try:
            # Construir query de busca
            search_query = topic
            if context_keywords:
                # Adicionar apenas o primeiro contexto para não poluir a busca
                search_query = f"{topic} {context_keywords[0]}"

            # Buscar fontes
            sources = self.google_search.search(
                query=search_query,
                num_results=5
            )

            # Validar quantidade mínima de fontes
            if len(sources) < MIN_SOURCES_FOR_VALID_TREND:
                logger.debug(f"Trend '{topic}' has only {len(sources)} sources, skipping")
                return None

            # Calcular score de relevância
            relevance_score = self._calculate_relevance_score(
                sources_count=len(sources),
                growth_score=growth_score
            )

            return {
                'topic': topic,
                'sources': sources,
                'sources_count': len(sources),
                'growth_score': growth_score,
                'relevance_score': relevance_score,
                'search_keywords': [topic] + (context_keywords or []),
            }

        except Exception as e:
            logger.error(f"Error validating trend '{topic}': {e}")
            return None

    def _calculate_relevance_score(self, sources_count: int, growth_score: int) -> int:
        """
        Calcula score de relevância baseado em fontes e crescimento.

        Args:
            sources_count: Número de fontes encontradas
            growth_score: Score de crescimento do Google Trends

        Returns:
            Score de 0 a 100
        """
        # Base score pelas fontes (máximo 50 pontos)
        source_score = min(sources_count * 10, 50)

        # Bonus pelo crescimento (máximo 50 pontos)
        # Growth score do Google Trends pode ser muito alto para "Breakout" trends
        growth_bonus = 0
        if growth_score > 0:
            if growth_score >= 1000:  # Breakout
                growth_bonus = 50
            elif growth_score >= 500:
                growth_bonus = 40
            elif growth_score >= 200:
                growth_bonus = 30
            elif growth_score >= 100:
                growth_bonus = 20
            else:
                growth_bonus = min(growth_score // 10, 10)

        return min(source_score + growth_bonus, 100)

    def get_search_keywords_for_opportunity(self, opportunity_title: str, sector: str) -> List[str]:
        """
        Extrai palavras-chave buscáveis de um título de oportunidade.

        Remove frases criativas e mantém apenas termos buscáveis.

        Args:
            opportunity_title: Título criativo da oportunidade
            sector: Setor de atuação

        Returns:
            Lista de palavras-chave para busca
        """
        # Palavras a remover (termos criativos, não buscáveis)
        stop_words = {
            'mina', 'ouro', 'próxima', 'grande', 'enorme', 'incrível',
            'segredo', 'revelado', 'chocante', 'bombástico', 'urgente',
            'exclusivo', 'imperdível', 'você', 'seu', 'sua', 'como',
        }

        # Extrair palavras do título
        words = opportunity_title.lower().split()

        # Filtrar stop words e palavras muito curtas
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        # Adicionar setor se não estiver presente
        sector_lower = sector.lower()
        if sector_lower not in ' '.join(keywords):
            keywords.append(sector_lower)

        # Retornar top 5 palavras-chave
        return keywords[:5]

    def enrich_opportunity_with_trends(
        self,
        opportunity: Dict[str, Any],
        discovered_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enriquece uma oportunidade com dados de tendências descobertas.

        Verifica se a oportunidade está alinhada com tendências reais
        e ajusta seu score baseado em dados verificáveis.

        Args:
            opportunity: Oportunidade gerada pela IA
            discovered_trends: Tendências descobertas para o setor

        Returns:
            Oportunidade enriquecida com dados de tendências
        """
        title = opportunity.get('titulo_ideia', '')
        title_lower = title.lower()

        # Verificar se a oportunidade está alinhada com alguma tendência
        matching_trend = None
        all_trends = (
            discovered_trends.get('general_trends', []) +
            discovered_trends.get('sector_trends', []) +
            discovered_trends.get('rising_topics', [])
        )

        for trend in all_trends:
            trend_topic = trend.get('topic', '').lower()
            if trend_topic and trend_topic in title_lower:
                matching_trend = trend
                break

        enriched = opportunity.copy()

        if matching_trend:
            # Oportunidade alinhada com tendência real
            enriched['trend_validated'] = True
            enriched['trend_sources'] = matching_trend.get('sources', [])
            enriched['trend_relevance_score'] = matching_trend.get('relevance_score', 0)

            # Bonus no score por estar alinhada com tendência verificada
            current_score = enriched.get('score', 50)
            bonus = min(matching_trend.get('relevance_score', 0) // 5, 10)
            enriched['score'] = min(current_score + bonus, 100)
        else:
            # Oportunidade não alinhada - penalizar levemente
            enriched['trend_validated'] = False
            enriched['trend_sources'] = []

            # Penalidade leve por não ter tendência verificada
            current_score = enriched.get('score', 50)
            enriched['score'] = max(current_score - 5, 0)

        return enriched
