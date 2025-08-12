from rest_framework import serializers

from .models import (
    CustomFont,
    CustomProfession,
    CustomSpecialization,
    PredefinedFont,
    PredefinedProfession,
    PredefinedSpecialization,
)


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
    """Serializer para profissões customizadas."""

    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True)

    class Meta:
        model = CustomProfession
        fields = [
            'id', 'name', 'created_by', 'created_by_username',
            'usage_count', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_by', 'usage_count', 'created_at']

    def create(self, validated_data):
        """Define automaticamente o usuário que criou a profissão."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class CustomSpecializationSerializer(serializers.ModelSerializer):
    """Serializer para especializações customizadas."""

    profession_name = serializers.CharField(
        source='profession.name', read_only=True)
    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True)

    class Meta:
        model = CustomSpecialization
        fields = [
            'id', 'name', 'profession', 'profession_name',
            'created_by', 'created_by_username', 'usage_count',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_by', 'usage_count', 'created_at']

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
    """Serializer para fontes customizadas."""

    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True)

    class Meta:
        model = CustomFont
        fields = [
            'id', 'name', 'created_by', 'created_by_username',
            'usage_count', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_by', 'usage_count', 'created_at']

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
