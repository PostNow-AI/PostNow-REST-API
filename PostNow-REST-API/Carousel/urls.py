"""
URL patterns para o app Carousel.
"""

from django.urls import path
from . import views

app_name = 'carousel'

urlpatterns = [
    # Lista e geração
    path('', views.CarouselListView.as_view(), name='carousel-list'),
    path('generate/', views.generate_carousel_manual, name='generate-manual'),
    
    # CRUD individual
    path('<int:pk>/', views.CarouselDetailView.as_view(), name='carousel-detail'),
    
    # Stats
    path('stats/', views.get_carousel_stats, name='carousel-stats'),
]

