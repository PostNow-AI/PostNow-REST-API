import uuid

from django.utils import timezone as tz

from Analytics.constants import AnalyticsEventName, AnalyticsResourceType
from Analytics.models import AnalyticsEvent


def mark_style_feedback(style, signal: str, user):
    """Mark a GeneratedVisualStyle with feedback and emit analytics event."""
    style.feedback_signal = signal
    style.save(update_fields=['feedback_signal'])

    event_name = (
        AnalyticsEventName.STYLE_ACCEPTED
        if signal == 'accepted'
        else AnalyticsEventName.STYLE_REJECTED
    )
    AnalyticsEvent.objects.create(
        event_name=event_name,
        occurred_at=tz.now(),
        user=user,
        client_session_id=uuid.uuid4(),
        resource_type=AnalyticsResourceType.GENERATED_VISUAL_STYLE,
        resource_id=str(style.id),
    )
