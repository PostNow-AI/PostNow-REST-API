from decimal import Decimal

from django.core.management.base import BaseCommand

from CreditSystem.models import AIModel


class Command(BaseCommand):
    help = 'Populate AI models with their configurations and credit costs'

    def handle(self, *args, **options):
        """Populate AI models with default configurations."""

        # Credit costs adjusted based on user feedback:
        # - Text generation reduced by 80% (now 20% of original cost)
        # - Image generation increased by 80% (now 180% of original cost)
        # Formula: (Provider Cost USD * 5.0 BRL/USD * 100 credits/BRL * 1.5 margin) * adjustment
        models_data = [
            {
                'name': 'gemini-1.5-flash',
                'provider': 'Google',
                # Reduced by 80% - was 0.04, now 0.008
                'cost_per_token': Decimal('0.008'),
                'cost_per_image': Decimal('0.00'),  # No image support
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'gemini-1.5-pro',
                'provider': 'Google',
                # Reduced by 80% - was 0.2, now 0.04
                'cost_per_token': Decimal('0.04'),
                'cost_per_image': Decimal('0.00'),  # No image support
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'gemini-imagen',
                'provider': 'Google',
                'cost_per_token': Decimal('0.1'),  # Minimal text processing
                # Image cost increased by 80% - was ~2.0, now 3.6
                'cost_per_image': Decimal('36'),
                'supports_image_generation': True,
                'is_active': True
            },
            {
                'name': 'claude-3-haiku',
                'provider': 'Anthropic',
                # Reduced by 80% - was 0.02, now 0.004
                'cost_per_token': Decimal('0.004'),
                'cost_per_image': Decimal('0.00'),
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'claude-3-sonnet',
                'provider': 'Anthropic',
                # Reduced by 80% - was 0.2, now 0.04
                'cost_per_token': Decimal('0.04'),
                'cost_per_image': Decimal('0.00'),
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'claude-3-opus',
                'provider': 'Anthropic',
                # Reduced by 80% - was 1.0, now 0.2
                'cost_per_token': Decimal('0.2'),
                'cost_per_image': Decimal('0.00'),
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'gpt-3.5-turbo',
                'provider': 'OpenAI',
                # Reduced by 80% - was 0.15, now 0.03
                'cost_per_token': Decimal('0.03'),
                'cost_per_image': Decimal('0.00'),
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'gpt-4',
                'provider': 'OpenAI',
                # Reduced by 80% - was 4.5, now 0.9
                'cost_per_token': Decimal('0.9'),
                'cost_per_image': Decimal('0.00'),
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'gpt-4-turbo',
                'provider': 'OpenAI',
                # Reduced by 80% - was 1.5, now 0.3
                'cost_per_token': Decimal('0.3'),
                'cost_per_image': Decimal('0.00'),
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'gpt-4o',
                'provider': 'OpenAI',
                # Reduced by 80% - was 0.8, now 0.16
                'cost_per_token': Decimal('0.16'),
                'cost_per_image': Decimal('0.00'),
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'gpt-4o-mini',
                'provider': 'OpenAI',
                # Reduced by 80% - was 0.06, now 0.012
                'cost_per_token': Decimal('0.012'),
                'cost_per_image': Decimal('0.00'),
                'supports_image_generation': False,
                'is_active': True
            },
            {
                'name': 'dall-e-3',
                'provider': 'OpenAI',
                'cost_per_token': Decimal('0.01'),  # Minimal text processing
                # Image cost increased by 80% - was ~4.0, now 7.2
                'cost_per_image': Decimal('7.2'),
                'supports_image_generation': True,
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
