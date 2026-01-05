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
    Curadoria inteligente de estilos usando Thompson Sampling + Histórico.
    
    Priorização (como solicitado):
    1. Estilos do onboarding (100 pontos)
    2. Estilos de campanhas anteriores (60 pontos)
    3. Performance no nicho via Thompson (40 pontos)
    4. Popularidade geral (10 pontos)
    
    Retorna estilos ordenados por probabilidade de sucesso.
    """
    
    # Determinar nicho
    niche = _determine_niche(profile.specialization if profile else "")
    
    # Buscar todos estilos ativos
    all_styles = VisualStyle.objects.filter(is_active=True)
    
    # 🆕 NOVO: Buscar histórico de estilos usados em campanhas
    from Campaigns.models import Campaign
    from collections import Counter
    
    # Estilos do onboarding
    onboarding_style_ids = profile.visual_style_ids if profile else []
    
    # Estilos de campanhas anteriores (apenas aprovadas/publicadas)
    previous_campaigns = Campaign.objects.filter(
        user=user,
        status__in=['pending_approval', 'approved', 'published']
    ).exclude(visual_styles__isnull=True)
    
    # Contar frequência de uso
    campaign_style_ids = []
    for campaign in previous_campaigns:
        if campaign.visual_styles:
            campaign_style_ids.extend(campaign.visual_styles)
    
    style_frequency = Counter(campaign_style_ids)
    
    # Calcular score para cada estilo
    style_scores = []
    
    for style in all_styles:
        bucket = f"niche={niche}"
        
        # Base score: Thompson Sampling
        stat = BanditArmStat.objects.filter(
            decision_type=DECISION_TYPE_STYLE_CURATION,
            policy_id="style_curation_v1",
            bucket=bucket,
            action=style.slug
        ).first()
        
        if stat:
            # Sample de distribuição Beta
            thompson_score = random.betavariate(stat.alpha, stat.beta)
        else:
            # Prior: Usar global_success_rate do estilo
            thompson_score = style.global_success_rate
            
            # Criar BanditArmStat inicial
            BanditArmStat.objects.create(
                decision_type=DECISION_TYPE_STYLE_CURATION,
                policy_id="style_curation_v1",
                bucket=bucket,
                action=style.slug,
                alpha=style.global_success_rate * 10,  # Prior forte
                beta=(1 - style.global_success_rate) * 10
            )
        
        # Inicializar score final
        final_score = 0
        
        # 1️⃣ PRIORIDADE 1: Estilos do ONBOARDING (100 pontos)
        if style.id in onboarding_style_ids:
            final_score += 100
        
        # 2️⃣ PRIORIDADE 2: Histórico de CAMPANHAS (60 pontos base + frequência)
        if style.id in style_frequency:
            usage_count = style_frequency[style.id]
            # 60 pontos base + até 30 pontos por uso frequente
            final_score += 60 + min(30, usage_count * 10)
        
        # 3️⃣ PRIORIDADE 3: Performance no NICHO via Thompson (40 pontos)
        final_score += thompson_score * 40
        
        # 4️⃣ PRIORIDADE 4: Popularidade GERAL (10 pontos)
        final_score += style.global_success_rate * 10
        
        style_scores.append((style, final_score))
    
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

