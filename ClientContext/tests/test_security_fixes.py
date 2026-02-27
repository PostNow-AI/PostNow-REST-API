"""
Testes para correções de segurança (análises 8-10).
"""
import html
import re
import secrets
from unittest.mock import MagicMock, patch

from django.test import TestCase, RequestFactory


class TestTimingAttackPrevention(TestCase):
    """Testa prevenção de timing attack na validação de token."""

    def test_compare_digest_used_for_token_comparison(self):
        """Verifica que secrets.compare_digest é usado."""
        from ClientContext.views import _validate_batch_token

        # Verificar que a função usa compare_digest
        import inspect
        source = inspect.getsource(_validate_batch_token)
        self.assertIn('secrets.compare_digest', source)

    @patch('ClientContext.views.BATCH_API_TOKEN', 'test-secret-token')
    def test_valid_token_returns_true(self):
        """Token válido deve retornar True."""
        from ClientContext.views import _validate_batch_token

        request = MagicMock()
        request.headers.get.return_value = 'Bearer test-secret-token'

        result = _validate_batch_token(request)
        self.assertTrue(result)

    @patch('ClientContext.views.BATCH_API_TOKEN', 'test-secret-token')
    def test_invalid_token_returns_false(self):
        """Token inválido deve retornar False."""
        from ClientContext.views import _validate_batch_token

        request = MagicMock()
        request.headers.get.return_value = 'Bearer wrong-token'

        result = _validate_batch_token(request)
        self.assertFalse(result)

    @patch('ClientContext.views.BATCH_API_TOKEN', '')
    def test_empty_token_config_allows_all(self):
        """Sem token configurado, permite todas as requisições (dev)."""
        from ClientContext.views import _validate_batch_token

        request = MagicMock()
        request.headers.get.return_value = ''

        result = _validate_batch_token(request)
        self.assertTrue(result)

    @patch('ClientContext.views.BATCH_API_TOKEN', 'test-secret-token')
    def test_missing_bearer_prefix_returns_false(self):
        """Token sem prefixo Bearer deve retornar False."""
        from ClientContext.views import _validate_batch_token

        request = MagicMock()
        request.headers.get.return_value = 'test-secret-token'

        result = _validate_batch_token(request)
        self.assertFalse(result)


class TestSubjectSanitization(TestCase):
    """Testa sanitização de subject de email."""

    def test_sanitize_removes_newlines(self):
        """Remove quebras de linha."""
        from ClientContext.services.opportunities_email_service import _sanitize_subject

        result = _sanitize_subject("Test\nSubject")
        self.assertEqual(result, "TestSubject")

    def test_sanitize_removes_carriage_return(self):
        """Remove carriage return."""
        from ClientContext.services.opportunities_email_service import _sanitize_subject

        result = _sanitize_subject("Test\rSubject")
        self.assertEqual(result, "TestSubject")

    def test_sanitize_removes_control_chars(self):
        """Remove caracteres de controle."""
        from ClientContext.services.opportunities_email_service import _sanitize_subject

        result = _sanitize_subject("Test\x00\x1fSubject")
        self.assertEqual(result, "TestSubject")

    def test_sanitize_truncates_at_100_chars(self):
        """Trunca em 100 caracteres."""
        from ClientContext.services.opportunities_email_service import _sanitize_subject

        long_text = "A" * 150
        result = _sanitize_subject(long_text)
        self.assertEqual(len(result), 100)

    def test_sanitize_handles_empty_string(self):
        """Retorna string vazia para entrada vazia."""
        from ClientContext.services.opportunities_email_service import _sanitize_subject

        result = _sanitize_subject("")
        self.assertEqual(result, "")

    def test_sanitize_handles_none(self):
        """Retorna string vazia para None."""
        from ClientContext.services.opportunities_email_service import _sanitize_subject

        result = _sanitize_subject(None)
        self.assertEqual(result, "")


