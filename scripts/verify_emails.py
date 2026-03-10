#!/usr/bin/env python3
"""
Teste completo dos 3 tipos de e-mail do PostNow.

1. Opportunities Email (Segunda) - Com enrichment Serper + Jina
2. Market Intelligence Email (Quarta) - Com enrichment Serper + Jina
3. Onboarding Emails (Dia 1, 3, 7) - Sem enrichment

Uso:
    python scripts/test_all_emails.py
    python scripts/test_all_emails.py --save  # Salva HTMLs para preview
"""
import os
import sys
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock data for testing
MOCK_USER_DATA = {
    'first_name': 'João',
    'business_name': 'Marketing Digital Pro',
    'specialization': 'Marketing Digital',
    'target_audience': 'Empreendedores e PMEs',
    'email': 'joao@example.com',
}

MOCK_TENDENCIES_DATA = {
    'polemica': {
        'titulo': '🔥 Polêmicas',
        'items': [
            {
                'titulo_ideia': 'Por que 90% das estratégias de marketing falham',
                'tipo': '🔥 Polêmica',
                'descricao': 'Análise crítica das falhas mais comuns em marketing digital',
                'score': 85,
                'url_fonte': 'https://exemplo.com/marketing-falhas',
                'enriched_sources': [
                    {'url': 'https://fonte1.com/artigo', 'title': 'Erros de Marketing', 'snippet': 'Principais erros...'},
                    {'url': 'https://fonte2.com/analise', 'title': 'Análise de Mercado', 'snippet': 'Estudo mostra...'},
                    {'url': 'https://fonte3.com/dicas', 'title': 'Como Evitar', 'snippet': 'Dicas práticas...'},
                ],
                'enriched_analysis': 'Esta oportunidade explora um tema polêmico que gera debate. '
                                   'Ângulos: 1) Provocar reflexão sobre práticas comuns. '
                                   '2) Apresentar casos reais de falhas. '
                                   '3) Oferecer soluções práticas.',
            },
        ],
    },
    'educativo': {
        'titulo': '🧠 Educativo',
        'items': [
            {
                'titulo_ideia': 'Como criar conteúdo que engaja nas redes sociais',
                'tipo': '🧠 Educativo',
                'descricao': 'Guia prático para aumentar engajamento',
                'score': 90,
                'url_fonte': 'https://exemplo.com/engajamento',
                'enriched_sources': [
                    {'url': 'https://guia.com/engajamento', 'title': 'Guia de Engajamento', 'snippet': 'Passo a passo...'},
                    {'url': 'https://tutorial.com/redes', 'title': 'Tutorial Redes', 'snippet': 'Como criar...'},
                ],
                'enriched_analysis': 'Conteúdo educativo com alta demanda. '
                                   'Foco em dicas práticas e acionáveis.',
            },
        ],
    },
    'newsjacking': {
        'titulo': '📰 Newsjacking',
        'items': [
            {
                'titulo_ideia': 'Nova atualização do Instagram muda algoritmo',
                'tipo': '📰 Newsjacking',
                'descricao': 'Aproveite a notícia para criar conteúdo relevante',
                'score': 88,
                'url_fonte': 'https://news.com/instagram',
                'enriched_sources': [
                    {'url': 'https://tech.com/instagram', 'title': 'Instagram Update', 'snippet': 'Nova mudança...'},
                    {'url': 'https://social.com/algoritmo', 'title': 'Algoritmo 2026', 'snippet': 'O que muda...'},
                    {'url': 'https://marketing.com/reels', 'title': 'Reels Dominam', 'snippet': 'Tendência...'},
                ],
                'enriched_analysis': 'Notícia quente! Ideal para newsjacking imediato. '
                                   'Aborde: impactos para criadores, como se adaptar, previsões.',
            },
        ],
    },
}

