"""Pytest configuration for ClientContext tests."""

import os
import django
import pytest

# Configure Django settings before importing any Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
django.setup()

# Configure pytest-asyncio to auto mode
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
