from django.urls import path

from . import views

app_name = 'auditsystem'

urlpatterns = [
    path('generate-daily-report/', views.generate_daily_audit_report,
         name='generate_daily_report'),
    path('webhooks/mailjet/', views.mailjet_webhook,
         name='mailjet_webhook'),

    # Behavior Dashboard endpoints
    path('dashboard/subscriptions/', views.subscription_stats_view,
         name='dashboard_subscriptions'),
    path('dashboard/onboardings/', views.onboarding_stats_view,
         name='dashboard_onboardings'),
    path('dashboard/images/', views.image_stats_view,
         name='dashboard_images'),
    path('dashboard/emails-sent/', views.email_sent_stats_view,
         name='dashboard_emails_sent'),
    path('dashboard/emails-opened/', views.email_opened_stats_view,
         name='dashboard_emails_opened'),

    # Posts dashboard endpoints
    path('dashboard/posts-total/', views.posts_total_stats_view,
         name='dashboard_posts_total'),
    path('dashboard/posts-email/', views.posts_email_stats_view,
         name='dashboard_posts_email'),
    path('dashboard/posts-manual/', views.posts_manual_stats_view,
         name='dashboard_posts_manual'),
]