MOCK_CONTEXT_DATA = {
    'market_panorama': 'O mercado de marketing digital cresce 25% ao ano no Brasil.',
    'market_tendencies': 'IA generativa, short-form video, personalização.',
    'market_challenges': 'Saturação de conteúdo, mudanças de algoritmo.',
    'market_sources': [
        {'url': 'https://mercado.com/tendencias', 'title': 'Tendências 2026'},
    ],
    'competition_main': 'Agências digitais tradicionais e ferramentas SaaS.',
    'competition_strategies': 'Foco em automação e resultados mensuráveis.',
    'competition_opportunities': 'Nicho de pequenos negócios mal atendido.',
    'competition_sources': [
        {'url': 'https://competicao.com/analise', 'title': 'Análise Competitiva'},
    ],
    'target_audience_profile': 'Empreendedores 25-45 anos, digitalmente ativos.',
    'target_audience_behaviors': 'Consomem conteúdo no Instagram e LinkedIn.',
    'target_audience_interests': 'Produtividade, crescimento de negócios, marketing.',
    'target_audience_sources': [],
    'tendencies_popular_themes': 'IA no marketing, Reels, UGC.',
    'tendencies_hashtags': '#marketingdigital #empreendedorismo #ia',
    'tendencies_keywords': 'automação, engajamento, conversão',
    'tendencies_sources': [
        {'url': 'https://trends.com/2026', 'title': 'Trends 2026'},
    ],
    'seasonal_relevant_dates': 'Black Friday, Natal, Dia do Consumidor.',
    'seasonal_local_events': 'Carnaval, festivais regionais.',
    'seasonal_sources': [],
    'brand_online_presence': 'Instagram: 5k seguidores, LinkedIn: 2k conexões.',
    'brand_reputation': 'Positiva, feedbacks destacam atendimento.',
    'brand_communication_style': 'Profissional mas acessível.',
    'brand_sources': [],
}


