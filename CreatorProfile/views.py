import base64

from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import CreatorProfile, UserBehavior
from .serializers import (
    CreatorProfileSerializer,
    OnboardingSerializer,
    OnboardingStatusSerializer,
    UserBehaviorSerializer,
)


class OnboardingStatusView(generics.RetrieveAPIView):
    """
    Get user's onboarding status.
    Used by frontend to determine if onboarding is required.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = CreatorProfile.objects.get(user=request.user)

            # Check which fields have data
            onboarding_fields = [
                'professional_name',
                'profession',
                'specialization',
                'linkedin_url',
                'instagram_username',
                'youtube_channel',
                'tiktok_username',
                'primary_color',
                'secondary_color',
                'accent_color_1',
                'accent_color_2',
                'accent_color_3',
                'primary_font',
                'secondary_font',
            ]

            filled_fields = 0
            for field in onboarding_fields:
                value = getattr(profile, field, None)
                if value and str(value).strip():
                    filled_fields += 1

            data = {
                'onboarding_completed': profile.onboarding_completed,
                'onboarding_skipped': profile.onboarding_skipped,
                'has_data': filled_fields > 0,
                'filled_fields_count': filled_fields,
                'total_fields_count': len(onboarding_fields),
            }

            serializer = OnboardingStatusSerializer(data)
            return Response(serializer.data)

        except CreatorProfile.DoesNotExist:
            # Profile doesn't exist, onboarding required
            data = {
                'onboarding_completed': False,
                'onboarding_skipped': False,
                'has_data': False,
                'filled_fields_count': 0,
                'total_fields_count': 14,  # 14 onboarding fields
            }

            serializer = OnboardingStatusSerializer(data)
            return Response(serializer.data)


class OnboardingView(generics.CreateAPIView):
    """
    Handle onboarding form submission.
    Creates or updates profile with optional fields.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OnboardingSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # Get or create profile
            profile, created = CreatorProfile.objects.get_or_create(
                user=request.user,
                defaults=serializer.validated_data
            )

            if not created:
                # Update existing profile
                for attr, value in serializer.validated_data.items():
                    setattr(profile, attr, value)
                profile.save()

            # Return complete profile data
            response_serializer = CreatorProfileSerializer(profile)

            return Response(
                {
                    'message': 'Dados salvos com sucesso!',
                    'profile': response_serializer.data
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )


class CreatorProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update complete creator profile.
    Supports partial updates for progressive profiling.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreatorProfileSerializer

    def get_object(self):
        profile, created = CreatorProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile

    def update(self, request, *args, **kwargs):
        """Handle partial updates with validation."""
        partial = kwargs.pop('partial', True)  # Always allow partial updates
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            self.perform_update(serializer)

        return Response({
            'message': 'Perfil atualizado com sucesso!',
            'profile': serializer.data
        })


class UserBehaviorView(generics.RetrieveUpdateAPIView):
    """
    Manage user behavioral data for personalization.
    Creates behavior profile if it doesn't exist.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserBehaviorSerializer

    def get_object(self):
        behavior, created = UserBehavior.objects.get_or_create(
            user=self.request.user
        )
        return behavior

    def update(self, request, *args, **kwargs):
        """Handle behavioral data updates."""
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            self.perform_update(serializer)

        return Response({
            'message': 'Dados comportamentais atualizados!',
            'behavior': serializer.data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def skip_onboarding(request):
    """
    Allow user to skip onboarding.
    All fields are optional, so skipping is always allowed.
    """
    try:
        profile = CreatorProfile.objects.get(user=request.user)
        profile.onboarding_skipped = True
        profile.save()

        return Response({
            'message': 'Onboarding pulado com sucesso!',
            'skipped': True
        })

    except CreatorProfile.DoesNotExist:
        # Create profile with skipped status
        profile = CreatorProfile.objects.create(
            user=request.user,
            onboarding_skipped=True
        )

        return Response({
            'message': 'Onboarding pulado com sucesso!',
            'skipped': True
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def onboarding_suggestions(request):
    """
    Get suggestions for onboarding fields.
    Used for autocomplete and quick selection.
    """

    # Popular profession suggestions
    profession_suggestions = [
        'Advogado',
        'Coach',
        'Consultor',
        'Médico',
        'Psicólogo',
        'Dentista',
        'Contador',
        'Arquiteto',
        'Designer',
        'Programador',
        'Médico',
        'Professor',
        'Fisioterapeuta',
        'Nutricionista',
        'Personal Trainer',
    ]

    # Popular specialization suggestions
    specialization_suggestions = [
        'Tributário',
        'Trabalhista',
        'Civil',
        'Executivo',
        'Empresarial',
        'Financeiro',
        'Digital',
        'Estratégico',
        'Cardiologia',
        'Ortopedia',
        'Psicologia Clínica',
        'Psicologia Organizacional',
        'Endodontia',
        'Ortodontia',
        'Contabilidade Tributária',
        'Contabilidade Societária',
        'Arquitetura Residencial',
        'Arquitetura Comercial',
        'Design Gráfico',
        'Design de Produto',
        'Desenvolvimento Web',
        'Desenvolvimento Mobile',
        'Clínica Geral',
        'Pediatria',
        'Educação Física',
        'Nutrição Esportiva',
        'Nutrição Clínica',
    ]

    # Popular font suggestions
    font_suggestions = [
        'Inter',
        'Roboto',
        'Open Sans',
        'Poppins',
        'Montserrat',
        'Lato',
        'Source Sans Pro',
        'Nunito',
        'Ubuntu',
        'Raleway',
        'Playfair Display',
        'Merriweather',
        'PT Sans',
        'Noto Sans',
        'Work Sans',
    ]

    # Popular color suggestions
    color_suggestions = [
        '#3B82F6',  # Blue
        '#EF4444',  # Red
        '#10B981',  # Green
        '#F59E0B',  # Yellow
        '#8B5CF6',  # Purple
        '#F97316',  # Orange
        '#06B6D4',  # Cyan
        '#EC4899',  # Pink
        '#84CC16',  # Lime
        '#6366F1',  # Indigo
        '#F43F5E',  # Rose
        '#14B8A6',  # Teal
        '#FBBF24',  # Amber
        '#A855F7',  # Violet
        '#22C55E',  # Emerald
    ]

    suggestions = {
        'professions': profession_suggestions,
        'specializations': specialization_suggestions,
        'fonts': font_suggestions,
        'colors': color_suggestions,
    }

    return Response(suggestions)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def reset_profile(request):
    """
    Reset user profile to start onboarding again.
    Used for testing or if user wants to restart.
    """
    try:
        profile = CreatorProfile.objects.get(user=request.user)
        profile.delete()

        return Response({
            'message': 'Perfil resetado com sucesso!',
            'reset': True
        })

    except CreatorProfile.DoesNotExist:
        return Response({
            'message': 'Nenhum perfil encontrado para resetar',
            'reset': False
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_user_profile(request):
    """
    Update user's basic profile information (name, surname).
    """
    try:
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        if not first_name and not last_name:
            return Response({
                'error': 'At least first_name or last_name must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        if first_name is not None:
            user.first_name = first_name.strip()
        if last_name is not None:
            user.last_name = last_name.strip()

        user.save()

        return Response({
            'message': 'Perfil atualizado com sucesso!',
            'user': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username
            }
        })

    except Exception as e:
        return Response({
            'error': f'Erro ao atualizar perfil: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_avatar(request):
    """
    Upload user avatar as base64 string.
    Validates image size and format.
    """
    try:
        avatar_data = request.data.get('avatar')

        if not avatar_data:
            return Response({
                'error': 'Avatar data is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate base64 format
        if not avatar_data.startswith('data:image/'):
            return Response({
                'error': 'Invalid image format. Must be base64 encoded image.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract base64 data
        try:
            # Remove data URL prefix
            base64_data = avatar_data.split(',')[1]
            # Decode to check size
            image_bytes = base64.b64decode(base64_data)
        except Exception:
            return Response({
                'error': 'Invalid base64 encoding'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check file size (1MB = 1,048,576 bytes)
        if len(image_bytes) > 1048576:
            return Response({
                'error': 'Image size exceeds 1MB limit'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate image format
        image_header = image_bytes[:8]
        valid_formats = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF
            b'GIF89a',  # GIF
        ]

        is_valid_format = any(image_header.startswith(fmt)
                              for fmt in valid_formats)
        if not is_valid_format:
            return Response({
                'error': 'Invalid image format. Only JPEG, PNG, and GIF are supported.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get or create profile and save avatar
        profile, created = CreatorProfile.objects.get_or_create(
            user=request.user
        )

        profile.avatar = avatar_data
        profile.save()

        return Response({
            'message': 'Avatar atualizado com sucesso!',
            'avatar': avatar_data
        })

    except Exception as e:
        return Response({
            'error': f'Erro ao fazer upload do avatar: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
