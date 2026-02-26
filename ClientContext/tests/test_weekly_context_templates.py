"""Tests for weekly context email templates."""

import pytest
from ClientContext.utils.weekly_context import (
    generate_opportunities_email_template,
    generate_market_intelligence_email_template,
    _generate_ranked_opportunities_html,
)


@pytest.fixture
def sample_user_data():
    """Sample user data for email templates."""
    return {
        'business_name': 'Minha Empresa',
        'user_name': 'João',
        'user__first_name': 'João',
    }


@pytest.fixture
def sample_context_data():
    """Sample context data for email templates."""
    return {
        'tendencies_data': {
            'polemica': {
                'titulo': '🔥 Polêmica & Debate',
                'items': [
                    {
                        'titulo_ideia': 'Debate sobre IA no mercado',
                        'score': 95,
                        'gatilho_criativo': 'Questione o status quo'
                    },
                    {
                        'titulo_ideia': 'Controvérsia em redes sociais',
                        'score': 88,
                        'gatilho_criativo': 'Tome uma posição clara'
                    }
                ]
            },
            'educativo': {
                'titulo': '📚 Educativo',
                'items': [
                    {
                        'titulo_ideia': 'Tutorial de produtividade',
                        'score': 82,
                        'gatilho_criativo': 'Ensine algo prático'
                    }
                ]
            }
        },
        'tendencies_hashtags': ['marketing', 'digital', 'vendas', 'empreendedorismo'],
        'tendencies_keywords': ['estratégia', 'crescimento', 'inovação'],
        'market_panorama': 'O mercado está em crescimento acelerado.',
        'market_tendencies': ['IA Generativa', 'Automação', 'Personalização'],
        'market_challenges': ['Concorrência acirrada', 'Mudanças regulatórias'],
        'competition_main': ['Empresa A', 'Empresa B', 'Empresa C'],
        'competition_strategies': 'Foco em diferenciação por qualidade.',
        'target_audience_profile': 'Empreendedores de 25-45 anos',
        'target_audience_behaviors': 'Ativos em LinkedIn e Instagram',
        'brand_online_presence': 'Forte presença em redes sociais',
        'brand_reputation': 'Reconhecida como inovadora',
        'seasonal_relevant_dates': ['Black Friday', 'Natal'],
        'seasonal_local_events': ['Web Summit', 'SXSW'],
    }


class TestGenerateRankedOpportunitiesHtml:
    """Tests for _generate_ranked_opportunities_html function."""

    def test_generate_html_with_valid_data(self, sample_context_data):
        """Test HTML generation with valid tendencies_data."""
        tendencies_data = sample_context_data['tendencies_data']

        html = _generate_ranked_opportunities_html(tendencies_data)

        assert html is not None
        assert len(html) > 0
        assert 'Polêmica' in html
        assert 'Debate sobre IA no mercado' in html
        assert '95%' in html
        assert 'Educativo' in html

    def test_generate_html_with_empty_data(self):
        """Test HTML generation with empty data."""
        html = _generate_ranked_opportunities_html({})

        assert html == ""

    def test_generate_html_with_none(self):
        """Test HTML generation with None."""
        html = _generate_ranked_opportunities_html(None)

        assert html == ""

    def test_generate_html_with_empty_items(self):
        """Test HTML generation when items list is empty."""
        tendencies_data = {
            'polemica': {
                'titulo': '🔥 Polêmica',
                'items': []
            }
        }

        html = _generate_ranked_opportunities_html(tendencies_data)

        assert html == ""

    def test_generate_html_limits_to_3_items(self):
        """Test that HTML limits to 3 items per category."""
        tendencies_data = {
            'educativo': {
                'titulo': '📚 Educativo',
                'items': [
                    {'titulo_ideia': f'Item {i}', 'score': 90-i, 'gatilho_criativo': ''}
                    for i in range(5)
                ]
            }
        }

        html = _generate_ranked_opportunities_html(tendencies_data)

        # Should only have items 0, 1, 2 (first 3)
        assert 'Item 0' in html
        assert 'Item 1' in html
        assert 'Item 2' in html
        assert 'Item 3' not in html
        assert 'Item 4' not in html

    def test_generate_html_respects_priority_order(self):
        """Test that categories follow priority order."""
        tendencies_data = {
            'outros': {
                'titulo': 'Outros',
                'items': [{'titulo_ideia': 'Outros Item', 'score': 50}]
            },
            'polemica': {
                'titulo': 'Polêmica',
                'items': [{'titulo_ideia': 'Polêmica Item', 'score': 90}]
            },
        }

        html = _generate_ranked_opportunities_html(tendencies_data)

        # Polêmica should come before Outros
        polemica_pos = html.find('Polêmica Item')
        outros_pos = html.find('Outros Item')
        assert polemica_pos < outros_pos


