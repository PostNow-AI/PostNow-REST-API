"""Testes unitarios para o modulo ClientContext."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from ClientContext.models import ClientContext
from ClientContext.serializers.context_serializer import WeeklyContextDataSerializer
from ClientContext.services.context_error_service import ContextErrorService
from ClientContext.services.context_stats_service import ContextStatsService
from ClientContext.utils.context_mapping import CONTEXT_FIELD_MAPPING
from ClientContext.utils.json_parser import extract_json_block, parse_ai_json_response


class TestContextMapping(TestCase):
    """Testes para o mapeamento de contexto."""

    def test_mapping_has_all_sections(self):
        """Verifica que todas as secoes esperadas estao no mapeamento."""
        expected_sections = [
            'mercado', 'concorrencia', 'publico', 'tendencias',
            'sazonalidade', 'sazonal', 'marca'
        ]
        for section in expected_sections:
            self.assertIn(section, CONTEXT_FIELD_MAPPING)

    def test_mapping_values_are_tuples(self):
        """Verifica que cada valor no mapeamento e uma tupla (field, default)."""
        for section, fields in CONTEXT_FIELD_MAPPING.items():
            for json_key, value in fields.items():
                self.assertIsInstance(value, tuple)
                self.assertEqual(len(value), 2)


class TestJsonParser(TestCase):
    """Testes para o parser de JSON."""

    def test_parse_ai_json_response_with_markdown(self):
        """Testa parsing de resposta com markdown."""
        raw = '```json{"contexto_pesquisado": {"mercado": {"panorama": "teste"}}}```'
        result = parse_ai_json_response(raw)
        self.assertEqual(result, {"mercado": {"panorama": "teste"}})

    def test_parse_ai_json_response_without_markdown(self):
        """Testa parsing de resposta sem markdown."""
        raw = '{"contexto_pesquisado": {"mercado": {"panorama": "teste"}}}'
        result = parse_ai_json_response(raw)
        self.assertEqual(result, {"mercado": {"panorama": "teste"}})

    def test_parse_ai_json_response_invalid_json(self):
        """Testa que JSON invalido retorna dict vazio."""
        raw = 'isso nao e json'
        result = parse_ai_json_response(raw)
        self.assertEqual(result, {})

    def test_parse_ai_json_response_missing_key(self):
        """Testa que chave ausente retorna dict vazio."""
        raw = '{"outra_chave": {"dados": "valor"}}'
        result = parse_ai_json_response(raw)
        self.assertEqual(result, {})

    def test_parse_ai_json_response_custom_key(self):
        """Testa parsing com chave customizada."""
        raw = '{"minha_chave": {"dados": "valor"}}'
        result = parse_ai_json_response(raw, key='minha_chave')
        self.assertEqual(result, {"dados": "valor"})

    def test_extract_json_block_simple(self):
        """Testa extracao de bloco JSON simples."""
        text = 'Texto antes {"key": "value"} texto depois'
        result = extract_json_block(text)
        self.assertEqual(result, '{"key": "value"}')

    def test_extract_json_block_nested(self):
        """Testa extracao de bloco JSON aninhado."""
        text = '{"outer": {"inner": "value"}}'
        result = extract_json_block(text)
        self.assertEqual(result, '{"outer": {"inner": "value"}}')

    def test_extract_json_block_with_markdown(self):
        """Testa extracao com markdown."""
        text = '```json\n{"key": "value"}\n```'
        result = extract_json_block(text)
        self.assertEqual(result, '{"key": "value"}')

    def test_extract_json_block_no_json(self):
        """Testa que texto sem JSON retorna None."""
        text = 'Texto sem JSON nenhum'
        result = extract_json_block(text)
        self.assertIsNone(result)

    def test_extract_json_block_unbalanced(self):
        """Testa que chaves desbalanceadas retornam None."""
        text = '{"key": "value"'
        result = extract_json_block(text)
        self.assertIsNone(result)


class TestContextStatsService(TestCase):
    """Testes para o servico de estatisticas."""

    def setUp(self):
        self.service = ContextStatsService()

    def test_calculate_batch_results_all_success(self):
        """Testa calculo quando todos sao sucesso."""
        results = [
            {'status': 'success'},
            {'status': 'success'},
            {'status': 'success'},
        ]
        start = timezone.now()
        end = start + timedelta(seconds=10)

        stats = self.service.calculate_batch_results(results, start, end)

        self.assertEqual(stats['processed'], 3)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['skipped'], 0)
        self.assertEqual(stats['duration_seconds'], 10.0)

    def test_calculate_batch_results_mixed(self):
        """Testa calculo com resultados mistos."""
        results = [
            {'status': 'success'},
            {'status': 'failed'},
            {'status': 'skipped'},
            {'status': 'success'},
        ]
        start = timezone.now()
        end = start + timedelta(seconds=5)

        stats = self.service.calculate_batch_results(results, start, end)

        self.assertEqual(stats['processed'], 2)
        self.assertEqual(stats['failed'], 1)
        self.assertEqual(stats['skipped'], 1)

    def test_calculate_batch_results_empty(self):
        """Testa calculo com lista vazia."""
        results = []
        start = timezone.now()
        end = start

        stats = self.service.calculate_batch_results(results, start, end)

        self.assertEqual(stats['processed'], 0)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['skipped'], 0)

    def test_build_completion_result_with_details(self):
        """Testa construcao de resultado com detalhes."""
        stats = {
            'processed': 5,
            'failed': 1,
            'skipped': 2,
            'duration_seconds': 15.0,
        }
        details = [{'user_id': 1}, {'user_id': 2}]

        result = self.service.build_completion_result(stats, total_users=8, details=details)

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['processed'], 5)
        self.assertEqual(result['failed'], 1)
        self.assertEqual(result['skipped'], 2)
        self.assertEqual(result['total_users'], 8)
        self.assertEqual(result['duration_seconds'], 15.0)
        self.assertEqual(result['details'], details)

    def test_build_completion_result_without_details(self):
        """Testa construcao de resultado sem detalhes."""
        stats = {
            'processed': 3,
            'failed': 0,
            'skipped': 0,
            'duration_seconds': 5.0,
        }

        result = self.service.build_completion_result(stats, total_users=3)

        self.assertNotIn('details', result)


class TestContextErrorService(TestCase):
    """Testes para o servico de erros."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = ContextErrorService()

    def test_store_error_creates_client_context(self):
        """Testa que store_error cria ClientContext se nao existir."""
        from asgiref.sync import async_to_sync

        async_to_sync(self.service.store_error)(self.user, "Erro de teste")

        context = ClientContext.objects.get(user=self.user)
        self.assertEqual(context.weekly_context_error, "Erro de teste")
        self.assertIsNotNone(context.weekly_context_error_date)

    def test_store_error_updates_existing(self):
        """Testa que store_error atualiza ClientContext existente."""
        from asgiref.sync import async_to_sync

        ClientContext.objects.create(user=self.user, weekly_context_error="Erro antigo")

        async_to_sync(self.service.store_error)(self.user, "Erro novo")

        context = ClientContext.objects.get(user=self.user)
        self.assertEqual(context.weekly_context_error, "Erro novo")

    def test_clear_error_removes_error(self):
        """Testa que clear_error remove o erro."""
        from asgiref.sync import async_to_sync

        ClientContext.objects.create(
            user=self.user,
            weekly_context_error="Erro",
            weekly_context_error_date=timezone.now()
        )

        async_to_sync(self.service.clear_error)(self.user)

        context = ClientContext.objects.get(user=self.user)
        self.assertIsNone(context.weekly_context_error)
        self.assertIsNone(context.weekly_context_error_date)

    def test_clear_error_nonexistent_context(self):
        """Testa que clear_error nao falha se ClientContext nao existir."""
        from asgiref.sync import async_to_sync

        # Nao deve lancar excecao
        async_to_sync(self.service.clear_error)(self.user)


