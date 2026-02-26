"""Tests for weekly context email service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ClientContext.services.weekly_context_email_service import (
    WeeklyContextEmailService,
    EMAIL_TYPE_OPPORTUNITIES,
    EMAIL_TYPE_MARKET_INTELLIGENCE,
)


def make_async_mock(return_value):
    """Create a mock that returns an async function."""
    async def async_func(*args, **kwargs):
        return return_value
    return MagicMock(side_effect=lambda func: async_func)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock()
    user.id = 1
    user.email = 'test@example.com'
    user.first_name = 'Test'
    user.username = 'testuser'
    return user


@pytest.fixture
def sample_context_data():
    """Sample context data for emails."""
    return {
        'user__id': 1,
        'user__email': 'test@example.com',
        'user__first_name': 'Test',
        'tendencies_data': {'polemica': {'items': []}},
        'tendencies_hashtags': ['test'],
        'tendencies_keywords': ['keyword'],
        'market_panorama': 'Test panorama',
        'market_tendencies': [],
    }


class TestEmailTypeConstants:
    """Tests for email type constants."""

    def test_opportunities_constant(self):
        """Test opportunities email type constant."""
        assert EMAIL_TYPE_OPPORTUNITIES == 'opportunities'

    def test_market_intelligence_constant(self):
        """Test market intelligence email type constant."""
        assert EMAIL_TYPE_MARKET_INTELLIGENCE == 'market_intelligence'


class TestWeeklyContextEmailService:
    """Tests for WeeklyContextEmailService."""

    def test_service_initialization(self):
        """Test service initializes with mailjet service."""
        service = WeeklyContextEmailService()

        assert service.mailjet_service is not None

    @pytest.mark.asyncio
    async def test_mail_weekly_context_with_no_users(self):
        """Test mail_weekly_context returns empty result when no users."""
        service = WeeklyContextEmailService()

        with patch.object(service, 'fetch_users_context_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []

            result = await service.mail_weekly_context()

            assert result['status'] == 'completed'
            assert result['total_users'] == 0
            assert result['processed'] == 0
            assert 'email_type' in result

    @pytest.mark.asyncio
    async def test_mail_weekly_context_includes_email_type(self):
        """Test mail_weekly_context includes email_type in result."""
        service = WeeklyContextEmailService()

        with patch.object(service, 'fetch_users_context_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []

            # Test opportunities type
            result = await service.mail_weekly_context(email_type=EMAIL_TYPE_OPPORTUNITIES)
            assert result['email_type'] == EMAIL_TYPE_OPPORTUNITIES

            # Test market intelligence type
            result = await service.mail_weekly_context(email_type=EMAIL_TYPE_MARKET_INTELLIGENCE)
            assert result['email_type'] == EMAIL_TYPE_MARKET_INTELLIGENCE

    @pytest.mark.asyncio
    async def test_mail_weekly_context_default_email_type(self):
        """Test mail_weekly_context uses opportunities as default."""
        service = WeeklyContextEmailService()

        with patch.object(service, 'fetch_users_context_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []

            result = await service.mail_weekly_context()

            assert result['email_type'] == EMAIL_TYPE_OPPORTUNITIES

    @pytest.mark.asyncio
    async def test_send_weekly_context_email_opportunities(self, mock_user, sample_context_data):
        """Test send_weekly_context_email with opportunities type."""
        service = WeeklyContextEmailService()

        with patch.object(service.mailjet_service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, {'status': 'sent'})

            with patch('ClientContext.services.weekly_context_email_service.sync_to_async') as mock_sync:
                mock_sync.side_effect = make_async_mock({'business_name': 'Test Business'}).side_effect

                result = await service.send_weekly_context_email(
                    mock_user,
                    sample_context_data,
                    email_type=EMAIL_TYPE_OPPORTUNITIES
                )

                assert result['status'] == 'success'
                assert result['email_type'] == EMAIL_TYPE_OPPORTUNITIES

                # Check subject contains opportunities indicator
                call_args = mock_send.call_args
                assert 'Oportunidades' in call_args.kwargs['subject']

    @pytest.mark.asyncio
    async def test_send_weekly_context_email_market_intelligence(self, mock_user, sample_context_data):
        """Test send_weekly_context_email with market intelligence type."""
        service = WeeklyContextEmailService()

        with patch.object(service.mailjet_service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, {'status': 'sent'})

            with patch('ClientContext.services.weekly_context_email_service.sync_to_async') as mock_sync:
                mock_sync.side_effect = make_async_mock({'business_name': 'Test Business'}).side_effect

                result = await service.send_weekly_context_email(
                    mock_user,
                    sample_context_data,
                    email_type=EMAIL_TYPE_MARKET_INTELLIGENCE
                )

                assert result['status'] == 'success'
                assert result['email_type'] == EMAIL_TYPE_MARKET_INTELLIGENCE

                # Check subject contains market intelligence indicator
                call_args = mock_send.call_args
                assert 'Inteligência' in call_args.kwargs['subject']

    @pytest.mark.asyncio
    async def test_send_weekly_context_email_failure(self, mock_user, sample_context_data):
        """Test send_weekly_context_email handles failure."""
        service = WeeklyContextEmailService()

        with patch.object(service.mailjet_service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (False, {'error': 'Send failed'})

            with patch('ClientContext.services.weekly_context_email_service.sync_to_async') as mock_sync:
                mock_sync.side_effect = make_async_mock({'business_name': 'Test Business'}).side_effect

                result = await service.send_weekly_context_email(
                    mock_user,
                    sample_context_data,
                    email_type=EMAIL_TYPE_OPPORTUNITIES
                )

                assert result['status'] == 'failed'
                assert 'error' in result

    @pytest.mark.asyncio
    async def test_send_weekly_context_email_exception(self, mock_user, sample_context_data):
        """Test send_weekly_context_email handles exceptions."""
        service = WeeklyContextEmailService()

        with patch.object(service.mailjet_service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception('Network error')

            with patch('ClientContext.services.weekly_context_email_service.sync_to_async') as mock_sync:
                mock_sync.side_effect = make_async_mock({'business_name': 'Test Business'}).side_effect

                result = await service.send_weekly_context_email(
                    mock_user,
                    sample_context_data,
                    email_type=EMAIL_TYPE_OPPORTUNITIES
                )

                assert result['status'] == 'failed'
                assert 'Network error' in result['error']


class TestEmailSubjects:
    """Tests for email subject lines."""

    @pytest.mark.asyncio
    async def test_opportunities_email_subject(self, mock_user, sample_context_data):
        """Test opportunities email has correct subject."""
        service = WeeklyContextEmailService()

        with patch.object(service.mailjet_service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, {})

            with patch('ClientContext.services.weekly_context_email_service.sync_to_async') as mock_sync:
                mock_sync.side_effect = make_async_mock({'business_name': 'Acme Corp'}).side_effect

                await service.send_weekly_context_email(
                    mock_user,
                    sample_context_data,
                    email_type=EMAIL_TYPE_OPPORTUNITIES
                )

                call_args = mock_send.call_args
                subject = call_args.kwargs['subject']
                assert '🚀' in subject
                assert 'Oportunidades' in subject
                assert 'Acme Corp' in subject

    @pytest.mark.asyncio
    async def test_market_intelligence_email_subject(self, mock_user, sample_context_data):
        """Test market intelligence email has correct subject."""
        service = WeeklyContextEmailService()

        with patch.object(service.mailjet_service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (True, {})

            with patch('ClientContext.services.weekly_context_email_service.sync_to_async') as mock_sync:
                mock_sync.side_effect = make_async_mock({'business_name': 'Acme Corp'}).side_effect

                await service.send_weekly_context_email(
                    mock_user,
                    sample_context_data,
                    email_type=EMAIL_TYPE_MARKET_INTELLIGENCE
                )

                call_args = mock_send.call_args
                subject = call_args.kwargs['subject']
                assert '🧠' in subject
                assert 'Inteligência' in subject
                assert 'Acme Corp' in subject
