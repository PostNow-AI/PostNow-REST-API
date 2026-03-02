"""
Helper functions for ClientContext views.

Extracted from views.py to follow SOLID principles.
"""
from typing import Any

from ClientContext.models import ClientContext


def check_step_result(result: dict, step_name: str) -> bool:
    """
    Verifica se o resultado de uma etapa indica sucesso.

    Args:
        result: Dict com resultado da etapa
        step_name: Nome da etapa (para logging)

    Returns:
        True se sucesso, False se falha
    """
    if not isinstance(result, dict):
        return True  # Assume sucesso se não for dict
    status_value = result.get('status', 'success')
    return status_value not in ('failed', 'error')


def build_context_data(client_context: ClientContext) -> dict:
    """
    Constrói dict de contexto a partir do modelo.

    Args:
        client_context: Instância do modelo ClientContext

    Returns:
        Dict com dados de contexto para serviços de email
    """
    return {
        'market_panorama': client_context.market_panorama,
        'market_tendencies': client_context.market_tendencies,
        'market_challenges': client_context.market_challenges,
        'competition_main': client_context.competition_main,
        'competition_strategies': client_context.competition_strategies,
        'competition_opportunities': client_context.competition_opportunities,
        'target_audience_profile': client_context.target_audience_profile,
        'target_audience_behaviors': client_context.target_audience_behaviors,
        'target_audience_interests': client_context.target_audience_interests,
        'tendencies_popular_themes': client_context.tendencies_popular_themes,
        'tendencies_hashtags': client_context.tendencies_hashtags,
        'tendencies_keywords': client_context.tendencies_keywords,
        'tendencies_data': client_context.tendencies_data,
    }


def build_full_context_data(client_context: ClientContext) -> dict:
    """
    Constrói dict completo de contexto para e-mail de inteligência de mercado.

    Args:
        client_context: Instância do modelo ClientContext

    Returns:
        Dict com dados completos incluindo sazonalidade e marca
    """
    return {
        'market_panorama': client_context.market_panorama,
        'market_tendencies': client_context.market_tendencies,
        'market_challenges': client_context.market_challenges,
        'competition_main': client_context.competition_main,
        'competition_strategies': client_context.competition_strategies,
        'competition_opportunities': client_context.competition_opportunities,
        'target_audience_profile': client_context.target_audience_profile,
        'target_audience_behaviors': client_context.target_audience_behaviors,
        'target_audience_interests': client_context.target_audience_interests,
        'seasonal_relevant_dates': client_context.seasonal_relevant_dates,
        'seasonal_local_events': client_context.seasonal_local_events,
        'brand_online_presence': client_context.brand_online_presence,
        'brand_reputation': client_context.brand_reputation,
        'brand_communication_style': client_context.brand_communication_style,
    }
