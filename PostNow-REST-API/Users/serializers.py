from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth.models import User
from rest_framework import serializers


class CustomRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def save(self, request):
        user = super().save(request)
        user.first_name = self.data.get('first_name', '')
        user.last_name = self.data.get('last_name', '')
        user.save()
        return user


class CustomUserDetailsSerializer(serializers.ModelSerializer):
    """Serializer for User model including UserProfile."""

    class Meta:
        model = User
        fields = ['id',  'email',
                  'first_name', 'last_name', 'is_superuser', 'is_staff']
        read_only_fields = ['id', 'email',
                            'first_name', 'last_name', 'is_superuser', 'is_staff']
