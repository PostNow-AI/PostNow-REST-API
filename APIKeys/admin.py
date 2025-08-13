from django.contrib import admin

from .models import UserAPIKey


@admin.register(UserAPIKey)
class UserAPIKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'provider', 'created_at', 'updated_at']
    list_filter = ['provider', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
