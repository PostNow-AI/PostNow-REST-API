
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import UserBehavior
from .serializers import (
    CreatorProfileSerializer,
    OnboardingSerializer,
    OnboardingStatusSerializer,
    UserBehaviorSerializer,
)
from .services import (
    AvatarService,
    CreatorProfileService,
    SuggestionService,
    UserProfileService,
)


class OnboardingStatusView(generics.RetrieveAPIView):
    """Get user's onboarding status."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = CreatorProfileService.get_or_create_profile(request.user)

            # Force save to ensure onboarding status is correctly calculated
            profile.save()

            status_data = CreatorProfileService.calculate_onboarding_status(
                profile)
            serializer = OnboardingStatusSerializer(status_data)
            return Response(serializer.data)
        except Exception:
            # Profile doesn't exist or error occurred, onboarding required
            status_data = {
                'onboarding_completed': False,
                'onboarding_skipped': False,
                'has_data': False,
                'filled_fields_count': 0,
                'total_fields_count': 14,
            }
            serializer = OnboardingStatusSerializer(status_data)
            return Response(serializer.data)


class OnboardingView(generics.CreateAPIView):
    """Handle onboarding form submission."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OnboardingSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = CreatorProfileService.update_profile_data(
            request.user, serializer.validated_data
        )
        response_serializer = CreatorProfileSerializer(profile)

        return Response(
            {
                'message': 'Dados salvos com sucesso!',
                'profile': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


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

        CreatorProfileService.update_profile_data(
            request.user, serializer.validated_data)

        return Response({
            'message': 'Perfil atualizado com sucesso!',
            'profile': serializer.data
        })


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

        return Response({
            'message': 'Dados comportamentais atualizados!',
            'behavior': serializer.data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def skip_onboarding(request):
    """Allow user to skip onboarding."""
    try:
        CreatorProfileService.skip_onboarding(request.user)
        return Response({
            'message': 'Onboarding pulado com sucesso!',
            'skipped': True
        })
    except Exception as e:
        return Response({
            'error': f'Erro ao pular onboarding: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def onboarding_suggestions(request):
    """Get suggestions for onboarding fields."""
    suggestions = SuggestionService.get_all_suggestions()
    return Response(suggestions)


@api_view(['DELETE'])
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


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_user_profile(request):
    """Update user's basic profile information."""
    try:
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        if not first_name and not last_name:
            return Response({
                'error': 'At least first_name or last_name must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = UserProfileService.update_user_profile(
            request.user, first_name, last_name
        )

        return Response({
            'message': 'Perfil atualizado com sucesso!',
            'user': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            }
        })

    except Exception as e:
        return Response({
            'error': f'Erro ao atualizar perfil: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_avatar(request):
    """Upload user avatar as base64 string."""
    try:
        avatar_data = request.data.get('avatar')
        is_valid, error_message = AvatarService.validate_avatar_data(
            avatar_data)

        if not is_valid:
            return Response({
                'error': error_message
            }, status=status.HTTP_400_BAD_REQUEST)

        profile = AvatarService.save_avatar(request.user, avatar_data)

        return Response({
            'message': 'Avatar atualizado com sucesso!',
            'avatar': avatar_data
        })

    except Exception as e:
        return Response({
            'error': f'Erro ao fazer upload do avatar: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
