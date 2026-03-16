"""
Prompts para geração de oportunidades de conteúdo.

Extraído de opportunities_generation_service.py conforme feedback do CTO:
"se é um prompt, deve ir no arquivo de prompts"
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def build_opportunities_prompt(
    context_data: Dict[str, Any],
    profile_data: Dict[str, Any],
    discovered_trends: Dict[str, Any] = None
) -> str:
    """Constrói o prompt para geração de oportunidades."""
    context_text = format_context_for_prompt(context_data)
    trends_text = format_discovered_trends(discovered_trends)

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


def format_context_for_prompt(context_data: Dict[str, Any]) -> str:
    """Formata os dados de contexto para inclusão no prompt."""
    sections = []

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

    if context_data.get('competition_main'):
        competitors = context_data['competition_main']
        if isinstance(competitors, list):
            sections.append(f"**Principais Concorrentes:**\n- " + "\n- ".join(str(c) for c in competitors))

    if context_data.get('competition_strategies'):
        sections.append(f"**Estratégias dos Concorrentes:**\n{context_data['competition_strategies']}")

    if context_data.get('competition_opportunities'):
        sections.append(f"**Oportunidades na Concorrência:**\n{context_data['competition_opportunities']}")

    if context_data.get('target_audience_profile'):
        sections.append(f"**Perfil do Público:**\n{context_data['target_audience_profile']}")

    if context_data.get('target_audience_behaviors'):
        sections.append(f"**Comportamento do Público:**\n{context_data['target_audience_behaviors']}")

    if context_data.get('target_audience_interests'):
        interests = context_data['target_audience_interests']
        if isinstance(interests, list):
            sections.append(f"**Interesses do Público:**\n- " + "\n- ".join(interests))

    if context_data.get('tendencies_popular_themes'):
        themes = context_data['tendencies_popular_themes']
        if isinstance(themes, list):
            sections.append(f"**Temas Populares:**\n- " + "\n- ".join(themes))

    if context_data.get('tendencies_hashtags'):
        hashtags = context_data['tendencies_hashtags']
        if isinstance(hashtags, list):
            sections.append(f"**Hashtags em Alta:**\n{', '.join(hashtags)}")

    if context_data.get('seasonal_relevant_dates'):
        dates = context_data['seasonal_relevant_dates']
        if isinstance(dates, list):
            sections.append(f"**Datas Relevantes:**\n- " + "\n- ".join(str(d) for d in dates))

    if context_data.get('seasonal_local_events'):
        events = context_data['seasonal_local_events']
        if isinstance(events, list):
            sections.append(f"**Eventos Locais:**\n- " + "\n- ".join(str(e) for e in events))

    return "\n\n".join(sections) if sections else "Contexto não disponível"


def format_discovered_trends(discovered_trends: Dict[str, Any] = None) -> str:
    """Formata tendências descobertas para inclusão no prompt de oportunidades."""
    if not discovered_trends or discovered_trends.get('validated_count', 0) == 0:
        return ""

    sections = ["""
============================================================
📈 TENDÊNCIAS PRÉ-VALIDADAS (Google Trends + fontes verificadas)
IMPORTANTE: PRIORIZE estes temas na geração de oportunidades.
Eles já foram validados com fontes reais.
============================================================"""]

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

    rising_topics = discovered_trends.get('rising_topics', [])
    if rising_topics:
        sections.append("\n📈 TÓPICOS EM CRESCIMENTO:")
        for trend in rising_topics[:5]:
            topic = trend.get('topic', '')
            growth = trend.get('growth_score', 0)
            sections.append(f"  - {topic} (crescimento: +{growth}%)")

    return '\n'.join(sections)
