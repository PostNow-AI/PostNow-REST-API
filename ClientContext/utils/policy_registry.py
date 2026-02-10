from __future__ import annotations

from typing import Dict

from ClientContext.utils.policy_types import WeeklyContextPolicy


def get_policies() -> Dict[str, WeeklyContextPolicy]:
    """
    Policies versionadas em código.
    Mantemos poucas opções para evitar risco operacional.
    """
    default = WeeklyContextPolicy(
        key="default",
        languages=["lang_pt", "lang_en"],
        min_selected_by_section={
            "mercado": 3,
            "tendencias": 3,
            "concorrencia": 3,
            "publico": 3,
            "sazonalidade": 1,
            "marca": 1,
        },
        allowlist_min_coverage={
            "mercado": 3,
            "tendencias": 3,
            "concorrencia": 3,
            "publico": 2,
            "sazonalidade": 2,
            "marca": 1,
        },
        allowlist_ratio_threshold=0.60,
    )

    business_strict = WeeklyContextPolicy(
        key="business_strict",
        languages=["lang_pt", "lang_en"],
        min_selected_by_section={
            **default.min_selected_by_section,
            # mantém mínimos altos nas seções críticas
        },
        allowlist_min_coverage={
            **default.allowlist_min_coverage,
            # permite cair no modo allowlist estrito mais cedo
            "mercado": 2,
            "tendencias": 2,
            "concorrencia": 2,
        },
        allowlist_ratio_threshold=0.70,
    )

    broad_discovery = WeeklyContextPolicy(
        key="broad_discovery",
        languages=["lang_pt", "lang_en"],
        min_selected_by_section={
            **default.min_selected_by_section,
            # aceita um pouco menos de cobertura para não bloquear nichos com pouco dado
            "mercado": 2,
            "tendencias": 2,
            "concorrencia": 2,
        },
        allowlist_min_coverage={
            **default.allowlist_min_coverage,
            # entra em allowlist estrita mais raramente
            "mercado": 4,
            "tendencias": 4,
            "concorrencia": 4,
        },
        allowlist_ratio_threshold=0.50,
    )

    return {p.key: p for p in (default, business_strict, broad_discovery)}


def is_valid_policy_key(key: str) -> bool:
    return bool(key) and key in get_policies()


def get_policy(key: str) -> WeeklyContextPolicy:
    policies = get_policies()
    return policies.get(key) or policies["default"]


