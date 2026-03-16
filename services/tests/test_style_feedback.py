"""Testes para o feedback loop de estilos visuais (Tarefas 1.1-1.6, 2.1-2.3, 3.2-3.3)."""

import json
from unittest.mock import Mock, patch, MagicMock


class TestFeedbackSignalField:
    """Tarefa 1.2: campo feedback_signal no GeneratedVisualStyle."""

    def test_default_is_pending(self):
        from CreatorProfile.models import GeneratedVisualStyle
        field = GeneratedVisualStyle._meta.get_field('feedback_signal')
        assert field.default == 'pending'

    def test_valid_choices(self):
        from CreatorProfile.models import GeneratedVisualStyle
        field = GeneratedVisualStyle._meta.get_field('feedback_signal')
        choice_values = [c[0] for c in field.choices]
        assert 'pending' in choice_values
        assert 'accepted' in choice_values
        assert 'rejected' in choice_values

    def test_max_length(self):
        from CreatorProfile.models import GeneratedVisualStyle
        field = GeneratedVisualStyle._meta.get_field('feedback_signal')
        assert field.max_length == 20

    def test_has_db_index(self):
        from CreatorProfile.models import GeneratedVisualStyle
        field = GeneratedVisualStyle._meta.get_field('feedback_signal')
        assert field.db_index is True


class TestEngagementScoreField:
    """Tarefa 3.3: campo engagement_score no GeneratedVisualStyle."""

    def test_field_exists_and_nullable(self):
        from CreatorProfile.models import GeneratedVisualStyle
        field = GeneratedVisualStyle._meta.get_field('engagement_score')
        assert field.null is True
        assert field.blank is True


class TestPostIdeaGeneratedStyleFK:
    """Tarefa 1.1: FK generated_style no PostIdea."""

    def test_fk_exists(self):
        from IdeaBank.models import PostIdea
        field = PostIdea._meta.get_field('generated_style')
        assert field.null is True
        assert field.blank is True

    def test_fk_on_delete_set_null(self):
        from django.db.models import SET_NULL
        from IdeaBank.models import PostIdea
        field = PostIdea._meta.get_field('generated_style')
        assert field.remote_field.on_delete is SET_NULL

    def test_fk_related_name(self):
        from IdeaBank.models import PostIdea
        field = PostIdea._meta.get_field('generated_style')
        assert field.remote_field.related_name == 'post_ideas'


class TestMarkStyleFeedback:
    """Tarefa 1.4 + 1.6: _mark_style_feedback marca e emite analytics."""

    @patch("IdeaBank.utils.style_feedback.AnalyticsEvent")
    def test_mark_accepted(self, mock_event_model):
        from IdeaBank.utils.style_feedback import mark_style_feedback as _mark_style_feedback

        style = Mock()
        user = Mock()

        _mark_style_feedback(style, 'accepted', user)

        style.save.assert_called_once_with(update_fields=['feedback_signal'])
        assert style.feedback_signal == 'accepted'
        mock_event_model.objects.create.assert_called_once()
        call_kwargs = mock_event_model.objects.create.call_args[1]
        assert call_kwargs['event_name'] == 'style_accepted'
        assert call_kwargs['resource_type'] == 'GeneratedVisualStyle'

    @patch("IdeaBank.utils.style_feedback.AnalyticsEvent")
    def test_mark_rejected(self, mock_event_model):
        from IdeaBank.utils.style_feedback import mark_style_feedback as _mark_style_feedback

        style = Mock()
        user = Mock()

        _mark_style_feedback(style, 'rejected', user)

        assert style.feedback_signal == 'rejected'
        call_kwargs = mock_event_model.objects.create.call_args[1]
        assert call_kwargs['event_name'] == 'style_rejected'


class TestImageGenerationRequestSerializer:
    """Tarefa 2.3: reuse_style_id no serializer."""

    def test_reuse_style_id_is_optional(self):
        from IdeaBank.serializers import ImageGenerationRequestSerializer
        s = ImageGenerationRequestSerializer(data={})
        assert s.is_valid()
        assert s.validated_data.get('reuse_style_id') is None

    def test_reuse_style_id_accepts_integer(self):
        from IdeaBank.serializers import ImageGenerationRequestSerializer
        s = ImageGenerationRequestSerializer(data={'reuse_style_id': 42})
        assert s.is_valid()
        assert s.validated_data['reuse_style_id'] == 42


class TestGeneratedVisualStyleSerializer:
    """Tarefa 2.1: serializer para estilos gerados."""

    def test_has_expected_fields(self):
        from CreatorProfile.serializers import GeneratedVisualStyleSerializer
        fields = GeneratedVisualStyleSerializer().get_fields()
        expected = ['id', 'name', 'style_data', 'is_favorite',
                    'times_used', 'feedback_signal', 'created_at']
        for f in expected:
            assert f in fields, f"Campo '{f}' faltando no serializer"

    def test_read_only_fields(self):
        from CreatorProfile.serializers import GeneratedVisualStyleSerializer
        meta = GeneratedVisualStyleSerializer.Meta
        for f in ['id', 'name', 'style_data', 'times_used', 'feedback_signal', 'created_at']:
            assert f in meta.read_only_fields


class TestEngagementMetricsModel:
    """Tarefa 3.2: model EngagementMetrics."""

    def test_model_exists(self):
        from SocialMediaIntegration.models import EngagementMetrics
        assert EngagementMetrics is not None

    def test_has_expected_fields(self):
        from SocialMediaIntegration.models import EngagementMetrics
        field_names = [f.name for f in EngagementMetrics._meta.get_fields()]
        for name in ['scheduled_post', 'instagram_media_id', 'impressions',
                     'reach', 'engagement', 'saves', 'shares',
                     'engagement_rate', 'fetched_at', 'raw_data']:
            assert name in field_names, f"Campo '{name}' faltando"

    def test_scheduled_post_is_one_to_one(self):
        from SocialMediaIntegration.models import EngagementMetrics
        field = EngagementMetrics._meta.get_field('scheduled_post')
        assert field.one_to_one is True

    def test_fk_chain_to_post_idea(self):
        """EngagementMetrics -> ScheduledPost -> PostIdea (FK chain)."""
        from SocialMediaIntegration.models import ScheduledPost
        field = ScheduledPost._meta.get_field('post_idea')
        assert field.null is True
        assert field.remote_field.related_name == 'scheduled_posts'


class TestCreatorProfileAdmin:
    """Tarefa 1.2: admin atualizado com feedback_signal."""

    def test_feedback_signal_in_list_display(self):
        from CreatorProfile.admin import GeneratedVisualStyleAdmin
        assert 'feedback_signal' in GeneratedVisualStyleAdmin.list_display

    def test_feedback_signal_in_list_filter(self):
        from CreatorProfile.admin import GeneratedVisualStyleAdmin
        assert 'feedback_signal' in GeneratedVisualStyleAdmin.list_filter


class TestCreatorProfileUrls:
    """Tarefa 2.1: novas URLs de estilos."""

    def test_styles_url_registered(self):
        from django.urls import reverse
        url = reverse('creator_profile:list_generated_styles')
        assert '/styles/' in url

    def test_toggle_favorite_url_registered(self):
        from django.urls import reverse
        url = reverse('creator_profile:toggle_style_favorite', kwargs={'style_id': 1})
        assert '/styles/1/favorite/' in url


class TestFetchEngagementMetricsCommand:
    """Tarefa 3.3: management command existe e e importavel."""

    def test_command_importable(self):
        from SocialMediaIntegration.management.commands.fetch_engagement_metrics import Command
        cmd = Command()
        assert cmd.help is not None
