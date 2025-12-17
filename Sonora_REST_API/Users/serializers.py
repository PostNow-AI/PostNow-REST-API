from rest_framework import serializers

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile."""

    class Meta:
        model = UserProfile
        fields = ['created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    message = serializers.CharField(allow_blank=True)
