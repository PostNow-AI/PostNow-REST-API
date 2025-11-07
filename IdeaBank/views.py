"""
New Post-based views for IdeaBank app.
"""

import asyncio
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Post, PostIdea, PostObjective, PostType
from .serializers import (
    ImageGenerationRequestSerializer,
    PostCreateSerializer,
    PostGenerationRequestSerializer,
    PostIdeaEditRequestSerializer,
    PostIdeaSerializer,
    PostOptionsSerializer,
    PostSerializer,
    PostWithIdeasSerializer,
)
from .services.daily_content_service import DailyContentService
from .services.post_ai_service import PostAIService

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination class for consistent pagination across the API."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PostListView(generics.ListCreateAPIView):
    """List and create posts with pagination."""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Override create to provide consistent response format."""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error creating post for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Erro ao criar post', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete posts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Override update to provide consistent response format."""
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error updating post {kwargs.get('pk')} for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Erro ao atualizar post', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Override destroy to provide consistent response format."""
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error deleting post {kwargs.get('pk')} for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Erro ao deletar post', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PostWithIdeasView(generics.RetrieveAPIView):
    """Retrieve a post with all its ideas."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostWithIdeasSerializer

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).prefetch_related('ideas')


class PostIdeaListView(generics.ListAPIView):
    """List post ideas for a specific post with pagination."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostIdeaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return PostIdea.objects.filter(
            post_id=post_id,
            post__user=self.request.user
        ).order_by('-created_at')


class PostIdeaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete post ideas."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostIdeaSerializer

    def get_queryset(self):
        return PostIdea.objects.filter(post__user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Override update to provide consistent response format."""
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error updating post idea {kwargs.get('pk')} for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Erro ao atualizar ideia', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Override destroy to provide consistent response format."""
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error deleting post idea {kwargs.get('pk')} for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Erro ao deletar ideia', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_post_idea(request):
    """Generate a post idea using AI based on post specifications."""
    serializer = PostGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(
            f"Invalid data for post generation by user {request.user.id}: {serializer.errors}")
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        post_data = serializer.validated_data
        include_image = post_data.get('include_image', False)

        # Create the post
        post = Post.objects.create(user=request.user, **post_data)

        # Generate content using AI service
        post_ai_service = PostAIService()
        result = post_ai_service.generate_post_content(
            user=request.user,
            post_data=post_data,
        )

        # Create the post idea with generated content
        post_idea = PostIdea.objects.create(
            post=post,
            content=result['content']
        )

        # Generate image if requested
        if include_image:
            try:
                post_data_with_ids = {
                    **post_data,
                    'post_id': post.id,
                    'post_idea_id': post_idea.id,
                    'post': post
                }

                image_url = post_ai_service.generate_image_for_post(
                    user=request.user,
                    post_data=post_data_with_ids,
                    content=result['content'],
                    custom_prompt=None,
                    regenerate=False
                )
                post_idea.image_url = image_url
                post_idea.save()
            except Exception as image_error:
                logger.warning(
                    f"Failed to generate image for post {post.id}: {image_error}")
                # Continue without image - don't fail the entire request

        # Serialize the response
        post_serializer = PostSerializer(post)
        idea_serializer = PostIdeaSerializer(post_idea)

        logger.info(
            f"Successfully generated post and idea for user {request.user.id}")
        return Response({
            'message': 'Post e ideia gerados com sucesso!',
            'post': post_serializer.data,
            'idea': idea_serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(
            f"Error generating post idea for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Erro na geração do post', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_image_for_idea(request, idea_id):
    """Generate an image for an existing post idea."""
    try:
        post_idea = PostIdea.objects.get(
            id=idea_id,
            post__user=request.user
        )
    except PostIdea.DoesNotExist:
        logger.warning(
            f"Post idea {idea_id} not found for user {request.user.id}")
        return Response(
            {'error': 'Ideia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ImageGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(
            f"Invalid data for image generation by user {request.user.id}: {serializer.errors}")
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        custom_prompt = serializer.validated_data.get('prompt')

        post_data = {
            'name': post_idea.post.name,
            'objective': post_idea.post.objective,
            'type': post_idea.post.type,
            'further_details': post_idea.post.further_details,
            'include_image': post_idea.post.include_image,
            'post_id': post_idea.post.id,
            'post_idea_id': post_idea.id,
            'post': post_idea.post
        }

        post_ai_service = PostAIService()
        image_url = post_ai_service.generate_image_for_post(
            user=request.user,
            post_data=post_data,
            content=post_idea.content,
            custom_prompt=custom_prompt,
            regenerate=False
        )

        post_idea.image_url = image_url
        post_idea.save()

        logger.info(
            f"Successfully generated image for idea {idea_id} by user {request.user.id}")
        return Response({
            'message': 'Imagem gerada com sucesso!',
            'image_url': image_url,
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            f"Error generating image for idea {idea_id} by user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Erro na geração da imagem', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def edit_post_idea(request, idea_id):
    """Edit/regenerate a post idea with optional AI assistance."""
    try:
        post_idea = PostIdea.objects.get(
            id=idea_id,
            post__user=request.user
        )
    except PostIdea.DoesNotExist:
        logger.warning(
            f"Post idea {idea_id} not found for user {request.user.id}")
        return Response(
            {'error': 'Ideia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PostIdeaEditRequestSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(
            f"Invalid data for idea edit by user {request.user.id}: {serializer.errors}")
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user_prompt = serializer.validated_data.get('prompt')
        ai_provider = serializer.validated_data.get(
            'preferred_provider', 'google')
        ai_model = serializer.validated_data.get(
            'preferred_model', 'gemini-2.5-flash')

        post_data = {
            'name': post_idea.post.name,
            'objective': post_idea.post.objective,
            'type': post_idea.post.type,
            'further_details': post_idea.post.further_details,
            'include_image': post_idea.post.include_image,
        }

        post_ai_service = PostAIService()
        result = post_ai_service.regenerate_post_content(
            user=request.user,
            post_data=post_data,
            current_content=post_idea.content,
            user_prompt=user_prompt,
            ai_provider=ai_provider,
            ai_model=ai_model
        )

        post_idea.content = result['content']
        post_idea.save()

        logger.info(
            f"Successfully edited idea {idea_id} by user {request.user.id}")
        return Response({
            'message': 'Ideia editada com sucesso!',
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            f"Error editing idea {idea_id} by user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Erro na edição da ideia', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def regenerate_image_for_idea(request, idea_id):
    """Regenerate the image for a post idea with optional custom prompt."""
    try:
        post_idea = PostIdea.objects.get(
            id=idea_id,
            post__user=request.user
        )
    except PostIdea.DoesNotExist:
        logger.warning(
            f"Post idea {idea_id} not found for user {request.user.id}")
        return Response(
            {'error': 'Ideia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ImageGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(
            f"Invalid data for image regeneration by user {request.user.id}: {serializer.errors}")
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        custom_prompt = serializer.validated_data.get('prompt')

        post_data = {
            'name': post_idea.post.name,
            'objective': post_idea.post.objective,
            'type': post_idea.post.type,
            'further_details': post_idea.post.further_details,
            'include_image': post_idea.post.include_image,
            'post_id': post_idea.post.id,
            'post_idea_id': post_idea.id,
            'post': post_idea.post
        }

        post_ai_service = PostAIService()
        image_url = post_ai_service.generate_image_for_post(
            user=request.user,
            post_data=post_data,
            content=post_idea.content,
            custom_prompt=custom_prompt,
            regenerate=True
        )

        post_idea.image_url = image_url
        post_idea.save()

        logger.info(
            f"Successfully regenerated image for idea {idea_id} by user {request.user.id}")
        return Response({
            'message': 'Imagem regenerada com sucesso!',
            'image_url': image_url,
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            f"Error regenerating image for idea {idea_id} by user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Erro na regeneração da imagem', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_post_options(request):
    """Get available options for post creation."""
    try:
        options = {
            'objectives': [
                {'value': choice[0], 'label': choice[1]}
                for choice in PostObjective.choices
            ],
            'types': [
                {'value': choice[0], 'label': choice[1]}
                for choice in PostType.choices
            ]
        }

        serializer = PostOptionsSerializer(options)
        return Response(serializer.data)
    except Exception as e:
        logger.error(
            f"Error getting post options for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Erro ao buscar opções', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_posts_with_ideas(request):
    """Get all user posts with their ideas."""
    try:
        posts = Post.objects.filter(
            user=request.user).prefetch_related('ideas')
        serializer = PostWithIdeasSerializer(posts, many=True)

        return Response({
            'posts': serializer.data,
            'total_posts': posts.count(),
            'total_ideas': sum(post.ideas.count() for post in posts)
        })
    except Exception as e:
        logger.error(
            f"Error getting user posts with ideas for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Erro ao buscar posts', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_post_stats(request):
    """Get statistics about user's posts and ideas."""
    try:
        total_posts = Post.objects.filter(user=request.user).count()
        total_ideas = PostIdea.objects.filter(post__user=request.user).count()

        # Count by post type
        post_types = {}
        for post_type, display_name in PostType.choices:
            count = Post.objects.filter(
                user=request.user, type=post_type).count()
            if count > 0:
                post_types[display_name] = count

        return Response({
            'total_posts': total_posts,
            'total_ideas': total_ideas,
            'post_types_distribution': post_types
        })
    except Exception as e:
        logger.error(
            f"Error getting post stats for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Erro ao buscar estatísticas', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@require_http_methods(["GET"])
def vercel_cron_daily_content_generation(request):
    """
    Vercel Cron endpoint for daily content generation
    Called automatically by Vercel at scheduled time
    """
    # Verify it's from Vercel (security check)
    auth_header = request.headers.get('Authorization', '')
    expected_auth = f"Bearer {settings.CRON_SECRET}"

    if auth_header != expected_auth:
        logger.warning("Unauthorized attempt to access cron endpoint")
        return JsonResponse({
            'error': 'Unauthorized'
        }, status=401)

    try:
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 5  # Process 5 users per batch, to avoid vercel timeouts

        service = DailyContentService()

        # Use asyncio to run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                service.process_users_batch_async(batch_number, batch_size)
            )
        finally:
            loop.close()

        logger.info(
            f"Successfully processed batch {batch_number} for daily content generation")
        return JsonResponse(result, status=200)

    except Exception as e:
        logger.error(f"Vercel cron job failed: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def manual_trigger_daily_generation(request):
    """
    Manual trigger for daily content generation (for testing)
    """
    try:
        service = DailyContentService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                service.process_all_users_async()
            )
        finally:
            loop.close()

        logger.info("Successfully completed manual daily content generation")
        return JsonResponse({
            'message': 'Daily content generation completed',
            'result': result
        }, status=200)

    except Exception as e:
        logger.error(f"Failed to generate daily content: {str(e)}")
        return JsonResponse({
            'error': 'Failed to generate daily content',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def mail_all_generated_content(request):
    """Fetch all user automatically generated content and email it to them."""
    try:
        service = DailyContentService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                service.mail_all_generated_content()
            )
        finally:
            loop.close()

        logger.info("Successfully completed emailing of generated content")
        return JsonResponse({
            'message': 'Emailing of generated content completed',
            'result': result
        }, status=200)

    except Exception as e:
        logger.error(f"Failed to email generated content: {str(e)}")
        return JsonResponse({
            'error': 'Failed to email generated content',
            'details': str(e)
        }, status=500)
