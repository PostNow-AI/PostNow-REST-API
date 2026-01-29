"""
URL Configuration for Social Media Integration app
"""

from django.urls import path

from .views import (
    InstagramAccountStatusView,
    InstagramCallbackView,
    InstagramConnectView,
    InstagramDisconnectView,
    InstagramHealthCheckView,
    InstagramMetricsView,
    InstagramNotificationsView,
    InstagramSyncView,
)

app_name = 'socialmedia'

urlpatterns = [
    # OAuth Flow
    path('instagram/connect/', InstagramConnectView.as_view(),
         name='instagram_connect'),
    path('instagram/callback/', InstagramCallbackView.as_view(),
         name='instagram_callback'),

    # Account Management
    path('instagram/status/', InstagramAccountStatusView.as_view(),
         name='instagram_status'),
    path('instagram/sync/', InstagramSyncView.as_view(), name='instagram_sync'),
    path('instagram/disconnect/', InstagramDisconnectView.as_view(),
         name='instagram_disconnect'),

    # Metrics
    path('instagram/metrics/', InstagramMetricsView.as_view(),
         name='instagram_metrics'),

    # Notifications
    path('instagram/notifications/', InstagramNotificationsView.as_view(),
         name='instagram_notifications'),

    # Admin/Health
    path('instagram/health/', InstagramHealthCheckView.as_view(),
         name='instagram_health'),
]
