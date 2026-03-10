#!/usr/bin/env python
"""
PREVIEW DE EMAIL LOCAL - Visualiza como os emails ficarão em produção

Este script gera o HTML dos emails usando os templates reais do projeto,
permitindo visualizar as mudanças (como footer dinâmico) antes de fazer deploy.

Uso:
    python scripts/preview_email_local.py

O script gera arquivos HTML que podem ser abertos no navegador.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def generate_opportunities_email_preview():
    """Gera preview do email de oportunidades."""
    from datetime import datetime

    # Importar o gerador real
    from ClientContext.utils.opportunities_email import generate_opportunities_email_template

    # Dados simulados do usuário
    user_data = {
        'first_name': 'Rogério',
        'email': 'rogeriofr86@gmail.com',
        'business_name': 'Supren Veg',
        'greeting_name': 'Rogério',
    }

    # Criar dados simulados de oportunidades
    tendencies_data = {
        'polemica': {
            'titulo': 'Conteúdo Polêmico',
            'items': [
                {
                    'titulo_ideia': 'Proteína vegana é realmente suficiente?',
                    'descricao': 'Debate sobre a eficácia das proteínas vegetais',
                    'score': 92,
                    'trend_validated': True,
                    'search_keywords': ['proteína vegana', 'nutrição', 'alimentação'],
                    'enriched_sources': [
                        {'title': 'Estudo sobre proteínas vegetais 2026', 'url': 'https://example.com/estudo'},
                        {'title': 'Nutrição vegana completa', 'url': 'https://example.com/nutricao'},
                    ]
                },
            ]
        },
        'educativo': {
            'titulo': 'Conteúdo Educativo',
            'items': [
                {
                    'titulo_ideia': 'Guia completo: Como montar uma alimentação vegana balanceada',
                    'descricao': 'Tutorial passo a passo para iniciantes',
                    'score': 88,
                    'trend_validated': True,
                    'search_keywords': ['guia vegano', 'alimentação', 'saúde'],
                    'enriched_sources': [
                        {'title': 'Guia Alimentar para Veganos', 'url': 'https://example.com/guia'},
                    ]
                },
            ]
        },
        'newsjacking': {
            'titulo': 'Oportunidades de Newsjacking',
            'items': [
                {
                    'titulo_ideia': 'O impacto da nova lei de rotulagem em alimentos veganos',
                    'descricao': 'Análise da regulamentação recente',
                    'score': 85,
                    'trend_validated': True,
                    'search_keywords': ['rotulagem', 'anvisa', 'veganos'],
                    'enriched_sources': [
                        {'title': 'ANVISA atualiza regras de rotulagem', 'url': 'https://example.com/anvisa'},
                    ]
                },
            ]
        },
    }

    # Gerar HTML
    html_content = generate_opportunities_email_template(
        tendencies_data=tendencies_data,
        user_data=user_data
    )

    return html_content


def generate_market_intelligence_preview():
    """Gera preview do email de inteligência de mercado."""
    from ClientContext.utils.weekly_context import generate_weekly_context_email_template
    from datetime import datetime

    # Dados simulados do usuário
    user_data = {
        'first_name': 'Rogério',
        'email': 'rogeriofr86@gmail.com',
        'business_name': 'Supren Veg',
        'greeting_name': 'Rogério',
        'specialization': 'Alimentação Vegana e Saudável',
    }

    # Dados simulados de contexto de mercado
    context_data = {
        'mercado': {
            'visao_geral': 'O mercado de alimentação vegana cresce 20% ao ano no Brasil, impulsionado pela maior conscientização sobre saúde e sustentabilidade.',
            'tamanho': 'R$ 5 bilhões em 2025, com projeção de R$ 8 bilhões em 2028',
            'tendencias': ['Proteínas alternativas', 'Sustentabilidade', 'Saúde integral', 'Plant-based premium'],
        },
        'publico': {
            'perfil_demografico': 'Jovens de 25-40 anos, urbanos, preocupados com saúde e meio ambiente',
            'dores_principais': ['Falta de opções saborosas', 'Preços altos', 'Falta de informação nutricional clara'],
            'oportunidades': ['Conteúdo educativo sobre nutrição', 'Receitas acessíveis', 'Desmistificação de mitos'],
        },
        'tendencias': {
            'temas_populares': ['Proteína vegetal completa', 'Receitas práticas do dia a dia', 'Estilo de vida sustentável'],
            'hashtags': ['#vegano', '#plantbased', '#receitas', '#saudavel'],
            'palavras_chave': ['vegano iniciante', 'proteína vegetal', 'comida saudável'],
        },
        'concorrencia': {
            'principais_players': ['Blog do Vegano', 'Veggie Brasil', 'Presunto Vegetariano'],
            'diferenciais': ['Foco em praticidade', 'Conteúdo científico acessível'],
        },
    }

    # Gerar HTML
    html_content = generate_weekly_context_email_template(
        context_data=context_data,
        user_data=user_data
    )

    return html_content


def generate_onboarding_emails_preview():
    """Gera preview dos emails de onboarding usando templates Django."""
    from django.template import Template, Context
    from datetime import datetime

    # Template email_1
    email_1_path = BASE_DIR / 'templates' / 'onboarding' / 'email_1.html'
    email_2_path = BASE_DIR / 'templates' / 'onboarding' / 'email_2.html'
    email_3_path = BASE_DIR / 'templates' / 'onboarding' / 'email_3.html'

    results = {}

    for name, path in [('email_1', email_1_path), ('email_2', email_2_path), ('email_3', email_3_path)]:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Substituir variáveis de template simples
            content = content.replace('{{ user_name }}', 'Rogério')
            content = content.replace('{{ onboarding_url }}', 'https://app.postnow.com.br/onboarding')

            # Para {% now "Y" %}, substituir pelo ano atual
            current_year = str(datetime.now().year)
            content = content.replace('{% now "Y" %}', current_year)

            results[name] = content

    return results


def generate_account_emails_preview():
    """Gera preview dos emails de conta (verificação, reset senha)."""
    from datetime import datetime

    results = {}

    # Email de confirmação
    confirm_path = BASE_DIR / 'templates' / 'account' / 'email' / 'email_confirmation_signup_message.html'
    if confirm_path.exists():
        with open(confirm_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Substituir variáveis
        content = content.replace('{{user.first_name}}', 'Rogério')
        content = content.replace('{{frontend_url}}', 'https://app.postnow.com.br')
        content = content.replace('{{key}}', 'abc123xyz')
        content = content.replace('{% now "Y" %}', str(datetime.now().year))

        results['email_confirmation'] = content

    # Email de reset de senha
    reset_path = BASE_DIR / 'templates' / 'account' / 'email' / 'password_reset_key_message.html'
    if reset_path.exists():
        with open(reset_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Substituir variáveis
        content = content.replace('{{user.first_name}}', 'Rogério')
        content = content.replace('{{frontend_url}}', 'https://app.postnow.com.br')
        content = content.replace('{{uid}}', 'abc123')
        content = content.replace('{{key}}', 'xyz789')
        content = content.replace('{% now "Y" %}', str(datetime.now().year))

        results['password_reset'] = content

    return results


def main():
    """Função principal."""
    print("\n" + "=" * 70)
    print("  PREVIEW DE EMAILS - Teste Local")
    print("=" * 70)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Ano atual (para footer): {datetime.now().year}")

    output_dir = Path('/tmp/postnow_email_previews')
    output_dir.mkdir(exist_ok=True)

    generated_files = []

    # 1. Email de Oportunidades
    print("\n📧 Gerando preview do email de Oportunidades...")
    try:
        html = generate_opportunities_email_preview()
        output_file = output_dir / 'opportunities_email.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        generated_files.append(('Oportunidades de Conteúdo', output_file))
        print(f"   ✅ Salvo em: {output_file}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    # 2. Email de Inteligência de Mercado
    print("\n📧 Gerando preview do email de Inteligência de Mercado...")
    try:
        html = generate_market_intelligence_preview()
        output_file = output_dir / 'market_intelligence_email.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        generated_files.append(('Inteligência de Mercado', output_file))
        print(f"   ✅ Salvo em: {output_file}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    # 3. Emails de Onboarding
    print("\n📧 Gerando previews dos emails de Onboarding...")
    try:
        emails = generate_onboarding_emails_preview()
        for name, html in emails.items():
            output_file = output_dir / f'onboarding_{name}.html'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            generated_files.append((f'Onboarding {name}', output_file))
            print(f"   ✅ {name}: {output_file}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    # 4. Emails de Conta
    print("\n📧 Gerando previews dos emails de Conta...")
    try:
        emails = generate_account_emails_preview()
        for name, html in emails.items():
            output_file = output_dir / f'account_{name}.html'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            generated_files.append((f'Conta: {name}', output_file))
            print(f"   ✅ {name}: {output_file}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    # Resumo
    print("\n" + "=" * 70)
    print("  RESUMO")
    print("=" * 70)
    print(f"\n📁 Todos os previews salvos em: {output_dir}\n")

    for name, path in generated_files:
        print(f"   📄 {name}")
        print(f"      {path}\n")

    print("\n💡 COMO VISUALIZAR:")
    print(f"   open {output_dir}")
    print("   Ou abra qualquer arquivo .html no navegador\n")

    print("🔍 O QUE VERIFICAR:")
    print(f"   1. Footer deve mostrar: © {datetime.now().year} PostNow")
    print("   2. Nome do usuário (Rogério) aparece corretamente")
    print("   3. Estrutura visual está ok")
    print("   4. Links estão formatados corretamente\n")

    print("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
