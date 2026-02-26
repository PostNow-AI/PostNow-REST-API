"""
Testes unitarios para o ContextEnrichmentService.

Estes testes verificam:
- Construcao de queries de busca
- Filtragem e deduplicacao de URLs
- Enriquecimento de oportunidades
- Tratamento de erros
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from ClientContext.models import ClientContext
from ClientContext.services.context_enrichment_service import (
    CATEGORY_TO_SECTION,
    ENRICHMENT_SOURCES_PER_OPPORTUNITY,
    ContextEnrichmentService,
)
from ClientContext.utils.source_quality import is_denied, score_source
from ClientContext.utils.url_dedupe import normalize_url_key

User = get_user_model()


def create_test_user(email, password="testpass123"):
    """Helper para criar usuario de teste"""
    username = email.split("@")[0]
    return User.objects.create_user(
        username=username,
        email=email,
        password=password
    )


class UrlDedupeTestCase(TestCase):
    """Testes para a funcao normalize_url_key"""

    def test_normalize_removes_querystring(self):
        """Teste: querystring e removida"""
        url = "https://example.com/page?utm_source=google"
        key = normalize_url_key(url)
        self.assertEqual(key, "example.com/page")

    def test_normalize_removes_fragment(self):
        """Teste: fragment e removido"""
        url = "https://example.com/page#section"
        key = normalize_url_key(url)
        self.assertEqual(key, "example.com/page")

    def test_normalize_lowercase_domain(self):
        """Teste: dominio e convertido para lowercase"""
        url = "https://EXAMPLE.COM/Page"
        key = normalize_url_key(url)
        # Domain lowercase, path preserva case na comparacao
        self.assertTrue(key.startswith("example.com"))

    def test_normalize_removes_trailing_slash(self):
        """Teste: barra final e removida (exceto raiz)"""
        url = "https://example.com/page/"
        key = normalize_url_key(url)
        self.assertEqual(key, "example.com/page")

    def test_normalize_root_keeps_slash(self):
        """Teste: raiz mantem a barra"""
        url = "https://example.com/"
        key = normalize_url_key(url)
        self.assertEqual(key, "example.com/")

    def test_normalize_empty_url(self):
        """Teste: URL vazia retorna string vazia"""
        self.assertEqual(normalize_url_key(""), "")
        self.assertEqual(normalize_url_key(None), "")


class SourceQualityTestCase(TestCase):
    """Testes para funcoes de qualidade de fonte"""

    def test_is_denied_blocks_spam_domains(self):
        """Teste: dominios de spam sao bloqueados"""
        # Dominios comumente bloqueados
        spam_urls = [
            "https://youtube.com/watch?v=123",
            "https://facebook.com/post/123",
            "https://instagram.com/p/abc",
            "https://twitter.com/user/status/123",
        ]
        # Pelo menos alguns devem ser bloqueados pelo denylist
        blocked_count = sum(1 for url in spam_urls if is_denied(url))
        # Esperamos que redes sociais sejam bloqueadas
        self.assertGreater(blocked_count, 0)

    def test_score_source_returns_numeric(self):
        """Teste: score_source retorna valor numerico"""
        url = "https://forbes.com/article/test"
        score = score_source("mercado", url)
        self.assertIsInstance(score, (int, float))

    def test_score_source_allowlist_boost(self):
        """Teste: sites na allowlist tem score maior"""
        # URLs de fontes confiaveis devem ter score positivo
        trusted_url = "https://forbes.com.br/negocios/test"
        spam_url = "https://random-unknown-site.xyz/article"

        trusted_score = score_source("mercado", trusted_url)
        unknown_score = score_source("mercado", spam_url)

        # Trusted deve ter score maior ou igual
        self.assertGreaterEqual(trusted_score, unknown_score)


class BuildSearchQueryTestCase(TestCase):
    """Testes para construcao de queries de busca"""

    def setUp(self):
        """Configuracao inicial"""
        self.service = ContextEnrichmentService(
            google_search_service=MagicMock(),
            ai_service=MagicMock(),
            semaphore_service=MagicMock(),
        )

    def test_build_query_with_titulo_only(self):
        """Teste: query apenas com titulo"""
        opportunity = {"titulo_ideia": "Inteligencia artificial no marketing"}
        query = self.service._build_search_query(opportunity)
        self.assertIn("Inteligencia artificial", query)

    def test_build_query_removes_emojis_from_tipo(self):
        """Teste: emojis sao removidos do tipo"""
        opportunity = {
            "titulo_ideia": "Nova tendencia",
            "tipo": "Polemica"
        }
        query = self.service._build_search_query(opportunity)
        self.assertNotIn("", query)

    def test_build_query_includes_tipo_if_different(self):
        """Teste: tipo e incluido se diferente do titulo"""
        opportunity = {
            "titulo_ideia": "Tendencia de mercado",
            "tipo": "Estudo de caso"
        }
        query = self.service._build_search_query(opportunity)
        self.assertIn("Tendencia de mercado", query)


class CategoryMappingTestCase(TestCase):
    """Testes para mapeamento de categorias"""

    def test_all_categories_have_section(self):
        """Teste: todas as categorias esperadas tem mapeamento"""
        expected_categories = [
            'polemica', 'educativo', 'newsjacking',
            'entretenimento', 'estudo_caso', 'futuro', 'outros'
        ]
        for category in expected_categories:
            self.assertIn(category, CATEGORY_TO_SECTION)

    def test_sections_are_valid(self):
        """Teste: secoes mapeadas sao validas"""
        valid_sections = {'tendencias', 'mercado', 'concorrencia'}
        for section in CATEGORY_TO_SECTION.values():
            self.assertIn(section, valid_sections)


class EnrichOpportunityTestCase(TestCase):
    """Testes para enriquecimento de oportunidade individual"""

    def setUp(self):
        """Configuracao inicial"""
        self.user = create_test_user("enrich_test@example.com")

        # Mock services
        self.mock_google = MagicMock()
        self.mock_ai = MagicMock()
        self.mock_semaphore = MagicMock()

        self.service = ContextEnrichmentService(
            google_search_service=self.mock_google,
            ai_service=self.mock_ai,
            semaphore_service=self.mock_semaphore,
        )

    def test_enrich_empty_titulo_returns_unchanged(self):
        """Teste: oportunidade sem titulo retorna sem mudancas"""
        opportunity = {"score": 85}

        result = asyncio.get_event_loop().run_until_complete(
            self.service._enrich_opportunity(opportunity, self.user, "mercado", set())
        )

        self.assertEqual(result, opportunity)

    @patch('ClientContext.services.context_enrichment_service.validate_url_permissive_async')
    def test_enrich_adds_enriched_sources(self, mock_validate):
        """Teste: enriquecimento adiciona enriched_sources"""
        mock_validate.return_value = True

        # Setup mock Google search results
        self.mock_google.search.return_value = [
            {"url": "https://forbes.com/article1", "title": "Artigo 1", "snippet": "Snippet 1"},
            {"url": "https://exame.com/article2", "title": "Artigo 2", "snippet": "Snippet 2"},
        ]

        # Setup mock AI response
        self.mock_ai.generate_text.return_value = "Analise gerada"

        opportunity = {
            "titulo_ideia": "Teste de tendencia",
            "tipo": "Educativo",
            "score": 90
        }

        result = asyncio.get_event_loop().run_until_complete(
            self.service._enrich_opportunity(opportunity, self.user, "tendencias", set())
        )

        self.assertIn("enriched_sources", result)
        self.assertIn("enriched_analysis", result)

    def test_enrich_handles_google_error(self):
        """Teste: trata erro do Google Search gracefully"""
        self.mock_google.search.side_effect = Exception("API Error")

        opportunity = {
            "titulo_ideia": "Teste de erro",
            "tipo": "Polemica",
            "score": 80
        }

        result = asyncio.get_event_loop().run_until_complete(
            self.service._enrich_opportunity(opportunity, self.user, "tendencias", set())
        )

        # Deve retornar listas vazias em vez de erro
        self.assertEqual(result.get("enriched_sources"), [])
        self.assertEqual(result.get("enriched_analysis"), "")


class FetchAndFilterSourcesTestCase(TestCase):
    """Testes para busca e filtragem de fontes"""

    def setUp(self):
        """Configuracao inicial"""
        self.mock_google = MagicMock()
        self.mock_ai = MagicMock()
        self.mock_semaphore = MagicMock()

        self.service = ContextEnrichmentService(
            google_search_service=self.mock_google,
            ai_service=self.mock_ai,
            semaphore_service=self.mock_semaphore,
        )

    @patch('ClientContext.services.context_enrichment_service.validate_url_permissive_async')
    def test_fetch_respects_limit(self, mock_validate):
        """Teste: busca respeita limite de fontes"""
        mock_validate.return_value = True

        # Return more results than needed
        self.mock_google.search.return_value = [
            {"url": f"https://example{i}.com/article", "title": f"Article {i}", "snippet": f"Snippet {i}"}
            for i in range(10)
        ]

        result = asyncio.get_event_loop().run_until_complete(
            self.service._fetch_and_filter_sources("test query", "mercado", set())
        )

        self.assertLessEqual(len(result), ENRICHMENT_SOURCES_PER_OPPORTUNITY)

    @patch('ClientContext.services.context_enrichment_service.validate_url_permissive_async')
    def test_fetch_skips_duplicate_urls(self, mock_validate):
        """Teste: busca pula URLs duplicadas"""
        mock_validate.return_value = True

        self.mock_google.search.return_value = [
            {"url": "https://example.com/article", "title": "Article", "snippet": "Snippet"},
            {"url": "https://other.com/article", "title": "Other Article", "snippet": "Other Snippet"},
        ]

        # Pre-add URL to used set
        used_urls = {normalize_url_key("https://example.com/article")}

        result = asyncio.get_event_loop().run_until_complete(
            self.service._fetch_and_filter_sources("test query", "mercado", used_urls)
        )

        # Should only return the non-duplicate URL
        result_urls = [r["url"] for r in result]
        self.assertNotIn("https://example.com/article", result_urls)

    def test_fetch_empty_results(self):
        """Teste: busca com resultados vazios retorna lista vazia"""
        self.mock_google.search.return_value = []

        result = asyncio.get_event_loop().run_until_complete(
            self.service._fetch_and_filter_sources("test query", "mercado", set())
        )

        self.assertEqual(result, [])


class EnrichAllCategoriesTestCase(TestCase):
    """Testes para enriquecimento de todas as categorias"""

    def setUp(self):
        """Configuracao inicial"""
        self.user = create_test_user("categories_test@example.com")

        self.mock_google = MagicMock()
        self.mock_google.search.return_value = []

        self.mock_ai = MagicMock()
        self.mock_semaphore = MagicMock()

        self.service = ContextEnrichmentService(
            google_search_service=self.mock_google,
            ai_service=self.mock_ai,
            semaphore_service=self.mock_semaphore,
        )

    def test_enrich_preserves_non_dict_categories(self):
        """Teste: categorias nao-dict sao preservadas"""
        tendencies_data = {
            "polemica": {"items": []},
            "metadata": "some_string_value"
        }

        result = asyncio.get_event_loop().run_until_complete(
            self.service._enrich_all_categories(tendencies_data, self.user, set())
        )

        self.assertEqual(result["metadata"], "some_string_value")

    def test_enrich_processes_only_top_3_items(self):
        """Teste: apenas top 3 items sao processados por categoria"""
        tendencies_data = {
            "polemica": {
                "titulo": "Polemicas",
                "items": [
                    {"titulo_ideia": f"Item {i}", "score": 100 - i}
                    for i in range(5)  # 5 items
                ]
            }
        }

        result = asyncio.get_event_loop().run_until_complete(
            self.service._enrich_all_categories(tendencies_data, self.user, set())
        )

        # Only 3 items should be in the result
        self.assertEqual(len(result["polemica"]["items"]), 3)


class EnrichUserContextTestCase(TestCase):
    """Testes para enriquecimento de contexto de usuario"""

    def setUp(self):
        """Configuracao inicial"""
        self.user = create_test_user("user_context_test@example.com")

        # Create ClientContext
        self.client_context = ClientContext.objects.create(
            user=self.user,
            context_enrichment_status='pending'
        )

        self.mock_google = MagicMock()
        self.mock_google.search.return_value = []

        self.mock_ai = MagicMock()
        self.mock_semaphore = MagicMock()

        self.service = ContextEnrichmentService(
            google_search_service=self.mock_google,
            ai_service=self.mock_ai,
            semaphore_service=self.mock_semaphore,
        )

    def test_enrich_empty_tendencies_marks_enriched(self):
        """Teste: tendencies_data vazio marca como enriched"""
        context_data = {"tendencies_data": {}}

        result = asyncio.get_event_loop().run_until_complete(
            self.service.enrich_user_context(self.user, context_data)
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "No opportunities to enrich")

        # Verify status was updated
        self.client_context.refresh_from_db()
        self.assertEqual(self.client_context.context_enrichment_status, "enriched")

    def test_enrich_updates_status_on_success(self):
        """Teste: status e atualizado apos sucesso"""
        context_data = {
            "tendencies_data": {
                "polemica": {
                    "titulo": "Polemicas",
                    "items": [{"titulo_ideia": "Teste", "score": 90}]
                }
            }
        }

        result = asyncio.get_event_loop().run_until_complete(
            self.service.enrich_user_context(self.user, context_data)
        )

        self.assertEqual(result["status"], "success")

        self.client_context.refresh_from_db()
        self.assertEqual(self.client_context.context_enrichment_status, "enriched")


class EnrichAllUsersContextTestCase(TestCase):
    """Testes para enriquecimento de contexto de todos os usuarios"""

    def setUp(self):
        """Configuracao inicial"""
        self.mock_google = MagicMock()
        self.mock_google.search.return_value = []

        self.mock_ai = MagicMock()
        self.mock_semaphore = MagicMock()

        self.service = ContextEnrichmentService(
            google_search_service=self.mock_google,
            ai_service=self.mock_ai,
            semaphore_service=self.mock_semaphore,
        )

    def test_no_pending_contexts_returns_completed(self):
        """Teste: sem contextos pendentes retorna completed"""
        # Ensure no pending contexts
        ClientContext.objects.filter(context_enrichment_status='pending').delete()

        result = asyncio.get_event_loop().run_until_complete(
            self.service.enrich_all_users_context(batch_number=1, batch_size=10)
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["processed"], 0)

    def test_batch_pagination_works(self):
        """Teste: paginacao por batch funciona"""
        # Create multiple users with pending contexts
        for i in range(5):
            user = create_test_user(f"batch_test_{i}@example.com")
            ClientContext.objects.create(
                user=user,
                context_enrichment_status='pending'
            )

        # Process batch 1 with size 2
        result = asyncio.get_event_loop().run_until_complete(
            self.service.enrich_all_users_context(batch_number=1, batch_size=2)
        )

        # Should process only 2 contexts
        self.assertEqual(result["total_contexts"], 2)
