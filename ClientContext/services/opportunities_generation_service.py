"""
Serviço de geração de oportunidades de conteúdo.

Este serviço transforma o contexto bruto (Fase 1) em oportunidades
ranqueadas no formato esperado pelo enriquecimento (Fase 2).

Fluxo:
    DOMINGO (Fase 1)  → WeeklyContextService gera contexto bruto
    DOMINGO (Fase 1b) → OpportunitiesGenerationService gera tendencies_data
    SEGUNDA (Fase 2)  → ContextEnrichmentService enriquece com fontes
    SEGUNDA           → OpportunitiesEmailService envia email
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

logger = logging.getLogger(__name__)


class OpportunitiesGenerationService:
    """
    Serviço para geração de oportunidades de conteúdo ranqueadas.

    Usa o contexto bruto do ClientContext para gerar oportunidades
    categorizadas e ranqueadas por potencial de engajamento.
    """

    def __init__(self, ai_service: Optional[AiService] = None):
        self.ai_service = ai_service or AiService()

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

        processed = 0
        failed = 0
        results = []

        for context_data in contexts:
            try:
                user = await sync_to_async(User.objects.get)(id=context_data['user_id'])
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

        Args:
            user: Instância do usuário
            context_data: Dados do contexto bruto

        Returns:
            Dict com resultado da geração
        """
        try:
            # Buscar perfil do usuário
            profile_data = await sync_to_async(get_creator_profile_data)(user)

            # Construir prompt
            prompt = self._build_opportunities_prompt(context_data, profile_data)

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
        profile_data: Dict[str, Any]
    ) -> str:
        """
        Constrói o prompt para geração de oportunidades.

        Segue as boas práticas identificadas:
        1. Persona clara
        2. Dados de entrada estruturados
        3. Tarefa específica
        4. Instruções rígidas
        5. Formato de saída JSON
        """
        # Formatar contexto para o prompt
        context_text = self._format_context_for_prompt(context_data)

        return f"""
Você é um estrategista de conteúdo especializado em identificar
oportunidades de engajamento em redes sociais. Sua função é analisar
dados de mercado e transformá-los em ideias de posts ranqueadas por
potencial de engajamento.

============================================================
📊 CONTEXTO PESQUISADO (dados do mercado e tendências)
============================================================
{context_text}

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
- 90-100: Viral potencial, timing perfeito
- 70-89: Alto engajamento esperado
- 50-69: Engajamento moderado
- Abaixo de 50: Não incluir

============================================================
⚠️ INSTRUÇÕES RÍGIDAS
============================================================
1. Baseie-se APENAS nos dados do contexto pesquisado
2. NÃO invente estatísticas, datas ou fontes
3. Score deve refletir potencial REAL de engajamento
4. Cada ideia deve ter título atrativo e descrição clara
5. Se não houver dados para uma categoria, retorne items vazio
6. Priorize temas relevantes para o público-alvo da empresa

============================================================
🧭 DIRETRIZES DE QUALIDADE
============================================================
- Títulos devem ser chamativos (estilo clickbait positivo)
- Descrições devem explicar O QUE postar e POR QUE funciona
- Considere o tom de voz da marca nas sugestões
- Foque em temas com potencial de viralização
- Evite assuntos muito genéricos ou saturados

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
        "url_fonte": ""
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
            )[offset:offset + limit]
        )
