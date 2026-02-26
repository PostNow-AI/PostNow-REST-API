"""
New Post-based views for IdeaBank app.
"""

import asyncio
import json
import logging

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from google.genai import types
from rest_framework import generics, permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AuditSystem.services import AuditService
from ClientContext.models import ClientContext
from ClientContext.serializers import ClientContextSerializer
from CreatorProfile.models import CreatorProfile
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.daily_post_amount_service import DailyPostAmountService
from services.s3_sevice import S3Service
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
from .services.mail_daily_error import MailDailyErrorService
from .services.mail_daily_ideas_service import MailDailyIdeasService
from .services.retry_ideas_service import RetryIdeasService
from .services.retry_weekly_feed import RetryWeeklyFeedService
from .services.weekly_feed_creation import WeeklyFeedCreationService

logger = logging.getLogger(__name__)


# Post management views


class PostListView(generics.ListCreateAPIView):
    """List and create posts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

        # Log post creation
        AuditService.log_post_operation(
            user=self.request.user,
            action="post_created",
            post_id=str(serializer.instance.id),
            status="success",
            details={"post_name": serializer.instance.name},
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
            details={'post_name': post_name}
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


# AI-powered post generation views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_post_idea(request):
    """Generate a post idea using AI based on post specifications."""
    user = request.user
    serializer = PostGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Dados inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        post_data = serializer.validated_data
        include_image_requested = post_data.get("include_image", False)
        include_image_generate_now = include_image_requested

        context = ClientContext.objects.filter(user=user).first()
        serializer = ClientContextSerializer(context)

        context_data = serializer.data if serializer else {}

        ai_service = AiService()
        prompt_service = AIPromptService()
        s3_service = S3Service()

        prompt_service.set_user(request.user)

        prompt = prompt_service.build_standalone_post_prompt(post_data, context_data)

        content_result = ai_service.generate_text(
            prompt,
            user,
            types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.9,
                response_modalities=[
                    "TEXT",
                ],
            )
        )

        content_json = content_result.replace(
            'json', '', 1).strip('`').strip()
        content_loaded = json.loads(content_json)

        image_url = ''

        if include_image_requested:
            try:
                user_logo = CreatorProfile.objects.filter(user=user).first().logo
                if user_logo and "data:image/" in user_logo and ";base64," in user_logo:
                    user_logo = user_logo.split(",")[1]

                semantic_prompt = prompt_service.semantic_analysis_prompt(
                    content_loaded)
                semantic_result = ai_service.generate_text(
                    semantic_prompt, user)
                semantic_json = semantic_result.replace(
                    'json', '', 1).strip('`').strip()
                semantic_loaded = json.loads(semantic_json)

                semantic_analysis = semantic_loaded.get(
                    'analise_semantica', {})

                image_prompt = prompt_service.image_generation_prompt(
                    semantic_analysis)

                image_result = ai_service.generate_image(
                    image_prompt,
                    user_logo,
                    user,
                    types.GenerateContentConfig(
                        temperature=0.7,
                        top_p=0.9,
                        response_modalities=[
                            "IMAGE",
                        ],
                        image_config=types.ImageConfig(
                            aspect_ratio="4:5",
                        ),
                    ))

                if not image_result:
                    image_url = ''
                else:
                    image_url = s3_service.upload_image(
                        user, image_result)

            except Exception as image_error:
                print(f"Warning: Failed to generate image: {image_error}")

        post = Post.objects.create(
            user=user,
            name=post_data.get('name'),
            type=post_data.get('type'),
            objective=post_data.get('objective'),
            further_details=post_data.get('further_details', ''),
            include_image=True if post_data.get('type') == 'feed' else False,
            is_automatically_generated=True,
            is_active=False
        )

        if post_data.get('type') == 'feed':
            post_content = f"""
                {content_loaded.get('legenda', '').strip()}\n\n\n{' '.join(content_loaded.get('hashtags', []))}\n\n\n{content_loaded.get('cta', '').strip()}
             """
        else:
            post_content = content_loaded.get('roteiro', '').strip()

        post_idea = PostIdea.objects.create(
            post=post,
            content=post_content,
            image_url=image_url if include_image else '',
            image_description=''
        )

        # Log successful post and content generation
        AuditService.log_content_generation(
            user=request.user,
            action='content_generated',
            status='success',
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
    user = request.user
    ai_service = AiService()
    prompt_service = AIPromptService()
    s3_service = S3Service()
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
        semantic_analysis = ''
        user_logo = CreatorProfile.objects.filter(user=user).first().logo
        if user_logo and "data:image/" in user_logo and ";base64," in user_logo:
            user_logo = user_logo.split(",")[1]

        if custom_prompt is not None:
            image_result = ai_service.generate_image(custom_prompt, user_logo, user, types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.9,
                response_modalities=[
                    "IMAGE",
                ],
                image_config=types.ImageConfig(
                    aspect_ratio="4:5",
                ),
            ))
        else:
            prompt_service.set_user(user)

            semantic_prompt = prompt_service.semantic_analysis_prompt(
                post_idea.content)
            semantic_result = ai_service.generate_text(
                semantic_prompt, user)
            semantic_json = semantic_result.replace(
                'json', '', 1).strip('`').strip()
            semantic_loaded = json.loads(semantic_json)

            semantic_analysis = semantic_loaded.get(
                'analise_semantica', {})

            image_prompt = prompt_service.image_generation_prompt(
                semantic_analysis)

            image_result = ai_service.generate_image(image_prompt, user_logo, user, types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.9,
                response_modalities=[
                    "IMAGE",
                ],
                image_config=types.ImageConfig(
                    aspect_ratio="4:5",
                ),
            ))

        if not image_result:
            image_url = ''
        else:
            image_url = s3_service.upload_image(
                user, image_result)

        post_idea.image_description = json.dumps(custom_prompt if custom_prompt is not None else semantic_analysis)
        post_idea.image_url = image_url
        post_idea.save()

        # Log successful image generation
        AuditService.log_image_generation(
            user=request.user,
            action='image_generated',
            status='success',
            details={
                'post_id': post_idea.post.id,
                'post_name': post_idea.post.name,
                'content_type': 'image',
                'ai_provider': 'dalle',
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
    ai_service = AiService()
    prompt_service = AIPromptService()
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
        user_prompt = request.data.get('improvement_prompt')

        post_data = {
            'name': post_idea.post.name,
            'objective': post_idea.post.objective,
            'type': post_idea.post.type,
            'further_details': post_idea.post.further_details,
            'include_image': post_idea.post.include_image,
            'content': post_idea.content
        }

        context = ClientContext.objects.filter(user=request.user).first()
        serializer = ClientContextSerializer(context)

        context_data = serializer.data if serializer else {}

        prompt_service.set_user(request.user)
        prompt = prompt_service.regenerate_standalone_post_prompt(post_data, user_prompt, context_data)

        content_result = ai_service.generate_text(
            prompt,
            request.user,
            types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.9,
                response_modalities=[
                    "TEXT",
                ],
            )
        )

        content_json = content_result.replace(
            'json', '', 1).strip('`').strip()
        content_loaded = json.loads(content_json)

        if post_data.get('type') == 'feed':
            post_content = f"""
                {content_loaded.get('legenda', '').strip()}\n\n\n{' '.join(content_loaded.get('hashtags', []))}\n\n\n{content_loaded.get('cta', '').strip()}
             """
        else:
            post_content = content_loaded.get('roteiro', '').strip()

        # Update the post idea
        post_idea.content = post_content
        post_idea.save()

        # Log successful content editing
        AuditService.log_content_generation(
            user=request.user,
            action='content_updated',
            status='success',
            details={
                'post_id': post_idea.post.id,
                'post_name': post_idea.post.name,
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
            }
        )

        return Response(
            {'error': f'Erro na edição da ideia: {str(e)}'},
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
        post_type = request.GET.get('post_type')
        posts = None
        if post_type == 'feed' or post_type is None:
            posts = Post.objects.filter(
                user=request.user,
                type='feed',
            ).exclude(
                Q(ideas__image_url__isnull=True) | Q(ideas__image_url__exact="")
            ).prefetch_related('ideas').distinct().order_by('-ideas__updated_at')
        elif post_type == 'reels' or post_type == 'story':
            posts = Post.objects.filter(
                user=request.user, type=post_type
            ).prefetch_related('ideas').distinct().order_by('-ideas__updated_at')
        serializer = PostWithIdeasSerializer(posts, many=True, context={'post_type': post_type})

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
        batch_size = 4  # Process 2 users per batch, to avoid vercel timeouts

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
def vercel_cron_weekly_feed_generation(request):
    """
    Vercel Cron endpoint for weekly feed generation
    Called automatically by Vercel at scheduled time
    """

    try:
        # Get batch number from query params (default to 1)
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 6  # Process 6 users per batch, to avoid vercel timeouts

        # Run async processing
        service = WeeklyFeedCreationService()

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
                service.process_weekly_ideas_for_users(
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
def manual_trigger_weekly_feed_generation(request):
    """
    Manual trigger for weekly feed generation (for testing)
    """
    try:
        service = WeeklyFeedCreationService()

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
                service.process_weekly_ideas_for_users(
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
def mail_all_user_errors(request):
    """Fetch all user automatically generated content and email it to them."""
    try:
        service = MailDailyErrorService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                service.send_error_report()
            )
        finally:
            loop.close()

        return JsonResponse({
            'message': 'Emailing of generated content completed',
            'result': result
        }, status=200)

    except Exception as e:
        return JsonResponse({
            'error': 'Failed to email errors',
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
        # Get batch number from query params (default to 1)
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 2  # Process 2 users per batch, to avoid vercel timeouts
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
                service.process_daily_ideas_for_failed_users(
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
                service.process_daily_ideas_for_failed_users(
                    batch_number=1, batch_size=10000)
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


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser, permissions.IsAuthenticated])
def admin_fetch_all_daily_posts(request):
    """Admin endpoint to fetch all daily posts for all users."""
    try:
        date = request.GET.get('date', None)
        result = DailyPostAmountService.get_daily_post_amounts(date=date)

        return JsonResponse(result, status=200)
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to fetch daily posts',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def vercel_cron_retry_weekly_feed_failed_users(request):
    """
    Vercel Cron endpoint for retrying failed daily content generation
    Called automatically by Vercel at 8:00 AM UTC
    """

    try:
        # Get batch number from query params (default to 1)
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 6  # Process 6 users per batch, to avoid vercel timeouts
        service = RetryWeeklyFeedService()

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
                service.process_weekly_feed_for_failed_users(
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
def manual_retry_weekly_feed_failed_users(request):
    """
    Manual trigger for retrying failed users (for testing)
    """
    try:
        # Run async processing
        service = RetryWeeklyFeedService()

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
                service.process_weekly_feed_for_failed_users(
                    batch_number=1, batch_size=10000)
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
