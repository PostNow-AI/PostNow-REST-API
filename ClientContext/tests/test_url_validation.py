"""
Testes para utilitários de validação de URL.

Estes testes verificam:
- Validação síncrona de formato de URL
- Validação assíncrona com requisições HTTP
- Comportamento em caso de erro (deve retornar False)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import TestCase

from ClientContext.utils.url_validation import (
    _validate_with_get,
    validate_url_permissive_async,
    validate_url_sync,
)


def run_async(coro):
    """Helper para executar funções async em testes."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class ValidateUrlSyncTestCase(TestCase):
    """Testes para validação síncrona de URL."""

    def test_url_https_valida_retorna_true(self):
        """Teste: URL HTTPS válida retorna True"""
        self.assertTrue(validate_url_sync("https://example.com"))

    def test_url_http_valida_retorna_true(self):
        """Teste: URL HTTP válida retorna True"""
        self.assertTrue(validate_url_sync("http://example.com"))

    def test_url_com_path_retorna_true(self):
        """Teste: URL com path retorna True"""
        self.assertTrue(validate_url_sync("https://example.com/path/to/page"))

    def test_url_sem_scheme_retorna_false(self):
        """Teste: URL sem scheme retorna False"""
        self.assertFalse(validate_url_sync("example.com"))

    def test_url_sem_netloc_retorna_false(self):
        """Teste: URL sem netloc retorna False"""
        self.assertFalse(validate_url_sync("https://"))

    def test_string_vazia_retorna_false(self):
        """Teste: string vazia retorna False"""
        self.assertFalse(validate_url_sync(""))

    def test_string_aleatoria_retorna_false(self):
        """Teste: string não-URL retorna False"""
        self.assertFalse(validate_url_sync("not-a-url"))

    def test_none_retorna_false(self):
        """Teste: None retorna False (via exception)"""
        self.assertFalse(validate_url_sync(None))


class ValidateUrlPermissiveAsyncTestCase(TestCase):
    """Testes para validação assíncrona de URL."""

    def test_formato_invalido_retorna_false(self):
        """Teste: formato de URL inválido retorna False sem chamada de rede"""
        result = run_async(validate_url_permissive_async("not-a-url"))
        self.assertFalse(result)

    def test_url_vazia_retorna_false(self):
        """Teste: URL vazia retorna False"""
        result = run_async(validate_url_permissive_async(""))
        self.assertFalse(result)

    def test_scheme_invalido_retorna_false(self):
        """Teste: scheme não-HTTP retorna False"""
        result = run_async(validate_url_permissive_async("ftp://example.com"))
        self.assertFalse(result)

    @patch('ClientContext.utils.url_validation.aiohttp.ClientSession')
    def test_head_sucesso_retorna_true(self, mock_session_class):
        """Teste: requisição HEAD com sucesso (2xx) retorna True"""
        # Configurar mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_session_class.return_value = mock_session

        result = run_async(validate_url_permissive_async("https://example.com"))
        self.assertTrue(result)

    @patch('ClientContext.utils.url_validation.aiohttp.ClientSession')
    def test_404_retorna_false(self, mock_session_class):
        """Teste: resposta 404 retorna False"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_session_class.return_value = mock_session

        result = run_async(validate_url_permissive_async("https://example.com"))
        self.assertFalse(result)

    @patch('ClientContext.utils.url_validation.aiohttp.ClientSession')
    def test_redirect_3xx_retorna_true(self, mock_session_class):
        """Teste: resposta 3xx redirect retorna True"""
        mock_response = AsyncMock()
        mock_response.status = 301
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_session_class.return_value = mock_session

        result = run_async(validate_url_permissive_async("https://example.com"))
        self.assertTrue(result)

    @patch('ClientContext.utils.url_validation.aiohttp.ClientSession')
    def test_exception_retorna_false(self, mock_session_class):
        """Teste: exception durante request retorna False (correção crítica)"""
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("Network error"))
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_session_class.return_value = mock_session

        result = run_async(validate_url_permissive_async("https://example.com"))
        # IMPORTANTE: Este é o teste da correção - antes retornava True
        self.assertFalse(result)


class ValidateWithGetTestCase(TestCase):
    """Testes para validação via GET (fallback)."""

    def test_get_sucesso_retorna_true(self):
        """Teste: requisição GET com sucesso retorna True"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        result = run_async(_validate_with_get(mock_session, "https://example.com"))
        self.assertTrue(result)

    def test_403_retorna_true(self):
        """Teste: 403 (rate limit) retorna True (assume válido)"""
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        result = run_async(_validate_with_get(mock_session, "https://example.com"))
        self.assertTrue(result)

    def test_500_retorna_false(self):
        """Teste: erro 500 retorna False"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        result = run_async(_validate_with_get(mock_session, "https://example.com"))
        self.assertFalse(result)

    def test_exception_retorna_false(self):
        """Teste: exception durante GET retorna False (correção crítica)"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        result = run_async(_validate_with_get(mock_session, "https://example.com"))
        # IMPORTANTE: Este é o teste da correção - antes retornava True
        self.assertFalse(result)
