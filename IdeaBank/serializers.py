from rest_framework import serializers

from .models import (
    Post,
    PostIdea,
    PostObjective,
    PostType,
)


# New Post-based serializers
class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model."""
    objective_display = serializers.CharField(
        source='get_objective_display', read_only=True)
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    ideas_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'name', 'objective', 'objective_display', 'type', 'type_display',
            'further_details', 'ideas_count', 'include_image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_ideas_count(self, obj):
        """Return the number of ideas for this post."""
        return obj.ideas.count()


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts."""

    class Meta:
        model = Post
        fields = [
            'name', 'objective', 'type', 'further_details', 'include_image'
        ]


class PostIdeaSerializer(serializers.ModelSerializer):
    """Serializer for PostIdea model."""
    content_preview = serializers.ReadOnlyField()
    post_name = serializers.CharField(source='post.name', read_only=True)
    post_type = serializers.CharField(
        source='post.get_type_display', read_only=True)

    class Meta:
        model = PostIdea
        fields = [
            'id', 'content', 'content_preview', 'image_url', 'post_name', 'post_type', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PostIdeaCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating post ideas."""

    class Meta:
        model = PostIdea
        fields = ['content', 'image_url']


class PostWithIdeasSerializer(serializers.ModelSerializer):
    """Serializer for Post with all its ideas."""
    objective_display = serializers.CharField(
        source='get_objective_display', read_only=True)
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    ideas = PostIdeaSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'name', 'objective', 'objective_display', 'type', 'type_display', 'ideas', 'further_details',
            'include_image', 'created_at', 'updated_at'
        ]


class PostGenerationRequestSerializer(serializers.Serializer):
    """Serializer for AI post generation requests."""

    # Required fields
    name = serializers.CharField(max_length=200, help_text="Nome do post")
    objective = serializers.ChoiceField(
        choices=PostObjective.choices, help_text="Objetivo do post")
    type = serializers.ChoiceField(
        choices=PostType.choices, help_text="Tipo de conteúdo")

    further_details = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Detalhes adicionais para a geração de conteúdo"
    )

    # Image generation preference
    include_image = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Se deve gerar imagem automaticamente para o post"
    )

    def validate(self, data):
        """Validate the request data."""
        # Ensure required fields are present
        required_fields = ['name', 'objective', 'type']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} é obrigatório.")

        return data


class PostIdeaEditRequestSerializer(serializers.Serializer):
    """Serializer for editing post ideas with optional AI regeneration."""

    prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Prompt opcional para regeneração do conteúdo"
    )


class ImageGenerationRequestSerializer(serializers.Serializer):
    """Serializer for image generation requests."""

    prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Prompt opcional para geração da imagem"
    )


class PostOptionsSerializer(serializers.Serializer):
    """Serializer for available post options."""
    objectives = serializers.ListField(
        child=serializers.DictField()
    )
    types = serializers.ListField(
        child=serializers.DictField()
    )
