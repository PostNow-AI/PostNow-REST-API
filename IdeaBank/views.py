
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .gemini_service import GeminiService
from .models import Campaign, CampaignIdea, CampaignObjective, SocialPlatform, VoiceTone
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
    """Generate campaign ideas using Gemini AI with the new structure and progress tracking."""
    serializer = IdeaGenerationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Create campaign first
        campaign_data = serializer.validated_data.copy()

        # Generate automatic title if none provided
        if not campaign_data.get('title') or campaign_data['title'].strip() == '':
            # Create a descriptive title based on objectives and platforms
            objectives = campaign_data.get('objectives', [])
            platforms = campaign_data.get('platforms', [])

            if objectives and platforms:
                objective_names = [dict(CampaignObjective.choices)[
                    obj] for obj in objectives if obj in dict(CampaignObjective.choices)]
                platform_names = [dict(SocialPlatform.choices)[
                    plat] for plat in platforms if plat in dict(SocialPlatform.choices)]

                if objective_names and platform_names:
                    campaign_data['title'] = f"Campanha de {', '.join(objective_names[:2])} para {', '.join(platform_names[:2])}"
                else:
                    campaign_data['title'] = "Campanha Gerada por IA"
            else:
                campaign_data['title'] = "Campanha Gerada por IA"

        campaign = Campaign.objects.create(
            user=request.user,
            **campaign_data
        )

        # Generate ideas using Gemini with progress tracking
        gemini_service = GeminiService()

        # Inject user's Gemini API key if present
        try:
            from APIKeys.models import UserAPIKey
            user_key = UserAPIKey.objects.filter(
                user=request.user, provider='gemini').first()
            if user_key:
                campaign_data['gemini_api_key'] = user_key.api_key
        except ImportError:
            # APIKeys app not available, continue without user key
            pass

        # Progress tracking function
        def progress_callback(progress_data):
            # In a real implementation, you might want to send this via WebSocket
            # or store it in a cache for the frontend to poll
            print(
                f"Progress: {progress_data['percentage']}% - {progress_data['current_step_name']}")

        # Generate 3 ideas for the campaign with progress
        ideas_data, final_progress = gemini_service.generate_campaign_ideas_with_progress(
            request.user, campaign_data, progress_callback)

        # Create 3 CampaignIdea objects (variations A, B, C)
        ideas = []
        variation_types = ['a', 'b', 'c']

        for i, idea_data in enumerate(ideas_data):
            if i >= 3:  # Ensure we only create 3 ideas
                break

            variation_type = variation_types[i]

            # Get variation content if available, otherwise use main content
            variations = idea_data.get('variations', [])
            variation_content = variations[i] if i < len(variations) else {}

            idea = CampaignIdea.objects.create(
                campaign=campaign,
                title=idea_data['title'],
                description=idea_data['description'],
                content=idea_data['content'],
                platform=idea_data['platform'],
                content_type=idea_data['content_type'],
                variation_type=variation_type,
                headline=variation_content.get('headline', ''),
                copy=variation_content.get('copy', ''),
                cta=variation_content.get('cta', ''),
                hashtags=variation_content.get('hashtags', []),
                visual_description=variation_content.get(
                    'visual_description', ''),
                color_composition=variation_content.get(
                    'color_composition', '')
            )
            ideas.append(idea)

        # Serialize response
        campaign_serializer = CampaignSerializer(campaign)
        ideas_serializer = CampaignIdeaSerializer(ideas, many=True)

        return Response({
            'message': 'Campanha e 3 ideias geradas com sucesso!',
            'campaign': campaign_serializer.data,
            'ideas': ideas_serializer.data,
            'progress': final_progress
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Erro na geração de campanhas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([])  # No authentication required
def generate_public_ideas(request):
    """Generate campaign ideas for public users without authentication with progress tracking."""
    serializer = IdeaGenerationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Check if user is authenticated and has API key
        user = request.user if request.user.is_authenticated else None
        api_key = None

        if user:
            try:
                from APIKeys.models import UserAPIKey
                user_key = UserAPIKey.objects.filter(
                    user=user, provider='gemini').first()
                if user_key:
                    api_key = user_key.api_key
            except ImportError:
                # APIKeys app not available, continue without user key
                pass

        # Generate ideas using Gemini without saving to database
        gemini_service = GeminiService()

        # Add API key to config if user has one
        config_data = serializer.validated_data.copy()
        if api_key:
            config_data['gemini_api_key'] = api_key

        # Progress tracking function
        def progress_callback(progress_data):
            print(
                f"Public Progress: {progress_data['percentage']}% - {progress_data['current_step_name']}")

        ideas_data, final_progress = gemini_service.generate_campaign_ideas_with_progress(
            user, config_data, progress_callback)

        # Return ideas without saving to database
        return Response({
            'message': 'Ideias geradas com sucesso!',
            'ideas': ideas_data,
            'progress': final_progress
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
    """Improve an existing campaign idea using AI with progress tracking."""
    try:
        # Get the idea
        idea = CampaignIdea.objects.get(
            id=idea_id, campaign__user=request.user)

        # Get improvement prompt
        improvement_prompt = request.data.get('improvement_prompt', '')
        if not improvement_prompt:
            return Response(
                {'error': 'Prompt de melhoria é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user's Gemini API key if present
        api_key = None
        try:
            from APIKeys.models import UserAPIKey
            user_key = UserAPIKey.objects.filter(
                user=request.user, provider='gemini').first()
            if user_key:
                api_key = user_key.api_key
        except ImportError:
            # APIKeys app not available, continue without user key
            pass

        # Improve idea using Gemini with progress tracking
        gemini_service = GeminiService()

        # Progress tracking function
        def progress_callback(progress_data):
            print(
                f"Idea Improvement Progress: {progress_data['percentage']}% - {progress_data['current_step_name']}")

        improved_data, final_progress = gemini_service.improve_idea_with_progress(
            request.user, idea, improvement_prompt, api_key, progress_callback)

        if improved_data:
            # Update the idea with improved content
            idea.title = improved_data.get('title', idea.title)
            idea.description = improved_data.get(
                'description', idea.description)
            idea.content = improved_data.get('content', idea.content)
            idea.save()

            # Serialize response
            idea_serializer = CampaignIdeaSerializer(idea)

            return Response({
                'message': 'Ideia melhorada com sucesso!',
                'idea': idea_serializer.data,
                'progress': final_progress
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Erro ao melhorar ideia: Falha na melhoria'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except CampaignIdea.DoesNotExist:
        return Response(
            {'error': 'Ideia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erro ao melhorar ideia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def campaigns_with_ideas(request):
    """Get all campaigns with their ideas grouped as children."""
    try:
        campaigns = Campaign.objects.filter(
            user=request.user).prefetch_related('ideas')

        result = []
        for campaign in campaigns:
            campaign_data = CampaignSerializer(campaign).data
            campaign_data['ideas'] = CampaignIdeaSerializer(
                campaign.ideas.all(), many=True).data
            result.append(campaign_data)

        return Response({
            'campaigns': result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Erro ao buscar campanhas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_idea_to_campaign(request, campaign_id):
    """Add a new idea to an existing campaign."""
    try:
        # Check if campaign exists and belongs to user
        try:
            campaign = Campaign.objects.get(id=campaign_id, user=request.user)
        except Campaign.DoesNotExist:
            return Response(
                {'error': 'Campanha não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate required fields
        required_fields = ['title', 'platform', 'content_type']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {'error': f'Campo obrigatório: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create the new idea
        idea_data = {
            'campaign': campaign,
            'title': request.data.get('title'),
            'description': request.data.get('description', ''),
            'content': request.data.get('content', ''),
            'platform': request.data.get('platform'),
            'content_type': request.data.get('content_type'),
            'variation_type': request.data.get('variation_type', ''),
            'headline': request.data.get('headline', ''),
            'copy': request.data.get('copy', ''),
            'cta': request.data.get('cta', ''),
            'hashtags': request.data.get('hashtags', []),
            'visual_description': request.data.get('visual_description', ''),
            'color_composition': request.data.get('color_composition', ''),
        }

        idea = CampaignIdea.objects.create(**idea_data)

        return Response(
            CampaignIdeaSerializer(idea).data,
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {'error': f'Erro ao criar ideia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_single_idea(request, campaign_id):
    """Generate a single idea for an existing campaign with progress tracking."""
    try:
        # Get campaign
        campaign = Campaign.objects.get(id=campaign_id, user=request.user)

        # Get idea parameters
        platform = request.data.get('platform', 'instagram')
        content_type = request.data.get('content_type', 'post')
        variation_type = request.data.get('variation_type', 'a')

        # Optional pre-filled content
        title = request.data.get('title', '')
        description = request.data.get('description', '')
        content = request.data.get('content', '')

        # Validate required fields
        if not platform or not content_type:
            return Response(
                {'error': 'Plataforma e tipo de conteúdo são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare campaign data
        campaign_data = {
            'title': campaign.title,
            'description': campaign.description,
            'objectives': campaign.objectives,
            'persona_age': campaign.persona_age,
            'persona_location': campaign.persona_location,
            'persona_income': campaign.persona_income,
            'persona_interests': campaign.persona_interests,
            'persona_behavior': campaign.persona_behavior,
            'persona_pain_points': campaign.persona_pain_points,
            'platforms': campaign.platforms,
            'content_types': campaign.content_types,
            'voice_tone': campaign.voice_tone,
            'product_description': campaign.product_description,
            'value_proposition': campaign.value_proposition,
            'campaign_urgency': campaign.campaign_urgency,
        }

        # Inject user's Gemini API key if present
        try:
            from APIKeys.models import UserAPIKey
            user_key = UserAPIKey.objects.filter(
                user=request.user, provider='gemini').first()
            if user_key:
                campaign_data['gemini_api_key'] = user_key.api_key
        except ImportError:
            # APIKeys app not available, continue without user key
            pass

        # Prepare idea parameters
        idea_params = {
            'platform': platform,
            'content_type': content_type,
            'variation_type': variation_type,
            'title': title,
            'description': description,
            'content': content,
        }

        # Generate idea using Gemini with progress tracking
        gemini_service = GeminiService()

        # Progress tracking function
        def progress_callback(progress_data):
            print(
                f"Single Idea Progress: {progress_data['percentage']}% - {progress_data['current_step_name']}")

        generated_idea, final_progress = gemini_service.generate_single_idea_with_progress(
            request.user, campaign_data, idea_params, progress_callback)

        if generated_idea:
            # Debug logging
            print("=== DEBUG: Generated idea content ===")
            print(f"Content type: {type(generated_idea.get('content'))}")
            print(f"Content value: {generated_idea.get('content')}")
            print(
                f"Content length: {len(str(generated_idea.get('content', '')))}")

            # Create the idea in the database
            idea = CampaignIdea.objects.create(
                campaign=campaign,
                title=generated_idea.get('title', f'Ideia para {platform}'),
                description=generated_idea.get('description', ''),
                content=generated_idea.get('content', ''),
                platform=platform,
                content_type=content_type,
                variation_type=variation_type,
                headline=generated_idea.get('headline', ''),
                copy=generated_idea.get('copy', ''),
                cta=generated_idea.get('cta', ''),
                hashtags=generated_idea.get('hashtags', []),
                visual_description=generated_idea.get(
                    'visual_description', ''),
                color_composition=generated_idea.get('color_composition', '')
            )

            # Serialize response
            idea_serializer = CampaignIdeaSerializer(idea)

            return Response({
                'message': 'Ideia gerada com sucesso!',
                'idea': idea_serializer.data,
                'progress': final_progress
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'Erro ao gerar ideia: Falha na geração'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Campaign.DoesNotExist:
        return Response(
            {'error': 'Campanha não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erro ao gerar ideia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Legacy views for backward compatibility
# Removed problematic legacy views that were causing type conflicts
