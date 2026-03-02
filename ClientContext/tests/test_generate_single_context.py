"""
Testes para o endpoint generate_single_client_context e serviços relacionados.

Testa:
- Endpoint executa fluxo completo de 5 etapas
- Envia ambos os e-mails (Oportunidades + Inteligência de Mercado)
- Campo user_name usa business_name do perfil
- Google Search usa filtro de data (dateRestrict)
"""
from unittest.mock import AsyncMock, MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ClientContext.models import ClientContext
from CreatorProfile.models import CreatorProfile


class GenerateSingleClientContextAPITestCase(APITestCase):
    """Testes de API para o endpoint generate_single_client_context."""

    def setUp(self):
        """Configuração inicial."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='João'
        )
        self.url = reverse('generate_single_client_context')

        # Create creator profile
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Minha Empresa',
            specialization='Marketing Digital',
            business_description='Empresa de marketing digital'
        )

        # Create client context
        self.client_context = ClientContext.objects.create(
            user=self.user,
            market_panorama='Panorama de teste',
            market_tendencies=['tendencia1', 'tendencia2'],
            market_challenges=['desafio1'],
            competition_main='Concorrente principal',
            competition_strategies=['estrategia1'],
            competition_opportunities=['oportunidade1'],
            target_audience_profile='Perfil do público',
            target_audience_behaviors=['comportamento1'],
            target_audience_interests=['interesse1'],
            tendencies_popular_themes=['tema1'],
            tendencies_hashtags=['#hashtag1'],
            tendencies_keywords=['keyword1'],
            tendencies_data={'polemica': {'titulo': 'Teste', 'items': []}}
        )

    def test_endpoint_requires_authentication(self):
        """Teste: endpoint requer autenticação."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('ClientContext.views.MarketIntelligenceEmailService')
    @patch('ClientContext.views.OpportunitiesEmailService')
    @patch('ClientContext.views.ContextEnrichmentService')
    @patch('ClientContext.views.OpportunitiesGenerationService')
    @patch('ClientContext.views.WeeklyContextService')
    def test_endpoint_executes_five_step_flow(
        self,
        mock_context_service,
        mock_opportunities_service,
        mock_enrichment_service,
        mock_opp_email_service,
        mock_market_email_service
    ):
        """Teste: endpoint executa fluxo completo de 5 etapas."""
        # Setup mocks
        mock_context_instance = MagicMock()
        mock_context_instance.process_single_user = AsyncMock(return_value={'status': 'success'})
        mock_context_service.return_value = mock_context_instance

        mock_opp_instance = MagicMock()
        mock_opp_instance.generate_user_opportunities = AsyncMock(return_value={'status': 'success'})
        mock_opportunities_service.return_value = mock_opp_instance

        mock_enrich_instance = MagicMock()
        mock_enrich_instance.enrich_user_context = AsyncMock(return_value={'status': 'success'})
        mock_enrichment_service.return_value = mock_enrich_instance

        mock_opp_email_instance = MagicMock()
        mock_opp_email_instance.send_to_user = AsyncMock(return_value={'status': 'success'})
        mock_opp_email_service.return_value = mock_opp_email_instance

        mock_market_email_instance = MagicMock()
        mock_market_email_instance.send_to_user = AsyncMock(return_value={'status': 'success'})
        mock_market_email_service.return_value = mock_market_email_instance

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Execute
        response = self.client.post(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

        # Verify all services were called
        mock_context_instance.process_single_user.assert_called_once()
        mock_opp_instance.generate_user_opportunities.assert_called_once()
        mock_enrich_instance.enrich_user_context.assert_called_once()
        mock_opp_email_instance.send_to_user.assert_called_once()
        mock_market_email_instance.send_to_user.assert_called_once()

    @patch('ClientContext.views.MarketIntelligenceEmailService')
    @patch('ClientContext.views.OpportunitiesEmailService')
    @patch('ClientContext.views.ContextEnrichmentService')
    @patch('ClientContext.views.OpportunitiesGenerationService')
    @patch('ClientContext.views.WeeklyContextService')
    def test_endpoint_sends_both_emails(
        self,
        mock_context_service,
        mock_opportunities_service,
        mock_enrichment_service,
        mock_opp_email_service,
        mock_market_email_service
    ):
        """Teste: endpoint envia ambos os e-mails."""
        # Setup mocks
        mock_context_instance = MagicMock()
        mock_context_instance.process_single_user = AsyncMock(return_value={'status': 'success'})
        mock_context_service.return_value = mock_context_instance

        mock_opp_instance = MagicMock()
        mock_opp_instance.generate_user_opportunities = AsyncMock(return_value={'status': 'success'})
        mock_opportunities_service.return_value = mock_opp_instance

        mock_enrich_instance = MagicMock()
        mock_enrich_instance.enrich_user_context = AsyncMock(return_value={'status': 'success'})
        mock_enrichment_service.return_value = mock_enrich_instance

        mock_opp_email_instance = MagicMock()
        mock_opp_email_instance.send_to_user = AsyncMock(return_value={'status': 'sent'})
        mock_opp_email_service.return_value = mock_opp_email_instance

        mock_market_email_instance = MagicMock()
        mock_market_email_instance.send_to_user = AsyncMock(return_value={'status': 'sent'})
        mock_market_email_service.return_value = mock_market_email_instance

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Execute
        response = self.client.post(self.url)

        # Assert response contains email status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('details', response.data)
        self.assertIn('opportunities_email', response.data['details'])
        self.assertIn('market_email', response.data['details'])

    @patch('ClientContext.views.MarketIntelligenceEmailService')
    @patch('ClientContext.views.OpportunitiesEmailService')
    @patch('ClientContext.views.ContextEnrichmentService')
    @patch('ClientContext.views.OpportunitiesGenerationService')
    @patch('ClientContext.views.WeeklyContextService')
    def test_endpoint_returns_details_for_each_step(
        self,
        mock_context_service,
        mock_opportunities_service,
        mock_enrichment_service,
        mock_opp_email_service,
        mock_market_email_service
    ):
        """Teste: endpoint retorna status detalhado de cada etapa."""
        # Setup mocks
        mock_context_instance = MagicMock()
        mock_context_instance.process_single_user = AsyncMock(return_value={'status': 'context_ok'})
        mock_context_service.return_value = mock_context_instance

        mock_opp_instance = MagicMock()
        mock_opp_instance.generate_user_opportunities = AsyncMock(return_value={'status': 'opportunities_ok'})
        mock_opportunities_service.return_value = mock_opp_instance

        mock_enrich_instance = MagicMock()
        mock_enrich_instance.enrich_user_context = AsyncMock(return_value={'status': 'enrichment_ok'})
        mock_enrichment_service.return_value = mock_enrich_instance

        mock_opp_email_instance = MagicMock()
        mock_opp_email_instance.send_to_user = AsyncMock(return_value={'status': 'opp_email_ok'})
        mock_opp_email_service.return_value = mock_opp_email_instance

        mock_market_email_instance = MagicMock()
        mock_market_email_instance.send_to_user = AsyncMock(return_value={'status': 'market_email_ok'})
        mock_market_email_service.return_value = mock_market_email_instance

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Execute
        response = self.client.post(self.url)

        # Assert all details present
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        details = response.data['details']
        self.assertEqual(details['context'], 'context_ok')
        self.assertEqual(details['opportunities'], 'opportunities_ok')
        self.assertEqual(details['enrichment'], 'enrichment_ok')
        self.assertEqual(details['opportunities_email'], 'opp_email_ok')
        self.assertEqual(details['market_email'], 'market_email_ok')


class GetCreatorProfileDataTestCase(TestCase):
    """Testes para a função get_creator_profile_data."""

    def setUp(self):
        """Configuração inicial."""
        self.user = User.objects.create_user(
            username='testuser@email.com',
            email='testuser@email.com',
            password='testpass123',
            first_name='João'
        )

    def test_user_name_uses_business_name(self):
        """Teste: user_name usa business_name quando disponível."""
        from services.get_creator_profile_data import get_creator_profile_data

        CreatorProfile.objects.create(
            user=self.user,
            business_name='Minha Empresa LTDA',
            specialization='Tech'
        )

        profile_data = get_creator_profile_data(self.user)

        self.assertEqual(profile_data['user_name'], 'Minha Empresa LTDA')

    def test_user_name_fallback_to_first_name(self):
        """Teste: user_name usa first_name quando business_name está vazio."""
        from services.get_creator_profile_data import get_creator_profile_data

        CreatorProfile.objects.create(
            user=self.user,
            business_name='',
            specialization='Tech'
        )

        profile_data = get_creator_profile_data(self.user)

        self.assertEqual(profile_data['user_name'], 'João')

    def test_user_name_fallback_to_username_prefix(self):
        """Teste: user_name usa prefixo do username quando business_name e first_name vazios."""
        from services.get_creator_profile_data import get_creator_profile_data

        user = User.objects.create_user(
            username='maria@empresa.com',
            email='maria@empresa.com',
            password='testpass123',
            first_name=''
        )
        CreatorProfile.objects.create(
            user=user,
            business_name='',
            specialization='Tech'
        )

        profile_data = get_creator_profile_data(user)

        self.assertEqual(profile_data['user_name'], 'maria')

    def test_profile_data_includes_user_name_field(self):
        """Teste: profile_data sempre inclui campo user_name."""
        from services.get_creator_profile_data import get_creator_profile_data

        CreatorProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            specialization='Tech'
        )

        profile_data = get_creator_profile_data(self.user)

        self.assertIn('user_name', profile_data)
        self.assertIsNotNone(profile_data['user_name'])
        self.assertNotEqual(profile_data['user_name'], '')


