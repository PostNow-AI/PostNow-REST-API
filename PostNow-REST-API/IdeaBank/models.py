from django.db import models


class PostIdea(models.Model):
    """Post idea with content and optional image."""
    content = models.TextField(blank=True)
    image_url = models.URLField(max_length=2000, blank=True, null=True)
    image_description = models.TextField(blank=True, null=True)
    post_id = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'post_ideas'

    def __str__(self):
        return f"PostIdea {self.id}"
