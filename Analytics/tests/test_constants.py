"""Testes para Analytics constants — novas constantes de feedback de estilo."""

from Analytics.constants import AnalyticsEventName, AnalyticsResourceType


class TestStyleFeedbackConstants:

    def test_style_accepted_in_allowed(self):
        assert AnalyticsEventName.STYLE_ACCEPTED in AnalyticsEventName.allowed()

    def test_style_rejected_in_allowed(self):
        assert AnalyticsEventName.STYLE_REJECTED in AnalyticsEventName.allowed()

    def test_generated_visual_style_in_resource_types(self):
        assert AnalyticsResourceType.GENERATED_VISUAL_STYLE in AnalyticsResourceType.allowed()

    def test_style_accepted_value(self):
        assert AnalyticsEventName.STYLE_ACCEPTED == "style_accepted"

    def test_style_rejected_value(self):
        assert AnalyticsEventName.STYLE_REJECTED == "style_rejected"

    def test_generated_visual_style_value(self):
        assert AnalyticsResourceType.GENERATED_VISUAL_STYLE == "GeneratedVisualStyle"
