from django.contrib import admin

from .models import CreatorProfile, OnboardingStepTracking, OnboardingTempData, VisualStylePreference


@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'business_name', 'specialization', 'onboarding_completed', 'created_at']
    list_filter = ['onboarding_completed', 'step_1_completed', 'step_2_completed']
    search_fields = ['user__email', 'user__username', 'business_name', 'specialization']
    readonly_fields = ['created_at', 'updated_at', 'onboarding_completed_at']


@admin.register(VisualStylePreference)
class VisualStylePreferenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']


@admin.register(OnboardingStepTracking)
class OnboardingStepTrackingAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'step_number', 'user', 'completed', 'visited_at']
    list_filter = ['step_number', 'completed']
    search_fields = ['session_id', 'user__email']
    readonly_fields = ['visited_at', 'completed_at']


@admin.register(OnboardingTempData)
class OnboardingTempDataAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'created_at', 'updated_at', 'expires_at']
    list_filter = ['created_at']
    search_fields = ['session_id']
    readonly_fields = ['created_at', 'updated_at']
