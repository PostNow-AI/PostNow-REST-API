"""
Campaign Policy - Thompson Sampling para decisões de campanhas.
Segue padrão de image_pregen_policy.py e text_variant_policy.py.
"""

import hashlib
import os
import random
from dataclasses import dataclass
from typing import List

from django.db import transaction
from django.utils import timezone

from Analytics.models import BanditArmStat, Decision


# ============================================================================
# DECISION TYPES
# ============================================================================

DECISION_TYPE_CAMPAIGN_TYPE = "campaign_type_suggestion"
DECISION_TYPE_CAMPAIGN_STRUCTURE = "campaign_structure"
DECISION_TYPE_VISUAL_STYLE_CURATION = "visual_style_curation"


# ============================================================================
# ACTIONS (Opções Disponíveis)
# ============================================================================

CAMPAIGN_TYPE_ACTIONS = [
    "branding",
    "sales",
    "launch",
    "education",
    "engagement",
    "lead_generation",
    "portfolio"
]

STRUCTURE_ACTIONS = [
    "aida",
    "pas",
    "funil",
    "bab",
    "storytelling",
    "simple"
]

# Estilos visuais - definidos dinamicamente baseado em VisualStyle model
# Por ora, lista estática será substituída por query do banco
VISUAL_STYLE_ACTIONS = [
    "minimal_clean",
    "corporate_blue",
    "modern_gradient",
    "bold_colorful",
    "professional_clean",
]


# ============================================================================
# POLICY IDS (Versionamento)
# ============================================================================

def get_active_campaign_type_policy_id() -> str:
    """Permite trocar policy por env var."""
    return os.getenv("CAMPAIGN_TYPE_POLICY_ID", "campaign_type_thompson_v1")


def get_active_structure_policy_id() -> str:
    return os.getenv("CAMPAIGN_STRUCTURE_POLICY_ID", "campaign_structure_thompson_v1")


def get_active_visual_style_policy_id() -> str:
    return os.getenv("VISUAL_STYLE_POLICY_ID", "visual_style_thompson_v1")


# ============================================================================
# BUCKET BUILDING (Contextualização)
# ============================================================================

def build_campaign_type_bucket(user, profile_data: dict) -> str:
    """
    Cria bucket para personalização de sugestão de tipo de campanha.
    
    Considera: nicho, maturidade do usuário, nível de atividade.
    """
    
    # Mapear nicho para categoria broad
    specialization = profile_data.get('specialization', '').lower()[:20]
    
    niche_mapping = {
        'advog': 'legal',
        'jurid': 'legal',
        'contab': 'financial',
        'financ': 'financial',
        'clinic': 'health',
        'medic': 'health',
        'saude': 'health',
        'consul': 'consulting',
        'ecommerce': 'retail',
        'loja': 'retail',
        'saas': 'tech',
        'tecnolog': 'tech',
    }
    
    niche = 'general'
    for keyword, category in niche_mapping.items():
        if keyword in specialization:
            niche = category
            break
    
    # Calcular maturidade (tempo desde cadastro)
    days_since_joined = (timezone.now() - user.date_joined).days
    if days_since_joined < 30:
        maturity = 'new'
    elif days_since_joined < 90:
        maturity = 'regular'
    else:
        maturity = 'advanced'
    
    # Nível de atividade (quantos posts criou)
    from IdeaBank.models import Post
    post_count = Post.objects.filter(user=user).count()
    
    if post_count < 10:
        activity = 'low'
    elif post_count < 50:
        activity = 'medium'
    else:
        activity = 'high'
    
    return f"niche={niche}|maturity={maturity}|activity={activity}"


def build_structure_bucket(campaign_type: str, profile_data: dict) -> str:
    """Bucket para escolha de estrutura baseado em tipo de campanha."""
    return f"campaign_type={campaign_type}"


def build_visual_style_bucket(niche: str, campaign_type: str) -> str:
    """Bucket para curadoria de estilos visuais."""
    return f"niche={niche}|campaign_type={campaign_type}"


# ============================================================================
# THOMPSON SAMPLING IMPLEMENTATION
# ============================================================================

def choose_action_thompson(
    decision_type: str,
    policy_id: str,
    bucket: str,
    available_actions: List[str]
) -> str:
    """
    Thompson Sampling: Escolhe ação baseado em distribuições Beta.
    Reutiliza lógica de image_pregen_policy.py.
    """
    
    # Buscar ou criar stats para cada ação
    stats = {}
    for action in available_actions:
        stat, created = BanditArmStat.objects.get_or_create(
            decision_type=decision_type,
            policy_id=policy_id,
            bucket=bucket,
            action=action,
            defaults={'alpha': 1.0, 'beta': 1.0}
        )
        stats[action] = stat
    
    # Sample de cada distribuição Beta
    samples = {
        action: random.betavariate(stats[action].alpha, stats[action].beta)
        for action in available_actions
    }
    
    # Retorna ação com maior sample
    return max(samples.items(), key=lambda x: x[1])[0]


# ============================================================================
# DECISION MAKERS
# ============================================================================

