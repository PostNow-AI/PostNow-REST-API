from django.contrib import admin
from django.utils.html import format_html

from .models import AIModel, CreditPackage, CreditTransaction, UserCredits


@admin.register(CreditPackage)
class CreditPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'credits', 'price',
                    'stripe_price_id', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'stripe_price_id']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'credits', 'price', 'stripe_price_id')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserCredits)
class UserCreditsAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'has_credits_display', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['last_updated']

    def has_credits_display(self, obj):
        if obj.has_credits:
            return format_html('<span style="color: green;">✓ Tem créditos</span>')
        return format_html('<span style="color: red;">✗ Sem créditos</span>')

    has_credits_display.short_description = 'Status dos Créditos'


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount',
                    'transaction_type', 'ai_model', 'created_at']
    list_filter = ['transaction_type', 'ai_model', 'created_at']
    search_fields = ['user__username',
                     'description', 'stripe_payment_intent_id']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Informações da Transação', {
            'fields': ('user', 'amount', 'transaction_type', 'ai_model', 'description')
        }),
        ('Stripe', {
            'fields': ('stripe_payment_intent_id',),
            'classes': ('collapse',)
        }),
        ('Data', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider',
                    'cost_per_token', 'is_active', 'created_at']
    list_filter = ['provider', 'is_active', 'created_at']
    search_fields = ['name', 'provider']
    readonly_fields = ['created_at']
    list_editable = ['is_active', 'cost_per_token']
