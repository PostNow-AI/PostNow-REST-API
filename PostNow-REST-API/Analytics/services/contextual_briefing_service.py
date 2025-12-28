"""
Contextual Briefing Service - IA para sugestões de objetivo de campanha.
Copia padrão de image_pregen_policy.py (Thompson Sampling) e adiciona features contextuais.

Sistema de Recompensa: Aprende quais sugestões funcionam melhor por contexto.
"""

import os
import random
from typing import Dict

from django.db import transaction
from django.utils import timezone

from Analytics.models import BanditArmStat, Decision
from services.ai_service import AiService


# ============================================================================
# DECISION TYPE
# ============================================================================

DECISION_TYPE_BRIEFING_SUGGESTION = "briefing_objective_suggestion"


# ============================================================================
# PROMPT VARIANTS (Ações do Bandit)
# ============================================================================

PROMPT_VARIANTS = {
    "template_authority": "template",  # Template: Posicionar como autoridade
    "template_sales": "template",  # Template: Aumentar vendas
    "template_education": "template",  # Template: Educar público
    "ai_custom_gemini": "ai",  # IA Gemini gera sugestão
}


# ============================================================================
# POLICY ID
# ============================================================================

def get_active_briefing_policy_id() -> str:
    """Permite trocar policy por env var."""
    return os.getenv("BRIEFING_SUGGESTION_POLICY_ID", "briefing_contextual_v1")


# ============================================================================
# BUCKET BUILDING (Contextualização)
# ============================================================================

def build_bucket(profile_data: Dict, user) -> str:
    """
    Cria bucket para personalização.
    
    Features:
    - niche: Nicho do negócio
    - maturity: Tempo no sistema
    - activity: Nível de uso
    """
    
    # Niche
    specialization = profile_data.get('specialization', '').lower()[:20]
    
    niche_mapping = {
        'advog': 'legal',
        'jurid': 'legal',
        'contab': 'financial',
        'financ': 'financial',
        'clinic': 'health',
        'medic': 'health',
        'consul': 'consulting',
        'ecommerce': 'retail',
        'loja': 'retail',
        'saas': 'tech',
    }
    
    niche = 'general'
    for keyword, category in niche_mapping.items():
        if keyword in specialization:
            niche = category
            break
    
    # Maturity
    days_since = (timezone.now() - user.date_joined).days
    maturity = 'new' if days_since < 30 else 'regular' if days_since < 90 else 'advanced'
    
    # Activity
    from IdeaBank.models import Post
    post_count = Post.objects.filter(user=user).count()
    activity = 'low' if post_count < 10 else 'medium' if post_count < 50 else 'high'
    
    return f"niche={niche}|maturity={maturity}|activity={activity}"


# ============================================================================
# THOMPSON SAMPLING (Copiado de image_pregen_policy.py)
# ============================================================================

def choose_action_thompson(policy_id: str, bucket: str, available_actions: list) -> str:
    """
    Thompson Sampling - Escolhe melhor variante de prompt.
    CÓPIA EXATA de image_pregen_policy.py linhas 44-73.
    """
    
    stats = {}
    for action in available_actions:
        stat, created = BanditArmStat.objects.get_or_create(
            decision_type=DECISION_TYPE_BRIEFING_SUGGESTION,
            policy_id=policy_id,
            bucket=bucket,
            action=action,
            defaults={'alpha': 1.0, 'beta': 1.0}
        )
        stats[action] = stat
    
    # Cold-start handling (primeiros 100 usuários)
    total_samples = sum(s.alpha + s.beta - 2 for s in stats.values())
    
    if total_samples < 100:
        # Priors fortes (assume 75% sucesso para templates)
        for action, stat in stats.items():
            if action.startswith("template"):
                stat.alpha = max(stat.alpha, 3.0)
                stat.beta = max(stat.beta, 1.0)
    
    # Sample de cada distribuição Beta
    samples = {
        action: random.betavariate(stats[action].alpha, stats[action].beta)
        for action in available_actions
    }
    
    return max(samples.items(), key=lambda x: x[1])[0]


# ============================================================================
# DECISION MAKER
# ============================================================================

def make_briefing_suggestion_decision(user, profile_data: dict) -> tuple[str, str]:
    """
    Gera sugestão de objetivo usando Contextual Bandits.
    
    Returns:
        (suggestion_text, decision_id)
    """
    
    policy_id = get_active_briefing_policy_id()
    bucket = build_bucket(profile_data, user)
    
    available_actions = list(PROMPT_VARIANTS.keys())
    
    # Thompson Sampling escolhe variante
    chosen_variant = choose_action_thompson(policy_id, bucket, available_actions)
    
    # Gerar sugestão baseada na variante
    suggestion = generate_suggestion(chosen_variant, profile_data, user)
    
    # Registrar decisão
    with transaction.atomic():
        decision = Decision.objects.create(
            decision_type=DECISION_TYPE_BRIEFING_SUGGESTION,
            action=chosen_variant,
            policy_id=policy_id,
            user=user,
            resource_type="BriefingSuggestion",
            context={
                'bucket': bucket,
                'suggestion_generated': suggestion,
                'suggestion_length': len(suggestion),
                'profile_niche': profile_data.get('specialization', '')[:50]
            },
            properties={}
        )
    
    return suggestion, str(decision.id)


