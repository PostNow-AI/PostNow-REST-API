"""
URL configuration for Sonora_REST_API project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from Sonora_REST_API.Users.views import (
    CsrfExemptConfirmEmailView,
    CsrfExemptPasswordResetFromKeyView,
    CsrfExemptPasswordResetView,
    GoogleLogin,
    delete_user_by_email,
    disconnect_social_account,
    google_auth,
    google_callback,
    list_social_accounts,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/v1/auth/", include("dj_rest_auth.urls")),
    path('api/v1/auth/registration/', include('dj_rest_auth.registration.urls')),
    # Add allauth URLs for email verification, but override confirm-email with CSRF-exempt version
    path('api/v1/auth/accounts/confirm-email/<str:key>/',
         CsrfExemptConfirmEmailView.as_view(), name='account_confirm_email'),
    path('api/v1/auth/accounts/password/reset/',
         CsrfExemptPasswordResetView.as_view(), name='account_reset_password'),
    path('api/v1/auth/accounts/password/reset/<str:uidb36>/<str:key>/',
         CsrfExemptPasswordResetFromKeyView.as_view(), name='account_reset_password_from_key'),
    path('api/v1/auth/accounts/', include('allauth.urls')),
    path('api/v1/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/v1/auth/google/auth/', google_auth, name='google_auth'),
    path('api/v1/auth/google/callback/',
         google_callback, name='google_callback'),

    # Social account management endpoints
    path('api/v1/auth/social-accounts/',
         list_social_accounts, name='list_social_accounts'),
    path('api/v1/auth/social-accounts/<int:account_id>/disconnect/',
         disconnect_social_account, name='disconnect_social_account'),
    path('api/v1/auth/delete-user/',
         delete_user_by_email, name='delete_user_by_email'),



    # Creator Profile endpoints
    path('api/v1/creator-profile/', include('CreatorProfile.urls')),
    path('api/v1/ideabank/', include('IdeaBank.urls')),

    # Global Options endpoints
    path('api/v1/global-options/', include('GlobalOptions.urls')),

    # Credit System endpoints
    path('api/v1/credits/', include('CreditSystem.urls')),

    # Audit System endpoints
    path('api/v1/audit/', include('AuditSystem.urls')),

    # Client Context endpoints
    path('api/v1/client-context/', include('ClientContext.urls')),

    # Analytics endpoints
    path('api/v1/analytics/', include('Analytics.urls')),

    # Onboarding Campaign endpoints
    path('api/v1/onboarding-campaign/', include('OnboardingCampaign.urls')),

    # Social Media Integration endpoints
    path('api/v1/social/', include('SocialMediaIntegration.urls')),
]
