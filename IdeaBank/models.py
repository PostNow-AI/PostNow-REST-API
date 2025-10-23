import base64
import json
import zlib

from django.contrib.auth.models import User
from django.db import models


class ChatHistory(models.Model):
    """Store conversation history for AI chat sessions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation_id = models.CharField(
        max_length=100,
        default='default',
        help_text="ID to distinguish different conversations"
    )
    history = models.TextField(
        help_text="Compressed and encoded chat history"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_histories'
        verbose_name = 'Chat History'
        verbose_name_plural = 'Chat Histories'
        ordering = ['-last_updated']
        unique_together = ('user', 'conversation_id')

    def __str__(self):
        return f"Chat history for {self.user.username} - {self.conversation_id}"

    def set_history(self, history_data):
        """Compress and encode history data for storage."""
        try:
            # Convert to JSON string
            json_str = json.dumps(history_data, ensure_ascii=False)
            # Compress using zlib
            compressed = zlib.compress(json_str.encode('utf-8'), level=9)
            # Encode to base64 for safe text storage
            encoded = base64.b64encode(compressed).decode('ascii')
            self.history = encoded
        except Exception as e:
            print(f"Error encoding history: {e}")
            self.history = ""

    def get_history(self):
        """Decode and decompress history data."""
        try:
            if not self.history:
                return []
            # Decode from base64
            compressed = base64.b64decode(self.history.encode('ascii'))
            # Decompress
            json_str = zlib.decompress(compressed).decode('utf-8')
            # Parse JSON
            return json.loads(json_str)
        except Exception as e:
            print(f"Error decoding history: {e}")
            return []


class PostType(models.TextChoices):
    LIVE = 'live', 'Live'
    REEL = 'reel', 'Reel'
    POST = 'post', 'Post'
    CAROUSEL = 'carousel', 'Carousel'
    STORY = 'story', 'Story'


class PostObjective(models.TextChoices):
    SALES = 'sales', 'Vendas'
    BRANDING = 'branding', 'Branding'
    ENGAGEMENT = 'engagement', 'Engajamento'
    AWARENESS = 'awareness', 'Conscientização'
    LEAD_GENERATION = 'lead_generation', 'Geração de Leads'
    EDUCATION = 'education', 'Educação'


class Gender(models.TextChoices):
    MALE = 'male', 'Masculino'
    FEMALE = 'female', 'Feminino'
    ALL = 'all', 'Todos'
    NON_BINARY = 'non_binary', 'Não Binário'


class Post(models.Model):
    """Post configuration for AI content generation."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Required fields
    name = models.CharField(
        max_length=200, help_text="Nome do post", blank=True, null=True)
    objective = models.CharField(
        max_length=50,
        choices=PostObjective.choices,
        help_text="Objetivo do post"
    )
    type = models.CharField(
        max_length=20,
        choices=PostType.choices,
        help_text="Tipo de conteúdo"
    )
    further_details = models.TextField(
        help_text="Detalhes adicionais para a geração de conteúdo",
        default="",
        null=True,
        blank=True
    )
    include_image = models.BooleanField(
        default=False, help_text="Incluir imagem gerada pela IA"
    )
    is_automatically_generated = models.BooleanField(
        default=False, help_text="Indica se o post foi gerado automaticamente"
    )
    is_active = models.BooleanField(
        default=True, help_text="Indica se o post está ativo"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_type_display()} ({self.get_objective_display()})"


class PostIdea(models.Model):
    """AI-generated ideas for posts."""
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='ideas')

    # AI-generated content
    content = models.TextField(
        help_text="Conteúdo completo gerado pela IA (Título, Texto, CTA)"
    )
    image_url = models.TextField(
        blank=True,
        null=True,
        help_text="URL da imagem gerada ou base64 data"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'post_ideas'
        verbose_name = 'Post Idea'
        verbose_name_plural = 'Post Ideas'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ideia para {self.post.name}"

    @property
    def content_preview(self):
        """Return a preview of the content (first 100 characters)."""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content
