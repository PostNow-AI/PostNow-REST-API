from django.core.management.base import BaseCommand

from CreditSystem.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create test Stripe price IDs for development (without actually calling Stripe)'

    def handle(self, *args, **options):
        plans = SubscriptionPlan.objects.filter(is_active=True)

        if not plans.exists():
            self.stdout.write(
                self.style.WARNING('No active subscription plans found')
            )
            return

        # Mock Stripe price IDs for testing
        test_price_ids = {
            'monthly': 'price_test_monthly_123',
            'quarterly': 'price_test_quarterly_456',
            'semester': 'price_test_semester_789',
            'yearly': 'price_test_yearly_012',
            'lifetime': 'price_test_lifetime_345'
        }

        self.stdout.write(
            f'Setting up test Stripe price IDs for {plans.count()} plans...\n')

        for plan in plans:
            test_price_id = test_price_ids.get(plan.interval)
            if test_price_id:
                plan.stripe_price_id = test_price_id
                plan.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {plan.name}: {test_price_id}')
                )

        self.stdout.write(
            self.style.SUCCESS('\n✅ Test Stripe price IDs configured!')
        )
        self.stdout.write(
            self.style.WARNING(
                '⚠️  These are test IDs - they won\'t work with real Stripe payments')
        )
