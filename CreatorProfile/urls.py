from django.urls import path

from . import views

app_name = 'creator_profile'

urlpatterns = [
    # Profile completion status - used to determine if onboarding is needed
    path('status/', views.ProfileCompletionStatusView.as_view(),
         name='completion_status'),

    # Onboarding endpoints
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('onboarding/skip/', views.skip_onboarding, name='skip_onboarding'),

    # Profile management
    path('profile/', views.CreatorProfileView.as_view(), name='profile'),
    path('profile/reset/', views.reset_profile, name='reset_profile'),

    # User behavior tracking
    path('behavior/', views.UserBehaviorView.as_view(), name='behavior'),

    # Helper endpoints for frontend
    path('choices/', views.profile_choices, name='profile_choices'),
    path('suggestions/', views.profile_suggestions, name='profile_suggestions'),
]
