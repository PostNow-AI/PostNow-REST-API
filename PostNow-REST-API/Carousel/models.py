from django.db import models
from django.contrib.auth.models import User
from IdeaBank.models import Post


class CarouselPost(models.Model):
    """Post em formato carrossel."""
    post = models.OneToOneField(
        Post, on_delete=models.CASCADE, related_name='carousel'
    )
    slide_count = models.IntegerField(default=7)
    narrative_type = models.CharField(
        max_length=50,
        choices=[('list', 'Lista/Checklist')],
        default='list'
    )
    visual_consistency_applied = models.BooleanField(default=True)
    logo_placement = models.CharField(
        max_length=20,
        choices=[
            ('first_last', 'Primeiro e Último Slide'),
            ('all_minimal', 'Todos os Slides (Watermark)'),
        ],
        default='first_last'
    )
    swipe_triggers = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carousel_posts'
        verbose_name = 'Carousel Post'
        verbose_name_plural = 'Carousel Posts'
        ordering = ['-created_at']

    def __str__(self):
        return f"Carrossel: {self.post.name}"


class CarouselSlide(models.Model):
    """Slide individual."""
    carousel = models.ForeignKey(
        CarouselPost, on_delete=models.CASCADE, related_name='slides'
    )
    sequence_order = models.IntegerField()
    title = models.CharField(max_length=100, blank=True)
    content = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    image_description = models.TextField(blank=True)
    has_arrow = models.BooleanField(default=True)
    has_numbering = models.BooleanField(default=True)

    class Meta:
        db_table = 'carousel_slides'
        verbose_name = 'Carousel Slide'
        verbose_name_plural = 'Carousel Slides'
        ordering = ['sequence_order']
        unique_together = ['carousel', 'sequence_order']

    def __str__(self):
        return f"Slide {self.sequence_order} - {self.title}"


class CarouselGenerationSource(models.Model):
    """Rastreamento de origem."""
    carousel = models.OneToOneField(
        CarouselPost, on_delete=models.CASCADE, related_name='generation_source'
    )
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Input Manual do Usuário'),
            ('from_post', 'Expandido de Post Existente'),
            ('weekly_context', 'Weekly Context/Oportunidade'),
        ]
    )
    original_theme = models.TextField()
    user_modifications = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carousel_generation_sources'
        verbose_name = 'Carousel Generation Source'
        verbose_name_plural = 'Carousel Generation Sources'

    def __str__(self):
        return f"{self.get_source_type_display()} - {self.carousel}"


class CarouselMetrics(models.Model):
    """Métricas básicas (MVP)."""
    carousel = models.OneToOneField(
        CarouselPost, on_delete=models.CASCADE, related_name='metrics'
    )
    generation_time = models.FloatField(default=0.0)
    generation_source = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carousel_metrics'
        verbose_name = 'Carousel Metrics'
        verbose_name_plural = 'Carousel Metrics'

    def __str__(self):
        return f"Métricas - {self.carousel}"

