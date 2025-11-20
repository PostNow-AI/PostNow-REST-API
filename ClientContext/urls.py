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
]
