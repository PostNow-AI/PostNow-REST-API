import uuid

from django.utils import timezone
from rest_framework import serializers

from .constants import AnalyticsEventName, AnalyticsResourceType
from .models import AnalyticsEvent


_DISALLOWED_JSON_KEYS = {
    "content",
    "post_content",
    "html",
    "prompt",
    "full_prompt",
    "raw",
}


def _validate_small_json_dict(value: dict, field_name: str) -> dict:
    if not isinstance(value, dict):
        raise serializers.ValidationError("Deve ser um objeto JSON (dict).")

    if len(value) > 50:
        raise serializers.ValidationError("Muito grande. Limite: 50 chaves.")

    for key, v in value.items():
        if not isinstance(key, str):
            raise serializers.ValidationError("Chaves devem ser strings.")

        key_lower = key.lower()
        if key_lower in _DISALLOWED_JSON_KEYS:
            raise serializers.ValidationError(
                f"Chave '{key}' não permitida em {field_name}."
            )

        if isinstance(v, str) and len(v) > 200:
            raise serializers.ValidationError(
                f"Valor muito grande para '{key}'. Limite: 200 caracteres."
            )

        if isinstance(v, (list, dict)) and len(str(v)) > 800:
            raise serializers.ValidationError(
                f"Valor muito complexo para '{key}'."
            )

    return value


class AnalyticsEventCreateSerializer(serializers.ModelSerializer):
    client_session_id = serializers.UUIDField()
    request_id = serializers.UUIDField(required=False, allow_null=True)
    decision_id = serializers.UUIDField(required=False, allow_null=True)

    occurred_at = serializers.DateTimeField(required=False)
    context = serializers.JSONField(required=False)
    properties = serializers.JSONField(required=False)

    class Meta:
        model = AnalyticsEvent
        fields = [
            "event_name",
            "occurred_at",
            "client_session_id",
            "request_id",
            "resource_type",
            "resource_id",
            "decision_id",
            "policy_id",
            "context",
            "properties",
        ]

    def validate_event_name(self, value: str) -> str:
        if value not in AnalyticsEventName.allowed():
            raise serializers.ValidationError("event_name inválido.")
        return value

    def validate_resource_type(self, value: str) -> str:
        if value and value not in AnalyticsResourceType.allowed():
            raise serializers.ValidationError("resource_type inválido.")
        return value

    def validate_context(self, value):
        return _validate_small_json_dict(value or {}, "context")

    def validate_properties(self, value):
        return _validate_small_json_dict(value or {}, "properties")

    def validate_policy_id(self, value: str) -> str:
        if value and len(value) > 120:
            raise serializers.ValidationError("policy_id muito longo.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and not user.is_authenticated:
            user = None

        ip_address = None
        user_agent = ""
        if request:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "") or ""

        occurred_at = validated_data.get("occurred_at") or timezone.now()

        # Garantir que client_session_id seja UUID
        client_session_id = validated_data["client_session_id"]
        if isinstance(client_session_id, str):
            client_session_id = uuid.UUID(client_session_id)

        return AnalyticsEvent.objects.create(
            user=user,
            event_name=validated_data["event_name"],
            occurred_at=occurred_at,
            client_session_id=client_session_id,
            request_id=validated_data.get("request_id"),
            resource_type=validated_data.get("resource_type", "") or "",
            resource_id=validated_data.get("resource_id", "") or "",
            decision_id=validated_data.get("decision_id"),
            policy_id=validated_data.get("policy_id", "") or "",
            context=validated_data.get("context", {}) or {},
            properties=validated_data.get("properties", {}) or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

