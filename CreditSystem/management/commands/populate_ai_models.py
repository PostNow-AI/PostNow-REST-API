from decimal import Decimal

from django.core.management.base import BaseCommand

from CreditSystem.models import AIModel


class Command(BaseCommand):
    help = 'Populate AI models with their configurations and credit costs'

    def handle(self, *args, **options):
        """Populate AI models with default configurations."""

        models_data = [
            {
                'name': 'gemini-1.5-flash',
                'provider': 'Google',
                'cost_per_token': Decimal('0.000001'),
                'is_active': True
            },
            {
                'name': 'gemini-1.5-pro',
                'provider': 'Google',
                'cost_per_token': Decimal('0.000002'),
                'is_active': True
            },
            {
                'name': 'claude-3-sonnet',
                'provider': 'Anthropic',
                'cost_per_token': Decimal('0.000003'),
                'is_active': True
            },
            {
                'name': 'claude-3-haiku',
                'provider': 'Anthropic',
                'cost_per_token': Decimal('0.00000025'),
                'is_active': True
            },
            {
                'name': 'gpt-4',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.00003'),
                'is_active': True
            },
            {
                'name': 'gpt-4-turbo',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.00001'),
                'is_active': True
            },
            {
                'name': 'gpt-3.5-turbo',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.000002'),
                'is_active': True
            },
            {
                'name': 'llama-3-8b',
                'provider': 'Meta',
                'cost_per_token': Decimal('0.0000005'),
                'is_active': True
            },
            {
                'name': 'llama-3-70b',
                'provider': 'Meta',
                'cost_per_token': Decimal('0.000001'),
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
                    self.style.SUCCESS(
                        f'AI Model created: {model.provider} - {model.name} '
                        f'(Cost: {model.cost_per_token} credits/token)'
                    )
                )
            else:
                # Update existing model
                for key, value in model_data.items():
                    if key != 'name':  # Don't update the name
                        setattr(model, key, value)
                model.save()

                self.stdout.write(
                    self.style.WARNING(
                        f'AI Model updated: {model.provider} - {model.name} '
                        f'(Cost: {model.cost_per_token} credits/token)'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated {len(models_data)} AI models'
            )
        )
