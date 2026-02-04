"""
Service for calculating behavior dashboard metrics.
Provides statistical data for admin dashboard monitoring user behavior.
"""
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from .models import AuditLog


class BehaviorDashboardService:
    """Service for calculating behavior dashboard metrics"""

    @staticmethod
    def _exclude_admin_users(queryset):
        """Exclude admin and staff users from queryset"""
        return queryset.exclude(
            Q(user__is_staff=True) | Q(user__is_superuser=True)
        )

    @staticmethod
    def _get_admin_emails() -> List[str]:
        """Get list of admin/staff user emails to exclude from statistics"""
        # Get emails from User model (staff and superuser)
        admin_user_emails = list(
            User.objects.filter(
                Q(is_staff=True) | Q(is_superuser=True)
            ).values_list('email', flat=True)
        )
        
        # Get emails from environment variable
        env_admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
        env_admin_emails = [email.strip() for email in env_admin_emails if email.strip()]
        
        # Combine and deduplicate
        all_admin_emails = list(set(admin_user_emails + env_admin_emails))
        
        return all_admin_emails

    @staticmethod
    def _generate_timeline(start_date: datetime, end_date: datetime, queryset, date_field='created_at') -> List[Dict[str, Any]]:
        """
        Generate daily timeline data for a queryset.

        Args:
            start_date: Start of the date range
            end_date: End of the date range
            queryset: Django queryset to aggregate
            date_field: Field name to use for date truncation

        Returns:
            List of dicts with date and count for each day
        """
        # Get counts per day from database
        daily_counts = queryset.annotate(
            date=TruncDate(date_field)
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Create a dict for quick lookup
        counts_dict = {item['date']: item['count'] for item in daily_counts}

        # Generate complete timeline with all dates
        timeline = []
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            timeline.append({
                'date': current_date.isoformat(),
                'count': counts_dict.get(current_date, 0)
            })
            current_date += timedelta(days=1)

        return timeline

    @staticmethod
    def _generate_timeline_from_messages(start_date: datetime, end_date: datetime, messages: List[Dict], date_field='ArrivedAt') -> List[Dict[str, Any]]:
        """
        Generate daily timeline data from Mailjet message list.

        Args:
            start_date: Start of the date range
            end_date: End of the date range
            messages: List of message dicts with date field
            date_field: Field name to use for date extraction

        Returns:
            List of dicts with date and count for each day
        """
        from collections import defaultdict
        from dateutil import parser
        
        # Count messages per day
        daily_counts = defaultdict(int)
        
        for msg in messages:
            date_str = msg.get(date_field)
            if date_str:
                try:
                    # Parse ISO datetime and extract date
                    msg_datetime = parser.isoparse(date_str)
                    msg_date = msg_datetime.date()
                    daily_counts[msg_date] += 1
                except Exception:
                    continue
        
        # Generate complete timeline with all dates
        timeline = []
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            timeline.append({
                'date': current_date.isoformat(),
                'count': daily_counts.get(current_date, 0)
            })
            current_date += timedelta(days=1)

        return timeline

    @staticmethod
    def get_subscription_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get subscription statistics for the given date range with daily timeline.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        from CreditSystem.models import UserSubscription

        queryset = UserSubscription.objects.filter(
            start_date__gte=start_date,
            start_date__lte=end_date
        )
        queryset = BehaviorDashboardService._exclude_admin_users(queryset)
        count = queryset.count()

        # Generate timeline
        timeline = BehaviorDashboardService._generate_timeline(
            start_date, end_date, queryset, 'start_date'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'subscriptions'
        }

    @staticmethod
    def get_onboarding_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get onboarding completion statistics for the given date range with daily timeline.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        from CreatorProfile.models import CreatorProfile

        queryset = CreatorProfile.objects.filter(
            onboarding_completed=True,
            onboarding_completed_at__gte=start_date,
            onboarding_completed_at__lte=end_date
        )
        queryset = BehaviorDashboardService._exclude_admin_users(queryset)
        count = queryset.count()

        # Generate timeline
        timeline = BehaviorDashboardService._generate_timeline(
            start_date, end_date, queryset, 'onboarding_completed_at'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'onboardings'
        }

    @staticmethod
    def get_image_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get image creation statistics for the given date range with daily timeline.
        Counts PostIdea objects with non-empty image_url.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        from IdeaBank.models import PostIdea

        queryset = PostIdea.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).exclude(
            Q(image_url__isnull=True) | Q(image_url__exact='')
        ).exclude(
            Q(post__user__is_staff=True) | Q(post__user__is_superuser=True)
        )
        count = queryset.count()

        # Generate timeline
        timeline = BehaviorDashboardService._generate_timeline(
            start_date, end_date, queryset, 'created_at'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'images'
        }

    @staticmethod
    def get_email_sent_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get email sent statistics for the given date range with daily timeline.
        Fetches data directly from Mailjet API.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        from IdeaBank.services.mail_service import MailService
        
        # Get admin emails to exclude
        admin_emails = BehaviorDashboardService._get_admin_emails()
        
        # Fetch statistics from Mailjet API
        mail_service = MailService()
        stats = mail_service.get_messages_statistics(start_date, end_date, exclude_emails=admin_emails)
        
        sent_messages = stats.get('sent_messages', [])
        count = len(sent_messages)
        
        # Generate timeline from messages
        timeline = BehaviorDashboardService._generate_timeline_from_messages(
            start_date, end_date, sent_messages, 'ArrivedAt'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'emails_sent'
        }

    @staticmethod
    def get_email_opened_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get email opened statistics for the given date range with daily timeline.
        Fetches data directly from Mailjet API.

        Note: This metric depends on email client behavior and may underreport
        actual opens due to privacy features blocking tracking pixels.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        from IdeaBank.services.mail_service import MailService
        
        # Get admin emails to exclude
        admin_emails = BehaviorDashboardService._get_admin_emails()
        
        # Fetch statistics from Mailjet API
        mail_service = MailService()
        stats = mail_service.get_messages_statistics(start_date, end_date, exclude_emails=admin_emails)
        
        opened_messages = stats.get('opened_messages', [])
        count = len(opened_messages)
        
        # Generate timeline from messages
        # Use OpenedAt if available, otherwise fall back to ArrivedAt
        timeline = BehaviorDashboardService._generate_timeline_from_messages(
            start_date, end_date, opened_messages, 'OpenedAt'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'emails_opened'
        }

    @staticmethod
    def get_posts_total_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get total posts creation statistics for the given date range with daily timeline.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        from IdeaBank.models import Post

        queryset = Post.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).exclude(
            Q(user__is_staff=True) | Q(user__is_superuser=True)
        )
        count = queryset.count()

        # Generate timeline
        timeline = BehaviorDashboardService._generate_timeline(
            start_date, end_date, queryset, 'created_at'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'posts_total'
        }

    @staticmethod
    def get_posts_email_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get posts created via email statistics for the given date range with daily timeline.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        from IdeaBank.models import Post

        queryset = Post.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            is_automatically_generated=True
        ).exclude(
            Q(user__is_staff=True) | Q(user__is_superuser=True)
        )
        count = queryset.count()

        # Generate timeline
        timeline = BehaviorDashboardService._generate_timeline(
            start_date, end_date, queryset, 'created_at'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'posts_email'
        }

    @staticmethod
    def get_posts_manual_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get manually created posts statistics for the given date range with daily timeline.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        from IdeaBank.models import Post

        queryset = Post.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            is_automatically_generated=False
        ).exclude(
            Q(user__is_staff=True) | Q(user__is_superuser=True)
        )
        count = queryset.count()

        # Generate timeline
        timeline = BehaviorDashboardService._generate_timeline(
            start_date, end_date, queryset, 'created_at'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'posts_manual'
        }
