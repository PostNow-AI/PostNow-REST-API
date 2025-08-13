from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário'
    fields = ('subscribed', 'subscription_date')


class UserAdmin(BaseUserAdmin):
    """Custom User admin with UserProfile inline."""
    inlines = (UserProfileInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""
    list_display = ['user', 'subscribed', 'subscription_date', 'created_at']
    list_filter = ['subscribed', 'created_at', 'subscription_date']
    search_fields = ['user__username', 'user__email',
                     'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
