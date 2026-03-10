"""
Testes unitários para batch_validation.py

Testa as funções de validação extraídas de views.py.
"""
import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from ClientContext.utils.batch_validation import (
    BATCH_API_TOKEN,
    MAX_BATCH_NUMBER,
    MIN_BATCH_NUMBER,
    SINGLE_CONTEXT_RATE_LIMIT_SECONDS,
    validate_batch_number,
    validate_batch_token,
)


class TestValidateBatchToken(TestCase):
    """Testes para validate_batch_token()"""

    def _create_mock_request(self, auth_header: str = None) -> MagicMock:
        """Helper para criar mock de request."""
        request = MagicMock()
        request.headers = {}
        if auth_header:
            request.headers['Authorization'] = auth_header
        return request

    @patch.dict(os.environ, {'CRON_SECRET': ''}, clear=False)
    def test_returns_true_when_no_token_configured(self):
        """Sem token configurado (desenvolvimento), permite acesso."""
        # Reimportar para pegar novo valor
        with patch('ClientContext.utils.batch_validation.BATCH_API_TOKEN', ''):
            request = self._create_mock_request()
            result = validate_batch_token(request)
            self.assertTrue(result)

    @patch('ClientContext.utils.batch_validation.BATCH_API_TOKEN', 'secret123')
    def test_returns_true_with_valid_token(self):
        """Token válido retorna True."""
        request = self._create_mock_request('Bearer secret123')
        result = validate_batch_token(request)
        self.assertTrue(result)

    @patch('ClientContext.utils.batch_validation.BATCH_API_TOKEN', 'secret123')
    def test_returns_false_with_invalid_token(self):
        """Token inválido retorna False."""
        request = self._create_mock_request('Bearer wrongtoken')
        result = validate_batch_token(request)
        self.assertFalse(result)

    @patch('ClientContext.utils.batch_validation.BATCH_API_TOKEN', 'secret123')
    def test_returns_false_without_bearer_prefix(self):
        """Token sem prefixo 'Bearer ' retorna False."""
        request = self._create_mock_request('secret123')
        result = validate_batch_token(request)
        self.assertFalse(result)

    @patch('ClientContext.utils.batch_validation.BATCH_API_TOKEN', 'secret123')
    def test_returns_false_without_auth_header(self):
        """Sem header Authorization retorna False."""
        request = self._create_mock_request()
        result = validate_batch_token(request)
        self.assertFalse(result)

    @patch('ClientContext.utils.batch_validation.BATCH_API_TOKEN', 'secret123')
    def test_returns_false_with_empty_auth_header(self):
        """Header Authorization vazio retorna False."""
        request = self._create_mock_request('')
        result = validate_batch_token(request)
        self.assertFalse(result)


class TestValidateBatchNumber(TestCase):
    """Testes para validate_batch_number()"""

    def test_valid_number_in_range(self):
        """Número válido dentro do range retorna o próprio número."""
        self.assertEqual(validate_batch_number('5'), 5)
        self.assertEqual(validate_batch_number('50'), 50)
        self.assertEqual(validate_batch_number('99'), 99)

    def test_returns_min_when_below_range(self):
        """Número abaixo do mínimo retorna MIN_BATCH_NUMBER."""
        self.assertEqual(validate_batch_number('0'), MIN_BATCH_NUMBER)
        self.assertEqual(validate_batch_number('-1'), MIN_BATCH_NUMBER)
        self.assertEqual(validate_batch_number('-100'), MIN_BATCH_NUMBER)

    def test_returns_max_when_above_range(self):
        """Número acima do máximo retorna MAX_BATCH_NUMBER."""
        self.assertEqual(validate_batch_number('101'), MAX_BATCH_NUMBER)
        self.assertEqual(validate_batch_number('999'), MAX_BATCH_NUMBER)
        self.assertEqual(validate_batch_number('1000000'), MAX_BATCH_NUMBER)

    def test_boundary_values(self):
        """Testa valores nos limites."""
        self.assertEqual(validate_batch_number('1'), MIN_BATCH_NUMBER)
        self.assertEqual(validate_batch_number('100'), MAX_BATCH_NUMBER)

    def test_returns_1_for_invalid_string(self):
        """String não numérica retorna 1."""
        self.assertEqual(validate_batch_number('abc'), 1)
        self.assertEqual(validate_batch_number(''), 1)
        self.assertEqual(validate_batch_number('1.5'), 1)
        self.assertEqual(validate_batch_number('one'), 1)

    def test_returns_1_for_none(self):
        """None retorna 1."""
        self.assertEqual(validate_batch_number(None), 1)

    def test_handles_whitespace(self):
        """Strings com espaços são aceitas (int() faz strip)."""
        self.assertEqual(validate_batch_number(' 5 '), 5)
        self.assertEqual(validate_batch_number('  '), 1)  # Só espaços = inválido


class TestConstants(TestCase):
    """Testes para constantes exportadas."""

    def test_rate_limit_is_5_minutes(self):
        """Rate limit deve ser 5 minutos (300 segundos)."""
        self.assertEqual(SINGLE_CONTEXT_RATE_LIMIT_SECONDS, 300)

    def test_batch_limits(self):
        """Limites de batch devem ser 1-100."""
        self.assertEqual(MIN_BATCH_NUMBER, 1)
        self.assertEqual(MAX_BATCH_NUMBER, 100)
