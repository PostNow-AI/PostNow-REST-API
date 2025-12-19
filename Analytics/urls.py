from django.urls import path

from .views import AnalyticsEventCreateView

app_name = "analytics"

urlpatterns = [
    path("events/", AnalyticsEventCreateView.as_view(), name="events"),
]

