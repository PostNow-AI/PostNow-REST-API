from django.urls import path

from .views import AnalyticsEventCreateView

app_name = "analytics"

urlpatterns = [
    path("analytic-events/", AnalyticsEventCreateView.as_view(), name="analytic-events"),
]

