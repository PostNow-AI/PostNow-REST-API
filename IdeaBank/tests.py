from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Post, PostIdea, PostObjective, PostType
from .serializers import (
    ImageGenerationRequestSerializer,
    PostCreateSerializer,
    PostGenerationRequestSerializer,
    PostIdeaSerializer,
    PostSerializer,
)


class PostModelTestCase(TestCase):
    """Test cases for Post model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_post_creation(self):
        """Test basic post creation."""
        post = Post.objects.create(
            user=self.user,
            name='Test Post',
            objective=PostObjective.SALES,
            type=PostType.POST,
            further_details='Test details'
        )

        self.assertEqual(post.name, 'Test Post')
        self.assertEqual(post.objective, PostObjective.SALES)
        self.assertEqual(post.type, PostType.POST)
        self.assertEqual(post.user, self.user)
        self.assertTrue(post.is_active)
        self.assertFalse(post.is_automatically_generated)

    def test_post_str_method(self):
        """Test Post string representation."""
        post = Post.objects.create(
            user=self.user,
            objective=PostObjective.SALES,
            type=PostType.POST
        )

        # Test with name
        post.name = 'Test Post'
        self.assertEqual(str(post), 'Test Post - Post (Vendas)')

        # Test without name
        post.name = None
        self.assertEqual(str(post), 'Sem nome - Post (Vendas)')

    def test_post_validation(self):
        """Test Post model validation."""
        # Test name validation
        post = Post(
            user=self.user,
            name='',  # Empty name should be allowed
            objective=PostObjective.SALES,
            type=PostType.POST
        )
        post.full_clean()  # Should not raise ValidationError

        # Test required fields
        with self.assertRaises(Exception):  # ValidationError
            post = Post(user=self.user, name='Test')
            post.full_clean()

    def test_post_manager_methods(self):
        """Test Post manager methods."""
        # Create test posts
        post1 = Post.objects.create(
            user=self.user,
            name='Active Post',
            objective=PostObjective.SALES,
            type=PostType.POST,
            is_active=True
        )
        Post.objects.create(
            user=self.user,
            name='Inactive Post',
            objective=PostObjective.BRANDING,
            type=PostType.REEL,
            is_active=False
        )
        post3 = Post.objects.create(
            user=self.user,
            name='Auto Post',
            objective=PostObjective.ENGAGEMENT,
            type=PostType.STORY,
            is_automatically_generated=True
        )

        # Test active posts
        active_posts = Post.objects.active()
        self.assertEqual(active_posts.count(), 2)
        self.assertIn(post1, active_posts)
        self.assertIn(post3, active_posts)

        # Test automatically generated posts
        auto_posts = Post.objects.automatically_generated()
        self.assertEqual(auto_posts.count(), 1)
        self.assertIn(post3, auto_posts)

        # Test by user
        user_posts = Post.objects.by_user(self.user)
        self.assertEqual(user_posts.count(), 3)

    def test_post_properties(self):
        """Test Post model properties."""
        post = Post.objects.create(
            user=self.user,
            name='Test Post',
            objective=PostObjective.SALES,
            type=PostType.POST
        )

        # Test ideas_count (should be 0)
        self.assertEqual(post.ideas_count, 0)

        # Test display_name
        self.assertEqual(post.display_name, 'Test Post')

        # Create an idea
        PostIdea.objects.create(
            post=post,
            content='Test content'
        )

        # Refresh from database
        post.refresh_from_db()
        self.assertEqual(post.ideas_count, 1)


class PostIdeaModelTestCase(TestCase):
    """Test cases for PostIdea model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            user=self.user,
            name='Test Post',
            objective=PostObjective.SALES,
            type=PostType.POST
        )

    def test_post_idea_creation(self):
        """Test basic PostIdea creation."""
        idea = PostIdea.objects.create(
            post=self.post,
            content='Test content for the post idea',
            image_url='https://example.com/image.jpg'
        )

        self.assertEqual(idea.post, self.post)
        self.assertEqual(idea.content, 'Test content for the post idea')
        self.assertEqual(idea.image_url, 'https://example.com/image.jpg')
        self.assertIsNone(idea.image_description)

    def test_post_idea_str_method(self):
        """Test PostIdea string representation."""
        idea = PostIdea.objects.create(
            post=self.post,
            content='Test content for idea that has enough characters to pass validation'
        )

        expected = f"Ideia para {self.post.display_name}"
        self.assertEqual(str(idea), expected)

    def test_post_idea_validation(self):
        """Test PostIdea model validation."""
        # Test content validation
        with self.assertRaises(Exception):  # ValidationError
            idea = PostIdea(post=self.post, content='')
            idea.full_clean()

        # Test valid content
        idea = PostIdea(
            post=self.post, content='Valid content with more than 10 characters to pass validation')
        idea.full_clean()  # Should not raise

    def test_post_idea_properties(self):
        """Test PostIdea model properties."""
        idea = PostIdea.objects.create(
            post=self.post,
            content='This is a test content for the post idea that has enough characters',
            image_url='https://example.com/image.jpg'
        )

        # Test content_preview
        self.assertEqual(
            idea.content_preview, 'This is a test content for the post idea that has enough characters')

        # Test has_image
        self.assertTrue(idea.has_image)

        # Test word_count
        self.assertEqual(idea.word_count, 12)  # Count the words

    def test_post_idea_manager_methods(self):
        """Test PostIdea manager methods."""
        idea1 = PostIdea.objects.create(
            post=self.post,
            content='Content with image that has enough characters to pass validation',
            image_url='https://example.com/image1.jpg'
        )
        PostIdea.objects.create(
            post=self.post,
            content='Content without image that also has enough characters for validation'
        )

        # Test with_images
        ideas_with_images = PostIdea.objects.with_images()
        self.assertEqual(ideas_with_images.count(), 1)
        self.assertIn(idea1, ideas_with_images)

        # Test by_post
        post_ideas = PostIdea.objects.by_post(self.post)
        self.assertEqual(post_ideas.count(), 2)


