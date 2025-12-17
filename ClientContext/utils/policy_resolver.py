from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ClientContext.utils.policy_registry import get_policy, is_valid_policy_key
from ClientContext.utils.policy_types import WeeklyContextPolicy


@dataclass(frozen=True)
class PolicyDecision:
    policy: WeeklyContextPolicy
    source: str  # "override" | "auto"
    reason: str
    override_value: Optional[str] = None


def _text(profile_data: Dict[str, Any], key: str) -> str:
    v = profile_data.get(key)
    return v.strip().lower() if isinstance(v, str) else ""


def resolve_policy(profile_data: Dict[str, Any]) -> PolicyDecision:
    """
    Resolve policy para um perfil.
    Precedência: override manual > automático.
    """
    override = _text(profile_data, "weekly_context_policy_override")
    if override:
        if is_valid_policy_key(override):
            return PolicyDecision(
                policy=get_policy(override),
                source="override",
                reason="manual_override",
                override_value=override,
            )
        # Override inválido: não quebra o fluxo; cai no auto e loga via reason
        # (log do uso fica no weekly_context_service)
        override_invalid_reason = f"invalid_override:{override}"
    else:
        override_invalid_reason = ""

    specialization = _text(profile_data, "specialization")
    desc = _text(profile_data, "business_description")
    products = _text(profile_data, "products_services")
    combined = " ".join([specialization, desc, products]).strip()

    if not specialization or len(desc) < 30:
        reason = "profile_incomplete_or_short_description"
        if override_invalid_reason:
            reason = f"{override_invalid_reason}|{reason}"
        return PolicyDecision(policy=get_policy("broad_discovery"), source="auto", reason=reason)

    regulated_keywords = (
        "advog", "jurid", "juríd", "contab", "contáb",
        "clinic", "clínic", "medic", "médic", "odont", "farmac",
        "saude", "saúde", "trabalhist", "previd", "oab",
        "invest", "finance", "seguro", "banco",
    )
    if any(k in combined for k in regulated_keywords):
        reason = "regulated_keywords_detected"
        if override_invalid_reason:
            reason = f"{override_invalid_reason}|{reason}"
        return PolicyDecision(policy=get_policy("business_strict"), source="auto", reason=reason)

    reason = "default_policy"
    if override_invalid_reason:
        reason = f"{override_invalid_reason}|{reason}"
    return PolicyDecision(policy=get_policy("default"), source="auto", reason=reason)


