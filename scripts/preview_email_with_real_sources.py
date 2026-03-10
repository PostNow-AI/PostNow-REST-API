#!/usr/bin/env python
"""
Preview de email com fontes reais do Serper.

Usa os resultados do teste de enrichment para gerar um email realista.
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Setup path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def load_test_results():
    """Carrega resultados do teste de enrichment."""
    results_file = Path('/tmp/enrichment_test_results.json')
    if results_file.exists():
        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def generate_email_with_real_sources():
    """Gera email com fontes reais."""
    from ClientContext.utils.opportunities_email import generate_opportunities_email_template

    # Carregar resultados do teste
    test_results = load_test_results()

    # Dados do usuário
    user_data = {
        'first_name': 'Rogério',
        'email': 'rogeriofr86@gmail.com',
        'business_name': 'Agência de Marketing',
        'greeting_name': 'Rogério',
    }

    # Construir tendencies_data com resultados reais
    if test_results:
        print("📂 Usando dados reais do teste de enrichment")
        tendencies_data = {}

        for result in test_results:
            category = result['category']
            sources = result.get('selected', [])

            # Mapear para formato esperado
            enriched_sources = [
                {'title': s['title'], 'url': s['url']}
                for s in sources
            ]

            # Títulos descritivos por categoria
            titles = {
                'polemica': '🔥 Conteúdo Polêmico',
                'educativo': '🧠 Conteúdo Educativo',
                'newsjacking': '📰 Newsjacking',
                'estudo_caso': '💼 Estudos de Caso',
                'entretenimento': '😂 Entretenimento',
                'futuro': '🔮 Tendências Futuras',
            }

            tendencies_data[category] = {
                'titulo': titles.get(category, category.title()),
                'items': [
                    {
                        'titulo_ideia': result['opportunity'],
                        'descricao': f'Análise de {len(sources)} fontes qualificadas sobre o tema.',
                        'score': 85,
                        'trend_validated': True,
                        'search_keywords': result['opportunity'].split()[:5],
                        'enriched_sources': enriched_sources,
                        'enriched_analysis': f'Encontradas {len(sources)} fontes relevantes para este tema.',
                    }
                ]
            }
    else:
        print("⚠️ Usando dados simulados (teste não encontrado)")
        tendencies_data = {
            'polemica': {
                'titulo': '🔥 Conteúdo Polêmico',
                'items': [{
                    'titulo_ideia': 'Por que 90% das estratégias de marketing falham',
                    'descricao': 'Debate sobre falhas comuns em marketing',
                    'score': 85,
                    'enriched_sources': [
                        {'title': 'A Falência do Marketing Fragmentado', 'url': 'https://lebbe.com.br/exemplo'},
                    ]
                }]
            },
            'educativo': {
                'titulo': '🧠 Conteúdo Educativo',
                'items': [{
                    'titulo_ideia': 'Como criar conteúdo que engaja',
                    'descricao': 'Guia completo de criação de conteúdo',
                    'score': 88,
                    'enriched_sources': [
                        {'title': 'Guia completo de conteúdo', 'url': 'https://sebrae.com.br/exemplo'},
                    ]
                }]
            },
        }

    # Gerar HTML
    html_content = generate_opportunities_email_template(
        tendencies_data=tendencies_data,
        user_data=user_data
    )

    return html_content, tendencies_data


def main():
    """Função principal."""
    print("\n" + "=" * 70)
    print("  PREVIEW DE EMAIL COM FONTES REAIS")
    print("=" * 70)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        html, tendencies_data = generate_email_with_real_sources()

        # Salvar HTML
        output_file = Path('/tmp/email_preview_real_sources.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Email gerado: {output_file}")

        # Mostrar resumo das fontes incluídas
        print("\n📋 Fontes incluídas no email:")
        for category, data in tendencies_data.items():
            items = data.get('items', [])
            for item in items:
                print(f"\n   {category.upper()}: {item.get('titulo_ideia', 'N/A')}")
                sources = item.get('enriched_sources', [])
                for src in sources:
                    print(f"      • {src.get('title', 'N/A')[:50]}...")
                    print(f"        {src.get('url', 'N/A')}")

        print(f"\n💡 Para visualizar:")
        print(f"   open {output_file}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())
