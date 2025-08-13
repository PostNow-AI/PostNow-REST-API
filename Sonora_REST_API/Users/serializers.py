from rest_framework import serializers

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile."""

    class Meta:
        model = UserProfile
        fields = ['subscribed', 'subscription_date',
                  'created_at', 'updated_at']
        read_only_fields = ['subscription_date', 'created_at', 'updated_at']


class UserSubscriptionStatusSerializer(serializers.Serializer):
    """Serializer for user subscription status."""
    subscribed = serializers.BooleanField()
    subscription_date = serializers.DateTimeField(allow_null=True)
    message = serializers.CharField(allow_blank=True)
