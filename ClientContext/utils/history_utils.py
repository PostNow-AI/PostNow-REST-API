"""Utility functions for handling context history and anti-repetition logic."""

import json
import logging
from datetime import timedelta
from typing import Set, List

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from .url_dedupe import normalize_url_key

logger = logging.getLogger(__name__)


async def get_recent_topics(user: User, lookback_weeks: int = 4) -> List[str]:
    """
    Recupera tópicos abordados nas últimas N semanas para evitar repetição.

    Args:
        user: User instance
        lookback_weeks: Number of weeks to look back (default: 4)

    Returns:
        List of unique topic strings
    """
    from ..models import ClientContextHistory

    cutoff_date = timezone.now() - timedelta(weeks=lookback_weeks)

    history = await sync_to_async(lambda: list(
        ClientContextHistory.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        ).values_list('tendencies_popular_themes', flat=True)
    ))()

    topics = []
    for item in history:
        if item:
            if isinstance(item, list):
                topics.extend(item)
            elif isinstance(item, str):
                try:
                    topics.extend(json.loads(item))
                except (json.JSONDecodeError, TypeError):
                    # Malformed JSON entry, skip silently
                    logger.debug("Skipping malformed JSON in topics history: %s", item[:100] if len(item) > 100 else item)

    return list(set(topics))


async def get_recent_url_keys(user: User, lookback_weeks: int = 4) -> Set[str]:
    """
    Recupera chaves (domain+path) usadas recentemente a partir do histórico.

    Args:
        user: User instance
        lookback_weeks: Number of weeks to look back

    Returns:
        Set of normalized URL keys
    """
    from ..models import ClientContextHistory

    cutoff_date = timezone.now() - timedelta(days=max(lookback_weeks, 1) * 7)

    histories = await sync_to_async(lambda: list(
        ClientContextHistory.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        )
        .order_by("-created_at")
        .values("tendencies_data")
    ))()

    used: Set[str] = set()

    for h in histories:
        data = h.get("tendencies_data") or {}
        if not isinstance(data, dict):
            continue

        for group in data.values():
            if not isinstance(group, dict):
                continue

            for item in (group.get("items") or []):
                if not isinstance(item, dict):
                    continue

                url = item.get("url_fonte")
                if isinstance(url, str) and url.startswith("http"):
                    key = normalize_url_key(url)
                    if key:
                        used.add(key)

    return used
