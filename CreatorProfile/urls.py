from django.urls import path

from . import views

app_name = 'creator_profile'

urlpatterns = [
    # Onboarding status - used to determine if onboarding is needed
    path('onboarding/status/', views.OnboardingStatusView.as_view(),
         name='onboarding_status'),

    # Onboarding endpoints
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('onboarding/skip/', views.skip_onboarding, name='skip_onboarding'),

    # Profile management
    path('profile/', views.CreatorProfileView.as_view(), name='profile'),
    path('profile/reset/', views.reset_profile, name='reset_profile'),

    # User behavior tracking
    path('behavior/', views.UserBehaviorView.as_view(), name='behavior'),

    # Helper endpoints for frontend
    path('onboarding/suggestions/', views.onboarding_suggestions,
         name='onboarding_suggestions'),

    # User profile management
    path('user/profile/', views.update_user_profile, name='update_user_profile'),
    path('user/avatar/', views.upload_avatar, name='upload_avatar'),
]
