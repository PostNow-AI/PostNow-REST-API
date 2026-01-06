"""
Views para o app Carousel.
Seguindo padrão DRF com APIViews.
"""
import logging

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Prefetch

from Carousel.models import CarouselPost, CarouselSlide
from Carousel.serializers import (
    CarouselPostSerializer,
    CarouselGenerationRequestSerializer
)
from Carousel.services.carousel_generation_service import CarouselGenerationService
from AuditSystem.services import AuditService

logger = logging.getLogger(__name__)


class CarouselListView(generics.ListAPIView):
    """
    GET /api/v1/carousel/
    Lista todos os carrosséis do usuário autenticado.
    """
    serializer_class = CarouselPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CarouselPost.objects.filter(
            post__user=self.request.user
        ).select_related(
            'post',
            'generation_source',
            'metrics'
        ).prefetch_related(
            Prefetch(
                'slides',
                queryset=CarouselSlide.objects.order_by('sequence_order')
            )
        )


class CarouselDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/carousel/<id>/
    PATCH /api/v1/carousel/<id>/
    DELETE /api/v1/carousel/<id>/
    """
    serializer_class = CarouselPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CarouselPost.objects.filter(
            post__user=self.request.user
        ).select_related(
            'post',
            'generation_source',
            'metrics'
        ).prefetch_related(
            Prefetch(
                'slides',
                queryset=CarouselSlide.objects.order_by('sequence_order')
            )
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_carousel_manual(request):
    """
    POST /api/v1/carousel/generate/
    Gera carrossel a partir de input manual do usuário.
    
    Request body:
    {
        "theme": "Tema do carrossel (mín 10 caracteres)"
    }
    
    Response:
    - 201 Created: Carrossel gerado com sucesso
    - 400 Bad Request: Validação falhou
    - 500 Internal Server Error: Erro na geração
    """
    serializer = CarouselGenerationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    theme = serializer.validated_data['theme']
    user = request.user

    try:
        logger.info(f"Iniciando geração de carrossel para usuário {user.id}")
        
        service = CarouselGenerationService()
        carousel = service.generate_from_manual_input(user, theme)

        # Audit log
        AuditService.log(
            user=user,
            action='carousel_generated',
            status='success',
            details={
                'theme': theme,
                'carousel_id': carousel.id,
                'slide_count': carousel.slide_count,
                'source_type': 'manual'
            }
        )

        logger.info(f"Carrossel {carousel.id} gerado com sucesso para usuário {user.id}")

        return Response(
            {
                'success': True,
                'message': 'Carrossel gerado com sucesso',
                'data': CarouselPostSerializer(carousel).data
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        logger.error(f"Erro ao gerar carrossel para usuário {user.id}: {str(e)}", exc_info=True)
        
        # Audit log de erro
        AuditService.log(
            user=user,
            action='carousel_generated',
            status='error',
            details={
                'theme': theme,
                'error': str(e)
            }
        )

        return Response(
            {
                'success': False,
                'message': 'Erro ao gerar carrossel',
                'error_code': 'CAROUSEL_GENERATION_ERROR',
                'errors': {'detail': str(e)}
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_carousel_stats(request):
    """
    GET /api/v1/carousel/stats/
    Retorna estatísticas dos carrosséis do usuário.
    """
    user = request.user
    
    total_carousels = CarouselPost.objects.filter(post__user=user).count()
    total_slides = CarouselSlide.objects.filter(carousel__post__user=user).count()
    
    return Response({
        'success': True,
        'data': {
            'total_carousels': total_carousels,
            'total_slides': total_slides,
        }
    })

