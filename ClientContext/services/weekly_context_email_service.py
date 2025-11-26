import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from ClientContext.utils.weekly_context import generate_weekly_context_email_template
from CreatorProfile.models import CreatorProfile
from django.contrib.auth.models import User
from services.mailjet_service import MailjetService

logger = logging.getLogger(__name__)


class WeeklyContextEmailService:
    def __init__(self):
        self.mailjet_service = MailjetService()

    async def send_weekly_context_email(self, user: User, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send weekly context email to a single user."""
        try:
            # Get user profile data
            user_data = await self._get_user_profile_data(user)

            # Generate email content
            subject = f"📈 Seu Contexto Semanal de Mercado - {user_data['business_name']}"
            html_content = generate_weekly_context_email_template(
                context_data, user_data)

            # Send email
            success, response = await self.mailjet_service.send_email(
                user=user,
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

    async def send_weekly_context_emails_batch(self, users_context_data: list) -> Dict[str, Any]:
        """Send weekly context emails to a batch of users."""
        processed = 0
        failed = 0
        results = []

        for user_context in users_context_data:
            try:
                user = user_context['user']
                context_data = user_context['context_data']

                result = await self.send_weekly_context_email(user, context_data)
                results.append(result)

                if result['status'] == 'success':
                    processed += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Error processing user context email: {str(e)}")
                failed += 1
                results.append({
                    'status': 'failed',
                    'user_id': user_context.get('user', {}).get('id', 'unknown'),
                    'error': str(e)
                })

        # Send fallback email to admins if there were failures
        if failed > 0:
            await self._send_failure_notification_to_admins(failed, len(users_context_data))

        return {
            'status': 'completed',
            'total_users': len(users_context_data),
            'processed': processed,
            'failed': failed,
            'results': results
        }

    @sync_to_async
    def _get_user_profile_data(self, user: User) -> Dict[str, str]:
        """Get user profile data for email personalization."""
        try:
            profile = CreatorProfile.objects.filter(user=user).first()

            if profile:
                return {
                    'user_name': user.first_name or user.username,
                    'business_name': profile.business_name or 'Sua Empresa',
                    'professional_name': profile.professional_name or user.first_name or user.username,
                    'profession': profile.profession or 'Profissional',
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

    async def send_weekly_context_test_email(self, user: User, test_context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a test weekly context email with sample data."""

        # Default test context data if not provided
        if not test_context_data:
            test_context_data = {
                'mercado': {
                    'panorama': 'O mercado está em constante evolução com foco em transformação digital e sustentabilidade.',
                    'tendencias': [
                        'Inteligência Artificial aplicada aos negócios',
                        'Sustentabilidade corporativa',
                        'Experiência do cliente personalizada'
                    ],
                    'desafios': [
                        'Adaptação às mudanças tecnológicas',
                        'Gestão de dados e privacidade',
                        'Competitividade crescente'
                    ],
                    'fontes': ['https://example.com/market-research']
                },
                'concorrencia': {
                    'principais': ['Empresa A', 'Empresa B', 'Startup C'],
                    'estrategias': 'Foco em inovação, parcerias estratégicas e expansão digital.',
                    'oportunidades': 'Diferenciação através de atendimento personalizado e soluções sob medida.',
                    'fontes': ['https://example.com/competition-analysis']
                },
                'publico': {
                    'perfil': 'Profissionais de 25-45 anos, focados em crescimento profissional e inovação.',
                    'comportamento_online': 'Ativo nas redes sociais profissionais, busca conteúdo educativo e networking.',
                    'interesses': ['Tecnologia', 'Empreendedorismo', 'Desenvolvimento profissional'],
                    'fontes': ['https://example.com/audience-insights']
                },
                'tendencias': {
                    'temas_populares': ['IA no trabalho', 'Produtividade', 'Liderança'],
                    'hashtags': ['#IA', '#Produtividade', '#Liderança', '#Inovação'],
                    'palavras_chave': ['inteligência artificial', 'produtividade', 'liderança', 'inovação'],
                    'fontes': ['https://example.com/trending-topics']
                }
            }

        return await self.send_weekly_context_email(user, test_context_data)

    async def _send_failure_notification_to_admins(self, failed_count: int, total_count: int):
        """Send notification to admins about email sending failures."""
        try:
            subject = f"⚠️ Falhas no Envio de Contexto Semanal - {failed_count}/{total_count}"
            html_content = f"""
            <h2>Relatório de Falhas - Contexto Semanal</h2>
            <p><strong>Total de usuários processados:</strong> {total_count}</p>
            <p><strong>Emails enviados com sucesso:</strong> {total_count - failed_count}</p>
            <p><strong>Falhas:</strong> {failed_count}</p>
            <p>Por favor, verifique os logs para mais detalhes sobre as falhas.</p>
            """

            await self.mailjet_service.send_fallback_email_to_admins(
                user=None,  # System operation
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(
                f"Failed to send failure notification to admins: {str(e)}")

    async def send_weekly_context_summary_to_admins(self, summary_data: Dict[str, Any]):
        """Send summary report to admins about weekly context email campaign."""
        try:
            subject = "📊 Relatório Semanal - Envio de Contexto de Mercado"

            html_content = f"""
            <h2>Relatório de Envio - Contexto Semanal</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Métrica</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Valor</strong></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">Total de usuários</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('total_users', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">Emails enviados</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('processed', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">Falhas</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('failed', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">Taxa de sucesso</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{((summary_data.get('processed', 0) / max(summary_data.get('total_users', 1), 1)) * 100):.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">Duração</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('duration_seconds', 0):.2f} segundos</td>
                </tr>
            </table>
            
            <h3>Status por usuário:</h3>
            <ul>
            """

            for result in summary_data.get('results', []):
                status_icon = "✅" if result['status'] == 'success' else "❌"
                html_content += f"<li>{status_icon} {result.get('email', 'N/A')} - {result['status']}</li>"

            html_content += """
            </ul>
            <p><em>Este é um relatório automático do sistema PostNow.</em></p>
            """

            await self.mailjet_service.send_fallback_email_to_admins(
                user=None,  # System operation
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(f"Failed to send summary report to admins: {str(e)}")
