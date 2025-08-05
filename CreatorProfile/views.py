from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import CreatorProfile, UserBehavior
from .serializers import (
    CreatorProfileSerializer,
    OnboardingSerializer,
    ProfileCompletionSerializer,
    UserBehaviorSerializer,
)


class ProfileCompletionStatusView(generics.RetrieveAPIView):
    """
    Get user's profile completion status.
    Used by frontend to determine if onboarding is required.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = CreatorProfile.objects.get(user=request.user)

            # Check which required fields are missing
            required_fields = [
                'main_platform',
                'niche',
                'experience_level',
                'primary_goal',
                'time_available',
            ]

            missing_fields = []
            for field in required_fields:
                if not getattr(profile, field, None):
                    missing_fields.append(field)

            # Calculate field statistics using same logic as model
            def is_field_filled(field_value):
                if field_value is None:
                    return False
                if isinstance(field_value, str):
                    return bool(field_value.strip())
                if isinstance(field_value, list):
                    return len(field_value) > 0
                if isinstance(field_value, bool):
                    return True  # Boolean fields are always considered "filled"
                return bool(field_value)

            profile_fields = [
                # Required fields
                profile.main_platform, profile.niche, profile.experience_level,
                profile.primary_goal, profile.time_available,

                # Important fields
                profile.specific_profession, profile.target_audience,
                profile.communication_tone, profile.expertise_areas,
                profile.preferred_duration, profile.complexity_level,
                profile.theme_diversity, profile.publication_frequency,

                # Optional fields
                profile.instagram_username, profile.linkedin_url,
                profile.twitter_username, profile.tiktok_username,
                profile.revenue_stage, profile.team_size, profile.revenue_goal,
                profile.authority_goal, profile.leads_goal, profile.has_designer,
                profile.current_tools, profile.tools_budget, profile.preferred_hours
            ]

            filled_fields = sum(
                1 for field in profile_fields if is_field_filled(field))
            filled_fields += 2  # Add user fields (name and email)
            total_fields = len(profile_fields) + 2

            data = {
                'onboarding_completed': profile.onboarding_completed,
                'completeness_percentage': profile.completeness_percentage,
                'required_fields_missing': missing_fields,
                'total_fields': total_fields,
                'filled_fields': filled_fields,
            }

            serializer = ProfileCompletionSerializer(data)
            return Response(serializer.data)

        except CreatorProfile.DoesNotExist:
            # Profile doesn't exist, onboarding required
            data = {
                'onboarding_completed': False,
                'completeness_percentage': 0,
                'required_fields_missing': [
                    'main_platform', 'niche', 'experience_level',
                    'primary_goal', 'time_available'
                ],
                'total_fields': 29,  # 27 profile fields + 2 user fields
                'filled_fields': 2,  # user.name and user.email
            }

            serializer = ProfileCompletionSerializer(data)
            return Response(serializer.data)


class OnboardingView(generics.CreateAPIView):
    """
    Handle onboarding form submission.
    Creates or updates profile with required fields only.
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
                    'message': 'Onboarding completado com sucesso!',
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
    Allow user to skip onboarding after required fields are completed.
    Only works if minimum required fields are already filled.
    """
    try:
        profile = CreatorProfile.objects.get(user=request.user)

        if not profile.onboarding_completed:
            return Response({
                'error': 'Campos obrigatórios não preenchidos',
                'message': 'Complete os campos obrigatórios antes de pular o onboarding',
                'required_fields': [
                    'main_platform', 'niche', 'experience_level',
                    'primary_goal', 'time_available'
                ]
            }, status=status.HTTP_400_BAD_REQUEST)

        # User can skip to main app
        return Response({
            'message': 'Onboarding pulado com sucesso!',
            'can_skip': True,
            'completeness_percentage': profile.completeness_percentage
        })

    except CreatorProfile.DoesNotExist:
        return Response({
            'error': 'Perfil não encontrado',
            'message': 'Complete o onboarding antes de pular',
            'can_skip': False
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_choices(request):
    """
    Get all available choices for profile fields.
    Used by frontend to populate select/radio options.
    """
    choices = {
        'platforms': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.PLATFORM_CHOICES
        ],
        'experience_levels': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.EXPERIENCE_CHOICES
        ],
        'goals': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.GOAL_CHOICES
        ],
        'time_options': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.TIME_CHOICES
        ],
        'communication_tones': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.TONE_CHOICES
        ],
        'content_durations': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.DURATION_CHOICES
        ],
        'complexity_levels': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.COMPLEXITY_CHOICES
        ],
        'frequencies': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.FREQUENCY_CHOICES
        ],
        'revenue_stages': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.REVENUE_CHOICES
        ],
        'team_sizes': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CreatorProfile.TEAM_CHOICES
        ],
    }

    return Response(choices)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_suggestions(request):
    """
    Get suggestions for profile fields based on popular choices.
    Used for autocomplete and quick selection.
    """

    # Popular niche suggestions based on specification
    niche_suggestions = [
        'Marketing jurídico',
        'Consultoria empresarial',
        'Coaching executivo',
        'Saúde e bem-estar',
        'Educação financeira',
        'Produtividade',
        'Empreendedorismo',
        'Tecnologia',
        'Marketing digital',
        'Recursos humanos',
        'Direito trabalhista',
        'Psicologia',
        'Nutrição',
        'Arquitetura',
        'Design gráfico',
    ]

    # Popular tools based on specification
    tool_suggestions = [
        'Canva',
        'Notion',
        'ChatGPT',
        'Figma',
        'Adobe Creative Suite',
        'Trello',
        'Buffer',
        'Hootsuite',
        'Later',
        'Mailchimp',
        'Google Analytics',
        'WordPress',
        'Shopify',
        'Zoom',
        'Slack',
    ]

    # Popular expertise areas
    expertise_suggestions = [
        'Estratégia de negócios',
        'Marketing de conteúdo',
        'Vendas consultivas',
        'Liderança',
        'Gestão de equipes',
        'Transformação digital',
        'Customer success',
        'Growth hacking',
        'SEO e SEM',
        'E-commerce',
        'Análise de dados',
        'Automação de processos',
        'Experiência do cliente',
        'Inovação',
        'Sustentabilidade',
    ]

    suggestions = {
        'niches': niche_suggestions,
        'tools': tool_suggestions,
        'expertise_areas': expertise_suggestions,
        'preferred_hours': [
            'Manhã (6h-12h)',
            'Tarde (12h-18h)',
            'Noite (18h-24h)',
            'Madrugada (0h-6h)',
        ]
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
