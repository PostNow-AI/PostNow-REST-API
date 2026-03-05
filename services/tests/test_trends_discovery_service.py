"""
Testes para TrendsDiscoveryService.

Usa mocks dos serviços de Google Trends e Google Search.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from services.trends_discovery_service import TrendsDiscoveryService


@pytest.fixture
def mock_google_trends():
    """Fixture que retorna um mock do GoogleTrendsService."""
    mock = MagicMock()
    mock.get_trending_searches.return_value = [
        'Tendência Brasil 1',
        'Tendência Brasil 2',
        'Tendência Brasil 3',
    ]
    mock.get_related_queries.return_value = {
        'rising': [
            {'query': 'query relacionada 1', 'value': 150},
            {'query': 'query relacionada 2', 'value': 100},
        ],
        'top': [
            {'query': 'query top 1', 'value': 80},
        ]
    }
    mock.get_related_topics.return_value = {
        'rising': [
            {'topic': 'tópico em crescimento', 'value': 200},
        ],
        'top': []
    }
    return mock


@pytest.fixture
def mock_google_search():
    """Fixture que retorna um mock do GoogleSearchService."""
    mock = MagicMock()
    mock.search.return_value = [
        {'url': 'https://example.com/1', 'title': 'Artigo 1', 'snippet': 'Snippet 1'},
        {'url': 'https://example.com/2', 'title': 'Artigo 2', 'snippet': 'Snippet 2'},
        {'url': 'https://example.com/3', 'title': 'Artigo 3', 'snippet': 'Snippet 3'},
    ]
    return mock


@pytest.fixture
def trends_discovery_service(mock_google_trends, mock_google_search):
    """Fixture que retorna uma instância do TrendsDiscoveryService com mocks."""
    return TrendsDiscoveryService(
        google_trends_service=mock_google_trends,
        google_search_service=mock_google_search,
    )


class TestTrendsDiscoveryServiceInit:
    """Testes de inicialização do serviço."""

    def test_init_with_defaults(self):
        """Testa inicialização com valores padrão."""
        with patch('services.trends_discovery_service.GoogleTrendsService'), \
             patch('services.trends_discovery_service.GoogleSearchService'):
            service = TrendsDiscoveryService()
            assert service.google_trends is not None
            assert service.google_search is not None

    def test_init_with_injected_services(self, mock_google_trends, mock_google_search):
        """Testa inicialização com serviços injetados."""
        service = TrendsDiscoveryService(
            google_trends_service=mock_google_trends,
            google_search_service=mock_google_search,
        )
        assert service.google_trends == mock_google_trends
        assert service.google_search == mock_google_search


class TestDiscoverTrendsForSector:
    """Testes para o método discover_trends_for_sector."""

    def test_discover_trends_returns_structure(self, trends_discovery_service):
        """Testa que retorna a estrutura correta."""
        result = trends_discovery_service.discover_trends_for_sector(
            sector='Marketing Digital',
            business_description='Agência de marketing',
            location='Brasil',
        )

        assert 'general_trends' in result
        assert 'sector_trends' in result
        assert 'rising_topics' in result
        assert 'validated_count' in result
        assert 'discovery_metadata' in result

    def test_discover_trends_validates_with_sources(
        self, mock_google_trends, mock_google_search
    ):
        """Testa que tendências são validadas com fontes."""
        service = TrendsDiscoveryService(
            google_trends_service=mock_google_trends,
            google_search_service=mock_google_search,
        )

        result = service.discover_trends_for_sector(sector='Tecnologia')

        # Verificar que Google Search foi chamado para validar
        assert mock_google_search.search.called

        # Verificar que tendências têm fontes
        for trend in result['general_trends']:
            assert 'sources' in trend
            assert len(trend['sources']) >= 2

    def test_discover_trends_filters_without_sources(
        self, mock_google_trends, mock_google_search
    ):
        """Testa que tendências sem fontes suficientes são filtradas."""
        # Mock que retorna apenas 1 fonte (mínimo é 2)
        mock_google_search.search.return_value = [
            {'url': 'https://example.com/1', 'title': 'Artigo 1', 'snippet': 'Snippet 1'},
        ]

        service = TrendsDiscoveryService(
            google_trends_service=mock_google_trends,
            google_search_service=mock_google_search,
        )

        result = service.discover_trends_for_sector(sector='Tecnologia')

        # Tendências sem fontes suficientes devem ser filtradas
        assert len(result['general_trends']) == 0

    def test_discover_trends_calculates_relevance_score(self, trends_discovery_service):
        """Testa que score de relevância é calculado."""
        result = trends_discovery_service.discover_trends_for_sector(
            sector='Marketing Digital'
        )

        for trend in result['general_trends']:
            assert 'relevance_score' in trend
            assert 0 <= trend['relevance_score'] <= 100


class TestDiscoverGeneralTrends:
    """Testes para descoberta de tendências gerais."""

    def test_discover_general_trends_calls_google_trends(
        self, trends_discovery_service, mock_google_trends
    ):
        """Testa que Google Trends é chamado para buscar trending searches."""
        trends_discovery_service._discover_general_trends()

        mock_google_trends.get_trending_searches.assert_called_with(country='brazil')

    def test_discover_general_trends_limits_results(
        self, mock_google_trends, mock_google_search
    ):
        """Testa que limita resultados a MAX_TRENDS_PER_CATEGORY."""
        # Mock com muitas tendências
        mock_google_trends.get_trending_searches.return_value = [
            f'Tendência {i}' for i in range(20)
        ]

        service = TrendsDiscoveryService(
            google_trends_service=mock_google_trends,
            google_search_service=mock_google_search,
        )

        result = service._discover_general_trends()

        # Deve limitar a 5 (MAX_TRENDS_PER_CATEGORY)
        assert len(result) <= 5


class TestDiscoverSectorTrends:
    """Testes para descoberta de tendências do setor."""

    def test_discover_sector_trends_calls_related_queries(
        self, trends_discovery_service, mock_google_trends
    ):
        """Testa que busca queries relacionadas ao setor."""
        trends_discovery_service._discover_sector_trends(
            sector='Marketing Digital',
            business_description='Agência de marketing'
        )

        mock_google_trends.get_related_queries.assert_called_with(
            keyword='Marketing Digital',
            timeframe='today 3-m',
            geo='BR'
        )

    def test_discover_sector_trends_prioritizes_rising(
        self, mock_google_trends, mock_google_search
    ):
        """Testa que prioriza queries em crescimento."""
        service = TrendsDiscoveryService(
            google_trends_service=mock_google_trends,
            google_search_service=mock_google_search,
        )

        result = service._discover_sector_trends(sector='Tecnologia')

        # Deve processar rising queries primeiro
        assert len(result) > 0


class TestValidateTrendWithSources:
    """Testes para validação de tendências com fontes."""

    def test_validate_trend_returns_none_without_sources(
        self, mock_google_trends, mock_google_search
    ):
        """Testa que retorna None se não houver fontes suficientes."""
        mock_google_search.search.return_value = []  # Sem fontes

        service = TrendsDiscoveryService(
            google_trends_service=mock_google_trends,
            google_search_service=mock_google_search,
        )

        result = service._validate_trend_with_sources('Tendência Teste')

        assert result is None

    def test_validate_trend_returns_dict_with_sources(
        self, mock_google_trends, mock_google_search
    ):
        """Testa que retorna dict válido com fontes suficientes."""
        service = TrendsDiscoveryService(
            google_trends_service=mock_google_trends,
            google_search_service=mock_google_search,
        )

        result = service._validate_trend_with_sources('Tendência Teste')

        assert result is not None
        assert result['topic'] == 'Tendência Teste'
        assert len(result['sources']) >= 2

    def test_validate_trend_includes_context_keywords(
        self, mock_google_trends, mock_google_search
    ):
        """Testa que inclui keywords de contexto na busca."""
        service = TrendsDiscoveryService(
            google_trends_service=mock_google_trends,
            google_search_service=mock_google_search,
        )

        service._validate_trend_with_sources(
            topic='IA',
            context_keywords=['tecnologia', 'brasil']
        )

        # Verificar que a busca incluiu o contexto
        call_args = mock_google_search.search.call_args
        assert 'IA tecnologia' in call_args[1]['query'] or 'IA tecnologia' in call_args[0][0]


class TestCalculateRelevanceScore:
    """Testes para cálculo de score de relevância."""

    def test_score_increases_with_sources(self, trends_discovery_service):
        """Testa que score aumenta com mais fontes."""
        score_2_sources = trends_discovery_service._calculate_relevance_score(
            sources_count=2, growth_score=0
        )
        score_5_sources = trends_discovery_service._calculate_relevance_score(
            sources_count=5, growth_score=0
        )

        assert score_5_sources > score_2_sources

    def test_score_increases_with_growth(self, trends_discovery_service):
        """Testa que score aumenta com maior crescimento."""
        score_no_growth = trends_discovery_service._calculate_relevance_score(
            sources_count=3, growth_score=0
        )
        score_high_growth = trends_discovery_service._calculate_relevance_score(
            sources_count=3, growth_score=500
        )

        assert score_high_growth > score_no_growth

    def test_score_max_100(self, trends_discovery_service):
        """Testa que score máximo é 100."""
        score = trends_discovery_service._calculate_relevance_score(
            sources_count=10, growth_score=2000
        )

        assert score == 100

    def test_breakout_trend_gets_max_growth_bonus(self, trends_discovery_service):
        """Testa que breakout trends (>1000) recebem bonus máximo."""
        score = trends_discovery_service._calculate_relevance_score(
            sources_count=3, growth_score=1000
        )

        # 30 (3 fontes * 10) + 50 (max growth bonus) = 80
        assert score == 80


class TestGetSearchKeywordsForOpportunity:
    """Testes para extração de keywords buscáveis."""

    def test_removes_creative_words(self, trends_discovery_service):
        """Testa que remove palavras criativas."""
        keywords = trends_discovery_service.get_search_keywords_for_opportunity(
            opportunity_title='A próxima mina de ouro da IA no Brasil',
            sector='Tecnologia'
        )

        assert 'mina' not in keywords
        assert 'ouro' not in keywords
        assert 'próxima' not in keywords

    def test_keeps_relevant_words(self, trends_discovery_service):
        """Testa que mantém palavras relevantes."""
        keywords = trends_discovery_service.get_search_keywords_for_opportunity(
            opportunity_title='Inteligência Artificial no Setor Público Brasil',
            sector='Tecnologia'
        )

        # Deve manter termos buscáveis
        assert any('intelig' in kw.lower() for kw in keywords)

    def test_adds_sector_if_missing(self, trends_discovery_service):
        """Testa que adiciona setor se não estiver presente."""
        keywords = trends_discovery_service.get_search_keywords_for_opportunity(
            opportunity_title='Inovação Digital',
            sector='Marketing'
        )

        assert 'marketing' in keywords

    def test_limits_to_five_keywords(self, trends_discovery_service):
        """Testa que limita a 5 keywords."""
        keywords = trends_discovery_service.get_search_keywords_for_opportunity(
            opportunity_title='Uma frase muito longa com muitas palavras diferentes para testar o limite',
            sector='Tecnologia'
        )

        assert len(keywords) <= 5


class TestEnrichOpportunityWithTrends:
    """Testes para enriquecimento de oportunidades com tendências."""

    def test_enriches_matching_opportunity(self, trends_discovery_service):
        """Testa enriquecimento de oportunidade que corresponde a tendência."""
        opportunity = {
            'titulo_ideia': 'Como usar Inteligência Artificial no Marketing',
            'score': 70,
        }
        discovered_trends = {
            'general_trends': [
                {
                    'topic': 'inteligência artificial',
                    'sources': [{'url': 'https://example.com'}],
                    'relevance_score': 80,
                }
            ],
            'sector_trends': [],
            'rising_topics': [],
        }

        enriched = trends_discovery_service.enrich_opportunity_with_trends(
            opportunity, discovered_trends
        )

        assert enriched['trend_validated'] is True
        assert len(enriched['trend_sources']) > 0
        assert enriched['score'] > opportunity['score']

    def test_penalizes_non_matching_opportunity(self, trends_discovery_service):
        """Testa penalização de oportunidade sem tendência correspondente."""
        opportunity = {
            'titulo_ideia': 'Tema Inventado Sem Relação',
            'score': 70,
        }
        discovered_trends = {
            'general_trends': [
                {'topic': 'outra tendência', 'sources': [], 'relevance_score': 50}
            ],
            'sector_trends': [],
            'rising_topics': [],
        }

        enriched = trends_discovery_service.enrich_opportunity_with_trends(
            opportunity, discovered_trends
        )

        assert enriched['trend_validated'] is False
        assert enriched['score'] < opportunity['score']
