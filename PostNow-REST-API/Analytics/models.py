import uuid

from django.conf import settings
from django.db import models


class AnalyticsEvent(models.Model):
    """
    Evento de produto/telemetria (não auditoria).

    Regras:
    - não armazenar conteúdo textual do post/prompt do usuário (somente len/hash/flags)
    - manter context/properties pequenos e estáveis (baixa cardinalidade)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    event_name = models.CharField(max_length=80)
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    client_session_id = models.UUIDField()
    request_id = models.UUIDField(null=True, blank=True)

    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=80, blank=True)

    decision_id = models.UUIDField(null=True, blank=True)
    policy_id = models.CharField(max_length=120, blank=True)

    context = models.JSONField(default=dict, blank=True)
    properties = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["occurred_at"]),
            models.Index(fields=["event_name", "occurred_at"]),
            models.Index(fields=["user", "occurred_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["decision_id"]),
            models.Index(fields=["policy_id"]),
            models.Index(fields=["client_session_id", "occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_name} ({self.occurred_at.isoformat()})"


class Decision(models.Model):
    """
    Representa uma decisão tomada por uma política (bandit/RL) no sistema.
    Ex.: 'image_pregen' com action 'pre_generate' vs 'on_demand'.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    decision_type = models.CharField(max_length=60)
    action = models.CharField(max_length=40)
    policy_id = models.CharField(max_length=120)

    occurred_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=80, blank=True)

    context = models.JSONField(default=dict, blank=True)
    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["decision_type", "occurred_at"]),
            models.Index(fields=["policy_id", "occurred_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["user", "occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.decision_type}:{self.action} ({self.policy_id})"


class DecisionOutcome(models.Model):
    """
    Resultado agregado de uma decisão (recompensa e métricas), calculado offline.
    """

    decision = models.OneToOneField(Decision, on_delete=models.CASCADE, related_name="outcome")
    computed_at = models.DateTimeField(auto_now_add=True)

    reward = models.FloatField(default=0.0)
    success = models.BooleanField(default=False)
    metrics = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["computed_at"]),
            models.Index(fields=["success"]),
        ]

    def __str__(self) -> str:
        return f"Outcome({self.decision_id}) reward={self.reward}"


class BanditArmStat(models.Model):
    """
    Estado do bandit por bucket/ação (Beta-Binomial para Thompson Sampling).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    decision_type = models.CharField(max_length=60)
    policy_id = models.CharField(max_length=120)

    bucket = models.CharField(max_length=120)
    action = models.CharField(max_length=40)

    alpha = models.FloatField(default=1.0)
    beta = models.FloatField(default=1.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("decision_type", "policy_id", "bucket", "action")
        indexes = [
            models.Index(fields=["decision_type", "policy_id"]),
            models.Index(fields=["bucket"]),
        ]

    def __str__(self) -> str:
        return f"{self.policy_id}:{self.bucket}:{self.action} a={self.alpha} b={self.beta}"

