from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .gemini_service import GeminiService
from .models import Campaign, CampaignIdea, VoiceTone
from .serializers import (
    CampaignDetailSerializer,
    CampaignIdeaSerializer,
    CampaignIdeaUpdateSerializer,
    CampaignSerializer,
    IdeaGenerationRequestSerializer,
)


class CampaignListView(generics.ListCreateAPIView):
    """List and create campaigns."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignSerializer

    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete campaigns."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignDetailSerializer

    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user)


class CampaignIdeaListView(generics.ListCreateAPIView):
    """List and create campaign ideas."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignIdeaSerializer

    def get_queryset(self):
        campaign_id = self.kwargs.get('campaign_id')
        if campaign_id:
            return CampaignIdea.objects.filter(
                campaign_id=campaign_id,
                campaign__user=self.request.user
            )
        return CampaignIdea.objects.filter(
            campaign__user=self.request.user
        )

    def perform_create(self, serializer):
        campaign_id = self.kwargs.get('campaign_id')
        campaign = Campaign.objects.get(id=campaign_id, user=self.request.user)
        serializer.save(campaign=campaign)


class CampaignIdeaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete campaign ideas."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignIdeaUpdateSerializer

    def get_queryset(self):
        return CampaignIdea.objects.filter(
            campaign__user=self.request.user
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_campaign_ideas(request):
    """Generate campaign ideas using Gemini AI with the new structure."""
    serializer = IdeaGenerationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Create campaign first
        campaign_data = serializer.validated_data.copy()
        campaign = Campaign.objects.create(
            user=request.user,
            **campaign_data
        )

        # Generate ideas using Gemini
        gemini_service = GeminiService()
        ideas_data = gemini_service.generate_campaign_ideas(
            request.user, campaign_data)

        # Create a single CampaignIdea per platform (store variations inside content JSON)
        ideas = []
        for idea_data in ideas_data:
            main_idea = CampaignIdea.objects.create(
                campaign=campaign,
                title=idea_data['title'],
                description=idea_data['description'],
                # Full JSON content includes variacao_a/b/c
                content=idea_data['content'],
                platform=idea_data['platform'],
                content_type=idea_data['content_type'],
                variation_type='a',
                headline=idea_data.get('variations', [{}])[0].get(
                    'headline', '') if idea_data.get('variations') else '',
                copy=idea_data.get('variations', [{}])[0].get(
                    'copy', '') if idea_data.get('variations') else '',
                cta=idea_data.get('variations', [{}])[0].get(
                    'cta', '') if idea_data.get('variations') else '',
                hashtags=idea_data.get('variations', [{}])[0].get(
                    'hashtags', []) if idea_data.get('variations') else [],
                visual_description=idea_data.get('variations', [{}])[0].get(
                    'visual_description', '') if idea_data.get('variations') else '',
                color_composition=idea_data.get('variations', [{}])[0].get(
                    'color_composition', '') if idea_data.get('variations') else ''
            )
            ideas.append(main_idea)

        # Serialize response
        campaign_serializer = CampaignSerializer(campaign)
        ideas_serializer = CampaignIdeaSerializer(ideas, many=True)

        return Response({
            'message': 'Campanha e ideias geradas com sucesso!',
            'campaign': campaign_serializer.data,
            'ideas': ideas_serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Erro na geração de campanhas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([])  # No authentication required
def generate_public_ideas(request):
    """Generate campaign ideas for public users without authentication."""
    serializer = IdeaGenerationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Generate ideas using Gemini without saving to database
        gemini_service = GeminiService()
        ideas_data = gemini_service.generate_campaign_ideas(
            None, serializer.validated_data)

        # Return ideas without saving to database
        return Response({
            'message': 'Ideias geradas com sucesso!',
            'ideas': ideas_data,
            'note': 'Estas ideias não foram salvas. Crie uma conta para salvar suas ideias.'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Erro na geração de ideias: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_campaign_stats(request):
    """Get statistics about user's campaigns and ideas."""
    total_campaigns = Campaign.objects.filter(user=request.user).count()
    active_campaigns = Campaign.objects.filter(
        user=request.user, status='active').count()
    draft_campaigns = Campaign.objects.filter(
        user=request.user, status='draft').count()
    completed_campaigns = Campaign.objects.filter(
        user=request.user, status='completed').count()

    total_ideas = CampaignIdea.objects.filter(
        campaign__user=request.user).count()
    approved_ideas = CampaignIdea.objects.filter(
        campaign__user=request.user, status='approved').count()
    draft_ideas = CampaignIdea.objects.filter(
        campaign__user=request.user, status='draft').count()

    return Response({
        'campaigns': {
            'total': total_campaigns,
            'active': active_campaigns,
            'draft': draft_campaigns,
            'completed': completed_campaigns,
        },
        'ideas': {
            'total': total_ideas,
            'approved': approved_ideas,
            'draft': draft_ideas,
        }
    })


@api_view(['GET'])
@permission_classes([])  # No authentication required
def get_public_options(request):
    """Get available options for idea generation (public endpoint)."""
    from .models import CampaignObjective, SocialPlatform

    # Define content types available for each platform
    platform_content_types = {
        'instagram': ['post', 'story', 'reel', 'carousel', 'live'],
        'tiktok': ['video', 'live'],
        'youtube': ['video', 'live'],
        'linkedin': ['post', 'carousel', 'video', 'live'],
    }

    return Response({
        'objectives': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CampaignObjective.choices
        ],
        'content_types': platform_content_types,
        'platforms': [
            {'value': choice[0], 'label': choice[1]}
            for choice in SocialPlatform.choices
        ],
        'voice_tones': [
            {'value': choice[0], 'label': choice[1]}
            for choice in VoiceTone.choices
        ]
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_available_options(request):
    """Get available options for idea generation."""
    from .models import CampaignObjective, SocialPlatform

    # Define content types available for each platform
    platform_content_types = {
        'instagram': ['post', 'story', 'reel', 'carousel', 'live'],
        'tiktok': ['video', 'live'],
        'youtube': ['video', 'live'],
        'linkedin': ['post', 'carousel', 'video', 'live'],
    }

    return Response({
        'objectives': [
            {'value': choice[0], 'label': choice[1]}
            for choice in CampaignObjective.choices
        ],
        'content_types': platform_content_types,
        'platforms': [
            {'value': choice[0], 'label': choice[1]}
            for choice in SocialPlatform.choices
        ],
        'voice_tones': [
            {'value': choice[0], 'label': choice[1]}
            for choice in VoiceTone.choices
        ]
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def improve_idea(request, idea_id):
    """Improve an existing campaign idea using AI."""
    try:
        # Get the idea
        idea = CampaignIdea.objects.get(
            id=idea_id, campaign__user=request.user)
    except CampaignIdea.DoesNotExist:
        return Response(
            {'error': 'Ideia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    improvement_prompt = request.data.get('improvement_prompt')
    if not improvement_prompt:
        return Response(
            {'error': 'Prompt de melhoria é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Use Gemini to improve the idea
        gemini_service = GeminiService()
        improved_idea_data = gemini_service.improve_idea(
            user=request.user,
            current_idea=idea,
            improvement_prompt=improvement_prompt
        )

        # Update the idea with improved content
        idea.title = improved_idea_data.get('title', idea.title)
        idea.description = improved_idea_data.get(
            'description', idea.description)
        idea.content = improved_idea_data.get('content', idea.content)
        idea.status = 'draft'  # Set status to draft after improvement
        idea.save()

        # Serialize and return updated idea
        serializer = CampaignIdeaSerializer(idea)
        return Response({
            'message': 'Ideia melhorada com sucesso!',
            'idea': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Erro ao melhorar ideia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Legacy views for backward compatibility
# Removed problematic legacy views that were causing type conflicts
