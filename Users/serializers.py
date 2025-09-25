from dj_rest_auth.registration.serializers import RegisterSerializer
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