class SerializerTestCase(TestCase):
    """Test cases for serializers."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            user=self.user,
            name='Test Post',
            objective=PostObjective.SALES,
            type=PostType.POST
        )

    def test_post_serializer(self):
        """Test PostSerializer."""
        serializer = PostSerializer(self.post)
        data = serializer.data

        self.assertEqual(data['name'], 'Test Post')
        self.assertEqual(data['objective'], PostObjective.SALES)
        self.assertEqual(data['type'], PostType.POST)
        self.assertEqual(data['objective_display'], 'Vendas')
        self.assertEqual(data['type_display'], 'Post')
        self.assertEqual(data['ideas_count'], 0)

    def test_post_create_serializer(self):
        """Test PostCreateSerializer."""
        data = {
            'name': 'New Post',
            'objective': PostObjective.BRANDING,
            'type': PostType.REEL,
            'further_details': 'Test details',
            'include_image': True
        }

        serializer = PostCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Test validation errors
        invalid_data = {
            'name': 'Test',
            # Missing objective and type
        }
        serializer = PostCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

    def test_post_idea_serializer(self):
        """Test PostIdeaSerializer."""
        idea = PostIdea.objects.create(
            post=self.post,
            content='Test content for idea that has enough characters to pass validation',
            image_url='https://example.com/image.jpg'
        )

        serializer = PostIdeaSerializer(idea)
        data = serializer.data

        self.assertEqual(
            data['content'], 'Test content for idea that has enough characters to pass validation')
        self.assertEqual(data['image_url'], 'https://example.com/image.jpg')
        self.assertEqual(data['post_name'], 'Test Post')
        self.assertTrue(data['has_image'])
        self.assertEqual(data['word_count'], 11)

    def test_post_generation_request_serializer(self):
        """Test PostGenerationRequestSerializer."""
        valid_data = {
            'objective': PostObjective.SALES,
            'type': PostType.POST,
            'name': 'Test Generation',
            'further_details': 'Test details',
            'include_image': True
        }

        serializer = PostGenerationRequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

        # Test required fields
        invalid_data = {
            'name': 'Test'
            # Missing objective and type
        }
        serializer = PostGenerationRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

    def test_image_generation_request_serializer(self):
        """Test ImageGenerationRequestSerializer."""
        valid_data = {
            'prompt': 'Test prompt for image',
            'style': 'realistic'
        }

        serializer = ImageGenerationRequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

        # Test prompt length validation
        long_prompt = 'x' * 501
        invalid_data = {'prompt': long_prompt}
        serializer = ImageGenerationRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class ViewTestCase(APITestCase):
    """Test cases for API views."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.post = Post.objects.create(
            user=self.user,
            name='Test Post',
            objective=PostObjective.SALES,
            type=PostType.POST
        )

    def test_post_list_view(self):
        """Test PostListView."""
        url = reverse('post-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_post_detail_view(self):
        """Test PostDetailView."""
        url = reverse('post-detail', kwargs={'pk': self.post.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Post')

    def test_post_creation(self):
        """Test post creation via API."""
        url = reverse('post-list')
        data = {
            'name': 'New API Post',
            'objective': PostObjective.BRANDING,
            'type': PostType.REEL,
            'further_details': 'Created via API',
            'include_image': False
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify post was created
        self.assertEqual(Post.objects.count(), 2)
        new_post = Post.objects.get(name='New API Post')
        self.assertEqual(new_post.objective, PostObjective.BRANDING)

    def test_post_idea_list_view(self):
        """Test PostIdeaListView."""
        # Create some ideas
        PostIdea.objects.create(
            post=self.post, content='This is idea number one with enough content')
        PostIdea.objects.create(
            post=self.post, content='This is idea number two with enough content')

        url = reverse('post-idea-list', kwargs={'post_id': self.post.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_post_options(self):
        """Test get_post_options endpoint."""
        url = reverse('post-options')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('objectives', response.data)
        self.assertIn('types', response.data)

        # Verify objectives structure
        objectives = response.data['objectives']
        self.assertTrue(len(objectives) > 0)
        self.assertIn('value', objectives[0])
        self.assertIn('label', objectives[0])

    def test_get_user_posts_with_ideas(self):
        """Test get_user_posts_with_ideas endpoint."""
        url = reverse('all-posts-with-ideas')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertIn('total_posts', response.data)
        self.assertIn('total_ideas', response.data)

    def test_get_post_stats(self):
        """Test get_post_stats endpoint."""
        # Create additional posts for stats
        Post.objects.create(
            user=self.user,
            objective=PostObjective.ENGAGEMENT,
            type=PostType.STORY
        )

        url = reverse('post-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_posts', response.data)
        self.assertIn('total_ideas', response.data)
        self.assertIn('post_types_distribution', response.data)

    @patch('IdeaBank.services.post_ai_service.PostAIService.generate_post_content')
    @patch('IdeaBank.services.post_ai_service.PostAIService.generate_image_for_post')
    def test_generate_post_idea(self, mock_generate_image, mock_generate_content):
        """Test generate_post_idea endpoint."""
        # Mock the AI service responses
        mock_generate_content.return_value = {'content': 'Generated content'}
        mock_generate_image.return_value = 'https://example.com/generated-image.jpg'

        url = reverse('generate-post-idea')
        data = {
            'name': 'AI Generated Post',
            'objective': PostObjective.SALES,
            'type': PostType.POST,
            'include_image': True
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify response structure
        self.assertIn('post', response.data)
        self.assertIn('idea', response.data)

        # Verify objects were created
        self.assertEqual(Post.objects.count(), 2)  # Original + new
        self.assertEqual(PostIdea.objects.count(), 1)

    def test_generate_post_idea_validation_error(self):
        """Test generate_post_idea with invalid data."""
        url = reverse('generate-post-idea')
        data = {
            'name': 'Test Post'
            # Missing required fields
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected endpoints."""
        self.client.force_authenticate(user=None)

        url = reverse('post-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ServiceTestCase(TestCase):
    """Test cases for services."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('IdeaBank.services.post_ai_service.PostAIService.generate_post_content')
    def test_post_ai_service_mock(self, mock_generate):
        """Test PostAIService with mocked AI calls."""
        from .services.post_ai_service import PostAIService

        mock_generate.return_value = {
            'content': 'Mocked AI generated content'
        }

        service = PostAIService()
        post_data = {
            'objective': PostObjective.SALES,
            'type': PostType.POST,
            'name': 'Test Post'
        }

        result = service.generate_post_content(self.user, post_data)

        self.assertEqual(result['content'], 'Mocked AI generated content')
        mock_generate.assert_called_once()


class IntegrationTestCase(APITestCase):
    """Integration tests for complex workflows."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_complete_post_workflow(self):
        """Test complete post creation and idea generation workflow."""
        # 1. Create a post
        post_url = reverse('post-list')
        post_data = {
            'name': 'Workflow Test Post',
            'objective': PostObjective.BRANDING,
            'type': PostType.REEL,
            'further_details': 'Testing complete workflow',
            'include_image': False
        }

        response = self.client.post(post_url, post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']

        # 2. Verify post was created
        post_detail_url = reverse('post-detail', kwargs={'pk': post_id})
        response = self.client.get(post_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Workflow Test Post')

        # 3. Get post with ideas (should be empty)
        ideas_url = reverse('postidea-list', kwargs={'post_id': post_id})
        response = self.client.get(ideas_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_user_isolation(self):
        """Test that users can only access their own data."""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )

        # Create post for other user
        other_post = Post.objects.create(
            user=other_user,
            name='Other User Post',
            objective=PostObjective.SALES,
            type=PostType.POST
        )

        # Try to access other user's post
        url = reverse('post-detail', kwargs={'pk': other_post.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify our user can only see their own posts
        list_url = reverse('post-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No posts for this user yet
        self.assertEqual(len(response.data['results']), 0)
