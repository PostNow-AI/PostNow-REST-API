"""
Serviço de geração de oportunidades de conteúdo.

Este serviço transforma o contexto bruto (Fase 1) em oportunidades
ranqueadas no formato esperado pelo enriquecimento (Fase 2).

Fluxo Melhorado (2026):
    DOMINGO (Fase 0)  → TrendsDiscoveryService descobre tendências REAIS
    DOMINGO (Fase 1)  → WeeklyContextService gera contexto com tendências
    DOMINGO (Fase 1b) → OpportunitiesGenerationService usa tendências validadas
    SEGUNDA (Fase 2)  → ContextEnrichmentService enriquece com fontes
    SEGUNDA           → OpportunitiesEmailService envia email

Mudanças principais:
    - Oportunidades são geradas com base em tendências PRÉ-VALIDADAS
    - Cada oportunidade inclui search_keywords para facilitar busca de fontes
    - Score é penalizado se não houver tendência validada associada
"""
import json
import logging
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db.models import Q

from ClientContext.models import ClientContext
from services.ai_service import AiService
from services.get_creator_profile_data import get_creator_profile_data
from services.trends_discovery_service import TrendsDiscoveryService

logger = logging.getLogger(__name__)


class OpportunitiesGenerationService:
    """
    Serviço para geração de oportunidades de conteúdo ranqueadas.

    Usa o contexto bruto do ClientContext para gerar oportunidades
    categorizadas e ranqueadas por potencial de engajamento.

    Fluxo melhorado (2026):
        - Usa tendências PRÉ-VALIDADAS do discovered_trends
        - Inclui search_keywords em cada oportunidade
        - Penaliza score de oportunidades sem tendência validada
    """

    def __init__(
        self,
        ai_service: Optional[AiService] = None,
        trends_discovery_service: Optional[TrendsDiscoveryService] = None,
    ):
        self.ai_service = ai_service or AiService()
        self.trends_discovery_service = trends_discovery_service or TrendsDiscoveryService()

    async def generate_all_users_opportunities(
        self,
        batch_number: int = 1,
        batch_size: int = 5
    ) -> Dict[str, Any]:
        """
        Gera oportunidades para todos os usuários com contexto gerado.

        Args:
            batch_number: Número do lote atual
            batch_size: Tamanho do lote

        Returns:
            Dict com resultados do processamento
        """
        offset = (batch_number - 1) * batch_size
        contexts = await self._get_contexts_for_opportunities(offset, batch_size)

        if not contexts:
            return {
                'status': 'completed',
                'processed': 0,
                'message': 'No contexts to process',
            }

        # Pre-fetch all users in a single query to avoid N+1
        user_ids = [ctx['user_id'] for ctx in contexts]
        users_queryset = await sync_to_async(list)(
            User.objects.filter(id__in=user_ids)
        )
        users_by_id = {user.id: user for user in users_queryset}

        processed = 0
        failed = 0
        results = []

        for context_data in contexts:
            try:
                user = users_by_id.get(context_data['user_id'])
                if not user:
                    logger.error(f"User {context_data['user_id']} not found")
                    failed += 1
                    continue
                result = await self.generate_user_opportunities(user, context_data)
                results.append(result)
                if result.get('status') == 'success':
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error generating opportunities for user {context_data['user_id']}: {e}")
                failed += 1
                results.append({
                    'user_id': context_data['user_id'],
                    'status': 'failed',
                    'error': str(e)
                })

        return {
            'status': 'completed',
            'processed': processed,
            'failed': failed,
            'total': len(contexts),
            'details': results,
        }

    async def generate_user_opportunities(
        self,
        user: User,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gera oportunidades para um usuário específico.

        Fluxo melhorado (2026):
            1. Busca tendências descobertas (discovered_trends)
            2. Inclui tendências validadas no prompt
            3. Enriquece cada oportunidade com dados de tendência
            4. Penaliza score de oportunidades sem tendência validada

        Args:
            user: Instância do usuário
            context_data: Dados do contexto bruto (inclui discovered_trends)

        Returns:
            Dict com resultado da geração
        """
        try:
            # Buscar perfil do usuário
            profile_data = await sync_to_async(get_creator_profile_data)(user)

            # Buscar tendências descobertas do ClientContext
            discovered_trends = context_data.get('discovered_trends', {})

            # Construir prompt com tendências validadas
            prompt = self._build_opportunities_prompt(
                context_data, profile_data, discovered_trends
            )

            # Chamar IA
            response = await sync_to_async(self.ai_service.generate_text)(
                [prompt], user
            )

            # Parsear resposta JSON
            tendencies_data = self._parse_opportunities_response(response)

            if not tendencies_data:
                logger.warning(f"No opportunities generated for user {user.id}")
                return {
                    'user_id': user.id,
                    'status': 'success',
                    'message': 'No opportunities identified',
                    'categories': 0
                }

            # Enriquecer oportunidades com dados de tendências validadas
            tendencies_data = self._enrich_opportunities_with_trends(
                tendencies_data, discovered_trends, profile_data.get('specialization', '')
            )

            # Salvar no modelo
            client_context = await sync_to_async(ClientContext.objects.get)(user=user)
            client_context.tendencies_data = tendencies_data
            client_context.context_enrichment_status = 'pending'
            await sync_to_async(client_context.save)()

            categories_count = len([k for k in tendencies_data.keys() if tendencies_data[k].get('items')])

            logger.info(f"Generated {categories_count} opportunity categories for user {user.id}")

            return {
                'user_id': user.id,
                'status': 'success',
                'categories': categories_count
            }

        except Exception as e:
            logger.error(f"Error generating opportunities for user {user.id}: {e}")
            return {
                'user_id': user.id,
                'status': 'failed',
                'error': str(e)
            }

    def _build_opportunities_prompt(
        self,
        context_data: Dict[str, Any],
        profile_data: Dict[str, Any],
        discovered_trends: Dict[str, Any] = None
    ) -> str:
        """
        Constrói o prompt para geração de oportunidades.

        Fluxo melhorado (2026):
        1. Persona clara
        2. Dados de entrada estruturados
        3. Tendências PRÉ-VALIDADAS do Google Trends
        4. Tarefa específica
        5. Instruções rígidas com foco em search_keywords
        6. Formato de saída JSON com campos extras
        """
        # Formatar contexto para o prompt
        context_text = self._format_context_for_prompt(context_data)

        # Formatar tendências descobertas
        trends_text = self._format_discovered_trends(discovered_trends)

        return f"""
Você é um estrategista de conteúdo especializado em identificar
oportunidades de engajamento em redes sociais. Sua função é analisar
dados de mercado e transformá-los em ideias de posts ranqueadas por
potencial de engajamento.

============================================================
📊 CONTEXTO PESQUISADO (dados do mercado e tendências)
============================================================
{context_text}
{trends_text}
============================================================
🏢 DADOS DA EMPRESA
============================================================
- Nome: {profile_data.get('business_name', 'Não informado')}
- Setor: {profile_data.get('specialization', 'Não informado')}
- Descrição: {profile_data.get('business_description', 'Não informado')}
- Público-alvo: {profile_data.get('target_audience', 'Não informado')}
- Interesses do público: {profile_data.get('target_interests', 'Não informado')}
- Tom de voz: {profile_data.get('voice_tone', 'Profissional')}

============================================================
📌 TAREFA PRINCIPAL
============================================================
Analise o contexto pesquisado e gere **oportunidades de conteúdo**
organizadas em 6 categorias, cada uma com 2-3 ideias ranqueadas.

**CATEGORIAS OBRIGATÓRIAS:**
1. **polemica** 🔥 - Temas que geram debate e engajamento alto
2. **educativo** 🧠 - Conteúdo que ensina e agrega valor
3. **newsjacking** 📰 - Aproveitar notícias e eventos atuais
4. **entretenimento** 😂 - Conteúdo leve e divertido
5. **estudo_caso** 💼 - Cases de sucesso e exemplos práticos
6. **futuro** 🔮 - Tendências e previsões do setor

**SCORE (0-100):**
- 90-100: Viral potencial, timing perfeito, baseado em tendência validada
- 70-89: Alto engajamento esperado
- 50-69: Engajamento moderado
- Abaixo de 50: Não incluir

============================================================
⚠️ INSTRUÇÕES RÍGIDAS
============================================================
1. PRIORIZE as tendências pré-validadas listadas acima
2. Baseie-se APENAS nos dados do contexto pesquisado
3. NÃO invente estatísticas, datas ou fontes
4. Score deve refletir potencial REAL de engajamento
5. Cada ideia deve ter título atrativo e descrição clara
6. Se não houver dados para uma categoria, retorne items vazio
7. Priorize temas relevantes para o público-alvo da empresa
8. OBRIGATÓRIO: Inclua "search_keywords" em cada item

============================================================
🧭 DIRETRIZES DE QUALIDADE
============================================================
- Títulos devem ser chamativos (estilo clickbait positivo)
- Descrições devem explicar O QUE postar e POR QUE funciona
- Considere o tom de voz da marca nas sugestões
- Foque em temas com potencial de viralização
- Evite assuntos muito genéricos ou saturados
- search_keywords: 3-5 palavras-chave BUSCÁVEIS (não criativas)
  Exemplo: "IA Generativa Setor Público Brasil" ao invés de "Mina de ouro das GovTechs"

============================================================
💬 FORMATO DE SAÍDA (JSON OBRIGATÓRIO)
============================================================
{{
  "polemica": {{
    "titulo": "Temas Polêmicos",
    "items": [
      {{
        "titulo_ideia": "Título atrativo da ideia",
        "descricao": "Descrição do conteúdo e por que funciona",
        "tipo": "Polêmica",
        "score": 95,
        "url_fonte": "",
        "search_keywords": ["palavra1", "palavra2", "palavra3"]
      }}
    ]
  }},
  "educativo": {{
    "titulo": "Conteúdo Educativo",
    "items": [...]
  }},
  "newsjacking": {{
    "titulo": "Newsjacking",
    "items": [...]
  }},
  "entretenimento": {{
    "titulo": "Entretenimento",
    "items": [...]
  }},
  "estudo_caso": {{
    "titulo": "Estudos de Caso",
    "items": [...]
  }},
  "futuro": {{
    "titulo": "Tendências e Futuro",
    "items": [...]
  }}
}}

============================================================
📝 OBSERVAÇÃO FINAL
============================================================
Retorne APENAS o JSON, sem texto adicional.
Todas as ideias devem ser em português brasileiro (PT-BR).
"""

    def _format_context_for_prompt(self, context_data: Dict[str, Any]) -> str:
        """Formata os dados de contexto para inclusão no prompt."""
        sections = []

        # Mercado
        if context_data.get('market_panorama'):
            sections.append(f"**Panorama do Mercado:**\n{context_data['market_panorama']}")

        if context_data.get('market_tendencies'):
            tendencies = context_data['market_tendencies']
            if isinstance(tendencies, list):
                sections.append(f"**Tendências do Mercado:**\n- " + "\n- ".join(tendencies))

        if context_data.get('market_challenges'):
            challenges = context_data['market_challenges']
            if isinstance(challenges, list):
                sections.append(f"**Desafios do Mercado:**\n- " + "\n- ".join(challenges))

        # Concorrência
        if context_data.get('competition_main'):
            competitors = context_data['competition_main']
            if isinstance(competitors, list):
                sections.append(f"**Principais Concorrentes:**\n- " + "\n- ".join(str(c) for c in competitors))

        if context_data.get('competition_strategies'):
            sections.append(f"**Estratégias dos Concorrentes:**\n{context_data['competition_strategies']}")

        if context_data.get('competition_opportunities'):
            sections.append(f"**Oportunidades na Concorrência:**\n{context_data['competition_opportunities']}")

        # Público
        if context_data.get('target_audience_profile'):
            sections.append(f"**Perfil do Público:**\n{context_data['target_audience_profile']}")

        if context_data.get('target_audience_behaviors'):
            sections.append(f"**Comportamento do Público:**\n{context_data['target_audience_behaviors']}")

        if context_data.get('target_audience_interests'):
            interests = context_data['target_audience_interests']
            if isinstance(interests, list):
                sections.append(f"**Interesses do Público:**\n- " + "\n- ".join(interests))

        # Tendências
        if context_data.get('tendencies_popular_themes'):
            themes = context_data['tendencies_popular_themes']
            if isinstance(themes, list):
                sections.append(f"**Temas Populares:**\n- " + "\n- ".join(themes))

        if context_data.get('tendencies_hashtags'):
            hashtags = context_data['tendencies_hashtags']
            if isinstance(hashtags, list):
                sections.append(f"**Hashtags em Alta:**\n{', '.join(hashtags)}")

        # Sazonalidade
        if context_data.get('seasonal_relevant_dates'):
            dates = context_data['seasonal_relevant_dates']
            if isinstance(dates, list):
                sections.append(f"**Datas Relevantes:**\n- " + "\n- ".join(str(d) for d in dates))

        if context_data.get('seasonal_local_events'):
            events = context_data['seasonal_local_events']
            if isinstance(events, list):
                sections.append(f"**Eventos Locais:**\n- " + "\n- ".join(str(e) for e in events))

        return "\n\n".join(sections) if sections else "Contexto não disponível"

    def _parse_opportunities_response(self, response: str) -> Dict[str, Any]:
        """
        Parseia a resposta da IA para extrair o JSON de oportunidades.

        Args:
            response: Resposta raw da IA

        Returns:
            Dict com as oportunidades ou dict vazio se falhar
        """
        try:
            # Limpar resposta
            cleaned = response.strip()

            # Remover markdown code blocks se presentes
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:]

            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()

            # Parsear JSON
            data = json.loads(cleaned)

            # Validar estrutura básica
            if not isinstance(data, dict):
                logger.warning("Response is not a dict")
                return {}

            # Validar categorias
            valid_categories = {'polemica', 'educativo', 'newsjacking', 'entretenimento', 'estudo_caso', 'futuro'}
            result = {}

            for category in valid_categories:
                if category in data and isinstance(data[category], dict):
                    result[category] = data[category]
                else:
                    # Criar categoria vazia se não existir
                    result[category] = {
                        'titulo': self._get_category_title(category),
                        'items': []
                    }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse opportunities JSON: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing opportunities response: {e}")
            return {}

    def _get_category_title(self, category: str) -> str:
        """Retorna o título padrão para uma categoria."""
        titles = {
            'polemica': 'Temas Polêmicos',
            'educativo': 'Conteúdo Educativo',
            'newsjacking': 'Newsjacking',
            'entretenimento': 'Entretenimento',
            'estudo_caso': 'Estudos de Caso',
            'futuro': 'Tendências e Futuro',
        }
        return titles.get(category, category.title())

    @sync_to_async
    def _get_contexts_for_opportunities(
        self,
        offset: int = 0,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Busca contextos que precisam de geração de oportunidades.

        Critério:
            - weekly_context_error IS NULL (contexto gerado com sucesso)
            - tendencies_data IS NULL OU tendencies_data é dict vazio {}

        Nota: Usamos Q objects para capturar tanto NULL quanto dicts vazios,
        já que o default do campo é dict (que cria {} ao invés de NULL).

        Inclui discovered_trends para usar na geração de oportunidades.
        """
        return list(
            ClientContext.objects.filter(
                weekly_context_error__isnull=True,  # Contexto gerado sem erro
            ).filter(
                # Pega NULL ou dict vazio {}
                Q(tendencies_data__isnull=True) | Q(tendencies_data={})
            ).select_related('user').values(
                'id', 'user_id',
                'market_panorama', 'market_tendencies', 'market_challenges',
                'competition_main', 'competition_strategies', 'competition_opportunities',
                'target_audience_profile', 'target_audience_behaviors', 'target_audience_interests',
                'tendencies_popular_themes', 'tendencies_hashtags', 'tendencies_keywords',
                'seasonal_relevant_dates', 'seasonal_local_events',
                'discovered_trends',  # Tendências pré-validadas (novo campo)
            ).order_by('id')[offset:offset + limit]  # Ordenação determinística
        )

    def _format_discovered_trends(self, discovered_trends: Dict[str, Any] = None) -> str:
        """
        Formata tendências descobertas para inclusão no prompt.

        Args:
            discovered_trends: Dict com tendências do TrendsDiscoveryService

        Returns:
            String formatada para o prompt
        """
        if not discovered_trends or discovered_trends.get('validated_count', 0) == 0:
            return ""

        sections = ["""
============================================================
📈 TENDÊNCIAS PRÉ-VALIDADAS (Google Trends + fontes verificadas)
IMPORTANTE: PRIORIZE estes temas na geração de oportunidades.
Eles já foram validados com fontes reais.
============================================================"""]

        # Tendências gerais
        general_trends = discovered_trends.get('general_trends', [])
        if general_trends:
            sections.append("\n🌍 TENDÊNCIAS GERAIS DO BRASIL:")
            for trend in general_trends[:5]:
                topic = trend.get('topic', '')
                relevance = trend.get('relevance_score', 0)
                sources = trend.get('sources', [])
                sections.append(f"  - {topic} (relevância: {relevance}/100)")
                if sources:
                    urls = [s.get('url', '') for s in sources[:2] if s.get('url')]
                    if urls:
                        sections.append(f"    Fontes: {', '.join(urls)}")

        # Tendências do setor
        sector_trends = discovered_trends.get('sector_trends', [])
        if sector_trends:
            sections.append("\n🎯 TENDÊNCIAS DO SETOR:")
            for trend in sector_trends[:5]:
                topic = trend.get('topic', '')
                relevance = trend.get('relevance_score', 0)
                keywords = trend.get('search_keywords', [])
                sections.append(f"  - {topic} (relevância: {relevance}/100)")
                if keywords:
                    sections.append(f"    Keywords: {', '.join(keywords[:3])}")

        # Tópicos em crescimento
        rising_topics = discovered_trends.get('rising_topics', [])
        if rising_topics:
            sections.append("\n📈 TÓPICOS EM CRESCIMENTO:")
            for trend in rising_topics[:5]:
                topic = trend.get('topic', '')
                growth = trend.get('growth_score', 0)
                sections.append(f"  - {topic} (crescimento: +{growth}%)")

        return '\n'.join(sections)

    def _enrich_opportunities_with_trends(
        self,
        tendencies_data: Dict[str, Any],
        discovered_trends: Dict[str, Any],
        sector: str
    ) -> Dict[str, Any]:
        """
        Enriquece oportunidades com dados de tendências e ajusta scores.

        Regras:
            - Se a oportunidade está alinhada com tendência validada: +10 pontos
            - Se a oportunidade NÃO tem tendência validada: -20 pontos
            - Se a oportunidade tem 0 fontes validadas: marcar como "não validado"

        Args:
            tendencies_data: Dados de oportunidades geradas pela IA
            discovered_trends: Tendências descobertas
            sector: Setor de atuação do usuário

        Returns:
            tendencies_data enriquecido
        """
        if not discovered_trends or discovered_trends.get('validated_count', 0) == 0:
            # Sem tendências validadas - aplicar penalidade leve em todos
            for category_key, category_data in tendencies_data.items():
                if isinstance(category_data, dict) and 'items' in category_data:
                    for item in category_data['items']:
                        current_score = item.get('score', 50)
                        item['score'] = max(current_score - 10, 0)
                        item['trend_validated'] = False
            return tendencies_data

        # Coletar todos os tópicos de tendências
        all_trend_topics = []
        for trend_list in ['general_trends', 'sector_trends', 'rising_topics']:
            trends = discovered_trends.get(trend_list, [])
            for trend in trends:
                topic = trend.get('topic', '').lower()
                if topic:
                    all_trend_topics.append({
                        'topic': topic,
                        'sources': trend.get('sources', []),
                        'relevance_score': trend.get('relevance_score', 0),
                    })

        # Processar cada oportunidade
        for category_key, category_data in tendencies_data.items():
            if not isinstance(category_data, dict) or 'items' not in category_data:
                continue

            for item in category_data['items']:
                title = item.get('titulo_ideia', '').lower()
                description = item.get('descricao', '').lower()
                content = f"{title} {description}"

                # Verificar se está alinhada com alguma tendência
                matching_trend = None
                for trend in all_trend_topics:
                    if trend['topic'] in content:
                        matching_trend = trend
                        break

                current_score = item.get('score', 50)

                if matching_trend:
                    # Oportunidade alinhada com tendência validada
                    item['trend_validated'] = True
                    item['trend_sources'] = matching_trend.get('sources', [])

                    # Bonus de +10 pontos
                    bonus = min(matching_trend.get('relevance_score', 0) // 10, 10)
                    item['score'] = min(current_score + bonus, 100)
                else:
                    # Oportunidade não alinhada - penalidade de -20 pontos
                    item['trend_validated'] = False
                    item['trend_sources'] = []
                    item['score'] = max(current_score - 20, 0)

                # Garantir que search_keywords existe
                if 'search_keywords' not in item or not item['search_keywords']:
                    item['search_keywords'] = self.trends_discovery_service.get_search_keywords_for_opportunity(
                        item.get('titulo_ideia', ''),
                        sector
                    )

        return tendencies_data
