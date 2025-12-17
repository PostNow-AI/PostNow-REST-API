import stripe
from django.conf import settings
from django.core.management.base import BaseCommand

from CreditSystem.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create Stripe prices for subscription plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating prices',
        )

    def handle(self, *args, **options):
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)

        if not stripe.api_key:
            self.stdout.write(
                self.style.ERROR('STRIPE_SECRET_KEY not found in settings')
            )
            return

        plans = SubscriptionPlan.objects.filter(is_active=True)

        if not plans.exists():
            self.stdout.write(
                self.style.WARNING('No active subscription plans found')
            )
            return

        self.stdout.write(
            f'Found {plans.count()} subscription plans to process')

        for plan in plans:
            self.stdout.write(f'\nProcessing: {plan.name}')

            if plan.stripe_price_id:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Already has Stripe price ID: {plan.stripe_price_id}')
                )
                continue

            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Would create Stripe price for ${plan.price:.2f} {plan.interval}')
                )
                continue

            try:
                # Create Stripe product first
                product = stripe.Product.create(
                    name=plan.name,
                    description=plan.description,
                )

                # Configure price parameters based on interval
                price_params = {
                    'product': product.id,
                    'unit_amount': int(plan.price * 100),  # Convert to cents
                    'currency': 'brl',  # Brazilian Real
                }

                if plan.interval == 'lifetime':
                    # One-time payment for lifetime
                    price_params['billing_scheme'] = 'per_unit'
                else:
                    # Recurring subscription
                    price_params['recurring'] = {
                        'interval': self._get_stripe_interval(plan.interval)}

                # Create Stripe price
                price = stripe.Price.create(**price_params)

                # Update plan with Stripe price ID
                plan.stripe_price_id = price.id
                plan.save()

                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Created Stripe price: {price.id}')
                )

            except stripe.error.StripeError as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Stripe error: {str(e)}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('\n✅ Stripe price setup completed!')
        )

    def _get_stripe_interval(self, plan_interval):
        """Convert plan interval to Stripe interval"""
        interval_mapping = {
            'monthly': 'month',
            'quarterly': 'month',  # We'll handle quarterly as 3-month interval
            'semester': 'month',   # We'll handle semester as 6-month interval
            'yearly': 'year',
        }
        return interval_mapping.get(plan_interval, 'month')
