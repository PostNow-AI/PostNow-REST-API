"""
New Post-based views for IdeaBank app.
"""

import asyncio
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import generics, permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AuditSystem.services import AuditService

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
from .services.daily_ideas_service import DailyIdeasService
from .services.mail_daily_ideas_service import MailDailyIdeasService
from .services.post_ai_service import PostAIService
from .services.retry_ideas_service import RetryIdeasService

logger = logging.getLogger(__name__)

# Post management views


class PostListView(generics.ListCreateAPIView):
    """List and create posts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

        # Log post creation
        AuditService.log_post_operation(
            user=self.request.user,
            action='post_created',
            post_id=str(serializer.instance.id),
            status='success',
            details={'post_name': serializer.instance.name}
        )


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete posts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        old_name = instance.name
        self.perform_update(serializer)

        # Log post update
        AuditService.log_post_operation(
            user=request.user,
            action='post_updated',
            post_id=str(instance.id),
            status='success',
            details={
                'old_name': old_name,
                'new_name': instance.name,
                'changes': list(serializer.validated_data.keys())
            }
        )

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        post_id = instance.id
        post_name = instance.name

        self.perform_destroy(instance)

        # Log post deletion
        AuditService.log_post_operation(
            user=request.user,
            action='post_deleted',
            post_id=str(post_id),
            status='success',
            details={'post_name': post_name}
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class PostWithIdeasView(generics.RetrieveAPIView):
    """Retrieve a post with all its ideas."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostWithIdeasSerializer

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).prefetch_related('ideas')