class TestGenerateOpportunitiesEmailTemplate:
    """Tests for generate_opportunities_email_template function."""

    def test_generate_template_with_valid_data(self, sample_context_data, sample_user_data):
        """Test template generation with valid data."""
        html = generate_opportunities_email_template(sample_context_data, sample_user_data)

        assert html is not None
        assert len(html) > 0
        assert '<!DOCTYPE html>' in html
        assert 'Oportunidades de Conteúdo' in html
        assert 'Minha Empresa' in html
        assert 'João' in html

    def test_generate_template_includes_hashtags(self, sample_context_data, sample_user_data):
        """Test that template includes hashtags."""
        html = generate_opportunities_email_template(sample_context_data, sample_user_data)

        assert '#marketing' in html
        assert '#digital' in html

    def test_generate_template_includes_keywords(self, sample_context_data, sample_user_data):
        """Test that template includes keywords."""
        html = generate_opportunities_email_template(sample_context_data, sample_user_data)

        assert 'estratégia' in html
        assert 'crescimento' in html

    def test_generate_template_includes_opportunities(self, sample_context_data, sample_user_data):
        """Test that template includes ranked opportunities."""
        html = generate_opportunities_email_template(sample_context_data, sample_user_data)

        assert 'Debate sobre IA no mercado' in html
        assert '95%' in html

    def test_generate_template_with_empty_context(self, sample_user_data):
        """Test template generation with empty context."""
        html = generate_opportunities_email_template({}, sample_user_data)

        assert html is not None
        assert 'Oportunidades de Conteúdo' in html
        assert 'Minha Empresa' in html

    def test_generate_template_includes_cta(self, sample_context_data, sample_user_data):
        """Test that template includes call-to-action."""
        html = generate_opportunities_email_template(sample_context_data, sample_user_data)

        assert 'Criar Conteúdo Agora' in html
        assert 'weekly-context' in html

    def test_generate_template_includes_footer_message(self, sample_context_data, sample_user_data):
        """Test that template includes footer about email schedule."""
        html = generate_opportunities_email_template(sample_context_data, sample_user_data)

        assert 'Segunda-feira' in html
        assert 'Quarta' in html


class TestGenerateMarketIntelligenceEmailTemplate:
    """Tests for generate_market_intelligence_email_template function."""

    def test_generate_template_with_valid_data(self, sample_context_data, sample_user_data):
        """Test template generation with valid data."""
        html = generate_market_intelligence_email_template(sample_context_data, sample_user_data)

        assert html is not None
        assert len(html) > 0
        assert '<!DOCTYPE html>' in html
        assert 'Inteligência de Mercado' in html
        assert 'Minha Empresa' in html
        assert 'João' in html

    def test_generate_template_includes_market_section(self, sample_context_data, sample_user_data):
        """Test that template includes market section."""
        html = generate_market_intelligence_email_template(sample_context_data, sample_user_data)

        assert 'Panorama do Mercado' in html
        assert 'crescimento acelerado' in html

    def test_generate_template_includes_competition_section(self, sample_context_data, sample_user_data):
        """Test that template includes competition section."""
        html = generate_market_intelligence_email_template(sample_context_data, sample_user_data)

        assert 'Concorrência' in html
        assert 'diferenciação' in html

    def test_generate_template_includes_audience_section(self, sample_context_data, sample_user_data):
        """Test that template includes audience section."""
        html = generate_market_intelligence_email_template(sample_context_data, sample_user_data)

        assert 'Seu Público' in html
        assert 'Empreendedores' in html
        assert 'LinkedIn' in html

    def test_generate_template_includes_brand_section(self, sample_context_data, sample_user_data):
        """Test that template includes brand section."""
        html = generate_market_intelligence_email_template(sample_context_data, sample_user_data)

        assert 'Sua Marca' in html
        assert 'inovadora' in html

    def test_generate_template_includes_seasonal_section(self, sample_context_data, sample_user_data):
        """Test that template includes seasonal section."""
        html = generate_market_intelligence_email_template(sample_context_data, sample_user_data)

        assert 'Calendário' in html
        assert 'Black Friday' in html

    def test_generate_template_with_empty_context(self, sample_user_data):
        """Test template generation with empty context."""
        html = generate_market_intelligence_email_template({}, sample_user_data)

        assert html is not None
        assert 'Inteligência de Mercado' in html

    def test_generate_template_includes_cta(self, sample_context_data, sample_user_data):
        """Test that template includes call-to-action."""
        html = generate_market_intelligence_email_template(sample_context_data, sample_user_data)

        assert 'Ver Análise Completa' in html

    def test_generate_template_includes_footer_message(self, sample_context_data, sample_user_data):
        """Test that template includes footer about email schedule."""
        html = generate_market_intelligence_email_template(sample_context_data, sample_user_data)

        assert 'Quarta-feira' in html
        assert 'Segunda' in html


class TestEmailTemplateDefaults:
    """Tests for default values in email templates."""

    def test_opportunities_template_default_business_name(self):
        """Test default business name in opportunities template."""
        html = generate_opportunities_email_template({}, {})

        assert 'Sua Empresa' in html

    def test_opportunities_template_default_user_name(self):
        """Test default user name in opportunities template."""
        html = generate_opportunities_email_template({}, {})

        assert 'Usuário' in html

    def test_market_intelligence_template_default_business_name(self):
        """Test default business name in market intelligence template."""
        html = generate_market_intelligence_email_template({}, {})

        assert 'Sua Empresa' in html

    def test_market_intelligence_template_default_user_name(self):
        """Test default user name in market intelligence template."""
        html = generate_market_intelligence_email_template({}, {})

        assert 'Usuário' in html
