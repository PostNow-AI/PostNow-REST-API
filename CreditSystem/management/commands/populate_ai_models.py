from decimal import Decimal

from django.core.management.base import BaseCommand

from CreditSystem.models import AIModel


class Command(BaseCommand):
    help = 'Populate AI models with their configurations and credit costs'

    def handle(self, *args, **options):
        """Populate AI models with default configurations."""

        # Credit costs include margin for business sustainability
        # Formula: (Provider Cost USD * 5.0 BRL/USD * 100 credits/BRL * 1.5 margin)
        models_data = [
            {
                'name': 'gemini-1.5-flash',
                'provider': 'Google',
                # Very affordable for users
                'cost_per_token': Decimal('0.0004'),
                'is_active': True
            },
            {
                'name': 'gemini-1.5-pro',
                'provider': 'Google',
                'cost_per_token': Decimal('0.002'),   # Premium model
                'is_active': True
            },
            {
                'name': 'claude-3-haiku',
                'provider': 'Anthropic',
                # Fastest, cheapest Claude
                'cost_per_token': Decimal('0.0002'),
                'is_active': True
            },
            {
                'name': 'claude-3-sonnet',
                'provider': 'Anthropic',
                'cost_per_token': Decimal('0.002'),   # Balanced Claude model
                'is_active': True
            },
            {
                'name': 'claude-3-opus',
                'provider': 'Anthropic',
                'cost_per_token': Decimal('0.01'),    # Most powerful Claude
                'is_active': True
            },
            {
                'name': 'gpt-3.5-turbo',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.0015'),  # Budget OpenAI option
                'is_active': True
            },
            {
                'name': 'gpt-4',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.045'),   # Legacy GPT-4
                'is_active': True
            },
            {
                'name': 'gpt-4-turbo',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.015'),   # Current best GPT-4
                'is_active': True
            },
            {
                'name': 'gpt-4o',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.008'),   # Latest GPT-4 Omni
                'is_active': True
            },
            {
                'name': 'gpt-4o-mini',
                'provider': 'OpenAI',
                # Affordable GPT-4 quality
                'cost_per_token': Decimal('0.0006'),
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
