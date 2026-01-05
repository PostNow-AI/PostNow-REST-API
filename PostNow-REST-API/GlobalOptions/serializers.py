from rest_framework import serializers

from .models import (
    CustomFont,
    CustomProfession,
    CustomSpecialization,
    PredefinedFont,
    PredefinedProfession,
    PredefinedSpecialization,
)
from Campaigns.models import VisualStyle, VisualStyleExample


class PredefinedProfessionSerializer(serializers.ModelSerializer):
    """Serializer para profissões predefinidas."""

    class Meta:
        model = PredefinedProfession
        fields = ['id', 'name', 'is_active']


class PredefinedSpecializationSerializer(serializers.ModelSerializer):
    """Serializer para especializações predefinidas."""

    profession_name = serializers.CharField(
        source='profession.name', read_only=True)

    class Meta:
        model = PredefinedSpecialization
        fields = ['id', 'name', 'profession', 'profession_name', 'is_active']


class PredefinedFontSerializer(serializers.ModelSerializer):
    """Serializer para fontes predefinidas."""

    class Meta:
        model = PredefinedFont
        fields = ['id', 'name', 'is_active']


class CustomProfessionSerializer(serializers.ModelSerializer):
    """Serializer for CustomProfession model."""

    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = CustomProfession
        fields = [
            'id', 'name', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CustomSpecializationSerializer(serializers.ModelSerializer):
    """Serializer for CustomSpecialization model."""

    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = CustomSpecialization
        fields = [
            'id', 'name', 'profession', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        """Define automaticamente o usuário que criou a especialização."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

    def validate(self, data):
        """Valida se a profissão existe e está ativa."""
        profession = data.get('profession')
        if profession and not profession.is_active:
            raise serializers.ValidationError(
                "A profissão selecionada não está ativa."
            )
        return data


class CustomFontSerializer(serializers.ModelSerializer):
    """Serializer for CustomFont model."""

    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = CustomFont
        fields = [
            'id', 'name', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        """Define automaticamente o usuário que criou a fonte."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ProfessionWithSpecializationsSerializer(serializers.Serializer):
    """Serializer para retornar profissão com suas especializações."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    is_custom = serializers.BooleanField()
    specializations = serializers.ListField(
        child=serializers.DictField()
    )


class FontListSerializer(serializers.Serializer):
    """Serializer para listar todas as fontes disponíveis."""

    predefined = PredefinedFontSerializer(many=True)
    custom = CustomFontSerializer(many=True)


class VisualStyleExampleSerializer(serializers.ModelSerializer):
    """Serializer para exemplos de estilos visuais."""
    
    class Meta:
        model = VisualStyleExample
        fields = [
            'id', 'image_url', 'content_preview', 
            'is_seed', 'is_featured', 'view_count', 'selection_count'
        ]


class VisualStyleSerializer(serializers.ModelSerializer):
    """Serializer para estilos visuais com exemplos."""
    
    # Incluir até 3 exemplos públicos
    examples = serializers.SerializerMethodField()

    class Meta:
        model = VisualStyle
        fields = [
            'id', 'name', 'slug', 'category', 'description', 
            'tags', 'success_rate_by_niche', 'global_success_rate',
            'image_prompt_modifiers', 'preview_image_url',
            'best_for_campaign_types', 'best_for_niches',
            'is_active', 'sort_order', 'examples', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'examples']
    
    def get_examples(self, obj):
        """Retorna até 3 exemplos públicos deste estilo."""
        examples = obj.public_examples.all()[:3]
        return VisualStyleExampleSerializer(examples, many=True).data

