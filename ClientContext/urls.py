from django.urls import path

from . import views

app_name = 'client_context'

urlpatterns = [
    path('generate-weekly-context/', views.generate_client_context,
         name='generate_weekly_context'),
    path('manual-generate-weekly-context/', views.manual_generate_client_context,
         name='manual_generate_weekly_context'),
    path('retry-generate-weekly-context/', views.retry_generate_client_context,
         name='retry_generate_weekly_context'),
    path('send-weekly-context-email/', views.send_weekly_context_email,
         name='send_weekly_context_email'),
    # Monday: Opportunities email (enriched)
    path('enrich-and-send-opportunities-email/', views.enrich_and_send_opportunities_email,
         name='enrich_and_send_opportunities_email'),
    # Wednesday: Market Intelligence email
    path('send-market-intelligence-email/', views.send_market_intelligence_email,
         name='send_market_intelligence_email'),
    path('generate-single-client-context/', views.generate_single_client_context,
         name='generate_single_client_context'),
]
