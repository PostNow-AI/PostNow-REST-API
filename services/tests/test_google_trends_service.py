"""
Testes para GoogleTrendsService.

Usa mocks do pytrends para evitar chamadas reais à API do Google Trends.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from services.google_trends_service import GoogleTrendsService


@pytest.fixture
def google_trends_service():
    """Fixture que retorna uma instância do GoogleTrendsService."""
    return GoogleTrendsService()


@pytest.fixture
def mock_pytrends():
    """Fixture que retorna um mock do TrendReq."""
    with patch('services.google_trends_service.TrendReq') as mock:
        yield mock


class TestGoogleTrendsServiceInit:
    """Testes de inicialização do serviço."""

    def test_init_default_values(self, google_trends_service):
        """Testa valores padrão de inicialização."""
        assert google_trends_service.language == 'pt-BR'
        assert google_trends_service.timezone_offset == 180

    def test_init_custom_values(self):
        """Testa inicialização com valores customizados."""
        service = GoogleTrendsService(language='en-US', timezone_offset=0)
        assert service.language == 'en-US'
        assert service.timezone_offset == 0


class TestGetTrendingSearches:
    """Testes para o método get_trending_searches."""

    def test_get_trending_searches_success(self, mock_pytrends):
        """Testa busca de trending searches com sucesso."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance

        # Simular retorno do pytrends
        mock_df = pd.DataFrame({0: ['Tendência 1', 'Tendência 2', 'Tendência 3']})
        mock_instance.trending_searches.return_value = mock_df

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_trending_searches(country='brazil')

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert 'Tendência 1' in result

    def test_get_trending_searches_empty(self, mock_pytrends):
        """Testa busca de trending searches quando não há resultados."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance

        mock_df = pd.DataFrame()  # DataFrame vazio
        mock_instance.trending_searches.return_value = mock_df

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_trending_searches(country='brazil')

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_trending_searches_error(self, mock_pytrends):
        """Testa tratamento de erro na busca de trending searches."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance
        mock_instance.trending_searches.side_effect = Exception("API Error")

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_trending_searches(country='brazil')

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0


class TestGetRelatedTopics:
    """Testes para o método get_related_topics."""

    def test_get_related_topics_success(self, mock_pytrends):
        """Testa busca de tópicos relacionados com sucesso."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance

        # Simular retorno do pytrends
        rising_df = pd.DataFrame({
            'topic_title': ['Tópico Rising 1', 'Tópico Rising 2'],
            'value': [100, 80]
        })
        top_df = pd.DataFrame({
            'topic_title': ['Tópico Top 1', 'Tópico Top 2'],
            'value': [90, 70]
        })

        mock_instance.related_topics.return_value = {
            'marketing': {
                'rising': rising_df,
                'top': top_df
            }
        }

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_related_topics(keyword='marketing')

        # Assert
        assert 'rising' in result
        assert 'top' in result
        assert len(result['rising']) == 2
        assert len(result['top']) == 2

    def test_get_related_topics_empty(self, mock_pytrends):
        """Testa busca de tópicos relacionados quando não há resultados."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance

        mock_instance.related_topics.return_value = {
            'marketing': {
                'rising': None,
                'top': None
            }
        }

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_related_topics(keyword='marketing')

        # Assert
        assert result == {'rising': [], 'top': []}


class TestGetRelatedQueries:
    """Testes para o método get_related_queries."""

    def test_get_related_queries_success(self, mock_pytrends):
        """Testa busca de queries relacionadas com sucesso."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance

        rising_df = pd.DataFrame({
            'query': ['query rising 1', 'query rising 2'],
            'value': [150, 120]
        })
        top_df = pd.DataFrame({
            'query': ['query top 1', 'query top 2'],
            'value': [100, 80]
        })

        mock_instance.related_queries.return_value = {
            'tecnologia': {
                'rising': rising_df,
                'top': top_df
            }
        }

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_related_queries(keyword='tecnologia')

        # Assert
        assert 'rising' in result
        assert 'top' in result
        assert len(result['rising']) == 2
        assert result['rising'][0]['query'] == 'query rising 1'


class TestGetInterestOverTime:
    """Testes para o método get_interest_over_time."""

    def test_get_interest_over_time_success(self, mock_pytrends):
        """Testa busca de interesse ao longo do tempo com sucesso."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance

        # Simular DataFrame de interesse
        mock_df = pd.DataFrame({
            'keyword1': [50, 60, 70, 80],
            'keyword2': [30, 40, 50, 60],
        })

        mock_instance.interest_over_time.return_value = mock_df

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_interest_over_time(keywords=['keyword1', 'keyword2'])

        # Assert
        assert 'keyword1' in result
        assert 'keyword2' in result
        assert result['keyword1']['trend'] == 'rising'  # 50 -> 80

    def test_get_interest_over_time_empty_keywords(self, google_trends_service):
        """Testa com lista vazia de keywords."""
        result = google_trends_service.get_interest_over_time(keywords=[])
        assert result == {}

    def test_get_interest_over_time_max_five_keywords(self, mock_pytrends):
        """Testa que limita a 5 keywords."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance
        mock_instance.interest_over_time.return_value = pd.DataFrame()

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        keywords = ['k1', 'k2', 'k3', 'k4', 'k5', 'k6', 'k7']
        service.get_interest_over_time(keywords=keywords)

        # Assert
        # Verifica que build_payload foi chamado com apenas 5 keywords
        call_args = mock_instance.build_payload.call_args
        assert len(call_args[0][0]) == 5


class TestGetSuggestions:
    """Testes para o método get_suggestions."""

    def test_get_suggestions_success(self, mock_pytrends):
        """Testa busca de sugestões com sucesso."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance

        mock_instance.suggestions.return_value = [
            {'title': 'Sugestão 1', 'type': 'Topic'},
            {'title': 'Sugestão 2', 'type': 'Search term'},
        ]

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_suggestions(keyword='marketing')

        # Assert
        assert len(result) == 2
        assert result[0]['title'] == 'Sugestão 1'

    def test_get_suggestions_error(self, mock_pytrends):
        """Testa tratamento de erro na busca de sugestões."""
        # Arrange
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance
        mock_instance.suggestions.side_effect = Exception("API Error")

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Act
        result = service.get_suggestions(keyword='marketing')

        # Assert
        assert result == []


class TestRateLimiting:
    """Testes para rate limiting."""

    def test_rate_limit_is_applied(self, mock_pytrends):
        """Testa que rate limiting é aplicado entre requests."""
        # Este teste verifica que o rate limiting não causa erros
        mock_instance = MagicMock()
        mock_pytrends.return_value = mock_instance
        mock_instance.trending_searches.return_value = pd.DataFrame({0: ['Test']})

        service = GoogleTrendsService()
        service._pytrends = mock_instance

        # Fazer duas chamadas em sequência
        result1 = service.get_trending_searches()
        result2 = service.get_trending_searches()

        assert result1 == result2
