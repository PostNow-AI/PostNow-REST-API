"""
Visual Style Curation Service - Rankeia estilos por Thompson Sampling.
Sistema de recompensa por posição: 1º = +1.0, 2º = +0.7, 3º = +0.4
"""

import random
from typing import List, Tuple

from django.db import transaction

from Analytics.models import BanditArmStat, Decision
from Campaigns.models import VisualStyle


DECISION_TYPE_STYLE_CURATION = "visual_style_curation"


def curate_styles_for_user(user, profile, limit: int = 3) -> List[VisualStyle]:
    """
    Curadoria inteligente de estilos usando Thompson Sampling.
    Retorna estilos ordenados por probabilidade de sucesso.
    """
    
    # Determinar nicho
    niche = _determine_niche(profile.specialization if profile else "")
    
    # Buscar todos estilos ativos
    all_styles = VisualStyle.objects.filter(is_active=True)
    
    # Calcular score Thompson para cada estilo
    style_scores = []
    
    for style in all_styles:
        bucket = f"niche={niche}"
        
        # Buscar BanditArmStat
        stat = BanditArmStat.objects.filter(
            decision_type=DECISION_TYPE_STYLE_CURATION,
            policy_id="style_curation_v1",
            bucket=bucket,
            action=style.slug
        ).first()
        
        if stat:
            # Sample de distribuição Beta
            score = random.betavariate(stat.alpha, stat.beta)
        else:
            # Prior: Usar global_success_rate do estilo
            score = style.global_success_rate
            
            # Criar BanditArmStat inicial
            BanditArmStat.objects.create(
                decision_type=DECISION_TYPE_STYLE_CURATION,
                policy_id="style_curation_v1",
                bucket=bucket,
                action=style.slug,
                alpha=style.global_success_rate * 10,  # Prior forte
                beta=(1 - style.global_success_rate) * 10
            )
        
        style_scores.append((style, score))
    
    # Ordenar por score (maior primeiro)
    sorted_styles = sorted(style_scores, key=lambda x: x[1], reverse=True)
    
    # Retornar top N
    return [s[0] for s in sorted_styles[:limit]]


def calculate_style_position_reward(decision: Decision, campaign) -> float:
    """
    Calcula reward baseado na posição de escolha.
    
    Recompensa:
    - 1º escolhido: +1.0
    - 2º escolhido: +0.7
    - 3º escolhido: +0.4
    - Não escolhido: -0.2
    - Bônus se campanha aprovada: +0.3
    """
    
    chosen_style = decision.action  # Ex: "minimal_clean"
    selected_styles = campaign.visual_styles  # Lista de slugs escolhidos
    
    if chosen_style in selected_styles:
        # Encontrar posição (0-indexed)
        position = selected_styles.index(chosen_style)
        
        # Reward decrescente por posição
        position_rewards = {
            0: 1.0,   # Primeiro (mais valorizado)
            1: 0.7,   # Segundo
            2: 0.4,   # Terceiro
        }
        
        reward = position_rewards.get(position, 0.2)
        
        # Bônus se campanha foi aprovada
        if campaign.is_fully_approved:
            reward += 0.3
        
        return min(1.0, reward)  # Cap em 1.0
    
    else:
        # Estilo não foi escolhido (penalidade)
        return -0.2


def _determine_niche(specialization: str) -> str:
    """Mapeia especialização para nicho broad."""
    
    spec_lower = specialization.lower()
    
    if any(k in spec_lower for k in ['advog', 'jurid']):
        return 'legal'
    elif any(k in spec_lower for k in ['contab', 'financ']):
        return 'financial'
    elif any(k in spec_lower for k in ['clinic', 'medic', 'saude']):
        return 'health'
    elif any(k in spec_lower for k in ['consul', 'estrateg']):
        return 'consulting'
    elif any(k in spec_lower for k in ['ecommerce', 'loja', 'varejo']):
        return 'retail'
    elif any(k in spec_lower for k in ['tech', 'software', 'saas']):
        return 'tech'
    else:
        return 'general'


def make_style_curation_decisions(user, profile, limit: int = 3) -> List[Tuple[VisualStyle, str]]:
    """
    Faz decisões de curadoria e registra cada uma.
    Retorna: [(style, decision_id), ...]
    """
    
    curated_styles = curate_styles_for_user(user, profile, limit)
    
    niche = _determine_niche(profile.specialization if profile else "")
    bucket = f"niche={niche}"
    
    results = []
    
    for style in curated_styles:
        with transaction.atomic():
            decision = Decision.objects.create(
                decision_type=DECISION_TYPE_STYLE_CURATION,
                action=style.slug,
                policy_id="style_curation_v1",
                user=user,
                resource_type="StyleCuration",
                context={
                    'bucket': bucket,
                    'niche': niche,
                    'style_name': style.name
                }
            )
        
        results.append((style, str(decision.id)))
    
    return results

