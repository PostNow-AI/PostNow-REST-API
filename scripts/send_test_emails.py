#!/usr/bin/env python3
"""
Teste end-to-end usando os serviços REAIS do PostNow.

Fluxo simulado:
1. Opportunities: SerperSearchService → generate_enriched_analysis (Gemini) → Template → Mailjet
2. Market Intelligence: SerperSearchService → Template → Mailjet

Uso:
    python scripts/send_test_emails.py --email seu@email.com
    python scripts/send_test_emails.py --email seu@email.com --only opportunities
    python scripts/send_test_emails.py --email seu@email.com --only market
"""
import os
import sys
import argparse
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables ANTES de importar Django
# Requer: SERPER_API_KEY, MJ_APIKEY_PUBLIC, MJ_APIKEY_PRIVATE, GEMINI_API_KEY (opcional)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
os.environ.setdefault('SENDER_EMAIL', 'contato@postnow.com.br')
os.environ.setdefault('SENDER_NAME', 'PostNow')

# Django setup
import django
django.setup()

from services.serper_search_service import SerperSearchService
from ClientContext.utils.search_utils import fetch_and_filter_sources, build_search_query
from ClientContext.utils.opportunities_email import generate_opportunities_email_template
from ClientContext.utils.market_intelligence_email import generate_market_intelligence_email


def send_via_mailjet(to_email: str, subject: str, html_content: str) -> tuple:
    """Envia e-mail via Mailjet API diretamente."""
    import requests

    response = requests.post(
        "https://api.mailjet.com/v3.1/send",
        auth=(os.environ['MJ_APIKEY_PUBLIC'], os.environ['MJ_APIKEY_PRIVATE']),
        json={
            "Messages": [{
                "From": {
                    "Email": os.environ['SENDER_EMAIL'],
                    "Name": os.environ['SENDER_NAME']
                },
                "To": [{"Email": to_email, "Name": "Teste PostNow"}],
                "Subject": subject,
                "HTMLPart": html_content,
            }]
        }
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('Messages', [{}])[0].get('Status') == 'success':
            return True, "Enviado com sucesso"
        return False, f"Status: {data}"
    return False, f"HTTP {response.status_code}: {response.text}"


def generate_analysis_with_gemini(opportunity: dict, sources: list) -> str:
    """
    Gera análise usando Gemini (mesmo fluxo do enrichment_analysis.py).
    Fallback para análise baseada em regras se Gemini não estiver disponível.
    """
    from google import genai
    from google.genai import types

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("      ⚠️ GEMINI_API_KEY não configurada, usando análise baseada em regras")
        return _generate_rule_based_analysis(opportunity, sources)

    try:
        client = genai.Client(api_key=api_key)

        titulo = opportunity.get('titulo_ideia', '')
        tipo = opportunity.get('tipo', '')
        descricao = opportunity.get('descricao', '')

        # Mesmo formato do enrichment_analysis.py
        sources_text = ""
        for i, source in enumerate(sources[:3], 1):
            sources_text += f"\n{i}. {source.get('title', 'Sem titulo')}\n"
            sources_text += f"   {source.get('snippet', '')}\n"

        prompt = f"""Analise a seguinte oportunidade de conteudo e forneca uma analise mais profunda:

OPORTUNIDADE:
- Titulo: {titulo}
- Tipo: {tipo}
- Descricao: {descricao}

FONTES ADICIONAIS ENCONTRADAS:
{sources_text}

Com base nas fontes adicionais, forneca:
1. Contexto expandido sobre o tema (2-3 frases)
2. Angulos de abordagem recomendados (2-3 sugestoes)
3. Pontos de atencao ou controversias relevantes

Responda de forma concisa e objetiva, em portugues brasileiro.
Maximo de 200 palavras no total."""

        config = types.GenerateContentConfig(response_modalities=["TEXT"])
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=config
        )

        return response.text.strip()

    except Exception as e:
        print(f"      ⚠️ Erro no Gemini: {e}")
        return _generate_rule_based_analysis(opportunity, sources)


