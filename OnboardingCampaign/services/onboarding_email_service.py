import logging
import os

import pytz
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils import timezone

from AuditSystem.services import AuditService
from OnboardingCampaign.models import OnboardingEmail
from services.mailjet_service import MailjetService

logger = logging.getLogger(__name__)

# Brazilian timezone
BRT = pytz.timezone('America/Sao_Paulo')

# Email schedule: days after subscription + time of day
EMAIL_SCHEDULE = {
    1: {'days': 1, 'hour': 10},   # Day 1 at 10 AM
    2: {'days': 3, 'hour': 10},   # Day 3 at 10 AM
    3: {'days': 7, 'hour': 10},   # Day 7 at 10 AM
}


class OnboardingEmailService:
    def __init__(self):
        self.mailjet_service = MailjetService()
        self.audit_service = AuditService()

    def send_onboarding_emails_sync(self, user_id: str = None) -> dict:
        """
        Send onboarding emails based on days since subscription.
        Calculates which email (1, 3, or 7 days) should be sent today and sends it immediately.

        Args:
            user_id: Optional user ID to process only that user's emails (for testing)

        Returns:
            dict with send statistics
        """
        import asyncio
        try:
            now = timezone.now()
            today = now.date()

            # Build query for users with active subscriptions and incomplete onboarding
            query = User.objects.filter(
                subscription_status__has_active_subscription=True,
                creator_profile__onboarding_completed=False
            ).select_related('subscription_status__current_subscription', 'creator_profile')

            # Filter by user_id if provided
            if user_id:
                query = query.filter(id=user_id)

            users = list(query)

            sent_count = 0
            failed_count = 0
            skipped_count = 0

            for user in users:
                try:
                    # Get subscription start date
                    subscription = user.subscription_status.current_subscription
                    if not subscription:
                        skipped_count += 1
                        logger.info(f"Skipped user {user.email} - no active subscription")
                        continue

                    start_date = subscription.start_date
                    if timezone.is_naive(start_date):
                        start_date = timezone.make_aware(start_date, BRT)

                    # Calculate days since subscription
                    days_since_subscription = (today - start_date.date()).days
                    # Determine which email to send
                    email_number = None
                    if days_since_subscription == 1:
                        email_number = 1
                    elif days_since_subscription == 3:
                        email_number = 2
                    elif days_since_subscription == 7:
                        email_number = 3
                    else:
                        # Not a sending day for this user
                        continue

                    # Check if this email was already sent
                    already_sent = OnboardingEmail.objects.filter(
                        user=user,
                        email_number=email_number,
                        sent_at__isnull=False
                    ).exists()

                    if already_sent:
                        logger.info(f"Email {email_number} already sent to {user.email}")
                        continue

                    # Render email template
                    user_name = user.first_name or user.username or 'Olá'
                    context = {
                        'user_name': user_name,
                        'onboarding_url': os.getenv('FRONTEND_URL', 'https://postnow.app/onboarding'),
                    }

                    template_name = f'onboarding/email_{email_number}.html'
                    html_content = render_to_string(template_name, context)

                    # Determine subject
                    subjects = {
                        1: "Deu tudo certo com o seu cadastro?",
                        2: "Um post pronto te esperando...",
                        3: "Não quero ser o \"chato\" do e-mail"
                    }
                    subject = subjects.get(email_number, "Complete seu onboarding na PostNow")

                    # Send email (run async operation in isolated context)
                    success, response = asyncio.run(
                        self.mailjet_service.send_email(
                            to_email=user.email,
                            subject=subject,
                            body=html_content
                        )
                    )

                    if success:
                        # Record the sent email
                        OnboardingEmail.objects.update_or_create(
                            user=user,
                            email_number=email_number,
                            defaults={
                                'sent_at': timezone.now()
                            }
                        )
                        sent_count += 1

                        logger.info(
                            f"Sent onboarding email {email_number} to {user.email} "
                            f"(day {days_since_subscription} since subscription)"
                        )
                    else:
                        failed_count += 1
                        logger.error(
                            f"Failed to send onboarding email {email_number} "
                            f"to {user.email}: {response}"
                        )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Error processing onboarding email for {user.email}: {e}"
                    )

            # Log to audit system
            self.audit_service.log_system_operation(
                user=None,
                action='onboarding_emails_cron',
                status='success',
                details={
                    'sent': sent_count,
                    'failed': failed_count,
                    'skipped': skipped_count,
                    'total_processed': len(users)
                }
            )

            return {
                'success': True,
                'sent': sent_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'total': len(users)
            }

        except Exception as e:
            logger.error(f"Error in send_onboarding_emails: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def get_campaign_status(user: User) -> dict:
        """
        Get the current status of the onboarding emails for a user.

        Args:
            user: The User instance

        Returns:
            dict with email status
        """
        try:
            emails = OnboardingEmail.objects.filter(
                user=user).order_by('email_number')

            email_status = []
            for email in emails:
                email_status.append({
                    'email_number': email.email_number,
                    'sent_at': email.sent_at,
                })

            return {
                'success': True,
                'user_email': user.email,
                'emails': email_status,
                'total_emails': emails.count()
            }

        except Exception as e:
            logger.error(
                f"Error getting campaign status for user {user.email}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
