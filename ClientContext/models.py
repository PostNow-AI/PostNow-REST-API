from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class ClientContext(models.Model):
    """Model to store client context information"""

    class Meta:
        app_label = 'ClientContext'
        db_table = 'client_contexts'
        verbose_name = 'Client Context'
        verbose_name_plural = 'Client Contexts'

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='client_context')

    weekly_context_error = models.TextField(default="", blank=True, null=True)
    weekly_context_error_date = models.DateTimeField(blank=True, null=True)

    market_panorama = models.TextField(default="", blank=True, null=True)
    market_tendencies = models.JSONField(default=list, blank=True, null=True)
    market_challenges = models.JSONField(default=list, blank=True, null=True)
    market_sources = models.JSONField(default=list, blank=True, null=True)

    competition_main = models.JSONField(default=list, blank=True, null=True)
    competition_strategies = models.TextField(
        default="", blank=True, null=True)
    competition_opportunities = models.TextField(
        default='', blank=True, null=True)
    competition_sources = models.JSONField(default=list, blank=True, null=True)

    target_audience_profile = models.TextField(
        default="", blank=True, null=True)
    target_audience_behaviors = models.TextField(
        default='', blank=True, null=True)
    target_audience_interests = models.JSONField(
        default=list, blank=True, null=True)
    target_audience_sources = models.JSONField(
        default=list, blank=True, null=True)

    tendencies_popular_themes = models.JSONField(
        default=list, blank=True, null=True)
    tendencies_hashtags = models.JSONField(default=list, blank=True, null=True)
    tendencies_keywords = models.JSONField(default=list, blank=True, null=True)
    tendencies_sources = models.JSONField(default=list, blank=True, null=True)

    seasonal_relevant_dates = models.JSONField(
        default=list, blank=True, null=True)
    seasonal_local_events = models.JSONField(
        default=list, blank=True, null=True)
    seasonal_sources = models.JSONField(default=list, blank=True, null=True)

    brand_online_presence = models.TextField(default="", blank=True, null=True)
    brand_reputation = models.TextField(default="", blank=True, null=True)
    brand_communication_style = models.TextField(
        default="", blank=True, null=True)
    brand_sources = models.JSONField(default=list, blank=True, null=True)

    # Dados de oportunidades/tendências (usado no e-mail de Segunda)
    tendencies_data = models.JSONField(default=dict, blank=True, null=True)

    # Status do enriquecimento (Fase 2)
    ENRICHMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('enriched', 'Enriched'),
        ('failed', 'Failed'),
    ]
    context_enrichment_status = models.CharField(
        max_length=20,
        choices=ENRICHMENT_STATUS_CHOICES,
        default='pending',
        blank=True,
        null=True
    )
    context_enrichment_date = models.DateTimeField(blank=True, null=True)
    context_enrichment_error = models.TextField(default="", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ClientContext {self.id}"
