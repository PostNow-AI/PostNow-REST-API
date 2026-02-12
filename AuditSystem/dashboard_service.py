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

    @staticmethod
    def get_login_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get user login statistics for the given date range with daily timeline.
        Counts successful login events from AuditLog.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with count, timeline, start_date, end_date, metric_name
        """
        queryset = AuditLog.objects.filter(
            action='login',
            status='success',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        queryset = BehaviorDashboardService._exclude_admin_users(queryset)
        count = queryset.count()

        # Generate timeline
        timeline = BehaviorDashboardService._generate_timeline(
            start_date, end_date, queryset, 'timestamp'
        )

        return {
            'count': count,
            'timeline': timeline,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metric_name': 'logins'
        }

    @staticmethod
    def get_login_details(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get detailed login list for the given date range.
        Returns individual login records with user info, timestamp, and subscription status.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with logins list, count, start_date, end_date
        """
        from CreditSystem.models import UserSubscription

        # Convert queryset to list to avoid consumption issues
        login_logs = list(AuditLog.objects.filter(
            action='login',
            status='success',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).exclude(
            Q(user__is_staff=True) | Q(user__is_superuser=True)
        ).select_related('user').order_by('-timestamp'))

        # Get all user IDs from logins
        user_ids = [log.user.id for log in login_logs if log.user]

        # Fetch subscriptions for these users (get most recent subscription per user)
        user_subscriptions = {}
        if user_ids:
            subscriptions = UserSubscription.objects.filter(
                user_id__in=user_ids
            ).select_related('plan').order_by('-start_date')

            for sub in subscriptions:
                if sub.user_id not in user_subscriptions:
                    user_subscriptions[sub.user_id] = {
                        'has_subscription': True,
                        'plan_name': sub.plan.name,
                        'start_date': sub.start_date.isoformat(),
                        'status': sub.status,
                        'status_display': sub.status_display,
                    }

        logins = []
        for log in login_logs:
            if log.user:
                subscription_info = user_subscriptions.get(log.user.id, {
                    'has_subscription': False,
                    'plan_name': None,
                    'start_date': None,
                    'status': None,
                    'status_display': None,
                })
                logins.append({
                    'id': log.id,
                    'user': {
                        'id': log.user.id,
                        'email': log.user.email,
                        'username': log.user.username,
                        'first_name': log.user.first_name,
                        'last_name': log.user.last_name,
                    },
                    'timestamp': log.timestamp.isoformat(),
                    'subscription': subscription_info,
                })

        return {
            'logins': logins,
            'count': len(logins),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }

    @staticmethod
    def get_onboarding_funnel_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get onboarding 2.0 funnel statistics for the given date range.
        Returns counts for each of the 20 steps grouped into 5 phases.

        Phases:
        1. Boas-vindas (1-3): Welcome, Business Name, Contact Info
        2. Seu Negócio (4-8): Niche, Description, Purpose, Personality, Products
        3. Seu Público (9-12): Target Audience, Interests, Location, Competitors
        4. Identidade Visual (13-17): Voice Tone, Visual Style, Logo, Colors, Preview
        5. Autenticação (18-20): Profile Ready, Signup, Paywall

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with step counts, phase counts, and conversion rates
        """
        from CreatorProfile.models import OnboardingStepTracking

        # Base query: tracking records in the period, excluding admins
        base_query = OnboardingStepTracking.objects.filter(
            visited_at__gte=start_date,
            visited_at__lte=end_date
        ).exclude(
            Q(user__is_staff=True) | Q(user__is_superuser=True)
        )

        # Step names for reference
        step_names = {
            1: 'welcome',
            2: 'business_name',
            3: 'contact_info',
            4: 'niche',
            5: 'description',
            6: 'purpose',
            7: 'personality',
            8: 'products',
            9: 'target_audience',
            10: 'interests',
            11: 'location',
            12: 'competitors',
            13: 'voice_tone',
            14: 'visual_style',
            15: 'logo',
            16: 'colors',
            17: 'preview',
            18: 'profile_ready',
            19: 'signup',
            20: 'paywall',
        }

        # Count unique sessions per step (completed=True)
        step_counts = {}
        for step_num in range(1, 21):
            step_key = f'step_{step_num}'
            step_counts[step_key] = base_query.filter(
                step_number=step_num,
                completed=True
            ).values('session_id').distinct().count()

        # Count unique sessions that visited each step (regardless of completion)
        step_visited = {}
        for step_num in range(1, 21):
            step_key = f'step_{step_num}_visited'
            step_visited[step_key] = base_query.filter(
                step_number=step_num
            ).values('session_id').distinct().count()

        # Phase counts (sessions that completed ALL steps in the phase)
        # Phase 1: steps 1-3
        phase_1_sessions = base_query.filter(
            step_number__lte=3, completed=True
        ).values('session_id').annotate(
            step_count=Count('step_number')
        ).filter(step_count=3).count()

        # Phase 2: steps 4-8
        phase_2_sessions = base_query.filter(
            step_number__gte=4, step_number__lte=8, completed=True
        ).values('session_id').annotate(
            step_count=Count('step_number')
        ).filter(step_count=5).count()

        # Phase 3: steps 9-12
        phase_3_sessions = base_query.filter(
            step_number__gte=9, step_number__lte=12, completed=True
        ).values('session_id').annotate(
            step_count=Count('step_number')
        ).filter(step_count=4).count()

        # Phase 4: steps 13-17
        phase_4_sessions = base_query.filter(
            step_number__gte=13, step_number__lte=17, completed=True
        ).values('session_id').annotate(
            step_count=Count('step_number')
        ).filter(step_count=5).count()

        # Phase 5: steps 18-20
        phase_5_sessions = base_query.filter(
            step_number__gte=18, step_number__lte=20, completed=True
        ).values('session_id').annotate(
            step_count=Count('step_number')
        ).filter(step_count=3).count()

        # Total sessions that started (visited step 1)
        started = base_query.filter(step_number=1).values('session_id').distinct().count()

        # Sessions that completed (completed step 20)
        completed = base_query.filter(step_number=20, completed=True).values('session_id').distinct().count()

        return {
            # Total counts
            'started': started,
            'completed': completed,
            # Per-step completed counts
            **step_counts,
            # Per-step visited counts
            **step_visited,
            # Phase completion counts
            'phase_1_completed': phase_1_sessions,
            'phase_2_completed': phase_2_sessions,
            'phase_3_completed': phase_3_sessions,
            'phase_4_completed': phase_4_sessions,
            'phase_5_completed': phase_5_sessions,
            # Step names for reference
            'step_names': step_names,
            # Metadata
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }

    @staticmethod
    def get_onboarding_step_details(start_date: datetime, end_date: datetime, step_number: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific onboarding step.
        Returns session-level data for drill-down analysis.

        Args:
            start_date: Start of the date range
            end_date: End of the date range
            step_number: The step number (1-20) to get details for

        Returns:
            Dict with step details, sessions list, and statistics
        """
        from CreatorProfile.models import OnboardingStepTracking

        # Step names for reference
        step_names = {
            1: 'Welcome', 2: 'Business Name', 3: 'Contact Info',
            4: 'Niche', 5: 'Description', 6: 'Purpose', 7: 'Personality', 8: 'Products',
            9: 'Target Audience', 10: 'Interests', 11: 'Location', 12: 'Competitors',
            13: 'Voice Tone', 14: 'Visual Style', 15: 'Logo', 16: 'Colors', 17: 'Preview',
            18: 'Profile Ready', 19: 'Signup', 20: 'Paywall',
        }

        step_names_pt = {
            1: 'Boas-vindas', 2: 'Nome do Negócio', 3: 'Contato',
            4: 'Nicho', 5: 'Descrição', 6: 'Propósito', 7: 'Personalidade', 8: 'Produtos',
            9: 'Público-Alvo', 10: 'Interesses', 11: 'Localização', 12: 'Concorrentes',
            13: 'Tom de Voz', 14: 'Estilo Visual', 15: 'Logo', 16: 'Cores', 17: 'Preview',
            18: 'Perfil Pronto', 19: 'Cadastro', 20: 'Pagamento',
        }

        # Base query for this step
        base_query = OnboardingStepTracking.objects.filter(
            visited_at__gte=start_date,
            visited_at__lte=end_date,
            step_number=step_number
        ).exclude(
            Q(user__is_staff=True) | Q(user__is_superuser=True)
        )

        # Get all sessions that reached this step
        sessions = base_query.select_related('user').order_by('-visited_at')

        # Calculate statistics
        total_visits = sessions.count()
        completed_count = sessions.filter(completed=True).count()
        completion_rate = (completed_count / total_visits * 100) if total_visits > 0 else 0

        # Calculate average time spent (for completed steps)
        completed_sessions = sessions.filter(
            completed=True,
            completed_at__isnull=False
        )

        total_time_seconds = 0
        time_count = 0
        for session in completed_sessions:
            if session.completed_at and session.visited_at:
                time_diff = (session.completed_at - session.visited_at).total_seconds()
                if 0 < time_diff < 3600:  # Ignore outliers (> 1 hour)
                    total_time_seconds += time_diff
                    time_count += 1

        avg_time_seconds = (total_time_seconds / time_count) if time_count > 0 else 0

        # Get previous step count for drop-off calculation
        prev_step_count = 0
        if step_number > 1:
            prev_step_count = OnboardingStepTracking.objects.filter(
                visited_at__gte=start_date,
                visited_at__lte=end_date,
                step_number=step_number - 1,
                completed=True
            ).exclude(
                Q(user__is_staff=True) | Q(user__is_superuser=True)
            ).values('session_id').distinct().count()

        # Get next step count for progression calculation
        next_step_count = 0
        if step_number < 20:
            next_step_count = OnboardingStepTracking.objects.filter(
                visited_at__gte=start_date,
                visited_at__lte=end_date,
                step_number=step_number + 1
            ).exclude(
                Q(user__is_staff=True) | Q(user__is_superuser=True)
            ).values('session_id').distinct().count()

        # Build sessions list (limit to last 50 for performance)
        sessions_list = []
        for session in sessions[:50]:
            session_data = {
                'session_id': session.session_id,
                'is_simulation': session.session_id.startswith('SIM_'),
                'visited_at': session.visited_at.isoformat(),
                'completed': session.completed,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'time_spent_seconds': None,
                'user': None,
            }

            # Calculate time spent
            if session.completed_at and session.visited_at:
                time_diff = (session.completed_at - session.visited_at).total_seconds()
                if 0 < time_diff < 3600:
                    session_data['time_spent_seconds'] = int(time_diff)

            # Add user info if available
            if session.user:
                session_data['user'] = {
                    'id': session.user.id,
                    'email': session.user.email,
                    'username': session.user.username,
                }

            sessions_list.append(session_data)

        # Calculate drop-off from previous step
        drop_off_count = prev_step_count - total_visits if prev_step_count > 0 else 0
        drop_off_rate = (drop_off_count / prev_step_count * 100) if prev_step_count > 0 else 0

        return {
            'step_number': step_number,
            'step_name': step_names.get(step_number, f'Step {step_number}'),
            'step_name_pt': step_names_pt.get(step_number, f'Etapa {step_number}'),
            'statistics': {
                'total_visits': total_visits,
                'completed': completed_count,
                'completion_rate': round(completion_rate, 1),
                'avg_time_seconds': round(avg_time_seconds, 1),
                'prev_step_count': prev_step_count,
                'next_step_count': next_step_count,
                'drop_off_count': drop_off_count,
                'drop_off_rate': round(drop_off_rate, 1),
                'progression_count': next_step_count,
                'progression_rate': round((next_step_count / total_visits * 100) if total_visits > 0 else 0, 1),
            },
            'sessions': sessions_list,
            'sessions_total': total_visits,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }

    @staticmethod
    def get_subscription_details(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get detailed subscription list for the given date range.
        Returns individual subscription records with user info, date, and plan type.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            Dict with subscriptions list, count, start_date, end_date
        """
        from CreditSystem.models import UserSubscription

        queryset = UserSubscription.objects.filter(
            start_date__gte=start_date,
            start_date__lte=end_date
        ).exclude(
            Q(user__is_staff=True) | Q(user__is_superuser=True)
        ).select_related('user', 'plan').order_by('-start_date')

        subscriptions = []
        for sub in queryset:
            subscriptions.append({
                'id': sub.id,
                'user': {
                    'id': sub.user.id,
                    'email': sub.user.email,
                    'username': sub.user.username,
                    'first_name': sub.user.first_name,
                    'last_name': sub.user.last_name,
                },
                'plan': {
                    'id': sub.plan.id,
                    'name': sub.plan.name,
                    'interval': sub.plan.interval,
                    'interval_display': sub.plan.interval_display,
                    'price': str(sub.plan.price),
                },
                'start_date': sub.start_date.isoformat(),
                'status': sub.status,
                'status_display': sub.status_display,
            })

        return {
            'subscriptions': subscriptions,
            'count': len(subscriptions),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }
