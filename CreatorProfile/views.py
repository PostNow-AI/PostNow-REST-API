
from AuditSystem.services import AuditService
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

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


class OnboardingStatusView(generics.RetrieveAPIView):
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
        return Response(serializer.data)


class Step1PersonalView(generics.RetrieveUpdateAPIView):
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

        # Log profile step 1 completion
        AuditService.log_profile_operation(
            user=request.user,
            action='profile_updated',
            status='success',
            resource_type='CreatorProfile',
            resource_id=updated_profile.id,
            details={
                'step': 1,
                'step_completed': updated_profile.step_1_completed,
                'current_step': updated_profile.current_step
            }
        )

        response_serializer = CreatorProfileSerializer(updated_profile)
        return Response({
            'message': 'Dados pessoais salvos com sucesso!',
            'step_completed': updated_profile.step_1_completed,
            'current_step': updated_profile.current_step,
            'profile': response_serializer.data
        })


class Step2BusinessView(generics.RetrieveUpdateAPIView):
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
            return Response({
                'error': 'Complete o passo 1 antes de prosseguir para o passo 2.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update the profile with step 2 data
        updated_profile = CreatorProfileService.update_profile_data(
            request.user, serializer.validated_data
        )

        # Log profile step 2 completion
        AuditService.log_profile_operation(
            user=request.user,
            action='profile_updated',
            status='success',
            resource_type='CreatorProfile',
            resource_id=updated_profile.id,
            details={
                'step': 2,
                'step_completed': updated_profile.step_2_completed,
                'current_step': updated_profile.current_step
            }
        )

        response_serializer = CreatorProfileSerializer(updated_profile)
        return Response({
            'message': 'Dados do negócio salvos com sucesso!',
            'step_completed': updated_profile.step_2_completed,
            'current_step': updated_profile.current_step,
            'profile': response_serializer.data
        })


class Step3BrandingView(generics.RetrieveUpdateAPIView):
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
            return Response({
                'error': 'Complete o passo 2 antes de prosseguir para o passo 3.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update the profile with step 3 data
        updated_profile = CreatorProfileService.update_profile_data(
            request.user, serializer.validated_data
        )

        # Log profile step 3 completion and onboarding status
        action = 'profile_updated'
        if updated_profile.onboarding_completed:
            action = 'profile_created'  # First time completion

        AuditService.log_profile_operation(
            user=request.user,
            action=action,
            status='success',
            resource_type='CreatorProfile',
            resource_id=updated_profile.id,
            details={
                'step': 3,
                'step_completed': updated_profile.step_3_completed,
                'current_step': updated_profile.current_step,
                'onboarding_completed': updated_profile.onboarding_completed
            }
        )

        response_serializer = CreatorProfileSerializer(updated_profile)
        return Response({
            'message': 'Dados de marca salvos com sucesso!' if not updated_profile.onboarding_completed else 'Onboarding completado com sucesso!',
            'step_completed': updated_profile.step_3_completed,
            'current_step': updated_profile.current_step,
            'onboarding_completed': updated_profile.onboarding_completed,
            'profile': response_serializer.data
        })


class CreatorProfileView(generics.RetrieveUpdateAPIView):
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

        # Log profile update
        AuditService.log_profile_operation(
            user=request.user,
            action='profile_updated',
            status='success',
            resource_type='CreatorProfile',
            resource_id=updated_profile.id,
            details={
                'changes': list(serializer.validated_data.keys()),
                'onboarding_completed': updated_profile.onboarding_completed
            }
        )

        response_serializer = CreatorProfileSerializer(updated_profile)
        return Response({
            'message': 'Perfil atualizado com sucesso!',
            'profile': response_serializer.data
        })


class ResetCreatorProfileStatusView(generics.GenericAPIView):
    """Reset user profile to start onboarding again."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            success = CreatorProfileService.reset_profile(request.user)
            if success:
                # Log profile reset
                AuditService.log_profile_operation(
                    user=request.user,
                    action='profile_deleted',
                    status='success',
                    resource_type='CreatorProfile',
                    details={'action': 'reset_profile'}
                )

                return Response({
                    'message': 'Perfil resetado com sucesso!',
                    'reset': True
                })
            else:
                return Response({
                    'message': 'Nenhum perfil encontrado para resetar',
                    'reset': False
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'message': 'Erro ao resetar o perfil',
                'reset': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompleteCreatorProfileStatusView(generics.GenericAPIView):
    """Complete user profile onboarding."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            success = CreatorProfileService.complete_profile(request.user)
            if success:
                # Log profile completion
                AuditService.log_profile_operation(
                    user=request.user,
                    action='profile_created',
                    status='success',
                    resource_type='CreatorProfile',
                    details={'action': 'complete_onboarding'}
                )

                return Response({
                    'message': 'Perfil completado com sucesso!',
                    'completed': True
                })
            else:
                return Response({
                    'message': 'Nenhum perfil encontrado para resetar',
                    'reset': False
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'message': 'Erro ao resetar o perfil',
                'reset': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserBehaviorView(generics.RetrieveUpdateAPIView):
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

        # Log behavior update
        AuditService.log_system_operation(
            user=request.user,
            action='system_operation',
            status='success',
            resource_type='UserBehavior',
            resource_id=instance.id,
            details={
                'behavior_updated': True,
                'changes': list(serializer.validated_data.keys())
            }
        )

        return Response({
            'message': 'Dados comportamentais atualizados!',
            'behavior': serializer.data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reset_profile(request):
    """Reset user profile to start onboarding again."""
    success = CreatorProfileService.reset_profile(request.user)

    if success:
        return Response({
            'message': 'Perfil resetado com sucesso!',
            'reset': True
        })
    else:
        return Response({
            'message': 'Nenhum perfil encontrado para resetar',
            'reset': False
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def generate_random_colors(request):
    """Generate a set of random colors for the user's palette."""
    from .models import generate_random_colors
    colors = generate_random_colors()
    return Response({
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
    return Response(suggestions)


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

    return Response({
        "message": "Creator Profile API is working correctly!",
        "total_profiles": total_profiles,
        "model_fields": field_names[:10],  # First 10 fields
        "endpoints_available": [
            "/api/v1/creator-profile/",
            "/api/v1/creator-profile/onboarding/step1/",
            "/api/v1/creator-profile/onboarding/step2/",
            "/api/v1/creator-profile/onboarding/step3/",
            "/api/v1/creator-profile/suggestions/"
        ]
    })
