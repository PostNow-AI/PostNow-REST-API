"""Tests for history utilities."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ClientContext.utils.history_utils import get_recent_topics, get_recent_url_keys


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock()
    user.id = 1
    return user


class TestGetRecentTopics:
    """Tests for get_recent_topics function."""

    @pytest.mark.asyncio
    async def test_get_recent_topics_with_list_data(self, mock_user):
        """Test getting topics when data is stored as list."""
        mock_history = [
            ['Marketing', 'Vendas'],
            ['Tech', 'Inovacao'],
        ]

        with patch('ClientContext.utils.history_utils.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=mock_history)

            topics = await get_recent_topics(mock_user, lookback_weeks=4)

            assert isinstance(topics, list)
            # Topics should be unique
            assert len(topics) == len(set(topics))

    @pytest.mark.asyncio
    async def test_get_recent_topics_with_json_string(self, mock_user):
        """Test getting topics when data is stored as JSON string."""
        mock_history = [
            json.dumps(['Marketing', 'Vendas']),
            json.dumps(['Tech']),
        ]

        with patch('ClientContext.utils.history_utils.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=mock_history)

            topics = await get_recent_topics(mock_user, lookback_weeks=4)

            assert isinstance(topics, list)

    @pytest.mark.asyncio
    async def test_get_recent_topics_with_empty_history(self, mock_user):
        """Test getting topics when history is empty."""
        with patch('ClientContext.utils.history_utils.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=[])

            topics = await get_recent_topics(mock_user, lookback_weeks=4)

            assert topics == []

    @pytest.mark.asyncio
    async def test_get_recent_topics_with_none_values(self, mock_user):
        """Test getting topics when some values are None."""
        mock_history = [
            ['Marketing'],
            None,
            ['Tech'],
        ]

        with patch('ClientContext.utils.history_utils.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=mock_history)

            topics = await get_recent_topics(mock_user, lookback_weeks=4)

            assert isinstance(topics, list)
            assert None not in topics


class TestGetRecentUrlKeys:
    """Tests for get_recent_url_keys function."""

    @pytest.mark.asyncio
    async def test_get_recent_url_keys_basic(self, mock_user):
        """Test getting URL keys from history."""
        mock_histories = [
            {
                'tendencies_data': {
                    'mercado': {
                        'items': [
                            {'url_fonte': 'https://example.com/article1'},
                            {'url_fonte': 'https://test.com/post'},
                        ]
                    }
                }
            }
        ]

        with patch('ClientContext.utils.history_utils.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=mock_histories)

            url_keys = await get_recent_url_keys(mock_user, lookback_weeks=4)

            assert isinstance(url_keys, set)
            assert len(url_keys) > 0

    @pytest.mark.asyncio
    async def test_get_recent_url_keys_empty_history(self, mock_user):
        """Test getting URL keys when history is empty."""
        with patch('ClientContext.utils.history_utils.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=[])

            url_keys = await get_recent_url_keys(mock_user, lookback_weeks=4)

            assert url_keys == set()

    @pytest.mark.asyncio
    async def test_get_recent_url_keys_invalid_urls(self, mock_user):
        """Test that invalid URLs are filtered out."""
        mock_histories = [
            {
                'tendencies_data': {
                    'mercado': {
                        'items': [
                            {'url_fonte': 'not-a-url'},
                            {'url_fonte': ''},
                            {'url_fonte': None},
                        ]
                    }
                }
            }
        ]

        with patch('ClientContext.utils.history_utils.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=mock_histories)

            url_keys = await get_recent_url_keys(mock_user, lookback_weeks=4)

            assert url_keys == set()

    @pytest.mark.asyncio
    async def test_get_recent_url_keys_handles_missing_data(self, mock_user):
        """Test handling of missing tendencies_data."""
        mock_histories = [
            {'tendencies_data': None},
            {'tendencies_data': {}},
            {},
        ]

        with patch('ClientContext.utils.history_utils.sync_to_async') as mock_sync:
            mock_sync.return_value = AsyncMock(return_value=mock_histories)

            url_keys = await get_recent_url_keys(mock_user, lookback_weeks=4)

            assert url_keys == set()
