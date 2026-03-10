"""Service para geração de relatórios diários de auditoria."""

from datetime import date
from typing import Any, Dict, List

from django.db.models import Count, Q

from services.daily_post_amount_service import DailyPostAmountService

from .models import AuditLog


class DailyReportService:
    """Gera relatórios diários de auditoria do sistema."""

    @staticmethod
    def generate_report(report_date: date) -> Dict[str, Any]:
        """
        Gera dados completos do relatório de auditoria.

        Args:
            report_date: Data do relatório.

        Returns:
            Dicionário com dados do relatório.
        """
        logs = AuditLog.objects.filter(
            timestamp__date=report_date
        ).select_related('user')

        summary = DailyReportService._build_summary(logs)
        categories = DailyReportService._build_category_counts(logs)
        content_gen = DailyReportService._build_content_generation_stats(logs)
        top_errors = DailyReportService._build_top_errors(logs)
        user_activity = DailyReportService._build_user_activity(logs)
        critical_ops = DailyReportService._build_critical_operations(logs)
        generated_posts = DailyPostAmountService.get_daily_post_amounts(report_date)

        return {
            'report_date': str(report_date),
            'summary': summary,
            'categories': categories,
            'content_generation': content_gen,
            'top_errors': top_errors,
            'user_activity': user_activity,
            'critical_operations': critical_ops,
            'generated_posts_amount': generated_posts,
        }

    @staticmethod
    def _build_summary(logs) -> Dict[str, Any]:
        """Constrói resumo de operações."""
        total = logs.count()
        successful = logs.filter(status='success').count()
        failed = logs.filter(status__in=['failure', 'error']).count()

        return {
            'total_operations': total,
            'successful_operations': successful,
            'failed_operations': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
        }

    @staticmethod
    def _build_category_counts(logs) -> Dict[str, int]:
        """Constrói contagem por categoria."""
        category_counts = logs.values('operation_category').annotate(
            count=Count('operation_category')
        ).order_by('-count')

        return {item['operation_category']: item['count'] for item in category_counts}

    @staticmethod
    def _build_content_generation_stats(logs) -> Dict[str, Any]:
        """Constrói estatísticas de geração de conteúdo."""
        content_logs = logs.filter(operation_category='content')
        attempts = content_logs.count()
        successes = content_logs.filter(status='success').count()
        failures = content_logs.filter(status__in=['failure', 'error']).count()

        return {
            'attempts': attempts,
            'successes': successes,
            'failures': failures,
            'success_rate': (successes / attempts * 100) if attempts > 0 else 0,
        }

    @staticmethod
    def _build_top_errors(logs) -> List[Dict[str, Any]]:
        """Constrói lista dos principais erros."""
        error_logs = logs.filter(
            status__in=['failure', 'error']
        ).exclude(error_message='')

        top_errors = error_logs.values('error_message').annotate(
            count=Count('error_message')
        ).order_by('-count')[:10]

        return list(top_errors)

    @staticmethod
    def _build_user_activity(logs) -> List[Dict[str, Any]]:
        """Constrói resumo de atividade por usuário."""
        user_activity = logs.values('user__username').annotate(
            operations=Count('user')
        ).filter(user__username__isnull=False).order_by('-operations')[:20]

        return list(user_activity)

    @staticmethod
    def _build_critical_operations(logs) -> List[Dict[str, Any]]:
        """Constrói lista de operações críticas."""
        critical_ops = logs.filter(
            Q(status__in=['error', 'failure']) |
            Q(action__in=['account_deleted', 'subscription_cancelled'])
        ).order_by('-timestamp')[:50]

        return [
            {
                'timestamp': op.timestamp.isoformat(),
                'user': op.user.username if op.user else 'Anonymous',
                'action': op.get_action_display(),
                'status': op.status,
                'error_message': op.error_message[:100] if op.error_message else '',
            }
            for op in critical_ops
        ]
