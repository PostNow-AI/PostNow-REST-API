import hashlib
import os
import random
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from Analytics.models import BanditArmStat, Decision


DECISION_TYPE_IMAGE_PREGEN = "image_pregen"
ACTION_PRE_GENERATE = "pre_generate"
ACTION_ON_DEMAND = "on_demand"


def get_active_image_pregen_policy_id() -> str:
    """
    Permite troca por env var sem mexer em .env automaticamente.
    """

    return os.getenv("IMAGE_PREGEN_POLICY_ID", "image_pregen_bandit_v0")


def build_bucket(context: dict) -> str:
    post_type = (context.get("post_type") or "unknown").lower()
    objective = (context.get("objective") or "unknown").lower()
    return f"type={post_type}|obj={objective}"


def _deterministic_roll(user_id: int, salt: str) -> int:
    raw = f"{user_id}:{salt}".encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()
    return int(h[:8], 16) % 100


def choose_action_v0(user_id: int, bucket: str) -> str:
    # Exploração determinística 50/50 por dia para evitar flapping por request
    salt = timezone.now().strftime("%Y-%m-%d") + "|" + bucket
    roll = _deterministic_roll(user_id, salt)
    return ACTION_PRE_GENERATE if roll < 50 else ACTION_ON_DEMAND


def choose_action_thompson(policy_id: str, bucket: str) -> str:
    actions = [ACTION_PRE_GENERATE, ACTION_ON_DEMAND]

    stats = {
        s.action: s
        for s in BanditArmStat.objects.filter(
            decision_type=DECISION_TYPE_IMAGE_PREGEN,
            policy_id=policy_id,
            bucket=bucket,
        )
    }

    # Criar estado default se não existir
    for action in actions:
        if action in stats:
            continue
        stats[action] = BanditArmStat.objects.create(
            decision_type=DECISION_TYPE_IMAGE_PREGEN,
            policy_id=policy_id,
            bucket=bucket,
            action=action,
            alpha=1.0,
            beta=1.0,
        )

    samples = {
        action: random.betavariate(stats[action].alpha, stats[action].beta)
        for action in actions
    }
    return max(samples.items(), key=lambda x: x[1])[0]


@dataclass(frozen=True)
class ImagePregenDecisionInput:
    user_id: int
    resource_type: str
    resource_id: str
    context: dict


def make_image_pregen_decision(user, resource_type: str, resource_id: str, context: dict) -> Decision:
    policy_id = get_active_image_pregen_policy_id()
    bucket = build_bucket(context)

    if policy_id == "image_pregen_bandit_v1":
        action = choose_action_thompson(policy_id=policy_id, bucket=bucket)
    else:
        action = choose_action_v0(user_id=user.id, bucket=bucket)

    with transaction.atomic():
        return Decision.objects.create(
            decision_type=DECISION_TYPE_IMAGE_PREGEN,
            action=action,
            policy_id=policy_id,
            user=user,
            resource_type=resource_type or "",
            resource_id=resource_id or "",
            context={**(context or {}), "bucket": bucket},
            properties={},
        )

