from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from AuditSystem.models import AuditLog, DailyReport
from AuditSystem.services import AuditService


class Command(BaseCommand):
    help = 'Generate daily audit report and send email to administrators'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date for the report (YYYY-MM-DD format). Defaults to yesterday.',
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send the report via email to administrators',
        )
        parser.add_argument(
            '--email-to',
            type=str,
            help='Email address to send report to (overrides default admin emails)',
        )

    def handle(self, *args, **options):
        # Determine the report date
        if options['date']:
            try:
                report_date = date.fromisoformat(options['date'])
            except ValueError:
                self.stderr.write(self.style.ERROR(
                    f'Invalid date format: {options["date"]}'))
                return
        else:
            # Default to yesterday
            report_date = date.today() - timedelta(days=1)

        self.stdout.write(f'Generating audit report for {report_date}')

        try:
            # Generate the report
            report_data = self._generate_report(report_date)

            # Save to database
            report = self._save_report(report_date, report_data)

            # Send email if requested
            if options['send_email']:
                self._send_email_report(report, options.get('email_to'))

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated report for {report_date}: {report.total_operations} operations')
            )

        except Exception as e:
            # Log the error
            AuditService.log_system_operation(
                user=None,
                action='maintenance',
                status='error',
                error_message=f'Failed to generate daily report: {str(e)}',
                details={'report_date': str(report_date)}
            )
            self.stderr.write(self.style.ERROR(
                f'Failed to generate report: {str(e)}'))
            raise

    def _generate_report(self, report_date):
        """Generate the complete audit report data"""
        # Query audit logs for the date
        logs = AuditLog.objects.filter(
            timestamp__date=report_date
        ).select_related('user')

        # Basic counts
        total_operations = logs.count()
        successful_operations = logs.filter(status='success').count()
        failed_operations = logs.filter(
            status__in=['failure', 'error']).count()

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
        }

        return report_data

    def _save_report(self, report_date, report_data):
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
            }
        )

        return report

    def _send_email_report(self, report, email_to=None):
        """Send the report via email"""
        if not email_to:
            # Default admin emails - you might want to configure this
            email_to = getattr(settings, 'ADMIN_EMAILS',
                               ['admin@postnow.com.br'])

        if isinstance(email_to, str):
            email_to = [email_to]

        subject = f'PostNow Daily Audit Report - {report.report_date}'

        # Generate HTML email content
        html_content = self._generate_html_report(report)

        try:
            send_mail(
                subject=subject,
                message=self._generate_text_report(
                    report),  # Plain text fallback
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=email_to,
                html_message=html_content,
            )

            # Log successful email send
            AuditService.log_email_operation(
                user=None,
                action='email_sent',
                status='success',
                details={
                    'subject': subject,
                    'recipients': email_to,
                    'report_date': str(report.report_date)
                }
            )

            self.stdout.write(f'Report email sent to: {", ".join(email_to)}')

        except Exception as e:
            # Log failed email send
            AuditService.log_email_operation(
                user=None,
                action='email_failed',
                status='error',
                error_message=str(e),
                details={
                    'subject': subject,
                    'recipients': email_to,
                    'report_date': str(report.report_date)
                }
            )
            raise

    def _generate_html_report(self, report):
        """Generate HTML version of the report"""
        data = report.report_data

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: #28a745; }}
                .error {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>PostNow Daily Audit Report</h1>
                <h2>{report.report_date}</h2>
            </div>

            <div class="summary">
                <h3>Summary</h3>
                <div class="metric">
                    <strong>Total Operations:</strong> {data['summary']['total_operations']}
                </div>
                <div class="metric">
                    <strong>Success Rate:</strong> {data['summary']['success_rate']:.1f}%
                </div>
                <div class="metric">
                    <strong>Successful:</strong> <span class="success">{data['summary']['successful_operations']}</span>
                </div>
                <div class="metric">
                    <strong>Failed:</strong> <span class="error">{data['summary']['failed_operations']}</span>
                </div>
            </div>

            <div class="section">
                <h3>Operations by Category</h3>
                <table>
                    <tr><th>Category</th><th>Count</th></tr>
        """

        for category, count in data['categories'].items():
            html += f"<tr><td>{category.title()}</td><td>{count}</td></tr>"

        html += """
                </table>
            </div>

            <div class="section">
                <h3>Content Generation</h3>
                <div class="metric">
                    <strong>Attempts:</strong> {data['content_generation']['attempts']}
                </div>
                <div class="metric">
                    <strong>Success Rate:</strong> {data['content_generation']['success_rate']:.1f}%
                </div>
            </div>
        """

        if data['top_errors']:
            html += """
            <div class="section">
                <h3>Top Errors</h3>
                <table>
                    <tr><th>Error Message</th><th>Count</th></tr>
            """
            for error in data['top_errors']:
                html += f"<tr><td>{error['error_message'][:100]}</td><td>{error['count']}</td></tr>"
            html += "</table></div>"

        html += """
        </body>
        </html>
        """

        return html

    def _generate_text_report(self, report):
        """Generate plain text version of the report"""
        data = report.report_data

        text = f"""PostNow Daily Audit Report - {report.report_date}

SUMMARY
=======
Total Operations: {data['summary']['total_operations']}
Success Rate: {data['summary']['success_rate']:.1f}%
Successful: {data['summary']['successful_operations']}
Failed: {data['summary']['failed_operations']}

OPERATIONS BY CATEGORY
======================
"""

        for category, count in data['categories'].items():
            text += f"{category.title()}: {count}\n"

        text += f"""

CONTENT GENERATION
==================
Attempts: {data['content_generation']['attempts']}
Success Rate: {data['content_generation']['success_rate']:.1f}%

"""

        if data['top_errors']:
            text += "TOP ERRORS\n==========\n"
            for error in data['top_errors'][:5]:  # Limit to top 5 for text version
                text += f"{error['error_message'][:80]}: {error['count']}\n"

        return text
