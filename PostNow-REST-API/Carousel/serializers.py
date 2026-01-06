from rest_framework import serializers
from Carousel.models import CarouselPost, CarouselSlide, CarouselGenerationSource, CarouselMetrics


class CarouselSlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarouselSlide
        fields = [
            'id', 'sequence_order', 'title', 'content',
            'image_url', 'image_description',
            'has_arrow', 'has_numbering'
        ]


class CarouselGenerationSourceSerializer(serializers.ModelSerializer):
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)

    class Meta:
        model = CarouselGenerationSource
        fields = ['id', 'source_type', 'source_type_display', 'original_theme', 'created_at']


class CarouselMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarouselMetrics
        fields = ['id', 'generation_time', 'generation_source', 'created_at']


class CarouselPostSerializer(serializers.ModelSerializer):
    slides = CarouselSlideSerializer(many=True, read_only=True)
    post_name = serializers.CharField(source='post.name', read_only=True)
    generation_source = CarouselGenerationSourceSerializer(read_only=True)
    metrics = CarouselMetricsSerializer(read_only=True)

    class Meta:
        model = CarouselPost
        fields = [
            'id', 'post_name', 'slide_count', 'narrative_type',
            'logo_placement', 'slides', 'generation_source', 'metrics',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CarouselGenerationRequestSerializer(serializers.Serializer):
    theme = serializers.CharField(
        max_length=500,
        help_text="Tema do carrossel"
    )

    def validate_theme(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Tema deve ter pelo menos 10 caracteres"
            )
        return value.strip()

