from decimal import Decimal

from django.core.management.base import BaseCommand

from CreditSystem.models import AIModel


class Command(BaseCommand):
    help = 'Populate AI models with their configurations and credit costs'

    def handle(self, *args, **options):
        """Populate AI models with default configurations."""

        # Credit costs include margin for business sustainability
        # Formula: (Provider Cost USD * 5.0 BRL/USD * 100 credits/BRL * 1.5 margin) * 100
        # Costs multiplied by 100x from original for higher credit consumption
        models_data = [
            {
                'name': 'gemini-1.5-flash',
                'provider': 'Google',
                # Very affordable for users
                'cost_per_token': Decimal('0.04'),
                'is_active': True
            },
            {
                'name': 'gemini-1.5-pro',
                'provider': 'Google',
                'cost_per_token': Decimal('0.2'),   # Premium model
                'is_active': True
            },
            {
                'name': 'claude-3-haiku',
                'provider': 'Anthropic',
                # Fastest, cheapest Claude
                'cost_per_token': Decimal('0.02'),
                'is_active': True
            },
            {
                'name': 'claude-3-sonnet',
                'provider': 'Anthropic',
                'cost_per_token': Decimal('0.2'),   # Balanced Claude model
                'is_active': True
            },
            {
                'name': 'claude-3-opus',
                'provider': 'Anthropic',
                'cost_per_token': Decimal('1.0'),    # Most powerful Claude
                'is_active': True
            },
            {
                'name': 'gpt-3.5-turbo',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.15'),  # Budget OpenAI option
                'is_active': True
            },
            {
                'name': 'gpt-4',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('4.5'),   # Legacy GPT-4
                'is_active': True
            },
            {
                'name': 'gpt-4-turbo',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('1.5'),   # Current best GPT-4
                'is_active': True
            },
            {
                'name': 'gpt-4o',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.8'),   # Latest GPT-4 Omni
                'is_active': True
            },
            {
                'name': 'gpt-4o-mini',
                'provider': 'OpenAI',
                # Affordable GPT-4 quality
                'cost_per_token': Decimal('0.06'),
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
