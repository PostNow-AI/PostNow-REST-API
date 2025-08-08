from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .gemini_service import GeminiService
from .models import CampaignIdea, IdeaGenerationConfig
from .serializers import (
    CampaignIdeaSerializer,
    CampaignIdeaUpdateSerializer,
    IdeaGenerationConfigSerializer,
    IdeaGenerationRequestSerializer,
)


class CampaignIdeaListView(generics.ListCreateAPIView):
    """List and create campaign ideas."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignIdeaSerializer

    def get_queryset(self):
        return CampaignIdea.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CampaignIdeaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete campaign ideas."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignIdeaUpdateSerializer

    def get_queryset(self):
        return CampaignIdea.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_ideas(request):
    """Generate campaign ideas using Gemini AI."""
    serializer = IdeaGenerationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Save configuration
        config_data = serializer.validated_data.copy()
        config = IdeaGenerationConfig.objects.create(
            user=request.user,
            **config_data
        )

        # Generate ideas using Gemini
        gemini_service = GeminiService()
        ideas_data = gemini_service.generate_ideas(request.user, config_data)

        # Create campaign ideas
        ideas = []
        for idea_data in ideas_data:
            idea = CampaignIdea.objects.create(
                user=request.user,
                config=config,
                **idea_data
            )
            ideas.append(idea)

        # Serialize response
        ideas_serializer = CampaignIdeaSerializer(ideas, many=True)
        config_serializer = IdeaGenerationConfigSerializer(config)

        return Response({
            'message': 'Ideias geradas com sucesso!',
            'ideas': ideas_serializer.data,
            'config': config_serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Erro na geração de ideias: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_idea_stats(request):
    """Get statistics about user's ideas."""
    total_ideas = CampaignIdea.objects.filter(user=request.user).count()
    draft_ideas = CampaignIdea.objects.filter(
        user=request.user, status='draft').count()
    approved_ideas = CampaignIdea.objects.filter(
        user=request.user, status='approved').count()
    archived_ideas = CampaignIdea.objects.filter(
        user=request.user, status='archived').count()

    return Response({
        'total_ideas': total_ideas,
        'draft_ideas': draft_ideas,
        'approved_ideas': approved_ideas,
        'archived_ideas': archived_ideas
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_available_options(request):
    """Get available options for idea generation."""
    from .models import CampaignObjective, ContentType, SocialPlatform

    return Response({
        'objectives': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CampaignObjective.choices
        ],
        'content_types': [
            {'value': choice[0], 'label': choice[1]}
            for choice in ContentType.choices
        ],
        'platforms': [
            {'value': choice[0], 'label': choice[1]}
            for choice in SocialPlatform.choices
        ]
    })
