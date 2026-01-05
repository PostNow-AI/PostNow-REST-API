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
    path('generate-single-client-context/', views.generate_single_client_context,
         name='generate_single_client_context'),
    
    # Weekly Context Web Page endpoints
    path('weekly-context/', views.WeeklyContextCurrentView.as_view(),
         name='weekly-context-current'),
    path('weekly-context/history/', views.WeeklyContextHistoryView.as_view(),
         name='weekly-context-history'),
    
    # ✅ NOVO: Market opportunities para campanhas
    path('weekly-context/opportunities/', views.get_market_opportunities,
         name='market-opportunities'),
]
