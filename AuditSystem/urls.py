from django.urls import path

from .views import (
    generate_daily_audit_report,
    mailjet_webhook,
    subscription_stats_view,
    onboarding_stats_view,
    image_stats_view,
    email_sent_stats_view,
    email_opened_stats_view,
    posts_total_stats_view,
    posts_email_stats_view,
    posts_manual_stats_view,
    login_stats_view,
    login_details_view,
    subscription_details_view,
    onboarding_funnel_view,
    onboarding_step_details_view,
    run_migrations,
    create_yearly_plan,
)

app_name = 'auditsystem'

urlpatterns = [
    path('generate-daily-report/', generate_daily_audit_report,
         name='generate_daily_report'),
    path('webhooks/mailjet/', mailjet_webhook,
         name='mailjet_webhook'),

    # Behavior Dashboard endpoints
    path('dashboard/subscriptions/', subscription_stats_view,
         name='dashboard_subscriptions'),
    path('dashboard/onboardings/', onboarding_stats_view,
         name='dashboard_onboardings'),
    path('dashboard/images/', image_stats_view,
         name='dashboard_images'),
    path('dashboard/emails-sent/', email_sent_stats_view,
         name='dashboard_emails_sent'),
    path('dashboard/emails-opened/', email_opened_stats_view,
         name='dashboard_emails_opened'),

    # Posts dashboard endpoints
    path('dashboard/posts-total/', posts_total_stats_view,
         name='dashboard_posts_total'),
    path('dashboard/posts-email/', posts_email_stats_view,
         name='dashboard_posts_email'),
    path('dashboard/posts-manual/', posts_manual_stats_view,
         name='dashboard_posts_manual'),

    # User behavior dashboard endpoints
    path('dashboard/logins/', login_stats_view,
         name='dashboard_logins'),

    # Detail endpoints for drill-down
    path('dashboard/logins/details/', login_details_view,
         name='dashboard_login_details'),
    path('dashboard/subscriptions/details/', subscription_details_view,
         name='dashboard_subscription_details'),
    path('dashboard/onboarding/funnel/', onboarding_funnel_view,
         name='dashboard_onboarding_funnel'),
    path('dashboard/onboarding/step/<int:step_number>/', onboarding_step_details_view,
         name='dashboard_onboarding_step_details'),

    # Admin maintenance endpoints
    path('admin/run-migrations/', run_migrations,
         name='admin_run_migrations'),
    path('admin/create-yearly-plan/', create_yearly_plan,
         name='admin_create_yearly_plan'),
]
