import base64
import json
import os
import time
import zlib

from django.conf import settings
from django.contrib.auth.models import User
from django.db import DatabaseError, OperationalError, models, transaction


class ChatHistory(models.Model):
    """Store aggregated conversation history for AI chat sessions per user."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    history = models.TextField(
        help_text="Compressed and encoded aggregated chat history for all conversations"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_histories'
        verbose_name = 'Chat History'
        verbose_name_plural = 'Chat Histories'
        ordering = ['-last_updated']

    def __str__(self):
        return f"Aggregated chat history for {self.user.username}"

    def set_history(self, history_data):
        """Compress and encode history data for storage with maximum compression."""
        try:
            # Convert to JSON string
            json_str = json.dumps(
                history_data, ensure_ascii=False, separators=(',', ':'))
            # Compress using zlib with maximum compression
            compressed = zlib.compress(json_str.encode('utf-8'), level=9)
            # Encode to base64 for safe text storage
            encoded = base64.b64encode(compressed).decode('ascii')
            self.history = encoded

            # Save to JSON file in debug mode only
            if settings.DEBUG:
                self._save_debug_json(history_data)

        except Exception as e:
            print(f"Error encoding history: {e}")
            self.history = ""

    def _save_debug_json(self, history_data):
        """Save history data to JSON file for debugging purposes (debug mode only)."""
        try:
            # Create debug directory if it doesn't exist
            debug_dir = os.path.join(settings.BASE_DIR, 'debug_chat_history')
            os.makedirs(debug_dir, exist_ok=True)

            # Create filename based on user
            filename = f"chat_history_{self.user.username}.json"
            filepath = os.path.join(debug_dir, filename)

            # Save the history data as readable JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving debug JSON file: {e}")
            # Don't raise exception - debug file saving failure shouldn't break the main functionality

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

    def append_interaction(self, new_history_data, max_retries=3):
        """Append new interaction to existing history with retry logic for connection errors."""
        last_error = None

        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    # Refresh the object from database to ensure we have latest data
                    self.refresh_from_db()

                    current_history = self.get_history()
                    if not isinstance(current_history, list):
                        current_history = []

                    # Append new history data
                    current_history.extend(new_history_data)

                    # Save the updated history
                    self.set_history(current_history)
                    self.save()

                # Success - exit retry loop
                return

            except (OperationalError, DatabaseError) as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if it's a connection-related error that we should retry
                if any(keyword in error_msg for keyword in [
                    'gone away', 'broken pipe', 'lost connection',
                    'server has gone away', 'connection lost'
                ]):
                    if attempt < max_retries - 1:  # Don't sleep on last attempt
                        # Exponential backoff: 1, 2, 4 seconds
                        sleep_time = (2 ** attempt)
                        print(
                            f"Database connection error (attempt {attempt + 1}/{max_retries}): {e}")
                        print(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                        continue
                    else:
                        print(
                            f"Failed to append interaction after {max_retries} attempts: {e}")
                        break
                else:
                    # Not a connection error, don't retry
                    print(f"Database error (not retryable): {e}")
                    break

            except Exception as e:
                last_error = e
                print(f"Unexpected error appending interaction: {e}")
                break

        # If we get here, all retries failed
        print(f"All retry attempts failed. Last error: {last_error}")

        # Final fallback: try to save just the new data without appending
        try:
            print("Attempting fallback: saving only new data...")
            with transaction.atomic():
                self.set_history(new_history_data)
                self.save()
            print("Fallback successful: saved new data only")
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            raise fallback_error  # Re-raise the original error if fallback fails


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
    image_description = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição da imagem usada para geração (opcional)"
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
