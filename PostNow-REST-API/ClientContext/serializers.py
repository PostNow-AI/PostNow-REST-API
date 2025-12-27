from rest_framework import serializers

from .models import ClientContext


class ClientContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContext
        fields = '__all__'


class CreateClientContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContext
        exclude = ['created_at', 'updated_at']


# Weekly Context Web Page Serializers
class OpportunityItemSerializer(serializers.Serializer):
    """Serializer for individual opportunity items."""
    titulo_ideia = serializers.CharField()
    score = serializers.IntegerField()
    explicacao_score = serializers.CharField()
    gatilho_criativo = serializers.CharField()
    url_fonte = serializers.URLField()
    texto_base_analisado = serializers.CharField()


class OpportunitySectionSerializer(serializers.Serializer):
    """Serializer for opportunity sections/categories."""
    titulo = serializers.CharField()
    count = serializers.IntegerField()
    items = OpportunityItemSerializer(many=True)


class WeeklyContextSerializer(serializers.Serializer):
    """Serializer for the complete Weekly Context response."""
    week_number = serializers.IntegerField()
    week_range = serializers.CharField()
    created_at = serializers.DateTimeField()
    business_name = serializers.CharField()
    has_previous = serializers.BooleanField()
    has_next = serializers.BooleanField()
    ranked_opportunities = serializers.DictField(
        child=OpportunitySectionSerializer()
    )
