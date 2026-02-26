"""Tests for data extraction utilities."""

import pytest
from ClientContext.utils.data_extraction import (
    extract_from_opportunities,
    normalize_section_structure,
    generate_hashtags_from_opportunities,
    generate_keywords_from_opportunities,
)


class TestExtractFromOpportunities:
    """Tests for extract_from_opportunities function."""

    def test_extract_with_valid_data(self):
        """Test extraction with valid fontes_analisadas data."""
        section_data = {
            'fontes_analisadas': [
                {
                    'titulo_original': 'Artigo sobre Marketing',
                    'oportunidades': [
                        {'titulo_ideia': 'Ideia 1', 'tipo': 'Viral'},
                        {'titulo_ideia': 'Ideia 2', 'tipo': 'Educativo'},
                    ]
                },
                {
                    'titulo_original': 'Tendencias 2024',
                    'oportunidades': [
                        {'titulo_ideia': 'Ideia 3', 'tipo': 'Newsjacking'},
                    ]
                }
            ]
        }

        fontes, opps, titles = extract_from_opportunities(section_data)

        assert len(fontes) == 2
        assert len(opps) == 3
        assert len(titles) == 2
        assert 'Artigo sobre Marketing' in titles
        assert 'Tendencias 2024' in titles

    def test_extract_with_empty_data(self):
        """Test extraction with empty data."""
        section_data = {}

        fontes, opps, titles = extract_from_opportunities(section_data)

        assert fontes == []
        assert opps == []
        assert titles == []

    def test_extract_with_empty_fontes(self):
        """Test extraction with empty fontes_analisadas."""
        section_data = {'fontes_analisadas': []}

        fontes, opps, titles = extract_from_opportunities(section_data)

        assert fontes == []
        assert opps == []
        assert titles == []

    def test_extract_with_missing_oportunidades(self):
        """Test extraction when fonte has no oportunidades key."""
        section_data = {
            'fontes_analisadas': [
                {'titulo_original': 'Artigo sem oportunidades'}
            ]
        }

        fontes, opps, titles = extract_from_opportunities(section_data)

        assert len(fontes) == 1
        assert opps == []
        assert titles == ['Artigo sem oportunidades']


class TestNormalizeSectionStructure:
    """Tests for normalize_section_structure function."""

    def test_normalize_dict_sections(self):
        """Test that dict sections remain unchanged."""
        context_data = {
            'mercado': {'panorama': 'Test'},
            'concorrencia': {'principais': []},
        }

        result = normalize_section_structure(context_data)

        assert isinstance(result['mercado'], dict)
        assert isinstance(result['concorrencia'], dict)
        assert result['mercado']['panorama'] == 'Test'

    def test_normalize_list_to_dict(self):
        """Test that list sections are converted to dict."""
        context_data = {
            'mercado': [{'panorama': 'Test from list'}],
            'tendencias': [],
        }

        result = normalize_section_structure(context_data)

        assert isinstance(result['mercado'], dict)
        assert result['mercado']['panorama'] == 'Test from list'
        assert isinstance(result['tendencias'], dict)
        assert result['tendencias'] == {}

    def test_normalize_string_to_dict(self):
        """Test that string sections are converted to empty dict."""
        context_data = {
            'mercado': 'invalid string value',
        }

        result = normalize_section_structure(context_data)

        assert isinstance(result['mercado'], dict)
        assert result['mercado'] == {}

    def test_normalize_preserves_other_keys(self):
        """Test that non-section keys are preserved."""
        context_data = {
            'mercado': {'test': 'value'},
            'custom_key': 'should remain',
        }

        result = normalize_section_structure(context_data)

        assert result['custom_key'] == 'should remain'


class TestGenerateHashtagsFromOpportunities:
    """Tests for generate_hashtags_from_opportunities function."""

    def test_generate_hashtags_basic(self):
        """Test basic hashtag generation."""
        opportunities = [
            {'titulo_ideia': 'Marketing Digital Avancado', 'tipo': 'Viral'},
            {'titulo_ideia': 'Tendencias Tech', 'tipo': 'Educativo'},
        ]

        hashtags = generate_hashtags_from_opportunities(opportunities)

        assert isinstance(hashtags, list)
        assert len(hashtags) <= 15  # max_hashtags default
        assert any('#Marketing' in h for h in hashtags)
        assert any('#Viral' in h for h in hashtags)

    def test_generate_hashtags_empty_list(self):
        """Test hashtag generation with empty list."""
        hashtags = generate_hashtags_from_opportunities([])

        assert hashtags == []

    def test_generate_hashtags_max_limit(self):
        """Test that max_hashtags limit is respected."""
        opportunities = [
            {'titulo_ideia': f'Palavra{i} Teste{i}', 'tipo': f'Tipo{i}'}
            for i in range(20)
        ]

        hashtags = generate_hashtags_from_opportunities(opportunities, max_hashtags=5)

        assert len(hashtags) <= 5

    def test_generate_hashtags_filters_short_words(self):
        """Test that short words are filtered out."""
        opportunities = [
            {'titulo_ideia': 'A de um', 'tipo': ''},
        ]

        hashtags = generate_hashtags_from_opportunities(opportunities)

        # Words with 3 or fewer chars should be filtered
        assert not any(len(h.replace('#', '')) <= 3 for h in hashtags)


class TestGenerateKeywordsFromOpportunities:
    """Tests for generate_keywords_from_opportunities function."""

    def test_generate_keywords_basic(self):
        """Test basic keyword generation."""
        opportunities = [
            {'titulo_ideia': 'Marketing Digital', 'gatilho_criativo': 'Engajamento'},
            {'titulo_ideia': 'Tendencias 2024', 'gatilho_criativo': 'Inovacao'},
        ]

        keywords = generate_keywords_from_opportunities(opportunities)

        assert isinstance(keywords, list)
        assert 'Marketing Digital' in keywords
        assert 'Engajamento' in keywords

    def test_generate_keywords_empty_list(self):
        """Test keyword generation with empty list."""
        keywords = generate_keywords_from_opportunities([])

        assert keywords == []

    def test_generate_keywords_max_limit(self):
        """Test that max_keywords limit is respected."""
        opportunities = [
            {'titulo_ideia': f'Titulo {i}', 'gatilho_criativo': f'Gatilho {i}'}
            for i in range(20)
        ]

        keywords = generate_keywords_from_opportunities(opportunities, max_keywords=5)

        assert len(keywords) <= 5

    def test_generate_keywords_handles_missing_fields(self):
        """Test keyword generation when fields are missing."""
        opportunities = [
            {'titulo_ideia': 'Apenas Titulo'},
            {'gatilho_criativo': 'Apenas Gatilho'},
            {},
        ]

        keywords = generate_keywords_from_opportunities(opportunities)

        assert 'Apenas Titulo' in keywords
        assert 'Apenas Gatilho' in keywords