# Post Idea management views
class PostIdeaListView(generics.ListAPIView):
    """List post ideas for a specific post."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostIdeaSerializer

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return PostIdea.objects.filter(
            post_id=post_id,
            post__user=self.request.user
        )


class PostIdeaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete post ideas."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostIdeaSerializer

    def get_queryset(self):
        return PostIdea.objects.filter(post__user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        # Log post idea update
        AuditService.log_content_generation(
            user=request.user,
            action='content_updated',
            status='success',
            resource_id=instance.id,
            details={'post_id': instance.post.id,
                     'post_name': instance.post.name}
        )

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        idea_id = instance.id
        post_name = instance.post.name

        self.perform_destroy(instance)

        # Log post idea deletion
        AuditService.log_content_generation(
            user=request.user,
            action='content_deleted',
            status='success',
            resource_id=idea_id,
            details={'post_name': post_name}
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


# AI-powered post generation views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_post_idea(request):
    """Generate a post idea using AI based on post specifications."""

    serializer = PostGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Create the post first
        post_data = serializer.validated_data
        include_image = post_data.get('include_image', False)

        # Create the post
        post = Post.objects.create(user=request.user, **post_data)

        # Generate content using AI
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
                # Add the created post ID and post_idea ID to post_data for image generation
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

                # Log successful image generation
                AuditService.log_image_generation(
                    user=request.user,
                    action='image_generated',
                    status='success',
                    resource_id=post_idea.id,
                    details={
                        'post_id': post.id,
                        'post_name': post.name,
                        'content_type': 'image',
                        'ai_provider': 'dalle'
                    }
                )
            except Exception as image_error:
                print(f"Warning: Failed to generate image: {image_error}")
                # Continue without image - don't fail the entire request

        # Serialize the response
        post_serializer = PostSerializer(post)
        idea_serializer = PostIdeaSerializer(post_idea)

        # Log successful post and content generation
        AuditService.log_content_generation(
            user=request.user,
            action='content_generated',
            status='success',
            resource_id=post_idea.id,
            details={
                'post_id': post.id,
                'post_name': post.name,
                'content_type': 'text',
                'ai_provider': 'gemini',
                'include_image': include_image
            }
        )

        return Response({
            'message': 'Post e ideia gerados com sucesso!',
            'post': post_serializer.data,
            'idea': idea_serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        # Log failed content generation
        AuditService.log_content_generation(
            user=request.user,
            action='content_generation_failed',
            status='error',
            error_message=str(e),
            details={
                'post_data': post_data,
                'include_image': include_image
            }
        )

        return Response(
            {'error': f'Erro na geração do post: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_image_for_idea(request, idea_id):
    """Generate an image for an existing post idea using DALL-E."""

    # Get the post idea
    try:
        post_idea = PostIdea.objects.get(
            id=idea_id,
            post__user=request.user
        )
    except PostIdea.DoesNotExist:
        return Response(
            {'error': 'Ideia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ImageGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get the custom prompt or use default
        custom_prompt = serializer.validated_data.get('prompt')

        # Prepare post data for image generation with IDs
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

        # Generate image
        post_ai_service = PostAIService()
        image_url = post_ai_service.generate_image_for_post(
            user=request.user,
            post_data=post_data,
            content=post_idea.content,
            custom_prompt=custom_prompt,
            regenerate=False
        )

        # Update the post idea with the image URL
        post_idea.image_url = image_url
        post_idea.save()

        # Log successful image generation
        AuditService.log_image_generation(
            user=request.user,
            action='image_generated',
            status='success',
            resource_id=post_idea.id,
            details={
                'post_id': post_idea.post.id,
                'post_name': post_idea.post.name,
                'content_type': 'image',
                'ai_provider': 'dalle',
                'custom_prompt': custom_prompt is not None
            }
        )

        return Response({
            'message': 'Imagem gerada com sucesso!',
            'image_url': image_url,
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Log failed image generation
        AuditService.log_email_operation(
            user=request.user,
            action='image_generation_failed',
            status='error',
            error_message=str(e),
            details={
                'idea_id': idea_id,
                'custom_prompt': custom_prompt is not None
            }
        )

        return Response(
            {'error': f'Erro na geração da imagem: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def edit_post_idea(request, idea_id):
    """Edit/regenerate a post idea with optional AI assistance."""

    # Get the post idea
    try:
        post_idea = PostIdea.objects.get(
            id=idea_id,
            post__user=request.user
        )
    except PostIdea.DoesNotExist:
        return Response(
            {'error': 'Ideia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PostIdeaEditRequestSerializer(data=request.data)
    if not serializer.is_valid():
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

        # Prepare post data
        post_data = {
            'name': post_idea.post.name,
            'objective': post_idea.post.objective,
            'type': post_idea.post.type,
            'further_details': post_idea.post.further_details,
            'include_image': post_idea.post.include_image,
        }

        # Regenerate content
        post_ai_service = PostAIService()
        result = post_ai_service.regenerate_post_content(
            user=request.user,
            post_data=post_data,
            current_content=post_idea.content,
            user_prompt=user_prompt,
            ai_provider=ai_provider,
            ai_model=ai_model
        )

        # Update the post idea
        post_idea.content = result['content']
        post_idea.save()

        # Log successful content editing
        AuditService.log_content_generation(
            user=request.user,
            action='content_updated',
            status='success',
            resource_id=post_idea.id,
            details={
                'post_id': post_idea.post.id,
                'post_name': post_idea.post.name,
                'ai_provider': ai_provider,
                'ai_model': ai_model,
                'user_prompt_provided': user_prompt is not None
            }
        )

        return Response({
            'message': 'Ideia editada com sucesso!',
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Log failed content editing
        AuditService.log_content_generation(
            user=request.user,
            action='content_generation_failed',
            status='error',
            error_message=str(e),
            details={
                'idea_id': idea_id,
                'ai_provider': ai_provider,
                'ai_model': ai_model
            }
        )

        return Response(
            {'error': f'Erro na edição da ideia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def regenerate_image_for_idea(request, idea_id):
    """Regenerate the image for a post idea with optional custom prompt."""

    # Get the post idea
    try:
        post_idea = PostIdea.objects.get(
            id=idea_id,
            post__user=request.user
        )
    except PostIdea.DoesNotExist:
        return Response(
            {'error': 'Ideia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ImageGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        custom_prompt = serializer.validated_data.get('prompt')

        # Prepare post data with IDs for image regeneration
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

        # Regenerate image
        post_ai_service = PostAIService()
        image_url = post_ai_service.generate_image_for_post(
            user=request.user,
            post_data=post_data,
            content=post_idea.content,
            custom_prompt=custom_prompt,
            regenerate=True
        )

        # Update the post idea with new image
        post_idea.image_url = image_url
        post_idea.save()

        # Log successful image regeneration
        AuditService.log_image_generation(
            user=request.user,
            action='image_updated',
            status='success',
            resource_id=post_idea.id,
            details={
                'post_id': post_idea.post.id,
                'post_name': post_idea.post.name,
                'content_type': 'image',
                'ai_provider': 'dalle',
                'regenerated': True,
                'custom_prompt': custom_prompt is not None
            }
        )

        return Response({
            'message': 'Imagem regenerada com sucesso!',
            'image_url': image_url,
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Log failed image regeneration
        AuditService.log_image_generation(
            user=request.user,
            action='image_generation_failed',
            status='error',
            error_message=str(e),
            details={
                'idea_id': idea_id,
                'regenerated': True,
                'custom_prompt': custom_prompt is not None
            }
        )

        return Response(
            {'error': f'Erro na regeneração da imagem: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Helper endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_post_options(request):
    """Get available options for post creation."""

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
        return Response(
            {'error': f'Erro ao buscar posts: {str(e)}'},
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
        return Response(
            {'error': f'Erro ao buscar estatísticas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@require_http_methods(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def vercel_cron_daily_content_generation(request):
    """
    Vercel Cron endpoint for daily content generation
    Called automatically by Vercel at scheduled time
    """

    try:
        # Get batch number from query params (default to 1)
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 3  # Process 3 users per batch, to avoid vercel timeouts

        # Run async processing
        service = DailyIdeasService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='daily_content_generation_started',
            status='info',
            resource_type='DailyContentGeneration',
        )

        try:
            result = loop.run_until_complete(
                service.process_daily_ideas_for_users(
                    batch_number=batch_number, batch_size=batch_size)
            )
            AuditService.log_system_operation(
                user=None,
                action='daily_content_generation_completed',
                status='success',
                resource_type='DailyContentGeneration',
            )
        finally:
            loop.close()

        return JsonResponse({
            'message': 'Daily content generation completed',
            'result': result
        }, status=200)

    except Exception as e:
        AuditService.log_system_operation(
            user=None,
            action='daily_content_generation_failed',
            status='error',
            resource_type='DailyContentGeneration',
            details=str(e)
        )
        return JsonResponse({
            'error': 'Failed to generate daily content',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def manual_trigger_daily_generation(request):
    """
    Manual trigger for daily content generation (for testing)
    """
    try:
        service = DailyIdeasService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='daily_content_generation_started',
            status='info',
            resource_type='DailyContentGeneration',
        )

        try:
            result = loop.run_until_complete(
                service.process_daily_ideas_for_users(
                    batch_number=1, batch_size=0)
            )
            AuditService.log_system_operation(
                user=None,
                action='daily_content_generation_completed',
                status='success',
                resource_type='DailyContentGeneration',
            )
        finally:
            loop.close()

        return JsonResponse({
            'message': 'Daily content generation completed',
            'result': result
        }, status=200)

    except Exception as e:
        AuditService.log_system_operation(
            user=None,
            action='daily_content_generation_failed',
            status='error',
            resource_type='DailyContentGeneration',
            details=str(e)
        )
        return JsonResponse({
            'error': 'Failed to generate daily content',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def mail_all_generated_content(request):
    """Fetch all user automatically generated content and email it to them."""
    try:
        service = MailDailyIdeasService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                service.mail_daily_ideas()
            )
        finally:
            loop.close()

        return JsonResponse({
            'message': 'Emailing of generated content completed',
            'result': result
        }, status=200)

    except Exception as e:
        return JsonResponse({
            'error': 'Failed to email generated content',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def vercel_cron_retry_failed_users(request):
    """
    Vercel Cron endpoint for retrying failed daily content generation
    Called automatically by Vercel at 8:00 AM UTC
    """

    try:
        service = RetryIdeasService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='daily_content_generation_started',
            status='info',
            resource_type='DailyContentGeneration',
        )

        try:
            result = loop.run_until_complete(
                service.process_daily_ideas_for_failed_users()
            )
            AuditService.log_system_operation(
                user=None,
                action='daily_content_generation_completed',
                status='success',
                resource_type='DailyContentGeneration',
            )
        finally:
            loop.close()

        return JsonResponse({
            'message': 'Daily content generation completed',
            'result': result
        }, status=200)

    except Exception as e:
        AuditService.log_system_operation(
            user=None,
            action='daily_content_generation_failed',
            status='error',
            resource_type='DailyContentGeneration',
            details=str(e)
        )
        return JsonResponse({
            'error': 'Failed to generate daily content',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def manual_trigger_retry_failed(request):
    """
    Manual trigger for retrying failed users (for testing)
    """
    try:
        # Run async processing
        service = RetryIdeasService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='daily_content_generation_started',
            status='info',
            resource_type='DailyContentGeneration',
        )

        try:
            result = loop.run_until_complete(
                service.process_daily_ideas_for_failed_users()
            )
            AuditService.log_system_operation(
                user=None,
                action='daily_content_generation_completed',
                status='success',
                resource_type='DailyContentGeneration',
            )
        finally:
            loop.close()

        return JsonResponse({
            'message': 'Daily content generation completed',
            'result': result
        }, status=200)

    except Exception as e:
        AuditService.log_system_operation(
            user=None,
            action='daily_content_generation_failed',
            status='error',
            resource_type='DailyContentGeneration',
            details=str(e)
        )
        return JsonResponse({
            'error': 'Failed to generate daily content',
            'details': str(e)
        }, status=500)
