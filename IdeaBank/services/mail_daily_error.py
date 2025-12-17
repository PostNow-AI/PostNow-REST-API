import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from services.mailjet_service import MailjetService

logger = logging.getLogger(__name__)


class MailDailyErrorService:
    def __init__(self):
        self.mailjet_service = MailjetService()

    @sync_to_async
    def _get_users_with_errors(self) -> list[dict]:
        """Get all users who have daily generation errors."""
        return list(
            User.objects.extra(
                select={'daily_generation_error': 'daily_generation_error'},
                where=["daily_generation_error IS NOT NULL"]
            ).filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().values('id', 'email', 'username', 'first_name', 'daily_generation_error')
        )

    async def send_error_report(self) -> Dict[str, Any]:
        """Send error report emails to users with daily generation errors."""
        users_with_errors = await self._get_users_with_errors()
        total = len(users_with_errors)

        if total == 0:
            return {
                'status': 'completed',
                'total_users': 0,
                'message': 'No users with errors found',
            }

        subject = "Erro ao gerar ideias diárias no PostNow"
        html_content = f"""
        <h1>Falha na Geração de Conteúdo Diário</h1>
        <p>Após um dia inteiro de tentativas, {total} usuários permanecem com erros:</p>
        """
        for user in users_with_errors:
            html_content += f"<p>- {user['email']}</p>"
            html_content += f"""
              <h2>Detalhes do Erro para {user['first_name']} ({user['email']})</h2>
              <p>{user.get('daily_generation_error', 'Nenhum detalhe de erro disponível.')}</p>
            """

        html_content += """
          <p>Por favor, verifique os logs do sistema para mais detalhes sobre esses erros.</p>
          <p>Atenciosamente,<br/>Equipe PostNow</p>
        """
        await self.mailjet_service.send_fallback_email_to_admins(
            subject, html_content)

        return {
            'status': 'completed',
            'total_users': total,
            'message': f'Error reports of {total} users sent to admins.',
        }