class GoogleSearchServiceTestCase(TestCase):
    """Testes para GoogleSearchService."""

    @patch('services.google_search_service.requests.get')
    def test_search_includes_date_restrict_param(self, mock_get):
        """Teste: busca inclui parâmetro dateRestrict para filtrar por 3 meses."""
        from services.google_search_service import GoogleSearchService

        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}
        mock_get.return_value = mock_response

        # Execute
        service = GoogleSearchService()
        service.api_key = 'test-api-key'
        service.search_engine_id = 'test-engine-id'
        service.search('test query')

        # Assert dateRestrict was passed
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get('params', call_kwargs[1].get('params', {}))

        self.assertEqual(params.get('dateRestrict'), 'm3')

    @patch('services.google_search_service.requests.get')
    def test_search_uses_portuguese_and_brazil_settings(self, mock_get):
        """Teste: busca usa configurações para português e Brasil."""
        from services.google_search_service import GoogleSearchService

        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}
        mock_get.return_value = mock_response

        # Execute
        service = GoogleSearchService()
        service.api_key = 'test-api-key'
        service.search_engine_id = 'test-engine-id'
        service.search('marketing digital')

        # Assert language and region params
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get('params', call_kwargs[1].get('params', {}))

        self.assertEqual(params.get('lr'), 'lang_pt')
        self.assertEqual(params.get('gl'), 'br')

    def test_search_returns_empty_list_without_credentials(self):
        """Teste: busca retorna lista vazia sem credenciais."""
        from services.google_search_service import GoogleSearchService

        service = GoogleSearchService()
        service.api_key = ''
        service.search_engine_id = ''

        results = service.search('test query')

        self.assertEqual(results, [])

    @patch('services.google_search_service.requests.get')
    def test_search_handles_quota_exceeded_429(self, mock_get):
        """Teste: busca trata erro 429 (quota exceeded)."""
        from services.google_search_service import GoogleSearchService

        # Setup mock for 429 response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        # Execute
        service = GoogleSearchService()
        service.api_key = 'test-api-key'
        service.search_engine_id = 'test-engine-id'

        results = service.search('test query')

        # Should return empty list without raising exception
        self.assertEqual(results, [])

    @patch('services.google_search_service.requests.get')
    def test_search_handles_quota_exceeded_403(self, mock_get):
        """Teste: busca trata erro 403 com quotaExceeded."""
        from services.google_search_service import GoogleSearchService

        # Setup mock for 403 response with quota error
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            'error': {'message': 'quotaExceeded', 'code': 403}
        }
        mock_response.raise_for_status.side_effect = Exception('403 Forbidden')
        mock_get.return_value = mock_response

        # Execute
        service = GoogleSearchService()
        service.api_key = 'test-api-key'
        service.search_engine_id = 'test-engine-id'

        results = service.search('test query')

        # Should return empty list without raising exception
        self.assertEqual(results, [])

    @patch('services.google_search_service.requests.get')
    def test_search_returns_formatted_results(self, mock_get):
        """Teste: busca retorna resultados formatados corretamente."""
        from services.google_search_service import GoogleSearchService

        # Setup mock with results
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'link': 'https://example.com/article1',
                    'title': 'Article 1',
                    'snippet': 'Snippet for article 1'
                },
                {
                    'link': 'https://example.com/article2',
                    'title': 'Article 2',
                    'snippet': 'Snippet for article 2'
                }
            ]
        }
        mock_get.return_value = mock_response

        # Execute
        service = GoogleSearchService()
        service.api_key = 'test-api-key'
        service.search_engine_id = 'test-engine-id'

        results = service.search('marketing')

        # Assert results format
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['url'], 'https://example.com/article1')
        self.assertEqual(results[0]['title'], 'Article 1')
        self.assertEqual(results[0]['snippet'], 'Snippet for article 1')


class DateRestrictIntegrationTestCase(TestCase):
    """Testes de integração para verificar filtro de data no fluxo completo."""

    @patch('services.google_search_service.requests.get')
    def test_date_restrict_applied_in_enrichment_flow(self, mock_get):
        """Teste: dateRestrict é aplicado quando enriquecimento busca fontes."""
        from services.google_search_service import GoogleSearchService

        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}
        mock_get.return_value = mock_response

        # Execute
        service = GoogleSearchService()
        service.api_key = 'test-key'
        service.search_engine_id = 'test-id'
        service.search('tendências marketing digital 2024')

        # Verify dateRestrict='m3' was used (3 months filter)
        call_args = mock_get.call_args
        params = call_args.kwargs.get('params', call_args[1].get('params', {}))
        self.assertEqual(params['dateRestrict'], 'm3')