# ============================================================================
# SUGGESTION GENERATION
# ============================================================================

def generate_suggestion(variant: str, profile_data: Dict, user) -> str:
    """Gera sugestão baseada na variante escolhida."""
    
    business_name = profile_data.get('business_name', 'sua empresa')
    specialization = profile_data.get('specialization', 'seu nicho')
    target_audience = profile_data.get('target_audience', 'seu público')
    products = profile_data.get('products_services', 'seus produtos/serviços')
    
    if variant == "template_authority":
        return f"Posicionar {business_name} como autoridade em {specialization}, educando {target_audience} sobre tendências e boas práticas do mercado."
    
    elif variant == "template_sales":
        return f"Aumentar vendas de {products}, demonstrando valor e diferenciais para {target_audience}."
    
    elif variant == "template_education":
        return f"Educar {target_audience} sobre {specialization}, construindo confiança e relacionamento de longo prazo."
    
    elif variant == "ai_custom_gemini":
        # Usar IA para gerar sugestão customizada
        try:
            ai_service = AiService()
            prompt = f"""Baseado neste perfil de negócio:
- Nome: {business_name}
- Especialização: {specialization}
- Público-alvo: {target_audience}
- Produtos/Serviços: {products}

Sugira em 1-2 frases curtas e diretas o objetivo de uma campanha de marketing para este negócio.
Seja específico e acionável."""
            
            result = ai_service.generate_text(
                prompt_list=[prompt],
                user=user,
                return_metadata=False
            )
            
            # Limpar e retornar
            return result.strip() if isinstance(result, str) else result.get('text', '').strip()
        
        except Exception as e:
            # Fallback para template se IA falhar
            return generate_suggestion("template_authority", profile_data, user)
    
    # Fallback
    return f"Criar campanha de marketing para {business_name}."


# ============================================================================
# REWARD CALCULATION
# ============================================================================

def calculate_briefing_reward(decision: Decision, campaign) -> float:
    """
    Calcula recompensa baseado em uso da sugestão.
    
    Recompensa:
    +1.0: Usuário manteve 90%+ da sugestão
    +0.6: Usuário manteve 70-90%
    +0.3: Usuário manteve 40-70%
    0.0: Usuário manteve 10-40%
    -0.5: Usuário apagou tudo e escreveu do zero
    """
    
    original_suggestion = decision.context.get('suggestion_generated', '')
    user_final_objective = campaign.objective
    
    if not original_suggestion or not user_final_objective:
        return 0.0
    
    # Similaridade simples (character overlap)
    # TODO: Migrar para embeddings em V2
    similarity = simple_text_similarity(original_suggestion, user_final_objective)
    
    if similarity > 0.9:
        reward = 1.0
    elif similarity > 0.7:
        reward = 0.6
    elif similarity > 0.4:
        reward = 0.3
    elif similarity > 0.1:
        reward = 0.0
    else:
        reward = -0.5
    
    # Bônus se campanha foi aprovada
    if campaign.is_fully_approved:
        reward += 0.2
    
    return max(-1.0, min(1.0, reward))  # Clamp [-1, 1]


def simple_text_similarity(text1: str, text2: str) -> float:
    """Similaridade simples baseada em caracteres comuns."""
    if not text1 or not text2:
        return 0.0
    
    # Normalizar
    t1 = set(text1.lower().split())
    t2 = set(text2.lower().split())
    
    # Jaccard similarity
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    
    return intersection / union if union > 0 else 0.0


def update_bandit_from_reward(decision: Decision, reward: float):
    """
    Atualiza bandit baseado na recompensa.
    Converte reward [-1, 1] para update de Beta distribution.
    """
    
    bucket = decision.context.get('bucket', 'default')
    
    try:
        arm_stat = BanditArmStat.objects.get(
            decision_type=decision.decision_type,
            policy_id=decision.policy_id,
            bucket=bucket,
            action=decision.action
        )
    except BanditArmStat.DoesNotExist:
        return
    
    # Converter reward para success probability
    success_prob = (reward + 1.0) / 2.0
    
    # Atualizar Beta-Binomial
    if reward > 0:
        arm_stat.alpha += success_prob
    else:
        arm_stat.beta += (1.0 - success_prob)
    
    arm_stat.save()

