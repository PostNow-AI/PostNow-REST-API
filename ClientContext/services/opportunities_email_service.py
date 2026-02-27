"""
Serviço de envio do e-mail de Oportunidades de Conteúdo (Segunda-feira).

Usa o template opportunities_email.py com dados enriquecidos (Fase 2).
"""
import logging
from collections import defaultdict
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

from ClientContext.models import ClientContext
from ClientContext.utils.opportunities_email import generate_opportunities_email_template
from services.get_creator_profile_data import get_creator_profile_data
from services.mailjet_service import MailjetService

logger = logging.getLogger(__name__)


class OpportunitiesEmailService:
    """Serviço para envio do e-mail de Oportunidades de Conteúdo."""

    def __init__(self):
        self.mailjet_service = MailjetService()

    @staticmethod
    async def fetch_users_with_opportunities() -> list:
        """Busca usuários com dados de oportunidades enriquecidas para envio."""
        return await sync_to_async(list)(
            ClientContext.objects.filter(
                weekly_context_error__isnull=True,  # Filtro correto para NULL
                context_enrichment_status='enriched',  # Apenas dados enriquecidos
            ).select_related('user').values(
                'id', 'user__id', 'user__email', 'user__first_name',
                'tendencies_data',
            )
        )

    async def mail_opportunities(self) -> Dict[str, Any]:
        """Envia e-mail de Oportunidades para todos os usuários."""
        contexts = await self.fetch_users_with_opportunities()

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
        """Envia e-mail de Oportunidades para um usuário."""
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

            # tendencies_data contém as oportunidades enriquecidas
            tendencies_data = context_data.get('tendencies_data', {})

            # Validar se há oportunidades para enviar
            # Verifica se items é uma lista não vazia com pelo menos um item válido
            has_opportunities = tendencies_data and any(
                isinstance(cat.get('items'), list) and len(cat.get('items', [])) > 0
                for cat in tendencies_data.values() if isinstance(cat, dict)
            )
            if not has_opportunities:
                logger.info(f"User {user.id} sem oportunidades para enviar, pulando")
                return {
                    'status': 'skipped',
                    'user_id': user.id,
                    'reason': 'no_opportunities'
                }

            subject = f"Oportunidades de Conteúdo - {business_name}"
            html_content = generate_opportunities_email_template(tendencies_data, user_data)

            success, response = await self.mailjet_service.send_email(
                to_email=user.email,
                subject=subject,
                body=html_content,
                attachments=None
            )

            if success:
                logger.info(f"Opportunities email sent to user {user.id}")
                return {
                    'status': 'success',
                    'user_id': user.id,
                    'email': user.email,
                }
            else:
                logger.error(f"Failed to send opportunities email to user {user.id}: {response}")
                return {
                    'status': 'failed',
                    'user_id': user.id,
                    'email': user.email,
                    'error': str(response)
                }

        except Exception as e:
            logger.error(f"Error sending opportunities email to user {user.id}: {str(e)}")
            return {
                'status': 'failed',
                'user_id': user.id,
                'error': str(e)
            }
