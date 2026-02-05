import logging
from collections import defaultdict
from typing import Any, Dict

from asgiref.sync import sync_to_async
from ClientContext.models import ClientContext
from ClientContext.utils.weekly_context import (
    generate_weekly_context_email_template,
    generate_opportunities_email_template,
    generate_market_intelligence_email_template,
)
from CreatorProfile.models import CreatorProfile
from django.contrib.auth.models import User
from services.mailjet_service import MailjetService

logger = logging.getLogger(__name__)

EMAIL_TYPE_OPPORTUNITIES = 'opportunities'
EMAIL_TYPE_MARKET_INTELLIGENCE = 'market_intelligence'


class WeeklyContextEmailService:
    def __init__(self):
        self.mailjet_service = MailjetService()

    async def fetch_users_context_data(self) -> list:
        """Fetch users and their weekly context data to be mailed."""
        return await sync_to_async(list)(
            ClientContext.objects.filter(
                weekly_context_error=None,
            ).select_related('user').values(
                'id', 'user__id', 'user__email', 'user__first_name', 
                'market_panorama', 'market_tendencies', 'market_challenges', 'market_opportunities', 'market_sources', 
                'competition_main', 'competition_strategies', 'competition_benchmark', 'competition_opportunities', 'competition_sources', 
                'target_audience_profile', 'target_audience_behaviors', 'target_audience_interests', 'target_audience_sources', 
                'tendencies_popular_themes', 'tendencies_data', 'tendencies_hashtags', 'tendencies_keywords', 'tendencies_sources', 
                'seasonal_relevant_dates', 'seasonal_local_events', 'seasonal_sources', 
                'brand_online_presence', 'brand_reputation', 'brand_communication_style', 'brand_sources', 
                'created_at', 'updated_at', 'user_id', 'weekly_context_error', 'weekly_context_error_date'
            )
        )

    async def mail_weekly_context(self, email_type=EMAIL_TYPE_OPPORTUNITIES):
        """Send weekly context emails to users."""
        contexts = await self.fetch_users_context_data()
        if not contexts:
            return {
                'status': 'completed',
                'total_users': 0,
                'processed': 0,
                'message': 'No users to process',
            }

        users_context = defaultdict(list)
        for context in contexts:
            user_id = context['user__id']
            users_context[user_id].append(context)

        processed = 0
        failed = 0

        for user_id in users_context.keys():
            try:
                user = await sync_to_async(User.objects.get)(id=user_id)
                # Assuming one context per user
                context_data = users_context[user_id][0]
                await self.send_weekly_context_email(user, context_data, email_type=email_type)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process user {user_id}: {str(e)}")
                failed += 1
                users_context[user_id] = {
                    'status': 'failed',
                    'user_id': user_id,
                    'error': str(e)
                }

        return {
            'status': 'completed',
            'total_users': len(users_context),
            'processed': processed,
            'failed': failed,
        }

    async def send_weekly_context_email(self, user: User, context_data: Dict[str, Any], email_type=None) -> Dict[str, Any]:
        """Send weekly context email to a single user."""
        try:
            # Get user profile data
            user_data = await self._get_user_profile_data(user)

            # Generate email content based on type
            if email_type == EMAIL_TYPE_OPPORTUNITIES:
                subject = f"🎯 Oportunidades de Conteúdo - {user_data['business_name']}"
                html_content = generate_opportunities_email_template(
                    context_data, user_data)
            elif email_type == EMAIL_TYPE_MARKET_INTELLIGENCE:
                subject = f"📊 Inteligência de Mercado - {user_data['business_name']}"
                html_content = generate_market_intelligence_email_template(
                    context_data, user_data)
            else:
                # Default: combined email (used by generate_single_client_context)
                subject = f"📈 Seu Contexto Semanal de Mercado - {user_data['business_name']}"
                html_content = generate_weekly_context_email_template(
                    context_data, user_data)

            # Send email
            success, response = await self.mailjet_service.send_email(
                to_email=user.email,
                subject=subject,
                body=html_content,
                attachments=None
            )

            if success:
                logger.info(
                    f"Weekly context email sent successfully to user {user.id} - {user.username}")
                return {
                    'status': 'success',
                    'user_id': user.id,
                    'email': user.email,
                    'message': 'Email sent successfully'
                }
            else:
                logger.error(
                    f"Failed to send weekly context email to user {user.id}: {response}")
                return {
                    'status': 'failed',
                    'user_id': user.id,
                    'email': user.email,
                    'error': str(response)
                }

        except Exception as e:
            logger.error(
                f"Error sending weekly context email to user {user.id}: {str(e)}")
            return {
                'status': 'failed',
                'user_id': user.id,
                'email': user.email,
                'error': str(e)
            }

    @sync_to_async
    def _get_user_profile_data(self, user: User) -> Dict[str, str]:
        """Get user profile data for email personalization."""
        try:
            profile = CreatorProfile.objects.filter(user=user).first()
            
            # Helper to safely get professional_name if it exists in model (it might not)
            prof_name = getattr(profile, 'professional_name', None) if profile else None

            if profile:
                return {
                    'user_name': user.first_name or user.username,
                    'business_name': profile.business_name or 'Sua Empresa',
                    'professional_name': prof_name or user.first_name or user.username,
                    'profession': getattr(profile, 'profession', 'Profissional'),
                    'specialization': profile.specialization or 'Mercado'
                }
            else:
                return {
                    'user_name': user.first_name or user.username,
                    'business_name': 'Sua Empresa',
                    'professional_name': user.first_name or user.username,
                    'profession': 'Profissional',
                    'specialization': 'Mercado'
                }

        except Exception as e:
            logger.error(
                f"Error getting user profile data for user {user.id}: {str(e)}")
            return {
                'user_name': user.first_name or user.username or 'Usuário',
                'business_name': 'Sua Empresa',
                'professional_name': user.first_name or user.username or 'Usuário',
                'profession': 'Profissional',
                'specialization': 'Mercado'
            }
