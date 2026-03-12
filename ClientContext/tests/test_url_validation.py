"""
Testes para utilitários de validação de URL.

Estes testes verificam:
- Validação síncrona de formato de URL
- Validação com requisições HTTP (mocked)
- Comportamento em caso de erro (deve retornar True - presunção de inocência)
"""

from unittest.mock import patch, MagicMock

from django.test import TestCase

from ClientContext.utils.url_validation import (
    coerce_url_to_str,
    recover_url,
    _is_soft_404,
    validate_url_sync,
)


class CoerceUrlToStrTestCase(TestCase):
    """Testes para coerção de valores para URL string."""

    def test_string_retorna_string(self):
        self.assertEqual(coerce_url_to_str("https://example.com"), "https://example.com")

    def test_none_retorna_vazio(self):
        self.assertEqual(coerce_url_to_str(None), "")

    def test_dict_com_url_retorna_url(self):
        self.assertEqual(coerce_url_to_str({"url": "https://example.com"}), "https://example.com")

    def test_dict_com_link_retorna_link(self):
        self.assertEqual(coerce_url_to_str({"link": "https://example.com"}), "https://example.com")

    def test_dict_vazio_retorna_vazio(self):
        self.assertEqual(coerce_url_to_str({}), "")

    def test_lista_retorna_primeiro_item(self):
        self.assertEqual(coerce_url_to_str(["https://a.com", "https://b.com"]), "https://a.com")

    def test_lista_vazia_retorna_vazio(self):
        self.assertEqual(coerce_url_to_str([]), "")


class RecoverUrlTestCase(TestCase):
    """Testes para recuperação de URL alucinada."""

    def test_match_exato(self):
        result = recover_url("https://example.com", ["https://example.com"])
        self.assertEqual(result, "https://example.com")

    def test_match_parcial(self):
        result = recover_url(
            "https://example.com/article?utm=123",
            ["https://example.com/article"]
        )
        self.assertEqual(result, "https://example.com/article")

    def test_sem_match_retorna_original(self):
        result = recover_url("https://hallucinated.com", ["https://real.com"])
        self.assertEqual(result, "https://hallucinated.com")

    def test_url_vazia_retorna_vazio(self):
        self.assertEqual(recover_url("", ["https://real.com"]), "")

    def test_none_retorna_vazio(self):
        self.assertEqual(recover_url(None, []), "")


class IsSoft404TestCase(TestCase):
    """Testes para detecção de soft 404."""

    def test_linkedin_not_found(self):
        self.assertTrue(_is_soft_404(
            "https://linkedin.com/pulse?trk=article_not_found",
            "Some content"
        ))

    def test_pagina_nao_encontrada(self):
        self.assertTrue(_is_soft_404("https://example.com", "Página não encontrada"))

    def test_page_not_found(self):
        self.assertTrue(_is_soft_404("https://example.com", "Page not found"))

    def test_pagina_normal(self):
        self.assertFalse(_is_soft_404("https://example.com", "Welcome to our site"))

    def test_body_vazio(self):
        self.assertFalse(_is_soft_404("https://example.com", ""))


class ValidateUrlSyncTestCase(TestCase):
    """Testes para validação síncrona de URL."""

    @patch('ClientContext.utils.url_validation.requests')
    def test_url_valida_200_retorna_true(self, mock_requests):
        mock_head = MagicMock()
        mock_head.status_code = 200
        mock_requests.head.return_value = mock_head

        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.url = "https://example.com"
        mock_get.text = "Normal page"
        mock_requests.get.return_value = mock_get

        self.assertTrue(validate_url_sync("https://example.com"))

    @patch('ClientContext.utils.url_validation.requests')
    def test_url_404_retorna_false(self, mock_requests):
        mock_head = MagicMock()
        mock_head.status_code = 404
        mock_requests.head.return_value = mock_head

        self.assertFalse(validate_url_sync("https://example.com/not-found"))

    @patch('ClientContext.utils.url_validation.requests')
    def test_timeout_retorna_true(self, mock_requests):
        """Timeout = presunção de inocência, retorna True."""
        import requests
        mock_requests.head.side_effect = requests.exceptions.Timeout()
        mock_requests.exceptions = requests.exceptions

        self.assertTrue(validate_url_sync("https://slow-site.com"))

    @patch('ClientContext.utils.url_validation.requests')
    def test_connection_error_retorna_true(self, mock_requests):
        """Connection error = presunção de inocência, retorna True."""
        import requests
        mock_requests.head.side_effect = requests.exceptions.ConnectionError()
        mock_requests.exceptions = requests.exceptions

        self.assertTrue(validate_url_sync("https://blocked-site.com"))

    @patch('ClientContext.utils.url_validation.requests')
    def test_soft_404_retorna_false(self, mock_requests):
        mock_head = MagicMock()
        mock_head.status_code = 200
        mock_requests.head.return_value = mock_head

        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.url = "https://linkedin.com/pulse?trk=article_not_found"
        mock_get.text = "we can't find the page you're looking for"
        mock_requests.get.return_value = mock_get

        self.assertFalse(validate_url_sync("https://linkedin.com/pulse/article"))