def _generate_rule_based_analysis(opportunity: dict, sources: list) -> str:
    """Análise baseada em regras (fallback quando Gemini não está disponível)."""
    titulo = opportunity.get('titulo_ideia', '')
    tipo = opportunity.get('tipo', '').replace('🧠', '').replace('🔥', '').replace('📰', '').strip()

    # Extrair insights das fontes
    source_insights = []
    for s in sources[:3]:
        snippet = s.get('snippet', '')
        if snippet and len(snippet) > 50:
            source_insights.append(snippet[:100])

    insights_text = " ".join(source_insights[:2]) if source_insights else ""

    analyses = {
        'Educativo': f"""Este conteúdo educativo aborda um tema de alta relevância para seu público.

Ângulos recomendados:
• Guia passo a passo com exemplos práticos
• Comparativo de ferramentas/métodos disponíveis
• Erros comuns a evitar (aprendizado reverso)

{f'Contexto das fontes: {insights_text[:150]}...' if insights_text else 'Use as fontes para embasar seus argumentos com dados e exemplos reais.'}""",

        'Polêmica': f"""Tema com alto potencial de engajamento por gerar debate.

Ângulos recomendados:
• Apresente dados que contradizem a crença comum
• Mostre múltiplos pontos de vista antes da sua conclusão
• Use perguntas provocativas para estimular discussão

{f'Contexto das fontes: {insights_text[:150]}...' if insights_text else 'As fontes mostram diferentes perspectivas que podem enriquecer a discussão.'}""",

        'Newsjacking': f"""Oportunidade de newsjacking com timing ideal para posicionamento.

Ângulos recomendados:
• Análise rápida do impacto para seu nicho
• Previsões e como se preparar para mudanças
• Opinião profissional com visão de mercado

{f'Contexto das fontes: {insights_text[:150]}...' if insights_text else 'Aproveite a atualidade do tema para se posicionar como referência no assunto.'}""",
    }

    return analyses.get(tipo, f"""Oportunidade identificada com potencial de engajamento.

Ângulos recomendados:
• Abordagem educativa com exemplos do seu nicho
• Storytelling conectando com experiências do público
• Call-to-action claro para próximos passos

{f'Contexto das fontes: {insights_text[:150]}...' if insights_text else 'Analise as fontes para criar conteúdo relevante e bem embasado.'}""")


async def test_opportunities_email(to_email: str):
    """
    Testa e-mail de Opportunities usando o fluxo REAL:
    1. Busca fontes via SerperSearchService
    2. Gera análise via Gemini (ou fallback)
    3. Gera HTML via generate_opportunities_email_template
    4. Envia via Mailjet
    """
    print("\n" + "=" * 60)
    print("1. OPPORTUNITIES EMAIL (Segunda-feira)")
    print("   Fluxo: Serper → Gemini → Template → Mailjet")
    print("=" * 60)

    serper = SerperSearchService()
    print(f"   Serper configurado: {serper.is_configured()}")
    print(f"   Gemini configurado: {bool(os.getenv('GEMINI_API_KEY'))}")

    user_data = {
        'first_name': 'Rogério',
        'business_name': 'PostNow',
        'specialization': 'Marketing Digital',
    }

    opportunities = [
        {
            'titulo_ideia': 'Como usar IA para criar conteúdo de marketing',
            'tipo': '🧠 Educativo',
            'descricao': 'Guia prático para usar ferramentas de IA no marketing',
            'score': 92,
        },
        {
            'titulo_ideia': 'Por que 80% das empresas falham no Instagram',
            'tipo': '🔥 Polêmica',
            'descricao': 'Análise dos erros mais comuns no Instagram',
            'score': 88,
        },
        {
            'titulo_ideia': 'Nova atualização do Instagram muda algoritmo',
            'tipo': '📰 Newsjacking',
            'descricao': 'Mudanças no algoritmo e como se adaptar',
            'score': 85,
        },
    ]

    enriched_opportunities = {}
    used_urls = set()

    for opp in opportunities:
        tipo = opp['tipo'].replace('🧠', '').replace('🔥', '').replace('📰', '').strip().lower()
        category_key = {'educativo': 'educativo', 'polêmica': 'polemica', 'newsjacking': 'newsjacking'}.get(tipo, 'outros')

        print(f"\n   [{category_key.upper()}] {opp['titulo_ideia'][:40]}...")

        # 1. Buscar fontes reais via SerperSearchService
        query = build_search_query(opp, category_key)
        news_query = build_search_query(opp, category_key, for_news=True)

        print(f"   → Buscando fontes: {query[:50]}...")

        sources = await fetch_and_filter_sources(
            serper, query, 'tendencias', used_urls,
            read_content=False, category_key=category_key, news_query=news_query
        )

        print(f"   → Encontradas: {len(sources)} fontes")
        for s in sources[:3]:
            print(f"      • {s.get('title', 'N/A')[:50]}...")

        # 2. Gerar análise via Gemini (ou fallback)
        print("   → Gerando análise...")
        analysis = generate_analysis_with_gemini(opp, sources)
        print(f"   → Análise: {analysis[:80]}...")

        # 3. Montar oportunidade enriquecida
        # Todas as fontes em enriched_sources (com título), url_fonte vazio
        opp['url_fonte'] = ''  # Não usar - mostra "Fonte principal" sem título
        opp['enriched_sources'] = sources[:3]  # Todas as fontes com título
        opp['enriched_analysis'] = analysis

        if category_key not in enriched_opportunities:
            enriched_opportunities[category_key] = {
                'titulo': opp['tipo'],
                'items': []
            }
        enriched_opportunities[category_key]['items'].append(opp)

    # 4. Gerar HTML via template real
    print("\n   Gerando HTML do e-mail...")
    html = generate_opportunities_email_template(enriched_opportunities, user_data)

    # 5. Enviar via Mailjet
    print("   Enviando via Mailjet...")
    success, msg = send_via_mailjet(
        to_email,
        "🎯 [TESTE] Oportunidades de Conteúdo - PostNow",
        html
    )

    if success:
        print(f"   ✅ E-MAIL ENVIADO para {to_email}")
    else:
        print(f"   ❌ ERRO: {msg}")

    return success