def test_opportunities_email(save_html=False):
    """Testa geração do e-mail de Opportunities."""
    print("\n" + "=" * 60)
    print("TESTE 1: E-MAIL DE OPPORTUNITIES (Segunda-feira)")
    print("=" * 60)

    try:
        from ClientContext.utils.opportunities_email import generate_opportunities_email_template

        html = generate_opportunities_email_template(
            tendencies_data=MOCK_TENDENCIES_DATA,
            user_data=MOCK_USER_DATA
        )

        # Validações
        checks = [
            ('Header presente', 'Oportunidades de Conteúdo' in html),
            ('Nome do usuário', MOCK_USER_DATA['first_name'] in html),
            ('Business name', MOCK_USER_DATA['business_name'] in html),
            ('Categoria Polêmica', 'Polêmica' in html or 'polemica' in html.lower()),
            ('Categoria Educativo', 'Educativo' in html or 'educativo' in html.lower()),
            ('Categoria Newsjacking', 'Newsjacking' in html or 'newsjacking' in html.lower()),
            ('Análise enriquecida', 'enriched' in html.lower() or 'análise' in html.lower()),
            ('Fontes/links', 'fonte' in html.lower() or 'http' in html),
            ('CTA presente', 'Criar Conteúdo' in html or 'Acessar' in html),
            ('Footer com ano', '2026' in html),
        ]

        passed = 0
        for name, result in checks:
            status = "✅" if result else "❌"
            print(f"  {status} {name}")
            if result:
                passed += 1

        print(f"\n  Resultado: {passed}/{len(checks)} verificações passaram")

        if save_html:
            path = '/tmp/test_opportunities_email.html'
            with open(path, 'w') as f:
                f.write(html)
            print(f"  📄 HTML salvo em: {path}")

        return passed == len(checks)

    except Exception as e:
        print(f"  ❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_intelligence_email(save_html=False):
    """Testa geração do e-mail de Market Intelligence."""
    print("\n" + "=" * 60)
    print("TESTE 2: E-MAIL DE MARKET INTELLIGENCE (Quarta-feira)")
    print("=" * 60)

    try:
        from ClientContext.utils.market_intelligence_email import generate_market_intelligence_email

        html = generate_market_intelligence_email(
            context_data=MOCK_CONTEXT_DATA,
            user_data=MOCK_USER_DATA
        )

        # Validações
        checks = [
            ('Header presente', 'Inteligência de Mercado' in html),
            ('Nome do usuário', MOCK_USER_DATA['first_name'] in html),
            ('Business name', MOCK_USER_DATA['business_name'] in html),
            ('Seção Mercado', 'mercado' in html.lower() or 'panorama' in html.lower()),
            ('Seção Concorrência', 'concorrência' in html.lower() or 'competição' in html.lower()),
            ('Seção Público', 'público' in html.lower() or 'audiência' in html.lower()),
            ('Seção Tendências', 'tendência' in html.lower()),
            ('Seção Calendário', 'calendário' in html.lower() or 'data' in html.lower()),
            ('Fontes/links', 'fonte' in html.lower() or 'http' in html),
            ('Footer com ano', '2026' in html),
        ]

        passed = 0
        for name, result in checks:
            status = "✅" if result else "❌"
            print(f"  {status} {name}")
            if result:
                passed += 1

        print(f"\n  Resultado: {passed}/{len(checks)} verificações passaram")

        if save_html:
            path = '/tmp/test_market_intelligence_email.html'
            with open(path, 'w') as f:
                f.write(html)
            print(f"  📄 HTML salvo em: {path}")

        return passed == len(checks)

    except Exception as e:
        print(f"  ❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_onboarding_emails(save_html=False):
    """Testa geração dos 3 e-mails de Onboarding."""
    print("\n" + "=" * 60)
    print("TESTE 3: E-MAILS DE ONBOARDING (Dia 1, 3, 7)")
    print("=" * 60)

    try:
        from django.template import Template, Context
        from django.conf import settings

        # Configure Django settings if not already
        if not settings.configured:
            settings.configure(
                TEMPLATES=[{
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': ['templates'],
                }],
                DEFAULT_CHARSET='utf-8',
            )

        import django
        django.setup()

        from django.template.loader import render_to_string

        onboarding_url = 'https://postnow.app/onboarding'
        user_name = MOCK_USER_DATA['first_name']

        all_passed = True

        for email_num in [1, 2, 3]:
            print(f"\n  --- Email {email_num} (Dia {[1, 3, 7][email_num-1]}) ---")

            try:
                html = render_to_string(
                    f'onboarding/email_{email_num}.html',
                    {'user_name': user_name, 'onboarding_url': onboarding_url}
                )

                checks = [
                    ('Nome do usuário', user_name in html),
                    ('URL de onboarding', onboarding_url in html),
                    ('CTA presente', 'onboarding' in html.lower()),
                    ('Assinatura CEO', 'Rogério' in html or 'CEO' in html),
                ]

                passed = 0
                for name, result in checks:
                    status = "✅" if result else "❌"
                    print(f"    {status} {name}")
                    if result:
                        passed += 1

                if passed != len(checks):
                    all_passed = False

                if save_html:
                    path = f'/tmp/test_onboarding_email_{email_num}.html'
                    with open(path, 'w') as f:
                        f.write(html)
                    print(f"    📄 HTML salvo em: {path}")

            except Exception as e:
                print(f"    ❌ ERRO no email {email_num}: {e}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"  ❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enrichment_pipeline():
    """Testa o pipeline de enrichment (Serper + Jina)."""
    print("\n" + "=" * 60)
    print("TESTE 4: PIPELINE DE ENRICHMENT (Serper + Jina)")
    print("=" * 60)

    serper_key = os.getenv('SERPER_API_KEY', '')

    if not serper_key:
        print("  ⚠️  SERPER_API_KEY não configurada - pulando teste de API real")
        print("  ℹ️  Testando apenas imports e estrutura...")

        try:
            from services.serper_search_service import SerperSearchService
            from services.jina_reader_service import JinaReaderService
            from services.source_evaluator_service import SourceEvaluatorService
            from ClientContext.utils.search_utils import (
                fetch_and_filter_sources,
                build_search_query,
                _generate_rule_based_queries,
            )

            print("  ✅ Imports OK")

            # Test query building
            opportunity = {'titulo_ideia': 'Como crescer no Instagram', 'tipo': 'Educativo'}
            query = build_search_query(opportunity, 'educativo')
            print(f"  ✅ build_search_query: '{query}'")

            # Test rule-based queries
            alt_queries = _generate_rule_based_queries('O segredo do marketing digital')
            print(f"  ✅ _generate_rule_based_queries: {alt_queries}")

            # Test service instantiation
            serper = SerperSearchService()
            jina = JinaReaderService()
            evaluator = SourceEvaluatorService()

            print(f"  ✅ SerperSearchService.is_configured(): {serper.is_configured()}")
            print(f"  ✅ JinaReaderService.is_configured(): {jina.is_configured()}")
            print(f"  ✅ SourceEvaluatorService.is_configured(): {evaluator.is_configured()}")

            return True

        except Exception as e:
            print(f"  ❌ ERRO: {e}")
            return False

    else:
        print("  ✅ SERPER_API_KEY configurada - testando API real")

        try:
            from services.serper_search_service import SerperSearchService

            serper = SerperSearchService()
            results = serper.search('marketing digital tendências 2026', num_results=3)

            print(f"  ✅ Serper retornou {len(results)} resultados")
            for i, r in enumerate(results[:3], 1):
                print(f"     {i}. {r.get('title', 'N/A')[:50]}...")

            return len(results) > 0

        except Exception as e:
            print(f"  ❌ ERRO na API: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Teste completo dos e-mails PostNow')
    parser.add_argument('--save', action='store_true', help='Salvar HTMLs em /tmp/')
    args = parser.parse_args()

    print("=" * 60)
    print("TESTE COMPLETO DOS E-MAILS POSTNOW")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {
        'Opportunities Email': test_opportunities_email(args.save),
        'Market Intelligence Email': test_market_intelligence_email(args.save),
        'Onboarding Emails': test_onboarding_emails(args.save),
        'Enrichment Pipeline': test_enrichment_pipeline(),
    }

    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM - verifique acima")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
