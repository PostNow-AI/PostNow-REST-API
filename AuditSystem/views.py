import os
from datetime import date, timedelta

from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from IdeaBank.services.mail_service import MailService
from services.daily_post_amount_service import DailyPostAmountService
from .models import AuditLog, DailyReport
from .services import AuditService


@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([])  # No authentication required
@permission_classes([AllowAny])  # Allow anyone to access
def generate_daily_audit_report(request):
    """
    Generate daily audit report and optionally send email to administrators.

    GET/POST parameters:
    - date (optional): Date for the report (YYYY-MM-DD format). Defaults to yesterday.
    - send_email (optional): Whether to send the report via email (default: false)
    - email_to (optional): Email address to send report to (overrides default admin emails)
    - format (optional): Response format - 'json' or 'html' (default: json)
    """

    if request.method == 'GET':
        params = request.GET
    else:
        params = request.data

    # Debug line

    # Determine the report date
    report_date_str = params.get('date')
    if report_date_str:
        try:
            report_date = date.fromisoformat(report_date_str)
        except ValueError:
            return Response(
                {'error': f'Formato de data inválido: {report_date_str}. Use o formato AAAA-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        # Default to yesterday
        report_date = date.today() - timedelta(days=1)

    send_email = params.get(
        'send_email', 'false').lower() in ('true', '1', 'yes')
    email_to = params.get('email_to')

    try:
        # Generate the report
        report_data = _generate_report(report_date)

        # Save to database
        report = _save_report(report_date, report_data)

        # Send email if requested
        email_sent = False
        if send_email:
            _send_email_report(report, email_to)
            email_sent = True

        # Check if HTML response is requested
        format_param = params.get('format', 'json').lower()
        if format_param == 'html':
            # Return HTML report directly
            html_content = _generate_html_report(report)
            return Response(
                html_content,
                content_type='text/html; charset=utf-8',
                status=status.HTTP_200_OK
            )

        # Default JSON response
        return Response({
            'success': True,
            'message': f'Relatório gerado com sucesso para {report_date}',
            'report_date': str(report_date),
            'total_operations': report.total_operations,
            'email_sent': email_sent,
            'report_data': report_data
        })

    except Exception as e:
        # Log the error
        AuditService.log_system_operation(
            user=None,
            action='maintenance',
            status='error',
            error_message=f'Failed to generate daily report: {str(e)}',
            details={'report_date': str(report_date)}
        )

        return Response(
            {'error': f'Falha ao gerar relatório: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _generate_report(report_date):
    """Generate the complete audit report data"""
    # Query audit logs for the date
    logs = AuditLog.objects.filter(
        timestamp__date=report_date
    ).select_related('user')

    # Basic counts
    total_operations = logs.count()
    successful_operations = logs.filter(status='success').count()
    failed_operations = logs.filter(status__in=['failure', 'error']).count()

    # Category counts
    category_counts = logs.values('operation_category').annotate(
        count=Count('operation_category')
    ).order_by('-count')

    # Action counts for content generation
    content_logs = logs.filter(operation_category='content')
    content_attempts = content_logs.count()
    content_successes = content_logs.filter(status='success').count()
    content_failures = content_logs.filter(
        status__in=['failure', 'error']).count()

    # Top errors
    error_logs = logs.filter(
        status__in=['failure', 'error']).exclude(error_message='')
    top_errors = error_logs.values('error_message').annotate(
        count=Count('error_message')
    ).order_by('-count')[:10]

    # User activity summary
    user_activity = logs.values('user__username').annotate(
        operations=Count('user')
    ).filter(user__username__isnull=False).order_by('-operations')[:20]

    # Recent critical operations
    critical_ops = logs.filter(
        Q(status__in=['error', 'failure']) |
        Q(action__in=['account_deleted', 'subscription_cancelled'])
    ).order_by('-timestamp')[:50]

    # Generated posts amount
    generated_posts_amount = DailyPostAmountService.get_daily_post_amounts(
        report_date)

    # Build report data
    report_data = {
        'report_date': str(report_date),
        'summary': {
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0,
        },
        'categories': {item['operation_category']: item['count'] for item in category_counts},
        'content_generation': {
            'attempts': content_attempts,
            'successes': content_successes,
            'failures': content_failures,
            'success_rate': (content_successes / content_attempts * 100) if content_attempts > 0 else 0,
        },
        'top_errors': list(top_errors),
        'user_activity': list(user_activity),
        'critical_operations': [
            {
                'timestamp': op.timestamp.isoformat(),
                'user': op.user.username if op.user else 'Anonymous',
                'action': op.get_action_display(),
                'status': op.status,
                'error_message': op.error_message[:100] if op.error_message else '',
            }
            for op in critical_ops
        ],
        'generated_posts_amount': generated_posts_amount,
    }

    return report_data


def _save_report(report_date, report_data):
    """Save the report to the database"""
    # Get category counts
    categories = report_data['categories']

    # Create or update the report
    report, created = DailyReport.objects.update_or_create(
        report_date=report_date,
        defaults={
            'total_operations': report_data['summary']['total_operations'],
            'successful_operations': report_data['summary']['successful_operations'],
            'failed_operations': report_data['summary']['failed_operations'],
            'auth_operations': categories.get('auth', 0),
            'account_operations': categories.get('account', 0),
            'profile_operations': categories.get('profile', 0),
            'post_operations': categories.get('post', 0),
            'content_operations': categories.get('content', 0),
            'credit_operations': categories.get('credit', 0),
            'subscription_operations': categories.get('subscription', 0),
            'email_operations': categories.get('email', 0),
            'system_operations': categories.get('system', 0),
            'content_generation_attempts': report_data['content_generation']['attempts'],
            'content_generation_successes': report_data['content_generation']['successes'],
            'content_generation_failures': report_data['content_generation']['failures'],
            'top_errors': report_data['top_errors'],
            'report_data': report_data,
            'total_users_active': report_data['generated_posts_amount']['user_amount'],
            'automatic_expected_posts_amount': report_data['generated_posts_amount']['automatic_expected_posts_amount'],
            'actual_automatic_posts_amount': report_data['generated_posts_amount']['actual_automatic_posts_amount'],
        }
    )

    return report


def _send_email_report(report, email_to=None):
    """Send the report via email using Mailjet"""
    if not email_to:
        # Default admin emails - you might want to configure this
        email_to = os.getenv('ADMIN_EMAILS', 'admin@postnow.com.br').split(',')

    if isinstance(email_to, str):
        email_to = [email_to]

    subject = f'Relatório de Auditoria Diário PostNow - {report.report_date}'

    # Generate HTML email content
    html_content = _generate_html_report(report)

    # Initialize MailService
    mail_service = MailService()

    # Send to each recipient
    success_count = 0
    errors = []

    for recipient in email_to:
        try:
            status_code, response = mail_service.send_email(
                recipient_email=recipient,
                subject=subject,
                html_content=html_content
            )

            if status_code == 200:
                success_count += 1
                # Log successful email send
                AuditService.log_email_operation(
                    user=None,
                    action='email_sent',
                    status='success',
                    details={
                        'subject': subject,
                        'recipient': recipient,
                        'report_date': str(report.report_date)
                    }
                )
            else:
                error_msg = f"Mailjet API error for {recipient}: Status {status_code}, Response: {response}"
                errors.append(error_msg)
                # Log failed email send
                AuditService.log_email_operation(
                    user=None,
                    action='email_failed',
                    status='error',
                    error_message=error_msg,
                    details={
                        'subject': subject,
                        'recipient': recipient,
                        'report_date': str(report.report_date),
                        'mailjet_response': response
                    }
                )

        except Exception as e:
            error_msg = f"Exception sending email to {recipient}: {str(e)}"
            errors.append(error_msg)
            # Log failed email send
            AuditService.log_email_operation(
                user=None,
                action='email_failed',
                status='error',
                error_message=error_msg,
                details={
                    'subject': subject,
                    'recipient': recipient,
                    'report_date': str(report.report_date)
                }
            )

    # If no emails were sent successfully, raise an exception
    if success_count == 0:
        raise Exception(
            f"Failed to send email to any recipients. Errors: {'; '.join(errors)}")

    # Log partial success if some emails failed
    if errors:
        AuditService.log_system_operation(
            user=None,
            action='system_warning',
            status='warning',
            details={
                'message': f'Audit report sent to {success_count}/{len(email_to)} recipients',
                'errors': errors,
                'report_date': str(report.report_date)
            }
        )


def _generate_html_report(report):
    """Generate HTML version of the report"""
    data = report.report_data

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Relatório de Auditoria Diário</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #ffffff;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 40px; text-align: center;">
                            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow Logo" style="width: 114px; height: 32px; margin-bottom: 20px;">
                            <h1 style="margin: 0; color: #8b5cf6; font-size: 24px; font-weight: 600;">
                                Relatório de Auditoria <span style="color: #ffffff;">Diário - {report.report_date} 📊</span>
                            </h1>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                        <!-- Daily Posts Generation Section -->
                        <table role="presentation" style="width: 100%; margin-bottom: 40px;">
                            <tr>
                                <td>
                                    <h2 style="margin: 0 0 8px 0; color: #8b5cf6; font-size: 20px; font-weight: 600;">Geração de Posts Diários</h2>
                                    <p style="margin: 0 0 20px 0; color: #1e293b; font-size: 16px;">
                                        Estatísticas da geração (automática e manual) de posts para usuários ativos.
                                    </p>
                                    <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                <div style="text-align: center;">
                                                    <div style="font-size: 24px; font-weight: bold; color: #8b5cf6;">{data['generated_posts_amount']['user_amount']}</div>
                                                    <div style="font-size: 12px; color: #64748b;">Usuários Ativos</div>
                                                </div>
                                            </td>
                                            <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                <div style="text-align: center;">
                                                    <div style="font-size: 24px; font-weight: bold; color: #17a2b8;">{data['generated_posts_amount']['automatic_expected_posts_amount']}</div>
                                                    <div style="font-size: 12px; color: #64748b;">Expectativa de posts automáticos</div>
                                                </div>
                                            </td>
                                            <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                <div style="text-align: center;">
                                                    <div style="font-size: 24px; font-weight: bold; color: #28a745;">{data['generated_posts_amount']['actual_automatic_posts_amount']}</div>
                                                    <div style="font-size: 12px; color: #64748b;">Posts Gerados</div>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                            <!-- Summary Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 8px 0; color: #8b5cf6; font-size: 20px; font-weight: 600;">Resumo Geral</h2>
                                        <p style="margin: 0 0 20px 0; color: #1e293b; font-size: 16px;">
                                            Visão geral das operações realizadas no sistema.
                                        </p>
                                     
                                        <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 24px; font-weight: bold; color: #8b5cf6;">{data['summary']['total_operations']}</div>
                                                        <div style="font-size: 12px; color: #64748b;">Total de Operações</div>
                                                    </div>
                                                </td>
                                                <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 24px; font-weight: bold; color: #28a745;">{data['summary']['success_rate']:.1f}%</div>
                                                        <div style="font-size: 12px; color: #64748b;">Taxa de Sucesso</div>
                                                    </div>
                                                </td>
                                                <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 24px; font-weight: bold; color: #28a745;">{data['summary']['successful_operations']}</div>
                                                        <div style="font-size: 12px; color: #64748b;">Operações Bem-Sucedidas</div>
                                                    </div>
                                                </td>
                                                <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">{data['summary']['failed_operations']}</div>
                                                        <div style="font-size: 12px; color: #64748b;">Operações com Falha</div>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>

                            <!-- Operations by Category Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 8px 0; color: #8b5cf6; font-size: 20px; font-weight: 600;">Operações por Categoria</h2>
                                        <p style="margin: 0 0 20px 0; color: #1e293b; font-size: 16px;">
                                            Distribuição das operações realizadas no sistema.
                                        </p>
                                        <table role="presentation" style="width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                                            <tr style="background-color: #f8fafc;">
                                                <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #e2e8f0;">Categoria</th>
                                                <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #e2e8f0;">Quantidade</th>
                                            </tr>"""

    for category, count in data['categories'].items():
        html += f"""
                                            <tr>
                                                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; color: #64748b;">{category.title()}</td>
                                                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-weight: 500;">{count}</td>
                                            </tr>"""

    html += f"""
                                        </table>
                                    </td>
                                </tr>
                            </table>

                            <!-- Content Generation Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 8px 0; color: #8b5cf6; font-size: 20px; font-weight: 600;">Geração de Conteúdo</h2>
                                        <p style="margin: 0 0 20px 0; color: #1e293b; font-size: 16px;">
                                            Estatísticas das operações de geração de conteúdo.
                                        </p>
                                        <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 24px; font-weight: bold; color: #8b5cf6;">{data['content_generation']['attempts']}</div>
                                                        <div style="font-size: 12px; color: #64748b;">Tentativas</div>
                                                    </div>
                                                </td>
                                                <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 24px; font-weight: bold; color: #28a745;">{data['content_generation']['success_rate']:.1f}%</div>
                                                        <div style="font-size: 12px; color: #64748b;">Taxa de Sucesso</div>
                                                    </div>
                                                </td>
                                                <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 24px; font-weight: bold; color: #28a745;">{data['content_generation']['successes']}</div>
                                                        <div style="font-size: 12px; color: #64748b;">Sucessos</div>
                                                    </div>
                                                </td>
                                                <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin: 10px; display: inline-block; min-width: 150px;">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">{data['content_generation']['failures']}</div>
                                                        <div style="font-size: 12px; color: #64748b;">Falhas</div>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>"""

    if data['top_errors']:
        html += """
                            <!-- Top Errors Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 8px 0; color: #8b5cf6; font-size: 20px; font-weight: 600;">Principais Erros</h2>
                                        <p style="margin: 0 0 20px 0; color: #1e293b; font-size: 16px;">
                                            Os erros mais comuns identificados no sistema.
                                        </p>
                                        <table role="presentation" style="width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                                            <tr style="background-color: #f8fafc;">
                                                <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #e2e8f0;">Mensagem de Erro</th>
                                                <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #e2e8f0;">Ocorrências</th>
                                            </tr>"""

        for error in data['top_errors']:
            html += f"""
                                            <tr>
                                                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; color: #64748b;">{error['error_message'][:100]}</td>
                                                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-weight: 500;">{error['count']}</td>
                                            </tr>"""

        html += """
                                        </table>
                                    </td>
                                </tr>
                            </table>"""

    html += """
                            <!-- Footer Section -->
                            <table role="presentation" style="width: 100%; background-color: #f8fafc; border-radius: 8px; border-top: 1px solid #e2e8f0;">
                                <tr>
                                    <td style="padding: 32px; text-align: center;">
                                        <p style="margin: 0 0 8px 0; color: #64748b; font-size: 14px; font-weight: 500;">
                                            Este é um relatório automático gerado pelo sistema PostNow.
                                        </p>
                                        <p style="margin: 0; color: #6a7282; font-size: 12px; font-weight: 500;">
                                            © 2025 PostNow. Monitoramento e auditoria do sistema.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>

    </table>
</body>
</html>"""

    return html


def _generate_text_report(report):
    """Generate plain text version of the report"""
    data = report.report_data

    text = f"""Relatório de Auditoria Diário PostNow - {report.report_date}

RESUMO
=======
Total de Operações: {data['summary']['total_operations']}
Taxa de Sucesso: {data['summary']['success_rate']:.1f}%
Bem-Sucedidas: {data['summary']['successful_operations']}
Com Falha: {data['summary']['failed_operations']}

OPERAÇÕES POR CATEGORIA
=======================
"""

    for category, count in data['categories'].items():
        text += f"{category.title()}: {count}\n"

    text += f"""

GERAÇÃO DE CONTEÚDO
===================
Tentativas: {data['content_generation']['attempts']}
Taxa de Sucesso: {data['content_generation']['success_rate']:.1f}%

"""

    if data['top_errors']:
        text += "PRINCIPAIS ERROS\n================\n"
        for error in data['top_errors'][:5]:  # Limit to top 5 for text version
            text += f"{error['error_message'][:80]}: {error['count']}\n"

    return text


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])  # No authentication required for webhooks
@permission_classes([AllowAny])  # Allow Mailjet to access
def mailjet_webhook(request):
    """
    Handle Mailjet webhook events.

    Mailjet sends events like 'open', 'click', 'bounce', 'spam', etc.
    This endpoint logs these events in the AuditLog.

    Expected payload from Mailjet:
    [
        {
            "event": "open",
            "time": 1433333949,
            "MessageID": 19421777835146490,
            "email": "api@mailjet.com",
            "mj_campaign_id": 7257,
            "mj_contact_id": 4,
            "customcampaign": "",
            "CustomID": "helloworld",
            "Payload": "",
            "ip": "127.0.0.1",
            "geo": "US",
            "agent": "Mozilla/5.0"
        }
    ]
    """
    try:
        # Mailjet sends an array of events
        events = request.data

        if not isinstance(events, list):
            events = [events]

        processed_events = []

        for event in events:
            event_type = event.get('event', '').lower()
            email = event.get('email', '')
            message_id = event.get('MessageID', '')
            custom_id = event.get('CustomID', '')
            ip_address = event.get('ip', '')
            user_agent = event.get('agent', '')
            timestamp = event.get('time')

            # Map Mailjet event types to our action types
            action_mapping = {
                'open': 'email_opened',
                'click': 'email_clicked',
                'bounce': 'email_bounced',
                'spam': 'email_failed',
                'blocked': 'email_failed',
                'unsub': 'email_failed',
            }

            action = action_mapping.get(event_type, 'email_failed')

            # Try to find the user by email
            user = None
            try:
                from django.contrib.auth.models import User
                user = User.objects.filter(email=email).first()
            except Exception:
                pass

            # Log the event
            details = {
                'event_type': event_type,
                'email': email,
                'message_id': str(message_id),
                'custom_id': custom_id,
                'ip': ip_address,
                'user_agent': user_agent,
                'timestamp': timestamp,
                'geo': event.get('geo', ''),
                'payload': event.get('Payload', ''),
            }

            # Remove empty values
            details = {k: v for k, v in details.items() if v}

            audit_log = AuditService.log_email_operation(
                user=user,
                action=action,
                status='success',
                details=details,
                resource_id=str(message_id),
            )

            processed_events.append({
                'event_type': event_type,
                'action': action,
                'email': email,
                'audit_log_id': audit_log.id
            })

        return Response({
            'success': True,
            'message': f'Processados {len(processed_events)} eventos com sucesso',
            'events': processed_events
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Log the error
        AuditService.log_system_operation(
            user=None,
            action='system_error',
            status='error',
            error_message=f'Erro ao processar webhook do Mailjet: {str(e)}',
            details={'request_data': request.data if hasattr(request, 'data') else {}}
        )

        return Response({
            'success': False,
            'error': f'Erro ao processar eventos: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
