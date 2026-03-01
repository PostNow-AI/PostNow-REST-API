"""
SocialMediaIntegration URL Configuration

API endpoints for Instagram integration and scheduled posts.
"""

from django.urls import path

from .views import (
    # Instagram Account
    InstagramAccountListView,
    InstagramAccountDetailView,
    InstagramAccountDisconnectView,
    # Scheduled Posts
    ScheduledPostListView,
    ScheduledPostDetailView,
    ScheduledPostCancelView,
    ScheduledPostPublishNowView,
    ScheduledPostRetryView,
    ScheduledPostCalendarView,
    ScheduledPostStatsView,
    # Cron
    cron_publish_scheduled,
    cron_retry_failed,
    cron_stats,
)

app_name = 'social'

urlpatterns = [
    # ============================================================
    # Instagram Account Endpoints
    # ============================================================
    path(
        'instagram/accounts/',
        InstagramAccountListView.as_view(),
        name='instagram-account-list'
    ),
    path(
        'instagram/accounts/<int:pk>/',
        InstagramAccountDetailView.as_view(),
        name='instagram-account-detail'
    ),
    path(
        'instagram/accounts/<int:pk>/disconnect/',
        InstagramAccountDisconnectView.as_view(),
        name='instagram-account-disconnect'
    ),

    # ============================================================
    # Scheduled Posts Endpoints
    # ============================================================
    path(
        'scheduled-posts/',
        ScheduledPostListView.as_view(),
        name='scheduled-post-list'
    ),
    path(
        'scheduled-posts/<int:pk>/',
        ScheduledPostDetailView.as_view(),
        name='scheduled-post-detail'
    ),
    path(
        'scheduled-posts/<int:pk>/cancel/',
        ScheduledPostCancelView.as_view(),
        name='scheduled-post-cancel'
    ),
    path(
        'scheduled-posts/<int:pk>/publish-now/',
        ScheduledPostPublishNowView.as_view(),
        name='scheduled-post-publish-now'
    ),
    path(
        'scheduled-posts/<int:pk>/retry/',
        ScheduledPostRetryView.as_view(),
        name='scheduled-post-retry'
    ),
    path(
        'scheduled-posts/calendar/',
        ScheduledPostCalendarView.as_view(),
        name='scheduled-post-calendar'
    ),
    path(
        'scheduled-posts/stats/',
        ScheduledPostStatsView.as_view(),
        name='scheduled-post-stats'
    ),

    # ============================================================
    # Cron Endpoints (GitHub Actions)
    # ============================================================
    path(
        'cron/publish-scheduled/',
        cron_publish_scheduled,
        name='cron-publish-scheduled'
    ),
    path(
        'cron/retry-failed/',
        cron_retry_failed,
        name='cron-retry-failed'
    ),
    path(
        'cron/stats/',
        cron_stats,
        name='cron-stats'
    ),
]
