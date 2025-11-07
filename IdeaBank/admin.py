from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from .models import Post, PostIdea


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin configuration for Post model."""

    # List display
    list_display = [
        'id', 'name', 'user', 'objective_display', 'type_display',
        'ideas_count', 'include_image', 'is_active', 'is_automatically_generated',
        'created_at'
    ]

    # List filters
    list_filter = [
        'objective', 'type', 'include_image', 'is_active',
        'is_automatically_generated', 'created_at', 'updated_at'
    ]

    # Search fields
    search_fields = [
        'name', 'user__username', 'user__email', 'further_details'
    ]

    # Ordering
    ordering = ['-created_at']

    # List editable fields
    list_editable = ['is_active']

    # Date hierarchy
    date_hierarchy = 'created_at'

    # Actions
    actions = [
        'mark_as_active', 'mark_as_inactive',
        'enable_image_generation', 'disable_image_generation'
    ]

    # Fieldsets for form
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('user', 'name', 'objective', 'type')
        }),
        (_('Configuração de Conteúdo'), {
            'fields': ('further_details', 'include_image')
        }),
        (_('Status e Controle'), {
            'fields': ('is_active', 'is_automatically_generated'),
            'classes': ('collapse',)
        }),
        (_('Metadados'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Readonly fields
    readonly_fields = ['created_at', 'updated_at', 'id']

    # Custom methods
    def objective_display(self, obj):
        """Display objective with color coding."""
        colors = {
            'sales': '#28a745',      # green
            'branding': '#007bff',   # blue
            'engagement': '#ffc107',  # yellow
            'awareness': '#17a2b8',  # cyan
            'lead_generation': '#fd7e14',  # orange
            'education': '#6f42c1',  # purple
        }
        color = colors.get(obj.objective, '#6c757d')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_objective_display()
        )
    objective_display.short_description = _('Objetivo')
    objective_display.admin_order_field = 'objective'

    def type_display(self, obj):
        """Display type with icons."""
        icons = {
            'post': '📝',
            'reel': '🎥',
            'live': '🔴',
            'carousel': '📸',
            'story': '📖'
        }
        icon = icons.get(obj.type, '📄')
        return f"{icon} {obj.get_type_display()}"
    type_display.short_description = _('Tipo')
    type_display.admin_order_field = 'type'

    def ideas_count(self, obj):
        """Display ideas count with link to related ideas."""
        count = obj.ideas_count
        if count > 0:
            url = f'/admin/IdeaBank/postidea/?post__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return '0'
    ideas_count.short_description = _('Ideias')

    # Custom actions
    def mark_as_active(self, request, queryset):
        """Mark selected posts as active."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d post foi marcado como ativo.',
                '%d posts foram marcados como ativos.',
                updated,
            ) % updated,
        )
    mark_as_active.short_description = _(
        'Marcar posts selecionados como ativos')

    def mark_as_inactive(self, request, queryset):
        """Mark selected posts as inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d post foi marcado como inativo.',
                '%d posts foram marcados como inativos.',
                updated,
            ) % updated,
        )
    mark_as_inactive.short_description = _(
        'Marcar posts selecionados como inativos')

    def enable_image_generation(self, request, queryset):
        """Enable image generation for selected posts."""
        updated = queryset.update(include_image=True)
        self.message_user(
            request,
            ngettext(
                'Geração de imagem habilitada para %d post.',
                'Geração de imagem habilitada para %d posts.',
                updated,
            ) % updated,
        )
    enable_image_generation.short_description = _(
        'Habilitar geração de imagem')

    def disable_image_generation(self, request, queryset):
        """Disable image generation for selected posts."""
        updated = queryset.update(include_image=False)
        self.message_user(
            request,
            ngettext(
                'Geração de imagem desabilitada para %d post.',
                'Geração de imagem desabilitada para %d posts.',
                updated,
            ) % updated,
        )
    disable_image_generation.short_description = _(
        'Desabilitar geração de imagem')

    # Custom queryset for performance
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        return super().get_queryset(request).annotate(
            ideas_count=Count('ideas')
        )


@admin.register(PostIdea)
class PostIdeaAdmin(admin.ModelAdmin):
    """Admin configuration for PostIdea model."""

    # List display
    list_display = [
        'id', 'post_link', 'content_preview', 'has_image_display',
        'word_count', 'created_at'
    ]

    # List filters
    list_filter = [
        'created_at', 'updated_at',
        ('post__objective', admin.RelatedFieldListFilter),
        ('post__type', admin.RelatedFieldListFilter),
        'post__user'
    ]

    # Search fields
    search_fields = [
        'content', 'image_description', 'post__name', 'post__user__username'
    ]

    # Ordering
    ordering = ['-created_at']

    # Date hierarchy
    date_hierarchy = 'created_at'

    # Actions
    actions = ['mark_posts_active', 'view_full_content']

    # Fieldsets
    fieldsets = (
        (_('Relacionamento'), {
            'fields': ('post',)
        }),
        (_('Conteúdo'), {
            'fields': ('content', 'image_description')
        }),
        (_('Imagem'), {
            'fields': ('image_url',),
            'classes': ('collapse',)
        }),
        (_('Metadados'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Readonly fields
    readonly_fields = ['created_at', 'updated_at', 'id']

    # Custom list display methods
    def post_link(self, obj):
        """Display post with link."""
        url = f'/admin/IdeaBank/post/{obj.post.id}/change/'
        return format_html('<a href="{}">{}</a>', url, obj.post.display_name)
    post_link.short_description = _('Post')
    post_link.admin_order_field = 'post__name'

    def content_preview(self, obj):
        """Display content preview."""
        preview = obj.content_preview
        if len(obj.content) > 100:
            return format_html(
                '<span title="{}">{}</span>',
                obj.content.replace('"', '&quot;'),
                preview
            )
        return preview
    content_preview.short_description = _('Conteúdo')

    def has_image_display(self, obj):
        """Display if idea has image."""
        if obj.has_image:
            return format_html('<span style="color: #28a745;">✓</span>')
        return format_html('<span style="color: #dc3545;">✗</span>')
    has_image_display.short_description = _('Imagem')
    has_image_display.admin_order_field = 'image_url'

    def word_count(self, obj):
        """Display word count."""
        count = obj.word_count
        if count > 200:
            return format_html('<span style="color: #ffc107;">{}</span>', count)
        elif count > 100:
            return format_html('<span style="color: #28a745;">{}</span>', count)
        else:
            return format_html('<span style="color: #dc3545;">{}</span>', count)
    word_count.short_description = _('Palavras')
    word_count.admin_order_field = 'content'

    # Custom actions
    def mark_posts_active(self, request, queryset):
        """Mark related posts as active."""
        post_ids = queryset.values_list('post_id', flat=True).distinct()
        updated = Post.objects.filter(id__in=post_ids).update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d post relacionado foi marcado como ativo.',
                '%d posts relacionados foram marcados como ativos.',
                updated,
            ) % updated,
        )
    mark_posts_active.short_description = _(
        'Marcar posts relacionados como ativos')

    def view_full_content(self, request, queryset):
        """Action to view full content (placeholder for future implementation)."""
        selected = queryset.count()
        self.message_user(
            request,
            ngettext(
                'Visualização completa disponível para %d ideia selecionada.',
                'Visualização completa disponível para %d ideias selecionadas.',
                selected,
            ) % selected,
        )
    view_full_content.short_description = _('Visualizar conteúdo completo')

    # Custom formfield overrides
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Optimize foreign key fields."""
        if db_field.name == 'post':
            # Only show active posts, ordered by creation date
            kwargs['queryset'] = Post.objects.filter(
                is_active=True).order_by('-created_at')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Custom admin site configuration
class IdeaBankAdminSite(admin.AdminSite):
    """Custom admin site for IdeaBank app."""
    site_header = _('IdeaBank Administração')
    site_title = _('IdeaBank Admin')
    index_title = _('Painel de Administração - IdeaBank')

    def get_app_list(self, request):
        """Customize app list ordering."""
        app_list = super().get_app_list(request)
        # Ensure IdeaBank models appear first
        for app in app_list:
            if app['app_label'] == 'IdeaBank':
                app['models'].sort(key=lambda x: x['name'])
        return app_list


# Create custom admin site instance
ideabank_admin = IdeaBankAdminSite(name='ideabank_admin')

# Register models with custom admin site
ideabank_admin.register(Post, PostAdmin)
ideabank_admin.register(PostIdea, PostIdeaAdmin)