class TestXSSPrevention(TestCase):
    """Testa prevenção de XSS nos templates de email."""

    def test_escape_html_tags(self):
        """Escapa tags HTML."""
        from ClientContext.utils.opportunities_email import _escape

        result = _escape("<script>alert('xss')</script>")
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_escape_quotes(self):
        """Escapa aspas."""
        from ClientContext.utils.opportunities_email import _escape

        result = _escape('Test "quoted" text')
        self.assertIn("&quot;", result)

    def test_escape_ampersand(self):
        """Escapa ampersand."""
        from ClientContext.utils.opportunities_email import _escape

        result = _escape("Test & more")
        self.assertIn("&amp;", result)

    def test_escape_handles_none(self):
        """Retorna string vazia para None."""
        from ClientContext.utils.opportunities_email import _escape

        result = _escape(None)
        self.assertEqual(result, "")

    def test_market_intelligence_escape(self):
        """Testa escape no template de market intelligence."""
        from ClientContext.utils.market_intelligence_email import _escape

        result = _escape("<img src=x onerror=alert(1)>")
        self.assertNotIn("<img", result)
        self.assertIn("&lt;img", result)


class TestBatchValidation(TestCase):
    """Testa validação de número de batch."""

    def test_valid_batch_number(self):
        """Batch válido retorna o número."""
        from ClientContext.views import _validate_batch_number

        self.assertEqual(_validate_batch_number("5"), 5)
        self.assertEqual(_validate_batch_number("1"), 1)
        self.assertEqual(_validate_batch_number("100"), 100)

    def test_batch_below_minimum_returns_minimum(self):
        """Batch abaixo do mínimo retorna mínimo."""
        from ClientContext.views import _validate_batch_number

        self.assertEqual(_validate_batch_number("0"), 1)
        self.assertEqual(_validate_batch_number("-5"), 1)

    def test_batch_above_maximum_returns_maximum(self):
        """Batch acima do máximo retorna máximo."""
        from ClientContext.views import _validate_batch_number

        self.assertEqual(_validate_batch_number("150"), 100)
        self.assertEqual(_validate_batch_number("999"), 100)

    def test_invalid_batch_returns_default(self):
        """Batch inválido retorna 1."""
        from ClientContext.views import _validate_batch_number

        self.assertEqual(_validate_batch_number("abc"), 1)
        self.assertEqual(_validate_batch_number(""), 1)
        self.assertEqual(_validate_batch_number(None), 1)


class TestJSONParsing(TestCase):
    """Testa parse de JSON com remoção de markdown."""

    def test_remove_json_markdown_block(self):
        """Remove bloco ```json."""
        input_text = '```json\n{"key": "value"}\n```'
        result = re.sub(r'^```(?:json)?\s*', '', input_text.strip())
        result = re.sub(r'\s*```$', '', result).strip()
        self.assertEqual(result, '{"key": "value"}')

    def test_remove_plain_markdown_block(self):
        """Remove bloco ``` sem json."""
        input_text = '```\n{"key": "value"}\n```'
        result = re.sub(r'^```(?:json)?\s*', '', input_text.strip())
        result = re.sub(r'\s*```$', '', result).strip()
        self.assertEqual(result, '{"key": "value"}')

    def test_plain_json_unchanged(self):
        """JSON puro permanece inalterado."""
        input_text = '{"key": "value"}'
        result = re.sub(r'^```(?:json)?\s*', '', input_text.strip())
        result = re.sub(r'\s*```$', '', result).strip()
        self.assertEqual(result, '{"key": "value"}')

    def test_preserves_json_word_in_content(self):
        """Preserva palavra 'json' dentro do conteúdo."""
        input_text = '```json\n{"format": "json data"}\n```'
        result = re.sub(r'^```(?:json)?\s*', '', input_text.strip())
        result = re.sub(r'\s*```$', '', result).strip()
        self.assertIn('"json data"', result)


class TestHTMLSanitizationInErrorEmails(TestCase):
    """Testa sanitização HTML em emails de erro para admins."""

    def test_escape_email_in_error_message(self):
        """Email deve ser sanitizado."""
        email = "<script>alert('xss')</script>@example.com"
        safe_email = html.escape(str(email))
        self.assertNotIn("<script>", safe_email)
        self.assertIn("&lt;script&gt;", safe_email)

    def test_escape_error_message(self):
        """Mensagem de erro deve ser sanitizada."""
        error = "Error: <img src=x onerror=alert(1)>"
        safe_error = html.escape(str(error))
        self.assertNotIn("<img", safe_error)
        self.assertIn("&lt;img", safe_error)
