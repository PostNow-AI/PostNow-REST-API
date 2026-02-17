"""Serializers DRF para o model ClientContext."""

from rest_framework import serializers

from ClientContext.models import ClientContext


class ClientContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContext
        fields = '__all__'


class CreateClientContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContext
        exclude = ['created_at', 'updated_at']
