import json
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from Carousel.models import CarouselPost, CarouselSlide, CarouselGenerationSource, CarouselMetrics
from Carousel.services.carousel_generation_service import CarouselGenerationService
from IdeaBank.models import Post, PostType
from CreatorProfile.models import CreatorProfile


class CarouselModelTests(TestCase):
    """Testes para os modelos do Carousel."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            user=self.user,
            name='Test Carousel Post',
            type=PostType.CAROUSEL,
            objective='engagement'
        )

    def test_create_carousel_post(self):
        """Testa criação de CarouselPost."""
        carousel = CarouselPost.objects.create(
            post=self.post,
            slide_count=7,
            narrative_type='list'
        )
        
        self.assertEqual(carousel.post, self.post)
        self.assertEqual(carousel.slide_count, 7)
        self.assertEqual(carousel.narrative_type, 'list')
        self.assertEqual(carousel.logo_placement, 'first_last')  # Default

    def test_create_carousel_slide(self):
        """Testa criação de CarouselSlide."""
        carousel = CarouselPost.objects.create(
            post=self.post,
            slide_count=7
        )
        
        slide = CarouselSlide.objects.create(
            carousel=carousel,
            sequence_order=1,
            title='Slide 1',
            content='Conteúdo do slide 1',
            has_arrow=True,
            has_numbering=True
        )
        
        self.assertEqual(slide.carousel, carousel)
        self.assertEqual(slide.sequence_order, 1)
        self.assertTrue(slide.has_arrow)
        self.assertTrue(slide.has_numbering)

    def test_carousel_slides_ordering(self):
        """Testa ordenação de slides."""
        carousel = CarouselPost.objects.create(
            post=self.post,
            slide_count=3
        )
        
        # Criar slides fora de ordem
        CarouselSlide.objects.create(carousel=carousel, sequence_order=3, title='Slide 3')
        CarouselSlide.objects.create(carousel=carousel, sequence_order=1, title='Slide 1')
        CarouselSlide.objects.create(carousel=carousel, sequence_order=2, title='Slide 2')
        
        slides = carousel.slides.all()
        self.assertEqual(slides[0].title, 'Slide 1')
        self.assertEqual(slides[1].title, 'Slide 2')
        self.assertEqual(slides[2].title, 'Slide 3')

    def test_carousel_generation_source(self):
        """Testa rastreamento de origem."""
        carousel = CarouselPost.objects.create(
            post=self.post,
            slide_count=7
        )
        
        source = CarouselGenerationSource.objects.create(
            carousel=carousel,
            source_type='manual',
            original_theme='Teste de tema'
        )
        
        self.assertEqual(source.carousel, carousel)
        self.assertEqual(source.source_type, 'manual')
        self.assertEqual(source.original_theme, 'Teste de tema')

    def test_carousel_metrics(self):
        """Testa métricas básicas."""
        carousel = CarouselPost.objects.create(
            post=self.post,
            slide_count=7
        )
        
        metrics = CarouselMetrics.objects.create(
            carousel=carousel,
            generation_time=45.5,
            generation_source='manual'
        )
        
        self.assertEqual(metrics.carousel, carousel)
        self.assertEqual(metrics.generation_time, 45.5)
        self.assertEqual(metrics.generation_source, 'manual')


class CarouselAPITests(TestCase):
    """Testes para os endpoints da API de Carousel."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_carousels_empty(self):
        """Testa listagem de carrosséis vazia."""
        response = self.client.get('/api/v1/carousel/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Pode retornar lista direta ou em 'data'
        data = response.data if isinstance(response.data, list) else response.data.get('data', [])
        self.assertEqual(len(data), 0)

    def test_carousel_generation_request_validation(self):
        """Testa validação do request de geração."""
        # Tema muito curto
        response = self.client.post('/api/v1/carousel/generate/', {
            'theme': 'Curto'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_carousel_generation_requires_auth(self):
        """Testa que geração requer autenticação."""
        self.client.force_authenticate(user=None)
        
        response = self.client.post('/api/v1/carousel/generate/', {
            'theme': 'Tema de teste suficientemente longo'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_carousel_stats(self):
        """Testa endpoint de estatísticas."""
        response = self.client.get('/api/v1/carousel/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_carousels', response.data.get('data', response.data))
        self.assertIn('total_slides', response.data.get('data', response.data))


class CarouselSerializerTests(TestCase):
    """Testes para os serializers."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

    def test_carousel_generation_request_serializer_valid(self):
        """Testa validação de request válido."""
        from Carousel.serializers import CarouselGenerationRequestSerializer
        
        data = {'theme': 'Tema de teste suficientemente longo'}
        serializer = CarouselGenerationRequestSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['theme'], data['theme'])

    def test_carousel_generation_request_serializer_invalid(self):
        """Testa validação de request inválido."""
        from Carousel.serializers import CarouselGenerationRequestSerializer
        
        # Tema muito curto
        data = {'theme': 'Curto'}
        serializer = CarouselGenerationRequestSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('theme', serializer.errors)


# Nota: Testes de geração completa (com IA) devem ser feitos manualmente
# ou com mocks, pois requerem chamadas reais à API de IA e podem ser lentos/caros


