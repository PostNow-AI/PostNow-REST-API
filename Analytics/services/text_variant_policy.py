import os

from django.db import transaction

from Analytics.models import Decision


DECISION_TYPE_TEXT_VARIANT = "text_variant"


def get_active_text_variant_policy_id() -> str:
    """
    Permite troca por env var sem mexer em .env automaticamente.
    """
    return os.getenv("TEXT_VARIANT_POLICY_ID", "text_variant_fixed_v0")


def make_text_variant_decision(user, resource_type: str, resource_id: str, context: dict) -> Decision:
    """
    Base mínima para bandit de variantes de texto.

    Nesta fase, não altera o comportamento: registra a decisão 'default' para permitir
    correlação futura com eventos (copy/save/regenerate).
    """
    policy_id = get_active_text_variant_policy_id()
    action = "default"

    with transaction.atomic():
        return Decision.objects.create(
            decision_type=DECISION_TYPE_TEXT_VARIANT,
            action=action,
            policy_id=policy_id,
            user=user,
            resource_type=resource_type or "",
            resource_id=resource_id or "",
            context=context or {},
            properties={},
        )

