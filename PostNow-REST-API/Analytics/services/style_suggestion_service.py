"""
Service para ranqueamento de estilos visuais usando Thompson Sampling.

Aprende quais estilos funcionam melhor para cada tipo de usuário.
CORRIGIDO: Usa decision_type + policy_id + bucket + action (padrão do sistema)
"""

import random
from typing import List
from django.contrib.auth.models import User
from Campaigns.models import VisualStyle
from Analytics.models import BanditArmStat, Decision


def rank_visual_styles(
    user: User,
    available_styles: List[VisualStyle],
    top_n: int = 18
) -> List[VisualStyle]:
    """
    Ranqueia estilos usando Thompson Sampling (Beta Distribution).
    
    Args:
        user: Usuário logado
        available_styles: Lista de estilos disponíveis
        top_n: Quantos retornar (default: todos 18, mas ranqueados)
    
    Returns:
        Lista de estilos ordenada por score Thompson
    """
    
    policy_id = 'style_ranking_thompson_v1'
    bucket = 'all_users'  # V2: Será segmentado por nicho
    
    style_scores = []
    
    for style in available_styles:
        # ✅ CORRIGIDO: Usa padrão decision_type+policy_id+bucket+action
        stat, created = BanditArmStat.objects.get_or_create(
            decision_type='visual_style_suggestion',
            policy_id=policy_id,
            bucket=bucket,
            action=str(style.id),  # ID do estilo como ação
            defaults={
                'alpha': 1.0,
                'beta': 1.0,
            }
        )
        
        # Thompson Sampling: sample from Beta distribution
        score = random.betavariate(stat.alpha, stat.beta)
        
        style_scores.append((style, score))
    
    # Ordenar por score (maior = melhor)
    style_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Pegar top N
    ranked = [style for style, score in style_scores[:top_n]]
    
    # Criar Decision para registro (não precisa de reward imediato)
    Decision.objects.create(
        user=user,
        decision_type='visual_style_ranking',
        action='ranked_list',  # ✅ CORRIGIDO: action ao invés de arm_id
        policy_id=policy_id,
        context={'ranked_count': len(ranked), 'bucket': bucket}
    )
    
    return ranked


def record_style_selection(user: User, selected_style_ids: List[int]):
    """
    Registra quais estilos usuário escolheu.
    Isso será usado para calcular reward depois.
    
    Args:
        user: Usuário que selecionou
        selected_style_ids: IDs dos estilos selecionados
    """
    policy_id = 'style_selection_v1'
    
    for style_id in selected_style_ids:
        Decision.objects.create(
            user=user,
            decision_type='visual_style_selected',
            action=str(style_id),  # ✅ CORRIGIDO: action ao invés de arm_id
            policy_id=policy_id,
            context={'source': 'user_selected'}
        )


def calculate_style_rewards_from_campaign(campaign) -> dict:
    """
    Calcula rewards para estilos baseado no sucesso da campanha.
    
    Retorna dict {style_id: reward}
    
    Lógica:
    - Se posts com este estilo tiveram alto engagement → reward alto
    - Se campanha foi gerada mas não usada → reward baixo
    """
    rewards = {}
    
    # TODO: Implementar quando tiver métricas de engagement
    # Por enquanto retorna 0.5 (neutro)
    for style_id in campaign.visual_styles:
        rewards[style_id] = 0.5
    
    return rewards

