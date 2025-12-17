from django.contrib import admin

from .models import CreatorProfile, VisualStylePreference


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
    list_filter = ("weekly_context_policy_override", "onboarding_completed")
    search_fields = ("business_name", "specialization", "user__email")
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


