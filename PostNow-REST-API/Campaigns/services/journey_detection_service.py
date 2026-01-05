"""
Journey Detection Service - Detecta jornada ideal do usuário.

Baseado nas 25 simulações:
- 40% usuários → RÁPIDA (Bruno, 2min)
- 50% usuários → GUIADA (Ana, Eduarda, 15-30min)
- 10% usuários → AVANÇADA (Carla, Daniel, 30min-2h)

Critérios de detecção:
- Tempo médio gasto em campanhas anteriores
- Quantidade de edições e revisões
- Uso de features avançadas
- Expertise declarada no onboarding
"""

import logging
from typing import Literal
from django.db.models import Avg, Count
from datetime import timedelta

logger = logging.getLogger(__name__)

JourneyType = Literal['quick', 'guided', 'advanced']


class JourneyDetectionService:
    """
    Detecta qual jornada é ideal para o usuário.
    """
    
    def detect_user_journey_type(self, user, context: dict = None) -> JourneyType:
        """
        Detecta tipo de jornada ideal para o usuário.
        
        Args:
            user: Usuário
            context: Contexto adicional (opcional)
                - explicit_choice: 'quick' | 'guided' | 'advanced' (se usuário escolheu)
                - urgency: bool (se há urgência detectada)
        
        Returns:
            'quick' | 'guided' | 'advanced'
        """
        try:
            # Se usuário escolheu explicitamente, respeitar
            if context and context.get('explicit_choice'):
                return context['explicit_choice']
            
            # Se há urgência, sugerir quick
            if context and context.get('urgency'):
                return 'quick'
            
            # Analisar comportamento histórico
            historical_journey = self._analyze_historical_behavior(user)
            
            if historical_journey:
                return historical_journey
            
            # Usuário novo: inferir do onboarding
            onboarding_journey = self._infer_from_onboarding(user)
            
            return onboarding_journey
            
        except Exception as e:
            logger.warning(f"Erro na detecção de jornada, usando guided: {str(e)}")
            return 'guided'  # Default seguro
    
    def _analyze_historical_behavior(self, user) -> JourneyType | None:
        """
        Analisa comportamento em campanhas anteriores.
        
        Returns:
            JourneyType se houver histórico suficiente, None caso contrário
        """
        try:
            from Campaigns.models import Campaign, CampaignJourneyEvent
            from IdeaBank.models import PostIdea
            from django.db.models import Avg, F, DurationField
            from datetime import timedelta
            
            # Buscar eventos de jornada do usuário
            journey_events = CampaignJourneyEvent.objects.filter(
                user=user,
                event_type='completed'
            )
            
            # Se tem eventos registrados, usar análise avançada
            if journey_events.count() >= 2:
                # Calcular tempo médio gasto
                avg_time = journey_events.aggregate(
                    avg_duration=Avg('time_spent')
                )['avg_duration']
                
                if avg_time:
                    # Quick: < 10 minutos
                    if avg_time < timedelta(minutes=10):
                        return 'quick'
                    # Advanced: > 45 minutos
                    elif avg_time > timedelta(minutes=45):
                        return 'advanced'
                    # Guided: entre 10-45 minutos
                    else:
                        return 'guided'
            
            # Fallback: Analisar campanhas e posts
            campaigns = Campaign.objects.filter(user=user, status='completed')
            
            if campaigns.count() < 2:
                # Histórico insuficiente
                return None
            
            campaign_count = campaigns.count()
            
            # Analisar taxa de edição
            total_posts = 0
            edited_posts = 0
            
            for campaign in campaigns[:10]:  # Últimas 10 campanhas
                posts = PostIdea.objects.filter(
                    campaignpost__campaign=campaign
                )
                total_posts += posts.count()
                # Post editado = updated_at diferente de created_at
                edited_posts += posts.filter(
                    updated_at__gt=F('created_at')
                ).count()
            
            edit_rate = edited_posts / total_posts if total_posts > 0 else 0
            
            # Decisão baseada em comportamento:
            # Alta edição (>50%) + muitas campanhas = Advanced
            if edit_rate > 0.5 and campaign_count >= 5:
                return 'advanced'
            
            # Muitas campanhas + baixa edição = Quick
            if campaign_count >= 10 and edit_rate < 0.2:
                return 'quick'
            
            # Usuário moderado = Guided
            if campaign_count >= 3:
                return 'guided'
            
            # Ainda aprendendo
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao analisar histórico: {str(e)}")
            return None
    
    def _infer_from_onboarding(self, user) -> JourneyType:
        """
        Infere jornada baseado em dados do onboarding.
        
        Heurísticas:
        - Profissão criativa (designer, social media) → advanced
        - Profissão executiva (CEO, diretor) → quick
        - Profissão técnica (consultor, coach) → guided
        """
        try:
            from CreatorProfile.models import CreatorProfile
            
            profile = CreatorProfile.objects.filter(user=user).first()
            
            if not profile:
                return 'guided'
            
            # Analisar especialização
            spec = (profile.specialization or '').lower()
            
            # Criativos → Advanced (querem controle total)
            creative_keywords = ['design', 'social media', 'criativ', 'fotograf', 'video']
            if any(kw in spec for kw in creative_keywords):
                return 'advanced'
            
            # Executivos → Quick (querem rapidez)
            exec_keywords = ['ceo', 'diretor', 'executiv', 'empresari', 'empreendedor']
            if any(kw in spec for kw in exec_keywords):
                return 'quick'
            
            # Consultores/Coaches → Guided (equilíbrio)
            return 'guided'
            
        except Exception as e:
            logger.warning(f"Erro ao inferir do onboarding: {str(e)}")
            return 'guided'
    
    def should_offer_quick_mode(self, user) -> bool:
        """
        Decide se deve oferecer/destacar modo rápido.
        
        Baseado em:
        - Urgência detectada
        - Perfil executivo
        - Histórico de criação rápida
        """
        journey = self.detect_user_journey_type(user)
        return journey == 'quick'
    
    def should_show_advanced_controls(self, user) -> bool:
        """
        Decide se deve mostrar controles avançados.
        
        Baseado em:
        - Perfil criativo/expert
        - Uso histórico de features avançadas
        """
        journey = self.detect_user_journey_type(user)
        return journey == 'advanced'
    
    def get_journey_reasoning(self, user, detected_journey: JourneyType) -> dict:
        """
        Retorna o raciocínio por trás da jornada detectada.
        
        Returns:
            dict com explicações para o usuário
        """
        try:
            from Campaigns.models import Campaign, CampaignJourneyEvent
            
            # Verificar se tem histórico
            events_count = CampaignJourneyEvent.objects.filter(user=user).count()
            campaigns_count = Campaign.objects.filter(user=user).count()
            
            reasons = []
            
            if events_count >= 2:
                # Tem histórico de uso
                reasons.append({
                    'type': 'historical',
                    'message': f'Baseado em {campaigns_count} campanhas anteriores'
                })
            else:
                # Baseado em perfil
                reasons.append({
                    'type': 'profile',
                    'message': 'Baseado no seu perfil e preferências'
                })
            
            # Explicação específica por jornada
            journey_explanations = {
                'quick': {
                    'title': 'Jornada Rápida',
                    'description': 'Crie campanhas em 2-5 minutos',
                    'benefits': [
                        'Configurações automáticas inteligentes',
                        'Geração instantânea',
                        'Pode revisar e ajustar depois'
                    ],
                    'ideal_for': 'Profissionais ocupados que confiam na IA'
                },
                'guided': {
                    'title': 'Jornada Guiada',
                    'description': 'Crie campanhas em 15-30 minutos',
                    'benefits': [
                        'Wizard passo a passo intuitivo',
                        'Recomendações personalizadas',
                        'Preview antes de gerar'
                    ],
                    'ideal_for': 'Equilibra qualidade e velocidade'
                },
                'advanced': {
                    'title': 'Jornada Avançada',
                    'description': 'Controle total sobre cada detalhe',
                    'benefits': [
                        'Todas as configurações disponíveis',
                        'Estruturas personalizadas',
                        'Métricas e analytics detalhados'
                    ],
                    'ideal_for': 'Especialistas que querem controle máximo'
                }
            }
            
            return {
                'journey': detected_journey,
                'reasons': reasons,
                **journey_explanations[detected_journey]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter raciocínio: {str(e)}")
            return {
                'journey': detected_journey,
                'reasons': [],
                'title': 'Jornada Guiada',
                'description': 'Recomendação padrão'
            }
    
    def track_journey_event(
        self,
        user,
        campaign,
        event_type: str,
        journey_type: JourneyType,
        time_spent: timedelta = None,
        satisfaction_rating: int = None
    ):
        """
        Registra evento de jornada para aprendizado futuro.
        
        Args:
            user: Usuário
            campaign: Campanha relacionada
            event_type: 'started' | 'completed' | 'abandoned' | 'switched'
            journey_type: Jornada escolhida
            time_spent: Tempo gasto (opcional)
            satisfaction_rating: Nota de 1-10 (opcional)
        """
        try:
            from Campaigns.models import CampaignJourneyEvent
            
            CampaignJourneyEvent.objects.create(
                user=user,
                campaign=campaign,
                journey_type=journey_type,
                event_type=event_type,
                time_spent=time_spent,
                satisfaction_rating=satisfaction_rating
            )
            
            logger.info(
                f"Journey event tracked: user={user.id}, "
                f"journey={journey_type}, event={event_type}"
            )
            
        except Exception as e:
            logger.error(f"Erro ao registrar evento de jornada: {str(e)}")

