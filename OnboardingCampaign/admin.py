from django.contrib import admin

from .models import OnboardingEmail


@admin.register(OnboardingEmail)
class OnboardingEmailAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'email_number',
        'sent_at',
        'created_at'
    ]
    list_filter = [
        'email_number',
        'sent_at'
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'sent_at'
    ]
    date_hierarchy = 'sent_at'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email do Usuário'
    user_email.admin_order_field = 'user__email'
