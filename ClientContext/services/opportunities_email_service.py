"""
Service for sending weekly opportunities email (Monday).
Contains only enriched content opportunities from Phase 2.
"""
import logging
from collections import defaultdict
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

from ClientContext.models import ClientContext
from ClientContext.utils.opportunities_email import (
    generate_opportunities_email_template,
    generate_opportunities_plain_text,
)
from services.get_creator_profile_data import get_creator_profile_data
from services.mailjet_service import MailjetService

logger = logging.getLogger(__name__)


class OpportunitiesEmailService:
    """Service for sending weekly opportunities emails on Mondays."""

    def __init__(self):
        self.mailjet_service = MailjetService()

    @staticmethod
    async def fetch_enriched_contexts() -> list:
        """Fetch users with enriched context data ready to be mailed."""
        return await sync_to_async(list)(
            ClientContext.objects.filter(
                weekly_context_error__isnull=True,
                context_enrichment_status='enriched',
            ).select_related('user').values(
                'id', 'user__id', 'user__email', 'user__first_name',
                'tendencies_data', 'context_enrichment_status',
                'context_enrichment_date', 'user_id',
            )
        )

    async def mail_opportunities(self) -> Dict[str, Any]:
        """Send opportunities emails to all users with enriched data."""
        contexts = await self.fetch_enriched_contexts()

        if not contexts:
            logger.info("No enriched contexts to mail")
            return {
                'status': 'completed',
                'total_users': 0,
                'processed': 0,
                'message': 'No users with enriched context to process',
            }

        users_context = defaultdict(list)
        for context in contexts:
            user_id = context['user__id']
            users_context[user_id].append(context)

        processed = 0
        failed = 0
        results = []

        for user_id in users_context.keys():
            try:
                user = await sync_to_async(User.objects.get)(id=user_id)
                context_data = users_context[user_id][0]
                result = await self.send_opportunities_email(user, context_data)
                results.append(result)

                if result.get('status') == 'success':
                    processed += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Failed to process user {user_id}: {str(e)}")
                failed += 1
                results.append({
                    'status': 'failed',
                    'user_id': user_id,
                    'error': str(e)
                })

        return {
            'status': 'completed',
            'total_users': len(users_context),
            'processed': processed,
            'failed': failed,
            'details': results,
        }

    async def send_opportunities_email(
        self,
        user: User,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send opportunities email to a single user."""
        try:
            # Get user profile data
            user_data = await sync_to_async(get_creator_profile_data)(user)

            # Extract tendencies_data for the template
            tendencies_data = context_data.get('tendencies_data') or {}

            # Generate email content
            subject = f"🎯 Oportunidades de Conteúdo da Semana - {user_data['business_name']}"
            html_content = generate_opportunities_email_template(
                tendencies_data, user_data
            )
            text_content = generate_opportunities_plain_text(
                tendencies_data, user_data
            )

            # Send email
            success, response = await self.mailjet_service.send_email(
                to_email=user.email,
                subject=subject,
                body=html_content,
                text_body=text_content,
                attachments=None
            )

            if success:
                logger.info(
                    f"Opportunities email sent successfully to user {user.id} - {user.email}"
                )
                return {
                    'status': 'success',
                    'user_id': user.id,
                    'email': user.email,
                    'message': 'Email sent successfully'
                }
            else:
                logger.error(
                    f"Failed to send opportunities email to user {user.id}: {response}"
                )
                return {
                    'status': 'failed',
                    'user_id': user.id,
                    'email': user.email,
                    'error': str(response)
                }

        except Exception as e:
            logger.error(
                f"Error sending opportunities email to user {user.id}: {str(e)}"
            )
            return {
                'status': 'failed',
                'user_id': user.id,
                'email': user.email,
                'error': str(e)
            }
