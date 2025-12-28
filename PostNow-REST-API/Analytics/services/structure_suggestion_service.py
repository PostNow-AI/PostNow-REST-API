"""
Structure Suggestion Service - IA para sugerir estrutura narrativa.
Usa Thompson Sampling baseado em contexto (tipo de campanha, nicho).
"""

import os
import random
from typing import List

from django.db import transaction

from Analytics.models import BanditArmStat, Decision


DECISION_TYPE_STRUCTURE_SUGGESTION = "campaign_structure_suggestion"

STRUCTURE_ACTIONS = ["aida", "pas", "funil", "bab", "storytelling", "simple"]


def get_active_structure_policy_id() -> str:
    return os.getenv("STRUCTURE_SUGGESTION_POLICY_ID", "structure_thompson_v1")


def build_bucket(campaign_type: str, niche: str) -> str:
    """Bucket: tipo de campanha + nicho"""
    return f"campaign_type={campaign_type}|niche={niche}"


def choose_action_thompson(policy_id: str, bucket: str, available_actions: List[str]) -> str:
    """Thompson Sampling - cópia de image_pregen_policy.py"""
    
    stats = {}
    for action in available_actions:
        stat, created = BanditArmStat.objects.get_or_create(
            decision_type=DECISION_TYPE_STRUCTURE_SUGGESTION,
            policy_id=policy_id,
            bucket=bucket,
            action=action,
            defaults={'alpha': 1.0, 'beta': 1.0}
        )
        stats[action] = stat
    
    # Cold-start: priors baseados em dados das simulações
    total_samples = sum(s.alpha + s.beta - 2 for s in stats.values())
    
    if total_samples < 50:
        # Priors das simulações
        priors = {
            "simple": (3.5, 0.5),  # 89% sucesso
            "aida": (3.2, 0.8),    # 87%
            "storytelling": (3.1, 0.9),  # 82%
            "funil": (3.0, 1.0),   # 81%
            "bab": (2.8, 1.2),     # 76%
            "pas": (2.6, 1.4),     # 72%
        }
        
        for action, (alpha, beta) in priors.items():
            if action in stats:
                stats[action].alpha = max(stats[action].alpha, alpha)
                stats[action].beta = max(stats[action].beta, beta)
    
    # Sample
    samples = {
        action: random.betavariate(stats[action].alpha, stats[action].beta)
        for action in available_actions
    }
    
    return max(samples.items(), key=lambda x: x[1])[0]


def make_structure_suggestion(user, campaign_type: str, niche: str):
    """Sugere estrutura narrativa usando Thompson Sampling."""
    
    policy_id = get_active_structure_policy_id()
    bucket = build_bucket(campaign_type, niche)
    
    suggested = choose_action_thompson(policy_id, bucket, STRUCTURE_ACTIONS)
    
    with transaction.atomic():
        decision = Decision.objects.create(
            decision_type=DECISION_TYPE_STRUCTURE_SUGGESTION,
            action=suggested,
            policy_id=policy_id,
            user=user,
            resource_type="StructureSuggestion",
            context={
                'bucket': bucket,
                'campaign_type': campaign_type,
                'niche': niche
            }
        )
    
    return suggested, str(decision.id)


def calculate_structure_reward(decision: Decision, campaign) -> float:
    """Reward: 1.0 se escolheu sugerido, -0.5 se rejeitou"""
    
    suggested_structure = decision.action
    chosen_structure = campaign.structure
    
    if suggested_structure == chosen_structure:
        # Aceitou sugestão
        reward = 1.0
        
        # Bônus se campanha foi aprovada
        if campaign.is_fully_approved:
            reward += 0.3
    else:
        # Rejeitou sugestão
        reward = -0.3
    
    return reward

