from django.urls import path

from . import views

app_name = 'creator_profile'

urlpatterns = [
    # Onboarding status - check current step and completion status
    path('onboarding/status/', views.OnboardingStatusView.as_view(),
         name='onboarding_status'),

    # Step-based onboarding endpoints
    path('onboarding/step1/', views.Step1BusinessView.as_view(),
         name='step1_business'),
    path('onboarding/step2/', views.Step2BrandingView.as_view(),
         name='step2_branding'),

    # Complete profile management
    path('profile/', views.CreatorProfileView.as_view(), name='profile'),
    path('profile/reset/', views.ResetCreatorProfileStatusView.as_view(),
         name='reset_profile'),
    path('profile/complete/', views.CompleteCreatorProfileStatusView.as_view(),
         name='complete_profile'),

    # Helper endpoints for frontend
    path('onboarding/suggestions/', views.onboarding_suggestions,
         name='onboarding_suggestions'),
    path('onboarding/colors/', views.generate_random_colors,
         name='generate_random_colors'),

    # TEMPORARY: Test endpoint to verify structure - Remove in production
    path('test/', views.test_structure, name='test_structure'),

    # Visual Style Preferences endpoints
    path('visual-style-preferences/', views.VisualStylePreferenceView.as_view(),
         name='visual_style_preferences_list'),

    # Onboarding step tracking
    path('onboarding/track/', views.track_onboarding_step,
         name='track_onboarding_step'),

    # Temporary data endpoints (for anonymous users)
    path('onboarding/temp-data/', views.save_onboarding_temp_data,
         name='save_onboarding_temp_data'),
    path('onboarding/link-data/', views.link_onboarding_data,
         name='link_onboarding_data'),
]