class TestWeeklyContextDataSerializer(TestCase):
    """Testes para o serializer de dados de contexto."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client_context = ClientContext.objects.create(user=self.user)

    def test_update_client_context_maps_fields(self):
        """Testa que update_client_context mapeia campos corretamente."""
        context_data = {
            'mercado': {
                'panorama': 'Mercado aquecido',
                'tendencias': ['IA', 'Automacao'],
            },
            'publico': {
                'perfil': 'Jovens profissionais',
            }
        }

        serializer = WeeklyContextDataSerializer(context_data)
        serializer.update_client_context(self.client_context)

        self.assertEqual(self.client_context.market_panorama, 'Mercado aquecido')
        self.assertEqual(self.client_context.market_tendencies, ['IA', 'Automacao'])
        self.assertEqual(self.client_context.target_audience_profile, 'Jovens profissionais')

    def test_update_client_context_uses_defaults(self):
        """Testa que campos ausentes usam valores default."""
        context_data = {}

        serializer = WeeklyContextDataSerializer(context_data)
        serializer.update_client_context(self.client_context)

        self.assertEqual(self.client_context.market_panorama, '')
        self.assertEqual(self.client_context.market_tendencies, [])

    def test_to_dict_returns_mapped_data(self):
        """Testa que to_dict retorna dados mapeados."""
        context_data = {
            'mercado': {
                'panorama': 'Teste',
            }
        }

        serializer = WeeklyContextDataSerializer(context_data)
        result = serializer.to_dict()

        self.assertIn('market_panorama', result)
        self.assertEqual(result['market_panorama'], 'Teste')
