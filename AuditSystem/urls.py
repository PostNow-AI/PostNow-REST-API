from django.urls import path

from . import views

app_name = 'auditsystem'

urlpatterns = [
    path('generate-daily-report/', views.generate_daily_audit_report,
         name='generate_daily_report'),
]
