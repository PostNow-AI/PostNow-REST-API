#!/usr/bin/env python3
"""
Script para configurar o Stripe automaticamente
"""
import os
import sys
from pathlib import Path

import django

# Adiciona o diretório raiz ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
django.setup()


def setup_stripe_products():
    """Configura os produtos do Stripe"""
    print("🔧 Configurando produtos do Stripe...")

    # Lista de produtos para criar
    products = [
        {
            'name': 'Pacote Básico - 100 Créditos',
            'price': 2500,  # R$ 25,00 em centavos
            'currency': 'brl',
            'description': '100 créditos para uso de modelos de IA'
        },
        {
            'name': 'Pacote Popular - 500 Créditos',
            'price': 10000,  # R$ 100,00 em centavos
            'currency': 'brl',
            'description': '500 créditos para uso de modelos de IA'
        },
        {
            'name': 'Pacote Profissional - 1000 Créditos',
            'price': 18000,  # R$ 180,00 em centavos
            'currency': 'brl',
            'description': '1000 créditos para uso de modelos de IA'
        },
        {
            'name': 'Pacote Empresarial - 2500 Créditos',
            'price': 40000,  # R$ 400,00 em centavos
            'currency': 'brl',
            'description': '2500 créditos para uso de modelos de IA'
        }
    ]

    try:
        import stripe

        # Verifica se a chave do Stripe está configurada
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEY não configurada!")
            print("Configure a variável de ambiente e tente novamente.")
            return False

        print(f"✅ Stripe configurado com chave: {stripe.api_key[:12]}...")

        # Cria os produtos
        for product_data in products:
            try:
                # Cria o produto
                product = stripe.Product.create(
                    name=product_data['name'],
                    description=product_data['description']
                )

                # Cria o preço
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=product_data['price'],
                    currency=product_data['currency']
                )

                print(f"✅ Produto criado: {product.name}")
                print(f"   ID: {product.id}")
                print(f"   Preço: {price.id}")
                print(f"   Valor: R$ {product_data['price']/100:.2f}")
                print()

            except stripe.error.StripeError as e:
                print(f"❌ Erro ao criar produto {product_data['name']}: {e}")
                continue

        print("🎉 Produtos do Stripe configurados com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Copie os Price IDs acima")
        print("2. Atualize os stripe_price_id no Django")
        print("3. Configure o webhook no dashboard do Stripe")

        return True

    except ImportError:
        print("❌ Stripe não está instalado!")
        print("Execute: pip install stripe")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def update_django_packages():
    """Atualiza os pacotes no Django com os IDs do Stripe"""
    print("\n🔄 Atualizando pacotes no Django...")

    # Aqui você pode implementar a atualização automática
    # dos stripe_price_id baseado nos produtos criados
    print("⚠️  Atualize manualmente os stripe_price_id no admin do Django")
    print("   ou execute o comando: python manage.py populate_credit_system")


def main():
    """Função principal"""
    print("🚀 Configuração Automática do Stripe")
    print("=" * 40)

    # Verifica se as variáveis de ambiente estão configuradas
    if not os.getenv('STRIPE_SECRET_KEY'):
        print("❌ Variáveis de ambiente não configuradas!")
        print("\n📝 Crie um arquivo .env com:")
        print("STRIPE_SECRET_KEY=sk_test_...")
        print("STRIPE_PUBLISHABLE_KEY=pk_test_...")
        print("STRIPE_WEBHOOK_SECRET=whsec_...")
        return

    # Configura os produtos
    if setup_stripe_products():
        update_django_packages()

    print("\n✅ Configuração concluída!")


if __name__ == '__main__':
    main()
