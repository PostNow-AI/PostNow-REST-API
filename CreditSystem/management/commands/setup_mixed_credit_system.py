from decimal import Decimal

from django.core.management.base import BaseCommand

from CreditSystem.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Set up subscription plans with the new monthly credit system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing plans with monthly credits',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                '🚀 Setting up Mixed Subscription + Credit System')
        )

        # Define subscription plans with monthly credits
        plans_config = [
            {
                'name': 'Basic Plan',
                'description': 'Basic subscription with 30 monthly credits',
                'interval': 'monthly',
                'price': Decimal('29.99'),
                'monthly_credits': Decimal('30.00'),
                'allow_credit_purchase': False,
            },
            {
                'name': 'Pro Plan',
                'description': 'Pro subscription with 100 monthly credits',
                'interval': 'monthly',
                'price': Decimal('59.99'),
                'monthly_credits': Decimal('100.00'),
                'allow_credit_purchase': True,
            },
            {
                'name': 'Enterprise Plan',
                'description': 'Enterprise subscription with 300 monthly credits',
                'interval': 'monthly',
                'price': Decimal('149.99'),
                'monthly_credits': Decimal('300.00'),
                'allow_credit_purchase': True,
            },
            {
                'name': 'Lifetime Plan',
                'description': 'Lifetime access with 50 monthly credits',
                'interval': 'lifetime',
                'price': Decimal('999.99'),
                'monthly_credits': Decimal('50.00'),
                'allow_credit_purchase': True,
            }
        ]

        created_count = 0
        updated_count = 0

        for plan_config in plans_config:
            try:
                plan, created = SubscriptionPlan.objects.get_or_create(
                    name=plan_config['name'],
                    defaults=plan_config
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created: {plan.name}')
                    )
                    self.stdout.write(f'   - Price: R$ {plan.price}')
                    self.stdout.write(
                        f'   - Monthly Credits: {plan.monthly_credits}')
                    self.stdout.write(
                        f'   - Allow Extra Purchase: {plan.allow_credit_purchase}')

                elif options['update_existing']:
                    # Update existing plan with new fields
                    updated = False

                    if not hasattr(plan, 'monthly_credits') or plan.monthly_credits == 0:
                        plan.monthly_credits = plan_config['monthly_credits']
                        updated = True

                    if not hasattr(plan, 'allow_credit_purchase'):
                        plan.allow_credit_purchase = plan_config['allow_credit_purchase']
                        updated = True

                    if updated:
                        plan.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'🔄 Updated: {plan.name}')
                        )
                        self.stdout.write(
                            f'   - Monthly Credits: {plan.monthly_credits}')
                        self.stdout.write(
                            f'   - Allow Extra Purchase: {plan.allow_credit_purchase}')
                    else:
                        self.stdout.write(f'ℹ️  Already exists: {plan.name}')
                else:
                    self.stdout.write(f'ℹ️  Already exists: {plan.name}')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Error with {plan_config["name"]}: {str(e)}')
                )

        self.stdout.write('')
        self.stdout.write('📊 Summary:')
        self.stdout.write(f'   Created: {created_count} plans')
        self.stdout.write(f'   Updated: {updated_count} plans')

        self.stdout.write('')
        self.stdout.write('💡 Fixed Pricing Information:')
        self.stdout.write('   - Text Generation: 0.02 credits per operation')
        self.stdout.write('   - Image Generation: 0.23 credits per operation')

        self.stdout.write('')
        self.stdout.write('📋 Usage Examples with Basic Plan (30 credits):')
        self.stdout.write('   - Pure text: 1,500 text generations/month')
        self.stdout.write('   - Pure images: 130 image generations/month')
        self.stdout.write(
            '   - Mixed usage: 50 texts + 20 images = 5.6 credits')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Setup completed!'))

        self.stdout.write('')
        self.stdout.write('🚨 Required Actions:')
        self.stdout.write('   1. Update Stripe price IDs for each plan')
        self.stdout.write('   2. Test subscription assignment to users')
        self.stdout.write('   3. Verify monthly credit reset functionality')
        self.stdout.write('   4. Update frontend to show fixed pricing')