async def test_market_intelligence_email(to_email: str):
    """
    Testa e-mail de Market Intelligence usando o fluxo REAL:
    1. Busca fontes via SerperSearchService
    2. Monta dados no formato correto (listas)
    3. Gera HTML via generate_market_intelligence_email
    4. Envia via Mailjet
    """
    print("\n" + "=" * 60)
    print("2. MARKET INTELLIGENCE EMAIL (Quarta-feira)")
    print("   Fluxo: Serper → Template → Mailjet")
    print("=" * 60)

    serper = SerperSearchService()

    user_data = {
        'first_name': 'Rogério',
        'business_name': 'PostNow',
        'specialization': 'Marketing Digital',
        'target_audience': 'Empreendedores e criadores de conteúdo',
    }

    # Buscar fontes reais para cada seção (igual ao MarketIntelligenceEnrichmentService)
    sections = {
        'market': 'marketing digital tendências Brasil 2026',
        'competition': 'ferramentas marketing digital concorrentes mlabs rd station',
        'audience': 'comportamento empreendedores redes sociais Brasil',
    }

    context_sources = {}

    for section, query in sections.items():
        print(f"\n   [{section.upper()}] Buscando fontes...")
        print(f"   → Query: {query[:50]}...")

        results = serper.search(query, num_results=3)
        context_sources[f'{section}_sources'] = [
            {'url': r['url'], 'title': r['title']} for r in results
        ]

        print(f"   → Encontradas: {len(results)} fontes")
        for r in results[:3]:
            print(f"      • {r['title'][:50]}...")

    # Dados de contexto com LISTAS (formato correto para o template)
    context_data = {
        # Mercado
        'market_panorama': 'O mercado de marketing digital no Brasil cresce 25% ao ano, impulsionado por IA generativa e automação. Empresas que adotam ferramentas inteligentes têm 3x mais engajamento e conseguem escalar produção de conteúdo.',
        'market_tendencies': [
            'IA generativa para criação de conteúdo',
            'Short-form video (Reels/TikTok) dominando engajamento',
            'Personalização em escala com dados first-party',
            'Social commerce integrando conteúdo e vendas',
        ],
        'market_challenges': [
            'Saturação de conteúdo nas plataformas',
            'Mudanças constantes de algoritmo',
            'Custo crescente de anúncios pagos',
            'Dificuldade em mensurar ROI de orgânico',
        ],
        'market_sources': context_sources.get('market_sources', []),

        # Concorrência
        'competition_main': [
            {'name': 'RD Station', 'followers': '500K+'},
            {'name': 'mLabs', 'followers': '300K+'},
            {'name': 'Postgrain', 'followers': '150K+'},
            {'name': 'Etus', 'followers': '100K+'},
        ],
        'competition_strategies': 'Foco em automação de posts, templates prontos, relatórios de analytics e integração com múltiplas redes sociais.',
        'competition_opportunities': 'Nicho de criadores individuais e pequenos negócios que precisam de conteúdo personalizado e ideias, não apenas agendamento.',
        'competition_sources': context_sources.get('competition_sources', []),

        # Público-alvo
        'target_audience_profile': 'Empreendedores e criadores de conteúdo, 25-45 anos, digitalmente ativos, buscando produtividade e crescimento online.',
        'target_audience_behaviors': 'Consomem conteúdo principalmente no Instagram, LinkedIn e YouTube. Preferem formatos curtos, práticos e acionáveis.',
        'target_audience_interests': [
            'Produtividade',
            'Marketing Digital',
            'Crescimento de negócios',
            'Redes sociais',
            'Vendas online',
        ],
        'target_audience_sources': context_sources.get('audience_sources', []),

        # Tendências
        'tendencies_popular_themes': [
            'IA no marketing',
            'Reels e vídeos curtos',
            'UGC (User Generated Content)',
            'Micro-influenciadores',
        ],
        'tendencies_hashtags': [
            '#marketingdigital',
            '#empreendedorismo',
            '#ia',
            '#produtividade',
            '#redessociais',
        ],
        'tendencies_keywords': [
            'automação',
            'engajamento',
            'conversão',
            'funil de vendas',
            'growth hacking',
        ],
        'tendencies_sources': [],

        # Calendário
        'seasonal_relevant_dates': [
            {'date': '15/03', 'event': 'Dia do Consumidor'},
            {'date': '20/04', 'event': 'Páscoa'},
            {'date': '11/05', 'event': 'Dia das Mães'},
            {'date': '12/06', 'event': 'Dia dos Namorados'},
        ],
        'seasonal_local_events': [
            {'date': 'Março', 'event': 'SXSW (referência global)'},
            {'date': 'Outubro', 'event': 'RD Summit'},
            {'date': 'Novembro', 'event': 'Black Friday'},
        ],
        'seasonal_sources': [],

        # Marca
        'brand_online_presence': 'Instagram com crescimento orgânico constante, LinkedIn para autoridade B2B, YouTube para tutoriais e cases de sucesso.',
        'brand_reputation': 'Feedbacks positivos destacam facilidade de uso, qualidade do conteúdo gerado e economia de tempo.',
        'brand_communication_style': 'Profissional mas acessível, foco em resultados práticos e linguagem direta sem jargões.',
        'brand_sources': [],
    }

    # Gerar HTML via template real
    print("\n   Gerando HTML do e-mail...")
    html = generate_market_intelligence_email(context_data, user_data)

    # Enviar via Mailjet
    print("   Enviando via Mailjet...")
    success, msg = send_via_mailjet(
        to_email,
        "📊 [TESTE] Inteligência de Mercado - PostNow",
        html
    )

    if success:
        print(f"   ✅ E-MAIL ENVIADO para {to_email}")
    else:
        print(f"   ❌ ERRO: {msg}")

    return success


async def main():
    parser = argparse.ArgumentParser(description='Envia e-mails de teste usando fluxo real')
    parser.add_argument('--email', required=True, help='E-mail do destinatário')
    parser.add_argument('--only', choices=['opportunities', 'market', 'all'],
                        default='all', help='Qual e-mail enviar')
    args = parser.parse_args()

    print("=" * 60)
    print("TESTE END-TO-END: FLUXO REAL DOS E-MAILS")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Destinatário: {args.email}")
    print("=" * 60)

    results = {}

    if args.only in ['opportunities', 'all']:
        results['Opportunities'] = await test_opportunities_email(args.email)

    if args.only in ['market', 'all']:
        results['Market Intelligence'] = await test_market_intelligence_email(args.email)

    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)

    all_success = True
    for name, success in results.items():
        status = "✅ Enviado" if success else "❌ Falhou"
        print(f"   {status}: {name}")
        if not success:
            all_success = False

    print("\n" + "=" * 60)
    if all_success:
        print(f"🎉 TODOS OS E-MAILS ENVIADOS PARA {args.email}!")
    else:
        print("⚠️  ALGUNS E-MAILS FALHARAM")
    print("=" * 60)

    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
