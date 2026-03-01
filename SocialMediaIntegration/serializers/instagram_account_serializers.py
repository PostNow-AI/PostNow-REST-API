"""
Instagram Account Serializers

Serializers for Instagram account management.
"""

from rest_framework import serializers

from ..models import InstagramAccount


class InstagramAccountSerializer(serializers.ModelSerializer):
    """Full serializer for Instagram Account."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_token_valid = serializers.BooleanField(read_only=True)
    days_until_expiration = serializers.IntegerField(read_only=True)

    class Meta:
        model = InstagramAccount
        fields = [
            'id',
            'instagram_user_id',
            'instagram_username',
            'instagram_name',
            'profile_picture_url',
            'facebook_page_id',
            'facebook_page_name',
            'status',
            'status_display',
            'is_token_valid',
            'days_until_expiration',
            'last_sync_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'instagram_user_id',
            'instagram_username',
            'instagram_name',
            'profile_picture_url',
            'facebook_page_id',
            'facebook_page_name',
            'status',
            'is_token_valid',
            'days_until_expiration',
            'last_sync_at',
            'created_at',
            'updated_at',
        ]


class InstagramAccountListSerializer(serializers.ModelSerializer):
    """Minimal serializer for listing Instagram accounts."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_token_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = InstagramAccount
        fields = [
            'id',
            'instagram_username',
            'instagram_name',
            'profile_picture_url',
            'status',
            'status_display',
            'is_token_valid',
        ]
