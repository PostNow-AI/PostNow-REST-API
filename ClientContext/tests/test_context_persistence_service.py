"""Tests for context persistence service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ClientContext.services.context_persistence_service import (
    ContextPersistenceService,
    ContextSectionData,
)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock()
    user.id = 1
    user.email = 'test@example.com'
    return user


@pytest.fixture
def mock_client_context():
    """Create a mock ClientContext."""
    context = MagicMock()
    context.id = 1
    context.user_id = 1
    return context


@pytest.fixture
def sample_context_data():
    """Create sample context data."""
    return {
        'mercado': {
            'panorama': 'Mercado em crescimento',
            'tendencias': ['IA', 'Automacao'],
            'desafios': ['Concorrencia'],
            'fontes': ['fonte1.com'],
            'fontes_analisadas': [
                {
                    'titulo_original': 'Artigo Mercado',
                    'oportunidades': [
                        {
                            'titulo_ideia': 'Ideia Mercado',
                            'tipo': 'Viral',
                            'texto_base_analisado': 'Texto base',
                            'gatilho_criativo': 'Gatilho'
                        }
                    ]
                }
            ]
        },
        'concorrencia': {
            'principais': ['Concorrente A'],
            'estrategias': 'Estrategia X',
            'oportunidades': 'Oportunidade Y',
            'fontes': [],
            'fontes_analisadas': []
        },
        'publico': {
            'perfil': 'Empreendedores',
            'comportamento_online': 'Ativo nas redes',
            'interesses': ['Marketing', 'Vendas'],
            'fontes': []
        },
        'tendencias': {
            'temas_populares': ['IA Generativa'],
            'hashtags': ['#IA', '#Tech'],
            'keywords': ['inteligencia artificial'],
            'fontes': [],
            'fontes_analisadas': []
        },
        'sazonalidade': {
            'datas_relevantes': ['Black Friday'],
            'eventos_locais': ['Web Summit'],
            'fontes': []
        },
        'marca': {
            'presenca_online': 'Forte',
            'reputacao': 'Positiva',
            'tom_comunicacao_atual': 'Profissional',
            'fontes': []
        }
    }


class TestContextSectionData:
    """Tests for ContextSectionData dataclass."""

    def test_context_section_data_creation(self):
        """Test creating a ContextSectionData instance."""
        data = ContextSectionData(
            raw=[{'key': 'value'}],
            opportunities=[{'titulo': 'Test'}],
            titles=['Title 1', 'Title 2']
        )

        assert data.raw == [{'key': 'value'}]
        assert data.opportunities == [{'titulo': 'Test'}]
        assert data.titles == ['Title 1', 'Title 2']


class TestContextPersistenceService:
    """Tests for ContextPersistenceService."""

    def test_extract_section(self, sample_context_data):
        """Test _extract_section method."""
        service = ContextPersistenceService()

        result = service._extract_section(sample_context_data, 'mercado')

        assert isinstance(result, ContextSectionData)
        assert len(result.raw) == 1
        assert len(result.opportunities) == 1
        assert 'Artigo Mercado' in result.titles

    def test_extract_section_missing(self):
        """Test _extract_section with missing section."""
        service = ContextPersistenceService()

        result = service._extract_section({}, 'mercado')

        assert isinstance(result, ContextSectionData)
        assert result.raw == []
        assert result.opportunities == []
        assert result.titles == []

    def test_update_market_fields(self, mock_client_context, sample_context_data):
        """Test _update_market_fields method."""
        service = ContextPersistenceService()
        mercado = service._extract_section(sample_context_data, 'mercado')

        service._update_market_fields(mock_client_context, sample_context_data, mercado)

        assert mock_client_context.market_panorama == 'Mercado em crescimento'
        assert mock_client_context.market_tendencies == ['IA', 'Automacao']

    def test_update_audience_fields(self, mock_client_context, sample_context_data):
        """Test _update_audience_fields method."""
        service = ContextPersistenceService()

        service._update_audience_fields(mock_client_context, sample_context_data)

        assert mock_client_context.target_audience_profile == 'Empreendedores'
        assert mock_client_context.target_audience_behaviors == 'Ativo nas redes'
        assert mock_client_context.target_audience_interests == ['Marketing', 'Vendas']

    def test_update_seasonal_fields(self, mock_client_context, sample_context_data):
        """Test _update_seasonal_fields method."""
        service = ContextPersistenceService()

        service._update_seasonal_fields(mock_client_context, sample_context_data)

        assert mock_client_context.seasonal_relevant_dates == ['Black Friday']
        assert mock_client_context.seasonal_local_events == ['Web Summit']

    def test_update_brand_fields(self, mock_client_context, sample_context_data):
        """Test _update_brand_fields method."""
        service = ContextPersistenceService()

        service._update_brand_fields(mock_client_context, sample_context_data)

        assert mock_client_context.brand_online_presence == 'Forte'
        assert mock_client_context.brand_reputation == 'Positiva'
        assert mock_client_context.brand_communication_style == 'Profissional'

    @pytest.mark.asyncio
    async def test_save_context(self, mock_user, sample_context_data):
        """Test save_context method."""
        service = ContextPersistenceService()
        mock_context = MagicMock()
        ranked_opportunities = {'mercado': {'items': []}}

        with patch('ClientContext.services.context_persistence_service.sync_to_async') as mock_sync:
            # Mock get_or_create
            mock_sync.return_value = AsyncMock(return_value=(mock_context, True))

            result = await service.save_context(
                user=mock_user,
                context_data=sample_context_data,
                ranked_opportunities=ranked_opportunities
            )

            assert result == mock_context
            assert mock_context.tendencies_data == ranked_opportunities
            assert mock_context.weekly_context_error is None

    @pytest.mark.asyncio
    async def test_save_context_history(self, mock_user, mock_client_context):
        """Test save_context_history method."""
        service = ContextPersistenceService()
        mock_history = MagicMock()

        with patch('ClientContext.services.context_persistence_service.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=mock_history)

            result = await service.save_context_history(mock_user, mock_client_context)

            assert result == mock_history
