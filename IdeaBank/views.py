"""
New Post-based views for IdeaBank app.
"""

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Gender, Post, PostIdea, PostObjective, PostType
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
from .services.post_ai_service import PostAIService


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


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete posts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)


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

        # Extract AI preferences
        ai_provider = post_data.pop('preferred_provider', 'google')
        ai_model = post_data.pop('preferred_model', 'gemini-1.5-flash')
        include_image = post_data.pop('include_image', False)

        # Create the post
        post = Post.objects.create(user=request.user, **post_data)

        # Generate content using AI
        post_ai_service = PostAIService()
        result = post_ai_service.generate_post_content(
            user=request.user,
            post_data=post_data,
            ai_provider=ai_provider,
            ai_model=ai_model
        )

        # Create the post idea with generated content
        post_idea = PostIdea.objects.create(
            post=post,
            content=result['content'],
            ai_provider=result['ai_provider'],
            ai_model=result['ai_model']
        )

        # Generate image if requested
        if include_image:
            try:
                image_url = post_ai_service.generate_image_for_post(
                    user=request.user,
                    post_data=post_data,
                    content=result['content']
                )
                post_idea.image_url = image_url
                post_idea.save()
            except Exception as image_error:
                print(f"Warning: Failed to generate image: {image_error}")
                # Continue without image - don't fail the entire request

        # Serialize the response
        post_serializer = PostSerializer(post)
        idea_serializer = PostIdeaSerializer(post_idea)

        return Response({
            'message': 'Post e ideia gerados com sucesso!',
            'post': post_serializer.data,
            'idea': idea_serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
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

        # Prepare post data for image generation
        post_data = {
            'name': post_idea.post.name,
            'objective': post_idea.post.objective,
            'type': post_idea.post.type,
        }

        # Generate image
        post_ai_service = PostAIService()
        image_url = post_ai_service.generate_image_for_post(
            user=request.user,
            post_data=post_data,
            content=post_idea.content,
            custom_prompt=custom_prompt
        )

        # Update the post idea with the image URL
        post_idea.image_url = image_url
        post_idea.save()

        return Response({
            'message': 'Imagem gerada com sucesso!',
            'image_url': image_url,
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
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
            'preferred_model', 'gemini-1.5-flash')

        # Prepare post data
        post_data = {
            'name': post_idea.post.name,
            'objective': post_idea.post.objective,
            'type': post_idea.post.type,
            'target_gender': post_idea.post.target_gender,
            'target_age': post_idea.post.target_age,
            'target_location': post_idea.post.target_location,
            'target_salary': post_idea.post.target_salary,
            'target_interests': post_idea.post.target_interests,
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
        post_idea.ai_provider = result['ai_provider']
        post_idea.ai_model = result['ai_model']
        post_idea.save()

        return Response({
            'message': 'Ideia editada com sucesso!',
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
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

        # Prepare post data
        post_data = {
            'name': post_idea.post.name,
            'objective': post_idea.post.objective,
            'type': post_idea.post.type,
        }

        # Regenerate image
        post_ai_service = PostAIService()
        image_url = post_ai_service.generate_image_for_post(
            user=request.user,
            post_data=post_data,
            content=post_idea.content,
            custom_prompt=custom_prompt
        )

        # Update the post idea with new image
        post_idea.image_url = image_url
        post_idea.save()

        return Response({
            'message': 'Imagem regenerada com sucesso!',
            'image_url': image_url,
            'idea': PostIdeaSerializer(post_idea).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
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
        ],
        'genders': [
            {'value': choice[0], 'label': choice[1]}
            for choice in Gender.choices
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
        approved_ideas = PostIdea.objects.filter(
            post__user=request.user,
            status='approved'
        ).count()
        draft_ideas = PostIdea.objects.filter(
            post__user=request.user,
            status='draft'
        ).count()

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
            'approved_ideas': approved_ideas,
            'draft_ideas': draft_ideas,
            'post_types_distribution': post_types
        })
    except Exception as e:
        return Response(
            {'error': f'Erro ao buscar estatísticas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
