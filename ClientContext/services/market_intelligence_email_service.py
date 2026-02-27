"""
Serviço de envio do e-mail de Inteligência de Mercado (Quarta-feira).

Este é um serviço SEPARADO do WeeklyContextEmailService.
Usa o template market_intelligence_email.py.
"""
import logging
from collections import defaultdict
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

from ClientContext.models import ClientContext
from ClientContext.utils.market_intelligence_email import generate_market_intelligence_email
from services.get_creator_profile_data import get_creator_profile_data
from services.mailjet_service import MailjetService

logger = logging.getLogger(__name__)


class MarketIntelligenceEmailService:
    """Serviço para envio do e-mail de Inteligência de Mercado."""

    def __init__(self):
        self.mailjet_service = MailjetService()

    @staticmethod
    async def fetch_users_context_data(
        batch_number: int = 1,
        batch_size: int = 0
    ) -> list:
        """
        Busca usuários e seus dados de contexto para envio.

        Args:
            batch_number: Número do batch (1-indexed)
            batch_size: Tamanho do batch (0 = todos)
        """
        offset = (batch_number - 1) * batch_size if batch_size > 0 else 0

        queryset = ClientContext.objects.filter(
            weekly_context_error__isnull=True,
        ).select_related('user').values(
            'id', 'user__id', 'user__email', 'user__first_name',
            'market_panorama', 'market_tendencies', 'market_challenges', 'market_sources',
            'competition_main', 'competition_strategies', 'competition_opportunities', 'competition_sources',
            'target_audience_profile', 'target_audience_behaviors', 'target_audience_interests', 'target_audience_sources',
            'tendencies_popular_themes', 'tendencies_hashtags', 'tendencies_keywords', 'tendencies_sources',
            'seasonal_relevant_dates', 'seasonal_local_events', 'seasonal_sources',
            'brand_online_presence', 'brand_reputation', 'brand_communication_style', 'brand_sources',
        )

        if batch_size > 0:
            queryset = queryset[offset:offset + batch_size]

        return await sync_to_async(list)(queryset)

    async def send_all(
        self,
        batch_number: int = 1,
        batch_size: int = 0
    ) -> Dict[str, Any]:
        """
        Envia e-mail de Inteligência de Mercado para usuários.

        Args:
            batch_number: Número do batch (1-indexed)
            batch_size: Tamanho do batch (0 = todos)
        """
        contexts = await self.fetch_users_context_data(batch_number, batch_size)

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
        skipped = 0

        for user_id in users_context.keys():
            try:
                user = await sync_to_async(User.objects.get)(id=user_id)
                context_data = users_context[user_id][0]
                result = await self.send_to_user(user, context_data)
                if result['status'] == 'success':
                    processed += 1
                elif result['status'] == 'skipped':
                    skipped += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed to process user {user_id}: {str(e)}")
                failed += 1

        return {
            'status': 'completed',
            'total_users': len(users_context),
            'processed': processed,
            'skipped': skipped,
            'failed': failed,
        }

    async def send_to_user(self, user: User, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envia e-mail de Inteligência de Mercado para um usuário."""
        try:
            user_data = await sync_to_async(get_creator_profile_data)(user)

            # Validar business_name
            business_name = user_data.get('business_name')
            if not business_name:
                logger.warning(f"User {user.id} sem business_name, pulando envio")
                return {
                    'status': 'skipped',
                    'user_id': user.id,
                    'reason': 'missing_business_name'
                }

            # Validar se há dados de contexto para enviar
            has_context = any([
                context_data.get('market_panorama'),
                context_data.get('competition_main'),
                context_data.get('target_audience_profile'),
                context_data.get('tendencies_popular_themes'),
            ])
            if not has_context:
                logger.info(f"User {user.id} sem dados de contexto, pulando envio")
                return {
                    'status': 'skipped',
                    'user_id': user.id,
                    'reason': 'no_context_data'
                }

            subject = f"Inteligência de Mercado - {business_name}"
            html_content = generate_market_intelligence_email(context_data, user_data)

            success, response = await self.mailjet_service.send_email(
                to_email=user.email,
                subject=subject,
                body=html_content,
                attachments=None
            )

            if success:
                logger.info(f"Market intelligence email sent to user {user.id}")
                return {
                    'status': 'success',
                    'user_id': user.id,
                    'email': user.email,
                }
            else:
                logger.error(f"Failed to send market intelligence email to user {user.id}: {response}")
                return {
                    'status': 'failed',
                    'user_id': user.id,
                    'email': user.email,
                    'error': str(response)
                }

        except Exception as e:
            logger.error(f"Error sending market intelligence email to user {user.id}: {str(e)}")
            return {
                'status': 'failed',
                'user_id': user.id,
                'error': str(e)
            }
