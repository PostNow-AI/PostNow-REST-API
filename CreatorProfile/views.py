
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes

from core.responses import APIResponse
from core.views import BaseAPIView

from .models import UserBehavior
from .serializers import (
    CreatorProfileSerializer,
    OnboardingStatusSerializer,
    Step1PersonalSerializer,
    Step2BusinessSerializer,
    Step3BrandingSerializer,
    UserBehaviorSerializer,
)
from .services import CreatorProfileService


class OnboardingStatusView(BaseAPIView, generics.RetrieveAPIView):
    """Get user's current onboarding status and step."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = CreatorProfileService.get_or_create_profile(request.user)
            status_data = {
                'current_step': profile.current_step,
                'step_1_completed': profile.step_1_completed,
                'step_2_completed': profile.step_2_completed,
                'step_3_completed': profile.step_3_completed,
                'onboarding_completed': profile.onboarding_completed,
                'profile_exists': True
            }
        except Exception:
            # Profile doesn't exist, user is at step 1
            status_data = {
                'current_step': 1,
                'step_1_completed': False,
                'step_2_completed': False,
                'step_3_completed': False,
                'onboarding_completed': False,
                'profile_exists': False
            }

        serializer = OnboardingStatusSerializer(status_data)
        return self.success_response(serializer.data)


class Step1PersonalView(BaseAPIView, generics.RetrieveUpdateAPIView):
    """Handle Step 1: Personal information (professional_name, profession, instagram_handle, whatsapp_number)"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = Step1PersonalSerializer

    def get_object(self):
        return CreatorProfileService.get_or_create_profile(self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update the profile with step 1 data
        updated_profile = CreatorProfileService.update_profile_data(
            request.user, serializer.validated_data
        )

        response_serializer = CreatorProfileSerializer(updated_profile)
        return self.success_response(
            data={
                'step_completed': updated_profile.step_1_completed,
                'current_step': updated_profile.current_step,
                'profile': response_serializer.data
            },
            message='Dados pessoais salvos com sucesso!'
        )


class Step2BusinessView(BaseAPIView, generics.RetrieveUpdateAPIView):
    """Handle Step 2: Business information (business_name, specialization, business_instagram_handle, business_website, business_city, business_description, target demographics)"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = Step2BusinessSerializer

    def get_object(self):
        return CreatorProfileService.get_or_create_profile(self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()

        # Check if step 1 is completed
        if not instance.step_1_completed:
            return self.bad_request_response('Complete o passo 1 antes de prosseguir para o passo 2.')

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update the profile with step 2 data
        updated_profile = CreatorProfileService.update_profile_data(
            request.user, serializer.validated_data
        )

        response_serializer = CreatorProfileSerializer(updated_profile)
        return self.success_response(
            data={
                'step_completed': updated_profile.step_2_completed,
                'current_step': updated_profile.current_step,
                'profile': response_serializer.data
            },
            message='Dados do negócio salvos com sucesso!'
        )


class Step3BrandingView(BaseAPIView, generics.RetrieveUpdateAPIView):
    """Handle Step 3: Branding information (logo, voice_tone, colors)"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = Step3BrandingSerializer

    def get_object(self):
        return CreatorProfileService.get_or_create_profile(self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()

        # Check if step 2 is completed
        if not instance.step_2_completed:
            return self.bad_request_response('Complete o passo 2 antes de prosseguir para o passo 3.')

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update the profile with step 3 data
        updated_profile = CreatorProfileService.update_profile_data(
            request.user, serializer.validated_data
        )

        message = 'Dados de marca salvos com sucesso!' if not updated_profile.onboarding_completed else 'Onboarding completado com sucesso!'
        response_serializer = CreatorProfileSerializer(updated_profile)
        return self.success_response(
            data={
                'step_completed': updated_profile.step_3_completed,
                'current_step': updated_profile.current_step,
                'onboarding_completed': updated_profile.onboarding_completed,
                'profile': response_serializer.data
            },
            message=message
        )


class CreatorProfileView(BaseAPIView, generics.RetrieveUpdateAPIView):
    """Get and update complete creator profile."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreatorProfileSerializer

    def get_object(self):
        return CreatorProfileService.get_or_create_profile(self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        updated_profile = CreatorProfileService.update_profile_data(
            request.user, serializer.validated_data)

        response_serializer = CreatorProfileSerializer(updated_profile)
        return self.success_response(
            data={'profile': response_serializer.data},
            message='Perfil atualizado com sucesso!'
        )


class ResetCreatorProfileStatusView(BaseAPIView, generics.GenericAPIView):
    """Reset user profile to start onboarding again."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            success = CreatorProfileService.reset_profile(request.user)
            if success:
                return self.success_response(
                    data={'reset': True},
                    message='Perfil resetado com sucesso!'
                )
            else:
                return self.not_found_response('Nenhum perfil encontrado para resetar')
        except Exception as e:
            return self.server_error_response(f'Erro ao resetar o perfil: {str(e)}')


class CompleteCreatorProfileStatusView(BaseAPIView, generics.GenericAPIView):
    """Complete user profile onboarding."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            success = CreatorProfileService.complete_profile(request.user)
            if success:
                return self.success_response(
                    data={'completed': True},
                    message='Perfil completado com sucesso!'
                )
            else:
                return self.not_found_response('Nenhum perfil encontrado para completar')
        except Exception as e:
            return self.server_error_response(f'Erro ao completar o perfil: {str(e)}')


class UserBehaviorView(BaseAPIView, generics.RetrieveUpdateAPIView):
    """Manage user behavioral data for personalization."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserBehaviorSerializer

    def get_object(self):
        behavior, created = UserBehavior.objects.get_or_create(
            user=self.request.user)
        return behavior

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return self.success_response(
            data={'behavior': serializer.data},
            message='Dados comportamentais atualizados!'
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reset_profile(request):
    """Reset user profile to start onboarding again."""
    success = CreatorProfileService.reset_profile(request.user)

    if success:
        return APIResponse.success(
            data={'reset': True},
            message='Perfil resetado com sucesso!'
        )
    else:
        return APIResponse.not_found('Nenhum perfil encontrado para resetar')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def generate_random_colors(request):
    """Generate a set of random colors for the user's palette."""
    from .models import generate_random_colors
    colors = generate_random_colors()
    return APIResponse.success(data={
        'colors': {
            'color_1': colors[0],
            'color_2': colors[1],
            'color_3': colors[2],
            'color_4': colors[3],
            'color_5': colors[4]
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def onboarding_suggestions(request):
    """Get suggestions for onboarding fields."""
    from .services import SuggestionService
    suggestions = SuggestionService.get_all_suggestions()
    return APIResponse.success(data=suggestions)


# TEMPORARY TEST ENDPOINT - Remove in production
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_structure(request):
    """Test endpoint to verify our model structure is working correctly."""
    from .models import CreatorProfile

    # Get total count of creator profiles
    total_profiles = CreatorProfile.objects.count()

    # Get a sample of field names from the model
    field_names = [field.name for field in CreatorProfile._meta.get_fields()]

    return APIResponse.success(data={
        "total_profiles": total_profiles,
        "model_fields": field_names[:10],  # First 10 fields
        "endpoints_available": [
            "/api/v1/creator-profile/",
            "/api/v1/creator-profile/onboarding/step1/",
            "/api/v1/creator-profile/onboarding/step2/",
            "/api/v1/creator-profile/onboarding/step3/",
            "/api/v1/creator-profile/suggestions/"
        ]
    }, message="Creator Profile API is working correctly!")
