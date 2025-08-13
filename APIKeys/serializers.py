from rest_framework import serializers

from .models import UserAPIKey


class UserAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAPIKey
        fields = ['id', 'provider', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SetAPIKeySerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=256, min_length=1)
    provider = serializers.ChoiceField(choices=UserAPIKey.PROVIDER_CHOICES)