def make_campaign_type_decision(user, profile_data: dict, context: dict = None) -> Decision:
    """
    Decide automaticamente qual tipo de campanha sugerir.
    
    Args:
        user: Usuário
        profile_data: Dados do CreatorProfile
        context: Contexto adicional (opcional)
    
    Returns:
        Decision object com action = tipo sugerido
    """
    
    policy_id = get_active_campaign_type_policy_id()
    bucket = build_campaign_type_bucket(user, profile_data)
    
    # Thompson Sampling
    action = choose_action_thompson(
        decision_type=DECISION_TYPE_CAMPAIGN_TYPE,
        policy_id=policy_id,
        bucket=bucket,
        available_actions=CAMPAIGN_TYPE_ACTIONS
    )
    
    # Registrar decisão
    with transaction.atomic():
        return Decision.objects.create(
            decision_type=DECISION_TYPE_CAMPAIGN_TYPE,
            action=action,
            policy_id=policy_id,
            user=user,
            resource_type="Campaign",
            context={
                'bucket': bucket,
                **(context or {})
            },
            properties={}
        )


def make_structure_decision(user, campaign_type: str, profile_data: dict) -> Decision:
    """Decide qual estrutura narrativa sugerir."""
    
    policy_id = get_active_structure_policy_id()
    bucket = build_structure_bucket(campaign_type, profile_data)
    
    action = choose_action_thompson(
        decision_type=DECISION_TYPE_CAMPAIGN_STRUCTURE,
        policy_id=policy_id,
        bucket=bucket,
        available_actions=STRUCTURE_ACTIONS
    )
    
    with transaction.atomic():
        return Decision.objects.create(
            decision_type=DECISION_TYPE_CAMPAIGN_STRUCTURE,
            action=action,
            policy_id=policy_id,
            user=user,
            resource_type="Campaign",
            context={
                'bucket': bucket,
                'campaign_type': campaign_type
            },
            properties={}
        )


def make_visual_style_curation_decision(
    user,
    niche: str,
    campaign_type: str,
    available_styles: List[str]
) -> Decision:
    """
    Decide quais 3 estilos visuais mostrar inicialmente (curadoria).
    
    Na prática, retorna os 3 top estilos para este contexto.
    """
    
    policy_id = get_active_visual_style_policy_id()
    bucket = build_visual_style_bucket(niche, campaign_type)
    
    # Para curadoria, "action" é uma lista de 3 estilos
    # Simplificação: escolher top 3 por Thompson Sampling
    
    if len(available_styles) <= 3:
        # Se tem 3 ou menos, retornar todos
        curated = available_styles
    else:
        # Escolher 3 melhores por sampling
        curated = []
        remaining = available_styles.copy()
        
        for _ in range(min(3, len(remaining))):
            chosen = choose_action_thompson(
                decision_type=DECISION_TYPE_VISUAL_STYLE_CURATION,
                policy_id=policy_id,
                bucket=bucket,
                available_actions=remaining
            )
            curated.append(chosen)
            remaining.remove(chosen)
    
    # Registrar decisão (action = lista em formato string)
    with transaction.atomic():
        return Decision.objects.create(
            decision_type=DECISION_TYPE_VISUAL_STYLE_CURATION,
            action=','.join(curated),  # "minimal,corporate,modern"
            policy_id=policy_id,
            user=user,
            resource_type="VisualStyleCuration",
            context={
                'bucket': bucket,
                'curated_styles': curated,
                'total_available': len(available_styles)
            },
            properties={}
        )


# ============================================================================
# REWARD CALCULATION (Para atualização de bandits)
# ============================================================================

def calculate_campaign_reward(campaign, decision: Decision) -> float:
    """
    Calcula recompensa de uma decisão baseado em resultado da campanha.
    
    Recompensa alta: Usuário aprovou tudo sem editar
    Recompensa média: Aprovou com algumas edições
    Recompensa baixa: Rejeitou ou abandonou
    
    Returns:
        Float entre -1.0 e 1.0
    """
    
    # Se campanha não foi completada, reward neutro
    if campaign.status not in ['approved', 'completed']:
        return 0.0
    
    # Calcular taxa de aprovação
    total_posts = campaign.campaign_posts.count()
    if total_posts == 0:
        return 0.0
    
    approved_posts = campaign.campaign_posts.filter(is_approved=True).count()
    approval_rate = approved_posts / total_posts
    
    # Calcular taxa de edição (proxy de satisfação)
    # (Lógica completa requer tracking de edições - simplificado por ora)
    
    # Recompensa baseada em aprovação
    if approval_rate >= 0.9:
        reward = 1.0  # Excelente
    elif approval_rate >= 0.7:
        reward = 0.5  # Bom
    elif approval_rate >= 0.5:
        reward = 0.0  # Neutro
    else:
        reward = -0.5  # Ruim
    
    return reward


def update_bandit_from_reward(decision: Decision, reward: float):
    """
    Atualiza estatísticas do bandit baseado na recompensa.
    Converte reward (-1 a 1) para update de Beta distribution.
    """
    
    bucket = decision.context.get('bucket', 'default')
    
    # Buscar stat
    try:
        arm_stat = BanditArmStat.objects.get(
            decision_type=decision.decision_type,
            policy_id=decision.policy_id,
            bucket=bucket,
            action=decision.action
        )
    except BanditArmStat.DoesNotExist:
        logger.warning(f"BanditArmStat não encontrado para decision {decision.id}")
        return
    
    # Converter reward [-1, 1] para success probability [0, 1]
    success_prob = (reward + 1.0) / 2.0
    
    # Atualizar Beta-Binomial
    if reward > 0:
        # Sucesso: aumenta alpha
        arm_stat.alpha += success_prob
    else:
        # Falha: aumenta beta
        arm_stat.beta += (1.0 - success_prob)
    
    arm_stat.save()
    
    logger.info(
        f"Updated bandit: {decision.decision_type}:{decision.action} "
        f"(bucket={bucket}) alpha={arm_stat.alpha:.2f} beta={arm_stat.beta:.2f}"
    )

