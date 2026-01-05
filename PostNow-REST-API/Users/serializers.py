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
    """Serializer for User model including CreatorProfile."""
    
    creator_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 
                  'is_superuser', 'is_staff', 'creator_profile']
        read_only_fields = ['id', 'email', 'first_name', 'last_name', 
                            'is_superuser', 'is_staff', 'creator_profile']
    
    def get_creator_profile(self, obj):
        """Retorna dados do CreatorProfile incluindo visual_style_ids."""
        try:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.get(user=obj)
            return {
                'id': profile.id,
                'business_name': profile.business_name,
                'visual_style_ids': profile.visual_style_ids or [],
                'voice_tone': profile.voice_tone,
                'specialization': profile.specialization,
                'onboarding_completed': profile.onboarding_completed,
            }
        except:
            return None
