from django.contrib import admin

from .models import CreatorProfile, GeneratedVisualStyle, OnboardingStepTracking, OnboardingTempData, VisualStylePreference


@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "business_name",
        "specialization",
        "user_email",
        "weekly_context_policy_override",
        "onboarding_completed",
        "updated_at",
    )
    list_filter = ("weekly_context_policy_override", "onboarding_completed", "step_1_completed", "step_2_completed")
    search_fields = ("business_name", "specialization", "user__email", "user__username")
    readonly_fields = ("created_at", "updated_at", "onboarding_completed_at")

    fieldsets = (
        ("Negócio", {
            "fields": (
                "user",
                "business_name",
                "specialization",
                "business_description",
                "products_services",
                "target_audience",
                "target_interests",
                "main_competitors",
                "reference_profiles",
            )
        }),
        ("Weekly Context (Override)", {
            "fields": ("weekly_context_policy_override",),
            "description": (
                "Use apenas em exceções. Deixe vazio para o sistema decidir automaticamente.\n"
                "Valores sugeridos: default, business_strict, broad_discovery."
            ),
        }),
        ("Status", {
            "fields": ("onboarding_completed", "onboarding_completed_at", "created_at", "updated_at"),
        }),
    )

    @admin.display(description="Email", ordering="user__email")
    def user_email(self, obj: CreatorProfile) -> str:
        return getattr(obj.user, "email", "")


@admin.register(VisualStylePreference)
class VisualStylePreferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(GeneratedVisualStyle)
class GeneratedVisualStyleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user_email', 'is_favorite', 'times_used', 'created_at')
    list_filter = ('is_favorite', 'created_at')
    search_fields = ('name', 'user__email')
    readonly_fields = ('created_at',)

    @admin.display(description="Email", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email


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
