from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    Post,
    PostIdea,
    PostObjective,
    PostType,
)


def validate_safe_string(value):
    """Validate that string doesn't contain potentially harmful content."""
    if not isinstance(value, str):
        return value

    # Basic validation - could be extended with more sophisticated checks
    dangerous_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
    value_lower = value.lower()

    for pattern in dangerous_patterns:
        if pattern in value_lower:
            raise serializers.ValidationError(
                _("Conteúdo contém caracteres potencialmente perigosos.")
            )

    return value


def validate_content_length(value):
    """Validate content is not too short or too long."""
    if len(value.strip()) < 10:
        raise serializers.ValidationError(
            _("Conteúdo deve ter pelo menos 10 caracteres.")
        )
    if len(value) > 10000:
        raise serializers.ValidationError(
            _("Conteúdo não pode exceder 10.000 caracteres.")
        )
    return value


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model with enhanced validation and display fields."""

    objective_display = serializers.CharField(
        source='get_objective_display',
        read_only=True,
        help_text=_("Nome descritivo do objetivo")
    )
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True,
        help_text=_("Nome descritivo do tipo")
    )
    ideas_count = serializers.SerializerMethodField(
        help_text=_("Número total de ideias geradas para este post")
    )
    has_image_ideas = serializers.SerializerMethodField(
        help_text=_("Indica se alguma ideia possui imagem")
    )

    class Meta:
        model = Post
        fields = [
            'id', 'name', 'objective', 'objective_display', 'type', 'type_display',
            'further_details', 'ideas_count', 'has_image_ideas', 'include_image',
            'is_automatically_generated', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at',
                            'updated_at', 'ideas_count', 'has_image_ideas']

    def get_ideas_count(self, obj):
        """Return the number of ideas for this post."""
        return obj.ideas_count

    def get_has_image_ideas(self, obj):
        """Return whether this post has any ideas with images."""
        return obj.has_image_ideas

    def validate_name(self, value):
        """Validate post name."""
        if value:
            value = value.strip()
            if len(value) < 3:
                raise serializers.ValidationError(
                    _("Nome deve ter pelo menos 3 caracteres.")
                )
            if len(value) > 200:
                raise serializers.ValidationError(
                    _("Nome não pode exceder 200 caracteres.")
                )
        return validate_safe_string(value)

    def validate_further_details(self, value):
        """Validate further details."""
        if value:
            value = value.strip()
            if len(value) > 2000:
                raise serializers.ValidationError(
                    _("Detalhes adicionais não podem exceder 2000 caracteres.")
                )
        return validate_safe_string(value)


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts with comprehensive validation."""

    class Meta:
        model = Post
        fields = [
            'name', 'objective', 'type', 'further_details', 'include_image'
        ]

    def validate(self, attrs):
        """Cross-field validation for post creation."""
        # Ensure required fields are present
        if not attrs.get('objective'):
            raise serializers.ValidationError({
                'objective': _("Objetivo é obrigatório.")
            })
        if not attrs.get('type'):
            raise serializers.ValidationError({
                'type': _("Tipo é obrigatório.")
            })

        # Additional business logic validation could be added here
        # For example, certain combinations might not be allowed

        return attrs

    def validate_name(self, value):
        """Validate post name for creation."""
        if value:
            value = value.strip()
            if len(value) < 3:
                raise serializers.ValidationError(
                    _("Nome deve ter pelo menos 3 caracteres.")
                )
        return validate_safe_string(value)

    def validate_further_details(self, value):
        """Validate further details for creation."""
        if value:
            value = value.strip()
        return validate_safe_string(value)


class PostIdeaSerializer(serializers.ModelSerializer):
    """Serializer for PostIdea model with enhanced fields."""

    content_preview = serializers.ReadOnlyField(
        help_text=_("Prévia do conteúdo (primeiros 100 caracteres)")
    )
    post_name = serializers.CharField(
        source='post.name',
        read_only=True,
        help_text=_("Nome do post associado")
    )
    post_type = serializers.CharField(
        source='post.get_type_display',
        read_only=True,
        help_text=_("Tipo do post associado")
    )
    has_image = serializers.SerializerMethodField(
        help_text=_("Indica se a ideia possui imagem")
    )
    word_count = serializers.SerializerMethodField(
        help_text=_("Número de palavras no conteúdo")
    )

    class Meta:
        model = PostIdea
        fields = [
            'id', 'content', 'content_preview', 'image_url', 'image_description',
            'post_name', 'post_type', 'has_image', 'word_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'content_preview',
                            'has_image', 'word_count']

    def get_has_image(self, obj):
        """Check if idea has an image."""
        return obj.has_image

    def get_word_count(self, obj):
        """Get word count of content."""
        return obj.word_count

    def validate_content(self, value):
        """Validate idea content."""
        return validate_content_length(validate_safe_string(value))

    def validate_image_description(self, value):
        """Validate image description."""
        if value:
            value = value.strip()
            if len(value) > 1000:
                raise serializers.ValidationError(
                    _("Descrição da imagem não pode exceder 1000 caracteres.")
                )
        return validate_safe_string(value)


class PostIdeaCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating post ideas with validation."""

    class Meta:
        model = PostIdea
        fields = ['content', 'image_url', 'image_description']

    def validate_content(self, value):
        """Validate content for creation."""
        if not value or not value.strip():
            raise serializers.ValidationError(_("Conteúdo é obrigatório."))
        return validate_content_length(validate_safe_string(value))

    def validate_image_url(self, value):
        """Validate image URL."""
        if value:
            value = value.strip()
            # Basic URL validation could be added here
        return value


class PostWithIdeasSerializer(serializers.ModelSerializer):
    """Serializer for Post with all its ideas."""

    objective_display = serializers.CharField(
        source='get_objective_display',
        read_only=True,
        help_text=_("Nome descritivo do objetivo")
    )
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True,
        help_text=_("Nome descritivo do tipo")
    )
    ideas = PostIdeaSerializer(
        many=True,
        read_only=True,
        help_text=_("Lista de ideias geradas para este post")
    )
    ideas_count = serializers.SerializerMethodField(
        help_text=_("Número total de ideias")
    )

    class Meta:
        model = Post
        fields = [
            'id', 'name', 'objective', 'objective_display', 'type', 'type_display',
            'ideas', 'ideas_count', 'further_details', 'include_image',
            'is_automatically_generated', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at',
                            'updated_at', 'ideas', 'ideas_count']

    def get_ideas_count(self, obj):
        """Return the number of ideas."""
        return obj.ideas_count


class PostGenerationRequestSerializer(serializers.Serializer):
    """Serializer for AI post generation requests with comprehensive validation."""

    # Required fields
    name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text=_("Nome opcional para o post a ser gerado")
    )
    objective = serializers.ChoiceField(
        choices=PostObjective.choices,
        help_text=_("Objetivo do conteúdo a ser gerado")
    )
    type = serializers.ChoiceField(
        choices=PostType.choices,
        help_text=_("Tipo de conteúdo a ser gerado")
    )

    further_details = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
        help_text=_("Detalhes adicionais para orientar a geração de conteúdo")
    )

    # Image generation preference
    include_image = serializers.BooleanField(
        required=False,
        default=False,
        help_text=_("Se deve gerar uma imagem automaticamente")
    )

    def validate(self, attrs):
        """Comprehensive validation for post generation request."""
        # Required field validation
        if not attrs.get('objective'):
            raise serializers.ValidationError({
                'objective': _("Objetivo é obrigatório para geração de conteúdo.")
            })
        if not attrs.get('type'):
            raise serializers.ValidationError({
                'type': _("Tipo é obrigatório para geração de conteúdo.")
            })

        # Validate name if provided
        name = attrs.get('name')
        if name:
            name = name.strip()
            if len(name) < 3:
                raise serializers.ValidationError({
                    'name': _("Nome deve ter pelo menos 3 caracteres.")
                })
            attrs['name'] = validate_safe_string(name)

        # Validate further details
        further_details = attrs.get('further_details')
        if further_details:
            further_details = further_details.strip()
            if len(further_details) > 2000:
                raise serializers.ValidationError({
                    'further_details': _("Detalhes adicionais não podem exceder 2000 caracteres.")
                })
            attrs['further_details'] = validate_safe_string(further_details)

        return attrs


class PostIdeaEditRequestSerializer(serializers.Serializer):
    """Serializer for editing post ideas with optional AI regeneration."""

    prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text=_("Prompt opcional para orientar a regeneração do conteúdo")
    )
    preferred_provider = serializers.ChoiceField(
        choices=['google', 'openai'],
        required=False,
        default='google',
        help_text=_("Provedor de IA preferido para regeneração")
    )
    preferred_model = serializers.CharField(
        required=False,
        default='gemini-2.5-flash',
        help_text=_("Modelo de IA preferido para regeneração")
    )

    def validate_prompt(self, value):
        """Validate edit prompt."""
        if value:
            value = value.strip()
            if len(value) > 1000:
                raise serializers.ValidationError(
                    _("Prompt não pode exceder 1000 caracteres.")
                )
        return validate_safe_string(value)


class ImageGenerationRequestSerializer(serializers.Serializer):
    """Serializer for image generation requests with validation."""

    prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text=_("Prompt opcional para orientar a geração da imagem")
    )
    style = serializers.ChoiceField(
        choices=['realistic', 'artistic', 'cartoon', 'minimalist'],
        required=False,
        default='realistic',
        help_text=_("Estilo preferido para a imagem gerada")
    )

    def validate_prompt(self, value):
        """Validate image generation prompt."""
        if value:
            value = value.strip()
            if len(value) > 500:
                raise serializers.ValidationError(
                    _("Prompt da imagem não pode exceder 500 caracteres.")
                )
        return validate_safe_string(value)


class PostOptionsSerializer(serializers.Serializer):
    """Serializer for available post options."""

    objectives = serializers.ListField(
        child=serializers.DictField(),
        help_text=_("Lista de objetivos disponíveis")
    )
    types = serializers.ListField(
        child=serializers.DictField(),
        help_text=_("Lista de tipos disponíveis")
    )
