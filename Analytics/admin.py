from django.contrib import admin

from .models import AnalyticsEvent, BanditArmStat, Decision, DecisionOutcome


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_name", "occurred_at", "user", "resource_type", "resource_id")
    list_filter = ("event_name", "resource_type", "policy_id")
    search_fields = ("resource_id", "policy_id", "user__email", "user__username")
    ordering = ("-occurred_at",)


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ("decision_type", "action", "policy_id", "occurred_at", "user")
    list_filter = ("decision_type", "policy_id", "action")
    search_fields = ("resource_id", "user__email", "user__username")
    ordering = ("-occurred_at",)


@admin.register(DecisionOutcome)
class DecisionOutcomeAdmin(admin.ModelAdmin):
    list_display = ("decision", "success", "reward", "computed_at")
    list_filter = ("success",)
    ordering = ("-computed_at",)


@admin.register(BanditArmStat)
class BanditArmStatAdmin(admin.ModelAdmin):
    list_display = ("policy_id", "decision_type", "bucket", "action", "alpha", "beta", "updated_at")
    list_filter = ("policy_id", "decision_type", "action")
    search_fields = ("bucket",)
    ordering = ("-updated_at",)

