"""
Weekly Context Service - Análise de Mercado e Oportunidades de Conteúdo.

Responsável por:
- Identificar oportunidades do mercado (trends, datas comemorativas, eventos)
- Calcular relevância para cada campanha/nicho
- Sugerir posts baseados em oportunidades

MVP: Calendário de datas + oportunidades curadas manualmente
V2: Integração com Google Trends + NewsAPI
V3: ML para detectar tendências automaticamente
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class WeeklyContextService:
    """
    Service para gerenciar contexto semanal e oportunidades de mercado.
    """
    
    # MVP: Calendário brasileiro de datas importantes (curado manualmente)
    BRAZILIAN_CALENDAR = {
        '01-01': {
            'title': 'Ano Novo',
            'category': 'seasonal',
            'keywords': ['metas', 'objetivos', 'novo ano', 'recomeço', 'planejamento'],
            'ideal_for': ['coaching', 'consultoria', 'educação'],
            'advance_days': 14  # Começar 2 semanas antes
        },
        '01-25': {
            'title': 'Aniversário de São Paulo',
            'category': 'regional',
            'keywords': ['são paulo', 'sampa', 'cidade', 'paulista'],
            'ideal_for': ['local_business', 'eventos'],
            'advance_days': 7
        },
        '02-14': {
            'title': 'Dia dos Namorados',
            'category': 'commercial',
            'keywords': ['amor', 'relacionamento', 'presente', 'casal'],
            'ideal_for': ['ecommerce', 'presentes', 'restaurantes'],
            'advance_days': 21
        },
        '03-08': {
            'title': 'Dia Internacional da Mulher',
            'category': 'awareness',
            'keywords': ['mulher', 'empoderamento', 'igualdade', 'feminino'],
            'ideal_for': ['consultoria', 'educação', 'saúde'],
            'advance_days': 14
        },
        '04-21': {
            'title': 'Tiradentes',
            'category': 'feriado',
            'keywords': ['feriado', 'descanso', 'viagem'],
            'ideal_for': ['turismo', 'lazer'],
            'advance_days': 7
        },
        '05-01': {
            'title': 'Dia do Trabalho',
            'category': 'awareness',
            'keywords': ['trabalho', 'carreira', 'profissional'],
            'ideal_for': ['rh', 'consultoria', 'coaching'],
            'advance_days': 14
        },
        '05-12': {
            'title': 'Dia das Mães',
            'category': 'commercial',
            'keywords': ['mãe', 'família', 'presente', 'homenagem'],
            'ideal_for': ['ecommerce', 'presentes', 'beleza'],
            'advance_days': 21
        },
        '06-12': {
            'title': 'Dia dos Namorados',
            'category': 'commercial',
            'keywords': ['amor', 'casal', 'presente'],
            'ideal_for': ['ecommerce', 'presentes'],
            'advance_days': 21
        },
        '08-11': {
            'title': 'Dia dos Pais',
            'category': 'commercial',
            'keywords': ['pai', 'família', 'presente', 'homenagem'],
            'ideal_for': ['ecommerce', 'presentes', 'tech'],
            'advance_days': 21
        },
        '09-07': {
            'title': 'Independência do Brasil',
            'category': 'feriado',
            'keywords': ['brasil', 'pátria', 'independência'],
            'ideal_for': ['educação', 'cultura'],
            'advance_days': 7
        },
        '10-12': {
            'title': 'Dia das Crianças',
            'category': 'commercial',
            'keywords': ['criança', 'brinquedo', 'diversão', 'família'],
            'ideal_for': ['ecommerce', 'educação', 'lazer'],
            'advance_days': 21
        },
        '11-15': {
            'title': 'Proclamação da República',
            'category': 'feriado',
            'keywords': ['república', 'feriado'],
            'ideal_for': ['educação'],
            'advance_days': 7
        },
        '11-20': {
            'title': 'Consciência Negra',
            'category': 'awareness',
            'keywords': ['consciência', 'igualdade', 'diversidade'],
            'ideal_for': ['educação', 'cultura', 'social'],
            'advance_days': 14
        },
        '11-24': {
            'title': 'Black Friday',
            'category': 'commercial',
            'keywords': ['desconto', 'promoção', 'oferta', 'compra'],
            'ideal_for': ['ecommerce', 'varejo', 'serviços'],
            'advance_days': 30  # Começar 1 mês antes!
        },
        '12-25': {
            'title': 'Natal',
            'category': 'seasonal',
            'keywords': ['natal', 'presente', 'família', 'celebração'],
            'ideal_for': ['ecommerce', 'presentes', 'restaurantes'],
            'advance_days': 30
        }
    }
    
    def get_opportunities_for_user(
        self,
        user,
        niche: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Retorna oportunidades relevantes para o usuário.
        
        Args:
            user: Usuário (para inferir nicho se não fornecido)
            niche: Nicho específico (opcional)
            limit: Quantidade máxima de oportunidades
        
        Returns:
            Lista de oportunidades ordenadas por relevância
        """
        try:
            # Inferir nicho do perfil se não fornecido
            if not niche:
                niche = self._infer_niche_from_user(user)
            
            # Buscar oportunidades próximas (próximos 60 dias)
            today = datetime.now()
            opportunities = []
            
            for day_month, data in self.BRAZILIAN_CALENDAR.items():
                # Parse data
                month, day = map(int, day_month.split('-'))
                
                # Calcular próxima ocorrência
                event_date = datetime(today.year, month, day)
                
                # Se já passou este ano, pegar ano que vem
                if event_date < today:
                    event_date = datetime(today.year + 1, month, day)
                
                # Considerar apenas próximos 60 dias
                days_until = (event_date - today).days
                
                if days_until > 60:
                    continue
                
                # Verificar se está no período de antecedência ideal
                advance_window_start = data['advance_days']
                advance_window_end = 3  # Até 3 dias antes
                
                # Relevância baseada em timing
                if days_until >= advance_window_end and days_until <= advance_window_start:
                    # Janela ideal
                    timing_relevance = 100
                elif days_until < advance_window_end:
                    # Muito próximo (urgente!)
                    timing_relevance = 90
                elif days_until > advance_window_start:
                    # Ainda cedo
                    timing_relevance = 70
                else:
                    continue
                
                # Relevância por nicho
                niche_relevance = 100 if niche in data.get('ideal_for', []) else 50
                
                # Score final
                relevance_score = int((timing_relevance + niche_relevance) / 2)
                
                opportunities.append({
                    'id': f"cal_{day_month.replace('-', '_')}",
                    'title': data['title'],
                    'summary': self._generate_summary(data, event_date, days_until),
                    'relevance_score': relevance_score,
                    'category': data['category'],
                    'date': event_date.strftime('%Y-%m-%d'),
                    'days_until': days_until,
                    'keywords': data['keywords']
                })
            
            # Ordenar por relevância
            opportunities.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Retornar top N
            return opportunities[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao buscar oportunidades: {str(e)}")
            return []
    
    def _infer_niche_from_user(self, user) -> str:
        """Infere nicho do perfil do usuário."""
        try:
            from CreatorProfile.models import CreatorProfile
            
            profile = CreatorProfile.objects.filter(user=user).first()
            
            if not profile or not profile.specialization:
                return 'general'
            
            spec = profile.specialization.lower()
            
            # Mapear especialização para nichos amplos
            niche_map = {
                'ecommerce': ['ecommerce', 'loja', 'varejo', 'venda'],
                'educação': ['educa', 'ensino', 'curso', 'professor'],
                'saúde': ['saúde', 'médic', 'clinic', 'nutrição'],
                'consultoria': ['consul', 'estratég', 'mentor', 'coach'],
                'tech': ['tech', 'software', 'saas', 'digital', 'tecnologia'],
                'marketing': ['marketing', 'publicidade', 'comunicação'],
                'advocacia': ['advog', 'jurídic', 'direito']
            }
            
            for niche, keywords in niche_map.items():
                if any(kw in spec for kw in keywords):
                    return niche
            
            return 'general'
            
        except Exception as e:
            logger.warning(f"Erro ao inferir nicho: {str(e)}")
            return 'general'
    
    def _generate_summary(self, data: Dict, event_date: datetime, days_until: int) -> str:
        """Gera resumo contextualizado da oportunidade."""
        
        title = data['title']
        category = data['category']
        
        # Templates por categoria
        if category == 'commercial':
            return f"{title} se aproxima ({days_until} dias). Prepare conteúdo sobre presentes, promoções e ofertas especiais para engajar seu público."
        
        elif category == 'seasonal':
            return f"{title} está chegando. Crie posts inspiradores, mensagens de boas festas e conteúdo que conecte emocionalmente com sua audiência."
        
        elif category == 'awareness':
            return f"{title} é uma excelente oportunidade para posicionar sua marca em causas relevantes e construir autoridade no tema."
        
        elif category == 'feriado':
            return f"Feriado de {title} se aproxima. Aproveite para engajar sua audiência com conteúdo leve, inspirador ou promocional."
        
        else:
            return f"{title} em {days_until} dias. Oportunidade de criar conteúdo relevante e oportuno para seu público."
    
    def score_relevance_for_campaign(
        self,
        opportunity: Dict,
        campaign_objective: str,
        campaign_niche: str
    ) -> float:
        """
        Calcula relevância específica de uma oportunidade para uma campanha.
        
        Returns:
            float: Score 0-100
        """
        try:
            # Base score da oportunidade
            base_score = opportunity.get('relevance_score', 50)
            
            # Boost por keyword matching
            campaign_words = set(campaign_objective.lower().split())
            opp_keywords = set(opportunity.get('keywords', []))
            
            keyword_overlap = len(campaign_words & opp_keywords)
            keyword_boost = min(20, keyword_overlap * 5)
            
            # Score final
            final_score = min(100, base_score + keyword_boost)
            
            return final_score
            
        except Exception as e:
            logger.warning(f"Erro ao calcular relevância: {str(e)}")
            return 50.0
