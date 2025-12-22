from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from CreditSystem.models import AIModel, CreditPackage

User = get_user_model()


class Command(BaseCommand):
    """
    Comando para popular dados iniciais do sistema de créditos
    """
    help = 'Popula o sistema de créditos com dados iniciais'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stripe-mode',
            choices=['test', 'production'],
            default='test',
            help='Modo do Stripe (test ou production)'
        )

    def handle(self, *args, **options):
        """Executa o comando"""
        stripe_mode = options['stripe_mode']

        self.stdout.write(
            f'Populando sistema de créditos em modo {stripe_mode}...')

        # Cria pacotes de créditos
        self._create_credit_packages(stripe_mode)

        # Cria modelos de IA
        self._create_ai_models()

        self.stdout.write(
            self.style.SUCCESS('Sistema de créditos populado com sucesso!')
        )

        if stripe_mode == 'test':
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  IMPORTANTE: Atualize os stripe_price_id com os IDs reais do Stripe!\n'
                    '1. Acesse o dashboard do Stripe\n'
                    '2. Vá para Products > Pricing\n'
                    '3. Copie os Price IDs\n'
                    '4. Atualize no admin do Django ou via shell\n'
                )
            )

    def _create_credit_packages(self, stripe_mode):
        """Cria pacotes de créditos iniciais"""
        if stripe_mode == 'test':
            # IDs de teste - SUBSTITUA pelos IDs reais do Stripe
            packages_data = [
                {
                    'name': 'Pacote Básico',
                    'credits': Decimal('100.00'),
                    'price': Decimal('25.00'),
                    'stripe_price_id': 'price_basic_100_credits_test',  # ⚠️ SUBSTITUIR
                    'is_active': True
                },
                {
                    'name': 'Pacote Popular',
                    'credits': Decimal('500.00'),
                    'price': Decimal('100.00'),
                    'stripe_price_id': 'price_popular_500_credits_test',  # ⚠️ SUBSTITUIR
                    'is_active': True
                },
                {
                    'name': 'Pacote Profissional',
                    'credits': Decimal('1000.00'),
                    'price': Decimal('180.00'),
                    'stripe_price_id': 'price_professional_1000_credits_test',  # ⚠️ SUBSTITUIR
                    'is_active': True
                },
                {
                    'name': 'Pacote Empresarial',
                    'credits': Decimal('2500.00'),
                    'price': Decimal('400.00'),
                    'stripe_price_id': 'price_enterprise_2500_credits_test',  # ⚠️ SUBSTITUIR
                    'is_active': True
                }
            ]
        else:
            # IDs de produção - SUBSTITUA pelos IDs reais do Stripe
            packages_data = [
                {
                    'name': 'Pacote Básico',
                    'credits': Decimal('100.00'),
                    'price': Decimal('25.00'),
                    'stripe_price_id': 'price_basic_100_credits_prod',  # ⚠️ SUBSTITUIR
                    'is_active': True
                },
                {
                    'name': 'Pacote Popular',
                    'credits': Decimal('500.00'),
                    'price': Decimal('100.00'),
                    'stripe_price_id': 'price_popular_500_credits_prod',  # ⚠️ SUBSTITUIR
                    'is_active': True
                },
                {
                    'name': 'Pacote Profissional',
                    'credits': Decimal('1000.00'),
                    'price': Decimal('180.00'),
                    'stripe_price_id': 'price_professional_1000_credits_prod',  # ⚠️ SUBSTITUIR
                    'is_active': True
                },
                {
                    'name': 'Pacote Empresarial',
                    'credits': Decimal('2500.00'),
                    'price': Decimal('400.00'),
                    'stripe_price_id': 'price_enterprise_2500_credits_prod',  # ⚠️ SUBSTITUIR
                    'is_active': True
                }
            ]

        for package_data in packages_data:
            package, created = CreditPackage.objects.get_or_create(
                stripe_price_id=package_data['stripe_price_id'],
                defaults=package_data
            )

            if created:
                self.stdout.write(
                    f'Pacote criado: {package.name} - R$ {package.price} ({package.credits} créditos)'
                )
            else:
                self.stdout.write(
                    f'Pacote já existe: {package.name}'
                )

    def _create_ai_models(self):
        """Cria modelos de IA iniciais"""
        models_data = [
            {
                'name': 'gemini-pro',
                'provider': 'Google',
                'cost_per_token': Decimal('0.000001'),
                'is_active': True
            },
            {
                'name': 'claude-3-sonnet',
                'provider': 'Anthropic',
                'cost_per_token': Decimal('0.000003'),
                'is_active': True
            },
            {
                'name': 'gpt-4',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.00003'),
                'is_active': True
            },
            {
                'name': 'gpt-3.5-turbo',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.000002'),
                'is_active': True
            }
        ]

        for model_data in models_data:
            model, created = AIModel.objects.get_or_create(
                name=model_data['name'],
                defaults=model_data
            )

            if created:
                self.stdout.write(
                    f'Modelo de IA criado: {model.provider} - {model.name}'
                )
            else:
                self.stdout.write(
                    f'Modelo de IA já existe: {model.provider} - {model.name}'
                )
