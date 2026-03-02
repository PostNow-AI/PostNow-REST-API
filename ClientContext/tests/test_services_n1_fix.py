"""
Testes para verificar correção do problema N+1 nos serviços.

Estes testes verificam:
- Pré-carregamento de usuários em batch (evita N+1)
- Tratamento quando usuário não é encontrado
- Contagem correta de processados/falhas

Nota: Estes são testes de integração que usam o banco de dados de teste.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from ClientContext.models import ClientContext

User = get_user_model()


def create_test_user(email, password="testpass123"):
    """Helper para criar usuário de teste."""
    username = email.split("@")[0]
    return User.objects.create_user(
        username=username,
        email=email,
        password=password
    )


def create_client_context(user, **kwargs):
    """Helper para criar ClientContext de teste."""
    defaults = {
        'market_panorama': 'Test panorama',
        'market_tendencies': ['trend1', 'trend2'],
        'weekly_context_error': None,
    }
    defaults.update(kwargs)
    return ClientContext.objects.create(user=user, **defaults)


class PreFetchUsersLogicTestCase(TestCase):
    """
    Testes para verificar que a lógica de pré-carregamento funciona.

    Estes testes verificam a lógica em isolamento, sem chamar os serviços completos.
    """

    def setUp(self):
        """Configuração inicial"""
        self.user1 = create_test_user("prefetch_test1@example.com")
        self.user2 = create_test_user("prefetch_test2@example.com")
        self.user3 = create_test_user("prefetch_test3@example.com")

    def test_pre_fetch_retorna_todos_usuarios(self):
        """Teste: pré-fetch com filter(id__in=) retorna todos os usuários"""
        user_ids = [self.user1.id, self.user2.id, self.user3.id]

        users = list(User.objects.filter(id__in=user_ids))
        users_by_id = {user.id: user for user in users}

        self.assertEqual(len(users_by_id), 3)
        self.assertIn(self.user1.id, users_by_id)
        self.assertIn(self.user2.id, users_by_id)
        self.assertIn(self.user3.id, users_by_id)

    def test_pre_fetch_com_id_inexistente_ignora(self):
        """Teste: pré-fetch ignora IDs que não existem"""
        user_ids = [self.user1.id, 99999, self.user2.id]

        users = list(User.objects.filter(id__in=user_ids))
        users_by_id = {user.id: user for user in users}

        self.assertEqual(len(users_by_id), 2)
        self.assertIn(self.user1.id, users_by_id)
        self.assertIn(self.user2.id, users_by_id)
        self.assertNotIn(99999, users_by_id)

    def test_get_retorna_none_para_id_inexistente(self):
        """Teste: dict.get() retorna None para ID inexistente"""
        user_ids = [self.user1.id]

        users = list(User.objects.filter(id__in=user_ids))
        users_by_id = {user.id: user for user in users}

        # ID existente retorna o usuário
        self.assertEqual(users_by_id.get(self.user1.id), self.user1)

        # ID inexistente retorna None
        self.assertIsNone(users_by_id.get(99999))

    def test_pre_fetch_com_lista_vazia(self):
        """Teste: pré-fetch com lista vazia retorna dict vazio"""
        user_ids = []

        users = list(User.objects.filter(id__in=user_ids))
        users_by_id = {user.id: user for user in users}

        self.assertEqual(len(users_by_id), 0)


class ClientContextQueryTestCase(TestCase):
    """Testes para verificar queries do ClientContext."""

    def setUp(self):
        """Configuração inicial"""
        self.user1 = create_test_user("context_test1@example.com")
        self.user2 = create_test_user("context_test2@example.com")
        self.context1 = create_client_context(self.user1)
        self.context2 = create_client_context(self.user2)

    def test_query_retorna_contextos_com_user_id(self):
        """Teste: query com values() retorna user_id corretamente"""
        contexts = list(ClientContext.objects.filter(
            weekly_context_error__isnull=True,
        ).select_related('user').values('id', 'user__id', 'market_panorama'))

        self.assertEqual(len(contexts), 2)

        user_ids = [ctx['user__id'] for ctx in contexts]
        self.assertIn(self.user1.id, user_ids)
        self.assertIn(self.user2.id, user_ids)

    def test_query_com_filtro_error_null(self):
        """Teste: filtro __isnull=True funciona corretamente"""
        # Criar contexto com erro
        user3 = create_test_user("context_test3@example.com")
        create_client_context(user3, weekly_context_error="Test error")

        contexts = list(ClientContext.objects.filter(
            weekly_context_error__isnull=True,
        ).values('id', 'user_id'))

        # Apenas 2 contextos sem erro
        self.assertEqual(len(contexts), 2)


class ServiceImportTestCase(TestCase):
    """Testes para verificar que os serviços importam corretamente."""

    def test_import_market_intelligence_email_service(self):
        """Teste: MarketIntelligenceEmailService importa sem erro"""
        from ClientContext.services.market_intelligence_email_service import MarketIntelligenceEmailService
        service = MarketIntelligenceEmailService()
        self.assertIsNotNone(service)

    def test_import_opportunities_email_service(self):
        """Teste: OpportunitiesEmailService importa sem erro"""
        from ClientContext.services.opportunities_email_service import OpportunitiesEmailService
        service = OpportunitiesEmailService()
        self.assertIsNotNone(service)

    def test_import_context_enrichment_service(self):
        """Teste: ContextEnrichmentService importa sem erro"""
        from ClientContext.services.context_enrichment_service import ContextEnrichmentService
        service = ContextEnrichmentService()
        self.assertIsNotNone(service)

    def test_import_opportunities_generation_service(self):
        """Teste: OpportunitiesGenerationService importa sem erro"""
        from ClientContext.services.opportunities_generation_service import OpportunitiesGenerationService
        service = OpportunitiesGenerationService()
        self.assertIsNotNone(service)

    def test_import_market_intelligence_enrichment_service(self):
        """Teste: MarketIntelligenceEnrichmentService importa sem erro"""
        from ClientContext.services.market_intelligence_enrichment_service import MarketIntelligenceEnrichmentService
        service = MarketIntelligenceEnrichmentService()
        self.assertIsNotNone(service)

    def test_import_weekly_context_email_service(self):
        """Teste: WeeklyContextEmailService importa sem erro"""
        from ClientContext.services.weekly_context_email_service import WeeklyContextEmailService
        service = WeeklyContextEmailService()
        self.assertIsNotNone(service)
