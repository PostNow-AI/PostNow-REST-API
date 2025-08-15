import json

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

        # Generate 3 ideas for the campaign
        ideas_data = gemini_service.generate_campaign_ideas(
            request.user, campaign_data)

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

        ideas_data = gemini_service.generate_campaign_ideas(
            user, config_data)

        # Return ideas without saving to database
        return Response({
            'message': 'Ideias geradas com sucesso!',
            'ideas': ideas_data,
            'note': 'Estas ideias não foram salvas. Crie uma conta para salvar suas ideias.',
            'api_key_used': 'user' if api_key else 'default'
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

        improved_idea_data = gemini_service.improve_idea(
            user=request.user,
            current_idea=idea,
            improvement_prompt=improvement_prompt,
            api_key=api_key
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
    """Generate a single idea using AI for an existing campaign."""
    try:
        # Check if campaign exists and belongs to user
        try:
            campaign = Campaign.objects.get(id=campaign_id, user=request.user)
        except Campaign.DoesNotExist:
            return Response(
                {'error': 'Campanha não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get idea generation parameters from request
        idea_params = {
            'title': request.data.get('title', ''),
            'description': request.data.get('description', ''),
            'content': request.data.get('content', ''),
            'platform': request.data.get('platform'),
            'content_type': request.data.get('content_type'),
            'variation_type': request.data.get('variation_type', 'a'),
        }

        # Debug logging
        print("=== DEBUG: Received idea_params ===")
        print(
            f"Platform: '{idea_params['platform']}' (type: {type(idea_params['platform'])})")
        print(
            f"Content Type: '{idea_params['content_type']}' (type: {type(idea_params['content_type'])})")
        print(
            f"Variation Type: '{idea_params['variation_type']}' (type: {type(idea_params['variation_type'])})")
        print(f"Raw request.data: {request.data}")
        print("=====================================")

        # Validate required fields
        platform = str(idea_params.get('platform', '')).strip()
        content_type = str(idea_params.get('content_type', '')).strip()
        variation_type = str(idea_params.get('variation_type', 'a')).strip()

        if not platform or not content_type:
            return Response(
                {'error': 'Plataforma e tipo de conteúdo são obrigatórios e não podem estar vazios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate content_type against model choices
        valid_content_types = ['post', 'story', 'reel',
                               'video', 'carousel', 'live', 'custom']
        if content_type not in valid_content_types:
            return Response(
                {'error': f'Tipo de conteúdo inválido. Valores permitidos: {", ".join(valid_content_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate platform against model choices
        valid_platforms = ['instagram', 'tiktok',
                           'youtube', 'linkedin', 'facebook', 'twitter']
        if platform not in valid_platforms:
            return Response(
                {'error': f'Plataforma inválida. Valores permitidos: {", ".join(valid_platforms)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate variation_type against model choices
        valid_variation_types = ['a', 'b', 'c']
        if variation_type not in valid_variation_types:
            return Response(
                {'error': f'Tipo de variação inválido. Valores permitidos: {", ".join(valid_variation_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use Gemini service to generate the idea
        from .gemini_service import GeminiService
        gemini_service = GeminiService()

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

        # Prepare campaign data for AI generation
        campaign_data = {
            'title': campaign.title,
            'description': campaign.description,
            'objectives': campaign.objectives,
            'platforms': campaign.platforms,
            'content_types': campaign.content_types,
            'voice_tone': campaign.voice_tone,
            'product_description': campaign.product_description,
            'value_proposition': campaign.value_proposition,
            'campaign_urgency': campaign.campaign_urgency,
            'persona_age': campaign.persona_age,
            'persona_location': campaign.persona_location,
            'persona_income': campaign.persona_income,
            'persona_interests': campaign.persona_interests,
            'persona_behavior': campaign.persona_behavior,
            'persona_pain_points': campaign.persona_pain_points,
        }

        if api_key:
            campaign_data['gemini_api_key'] = api_key

        # Generate idea using AI with the new single idea method
        print("=== DEBUG: Calling Gemini service for single idea ===")
        idea_data = gemini_service.generate_single_idea(
            request.user, campaign_data, idea_params)

        if not idea_data:
            print("=== DEBUG: No idea generated ===")
            return Response(
                {'error': 'Falha ao gerar ideia com IA'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        print(f"=== DEBUG: Generated idea data: {idea_data} ===")
        print(
            f"=== DEBUG: Content field from AI: '{idea_data.get('content', 'NOT_FOUND')}' ===")
        print(
            f"=== DEBUG: Title field from AI: '{idea_data.get('title', 'NOT_FOUND')}' ===")
        print(
            f"=== DEBUG: Description field from AI: '{idea_data.get('description', 'NOT_FOUND')}' ===")
        print(f"=== DEBUG: All AI fields: {list(idea_data.keys())} ===")
        print(f"=== DEBUG: AI data type: {type(idea_data)} ===")
        print(
            f"=== DEBUG: AI data length: {len(str(idea_data)) if idea_data else 'N/A'} ===")

        # Check if content is actually a string and not empty
        ai_content = idea_data.get('content', '')
        print(f"=== DEBUG: AI content type: {type(ai_content)} ===")
        print(
            f"=== DEBUG: AI content length: {len(str(ai_content)) if ai_content else 0} ===")
        print(f"=== DEBUG: AI content is empty: {not ai_content} ===")
        print(
            f"=== DEBUG: AI content is dict: {isinstance(ai_content, dict)} ===")
        print(
            f"=== DEBUG: AI content keys: {list(ai_content.keys()) if isinstance(ai_content, dict) else 'N/A'} ===")

        # Check if variations exist in the content
        if isinstance(ai_content, dict):
            variations = ai_content.get('variacao_a', {})
            print(
                f"=== DEBUG: Variation A keys: {list(variations.keys()) if variations else 'N/A'} ===")
            print(
                f"=== DEBUG: Variation A headline: '{variations.get('headline', 'NOT_FOUND')}' ===")
            print(
                f"=== DEBUG: Variation A copy length: {len(str(variations.get('copy', '')))} ===")

        # Validate that AI generated essential content
        ai_content = idea_data.get('content', {})
        user_content = idea_params.get('content', '')

        # Check if we have valid content from AI or user
        has_valid_content = False

        if ai_content and isinstance(ai_content, dict):
            has_valid_content = True
            print("=== DEBUG: AI generated valid content object ===")
        elif user_content and isinstance(user_content, str):
            try:
                json.loads(user_content)
                has_valid_content = True
                print("=== DEBUG: User provided valid JSON content ===")
            except json.JSONDecodeError:
                print("=== DEBUG: User content is not valid JSON ===")

        if not has_valid_content:
            print("=== DEBUG: No valid content generated by AI or provided by user ===")
            return Response(
                {'error': 'A IA não conseguiu gerar conteúdo válido. Tente novamente ou forneça o conteúdo em formato JSON válido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the CampaignIdea object
        print("=== DEBUG: Creating CampaignIdea object ===")
        try:
            # Ensure we have content - prioritize AI-generated content over user input
            final_title = idea_data.get(
                'title', '') or idea_params['title'] or 'Título Gerado por IA'
            final_description = idea_data.get(
                'description', '') or idea_params['description'] or 'Descrição Gerada por IA'

            # Handle content field - it should be a JSON object, not a string
            ai_content = idea_data.get('content', {})
            user_content = idea_params.get('content', '')

            # If user provided content as string, try to parse it as JSON
            if user_content and isinstance(user_content, str):
                try:
                    user_content_parsed = json.loads(user_content)
                    final_content = json.dumps(
                        user_content_parsed, ensure_ascii=False)
                except json.JSONDecodeError:
                    # If user content is not valid JSON, use AI content
                    final_content = json.dumps(
                        ai_content, ensure_ascii=False) if ai_content else '{}'
            else:
                # Use AI content or empty JSON object
                final_content = json.dumps(
                    ai_content, ensure_ascii=False) if ai_content else '{}'

            print(f"=== DEBUG: Final title: '{final_title}' ===")
            print(f"=== DEBUG: Final description: '{final_description}' ===")
            print(f"=== DEBUG: Final content (JSON): '{final_content}' ===")

            idea = CampaignIdea.objects.create(
                campaign=campaign,
                title=final_title,
                description=final_description,
                content=final_content,  # This should be a JSON string
                platform=platform,  # Use validated platform
                content_type=content_type,  # Use validated content_type
                variation_type=variation_type,
                # Extract data from the first variation (variacao_a) for the main fields
                headline=idea_data.get('content', {}).get('variacao_a', {}).get(
                    'headline', '') or idea_data.get('headline', ''),
                copy=idea_data.get('content', {}).get('variacao_a', {}).get(
                    'copy', '') or idea_data.get('copy', ''),
                cta=idea_data.get('content', {}).get('variacao_a', {}).get(
                    'cta', '') or idea_data.get('cta', ''),
                hashtags=idea_data.get('content', {}).get('variacao_a', {}).get(
                    'hashtags', []) or idea_data.get('hashtags', []),
                visual_description=idea_data.get('content', {}).get('variacao_a', {}).get(
                    'visual_description', '') or idea_data.get('visual_description', ''),
                color_composition=idea_data.get('content', {}).get('variacao_a', {}).get(
                    'color_composition', '') or idea_data.get('color_composition', ''),
            )
            print(
                f"=== DEBUG: CampaignIdea created successfully: {idea.id} ===")
        except Exception as create_error:
            print(
                f"=== DEBUG: Error creating CampaignIdea: {str(create_error)} ===")
            raise create_error

        return Response(
            CampaignIdeaSerializer(idea).data,
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        print(f"=== DEBUG: Exception caught: {str(e)} ===")
        print(f"=== DEBUG: Exception type: {type(e)} ===")
        import traceback
        print(f"=== DEBUG: Traceback: {traceback.format_exc()} ===")
        return Response(
            {'error': f'Erro ao gerar ideia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Legacy views for backward compatibility
# Removed problematic legacy views that were causing type conflicts
