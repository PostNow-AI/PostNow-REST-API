from django.contrib import admin

from .models import (
    CustomFont,
    CustomProfession,
    CustomSpecialization,
    CustomSpecializationForProfession,
    PredefinedFont,
    PredefinedProfession,
    PredefinedSpecialization,
)


@admin.register(CustomProfession)
class CustomProfessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by',
                    'usage_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'created_by__email', 'created_by__first_name']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['-usage_count', 'name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'is_active')
        }),
        ('Usuário', {
            'fields': ('created_by',)
        }),
        ('Estatísticas', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomSpecialization)
class CustomSpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'profession', 'created_by',
                    'usage_count', 'is_active', 'created_at']
    list_filter = ['profession', 'is_active', 'created_at']
    search_fields = ['name', 'profession__name', 'created_by__email']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['profession__name', '-usage_count', 'name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'profession', 'is_active')
        }),
        ('Usuário', {
            'fields': ('created_by',)
        }),
        ('Estatísticas', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomFont)
class CustomFontAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by',
                    'usage_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'created_by__email']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['-usage_count', 'name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'is_active')
        }),
        ('Usuário', {
            'fields': ('created_by',)
        }),
        ('Estatísticas', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PredefinedProfession)
class PredefinedProfessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'is_active')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PredefinedSpecialization)
class PredefinedSpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'profession', 'is_active', 'created_at']
    list_filter = ['profession', 'is_active', 'created_at']
    search_fields = ['name', 'profession__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['profession__name', 'name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'profession', 'is_active')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PredefinedFont)
class PredefinedFontAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'is_active')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomSpecializationForProfession)
class CustomSpecializationForProfessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'profession_name', 'created_by',
                    'usage_count', 'is_active', 'created_at']
    list_filter = ['profession_name', 'is_active', 'created_at']
    search_fields = ['name', 'profession_name', 'created_by__email']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['profession_name', '-usage_count', 'name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'profession_name', 'is_active')
        }),
        ('Usuário', {
            'fields': ('created_by',)
        }),
        ('Estatísticas', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
