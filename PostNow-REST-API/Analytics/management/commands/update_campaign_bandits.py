"""
Management command para atualizar bandits de campanhas.
Roda diariamente via cron para processar campanhas finalizadas.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from Campaigns.models import Campaign
from Analytics.models import Decision
from Analytics.services.campaign_policy import (
    DECISION_TYPE_CAMPAIGN_TYPE,
    DECISION_TYPE_CAMPAIGN_STRUCTURE,
    DECISION_TYPE_VISUAL_STYLE_CURATION,
    calculate_campaign_reward,
    update_bandit_from_reward,
)


class Command(BaseCommand):
    help = 'Atualiza estatísticas dos bandits de campanhas baseado em resultados'
    
    def handle(self, *args, **options):
        """
        Processa campanhas finalizadas nas últimas 24h.
        Calcula rewards e atualiza bandits.
        """
        
        cutoff = timezone.now() - timedelta(hours=24)
        
        # Buscar decisões sem outcome das últimas 24h
        decision_types = [
            DECISION_TYPE_CAMPAIGN_TYPE,
            DECISION_TYPE_CAMPAIGN_STRUCTURE,
            DECISION_TYPE_VISUAL_STYLE_CURATION,
        ]
        
        pending_decisions = Decision.objects.filter(
            decision_type__in=decision_types,
            occurred_at__gte=cutoff,
            outcome__isnull=True
        )
        
        self.stdout.write(f"Processando {pending_decisions.count()} decisões...")
        
        updated_count = 0
        
        for decision in pending_decisions:
            try:
                # Buscar campanha relacionada
                campaign_id = decision.context.get('campaign_id') or decision.resource_id
                
                if not campaign_id:
                    continue
                
                try:
                    campaign = Campaign.objects.get(id=campaign_id)
                except Campaign.DoesNotExist:
                    continue
                
                # Calcular reward
                reward = calculate_campaign_reward(campaign, decision)
                
                # Atualizar bandit
                update_bandit_from_reward(decision, reward)
                
                # Criar outcome
                from Analytics.models import DecisionOutcome
                DecisionOutcome.objects.create(
                    decision=decision,
                    reward=reward,
                    success=(reward > 0),
                    metrics={
                        'approval_rate': campaign.posts_approved_count / campaign.post_count
                        if campaign.post_count > 0 else 0
                    }
                )
                
                updated_count += 1
                
            except Exception as e:
                self.stderr.write(f"Erro ao processar decision {decision.id}: {str(e)}")
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ {updated_count} bandits atualizados com sucesso!')
        )

