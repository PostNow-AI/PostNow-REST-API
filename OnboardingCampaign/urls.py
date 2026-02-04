from django.urls import path

from . import views

app_name = 'onboarding_campaign'

urlpatterns = [
    path('cron/send-emails/', views.send_onboarding_emails_cron,
         name='send_emails_cron'),
]
