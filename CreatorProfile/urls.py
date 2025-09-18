from django.urls import path

from . import views

app_name = 'creator_profile'

urlpatterns = [
    # Onboarding status - check current step and completion status
    path('onboarding/status/', views.OnboardingStatusView.as_view(),
         name='onboarding_status'),

    # Step-based onboarding endpoints
    path('onboarding/step1/', views.Step1PersonalView.as_view(),
         name='step1_personal'),
    path('onboarding/step2/', views.Step2BusinessView.as_view(),
         name='step2_business'),
    path('onboarding/step3/', views.Step3BrandingView.as_view(),
         name='step3_branding'),

    # Complete profile management
    path('profile/', views.CreatorProfileView.as_view(), name='profile'),
    path('profile/reset/', views.reset_profile, name='reset_profile'),

    # User behavior tracking
    path('behavior/', views.UserBehaviorView.as_view(), name='behavior'),

    # Helper endpoints for frontend
    path('onboarding/suggestions/', views.onboarding_suggestions,
         name='onboarding_suggestions'),
    path('onboarding/colors/', views.generate_random_colors,
         name='generate_random_colors'),

    # TEMPORARY: Test endpoint to verify structure - Remove in production
    path('test/', views.test_structure, name='test_structure'),
]
