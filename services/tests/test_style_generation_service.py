"""Testes para style_generation_service -- geracao de estilo visual via IA."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from services.style_generation_service import (  # noqa: E501
    _parse_style_json,
    _default_style,
    _get_style_direction,
    _gather_market_context,
    _gather_previous_styles,
    _gather_favorite_styles,
    _gather_performance_data,
    _format_content_type_context,
    STYLE_GENERATION_PROMPT_SYSTEM,
    STYLE_GENERATION_PROMPT_TEMPLATE,
    STYLE_DIRECTIONS,
    DEFAULT_STYLE_DIRECTION,
)


class TestParseStyleJson:
    """Testes para parsing do JSON retornado pela IA."""

    def _valid_style_json(self, **overrides):
        base = {
            "name": "Editorial Minimalista",
            "aesthetic": "Clean minimalist design inspired by editorial magazines",
            "colors": {
                "background": "warm ivory",
                "primary": "deep cobalt blue",
                "accent": "vivid coral",
                "text": "dark charcoal",
            },
            "lighting": "soft overcast nordic daylight",
            "typography": "modern bold sans-serif",
            "composition": "title upper third centered, main visual centered 40%",
            "mood": "professional, confident",
            "references": ["editorial magazine layout"],
        }
        base.update(overrides)
        return json.dumps(base)

    def test_valid_json(self):
        result = _parse_style_json(self._valid_style_json())
        assert result["name"] == "Editorial Minimalista"
        assert result["colors"]["background"] == "warm ivory"

    def test_json_with_markdown_blocks(self):
        raw = f"```json\n{self._valid_style_json()}\n```"
        result = _parse_style_json(raw)
        assert result["name"] == "Editorial Minimalista"

    def test_json_with_generic_markdown(self):
        raw = f"```\n{self._valid_style_json()}\n```"
        result = _parse_style_json(raw)
        assert result["name"] == "Editorial Minimalista"

    def test_invalid_json_returns_default(self):
        result = _parse_style_json("this is not json")
        assert result["name"] == "Minimalista Profissional"
        assert "aesthetic" in result
        assert "colors" in result

    def test_empty_string_returns_default(self):
        result = _parse_style_json("")
        assert result["name"] == "Minimalista Profissional"

    def test_missing_fields_filled_with_defaults(self):
        partial = json.dumps({
            "name": "Meu Estilo",
            "aesthetic": "Bold colorful design",
        })
        result = _parse_style_json(partial)
        assert result["name"] == "Meu Estilo"
        assert result["aesthetic"] == "Bold colorful design"
        assert "background" in result["colors"]
        assert result["lighting"]
        assert result["typography"]
        assert result["composition"]

    def test_complete_json_not_modified(self):
        original = self._valid_style_json(name="Teste Completo")
        result = _parse_style_json(original)
        assert result["name"] == "Teste Completo"
        assert result["lighting"] == "soft overcast nordic daylight"

    def test_json_with_extra_whitespace(self):
        raw = f"  \n\n  {self._valid_style_json()}  \n\n  "
        result = _parse_style_json(raw)
        assert result["name"] == "Editorial Minimalista"


class TestDefaultStyle:
    """Testa que o estilo default e valido e completo."""

    def test_has_all_required_fields(self):
        style = _default_style()
        required = ["name", "aesthetic", "colors", "lighting", "typography", "composition"]
        for field in required:
            assert field in style, f"Campo '{field}' faltando no default"

    def test_colors_has_all_keys(self):
        colors = _default_style()["colors"]
        for key in ["background", "primary", "accent", "text"]:
            assert key in colors, f"Cor '{key}' faltando no default"

    def test_no_hex_in_default(self):
        style_str = json.dumps(_default_style())
        assert "#" not in style_str

    def test_colors_are_descriptive(self):
        colors = _default_style()["colors"]
        for key, value in colors.items():
            assert len(value) > 3, f"Cor '{key}' muito curta: '{value}'"
            assert " " in value, f"Cor '{key}' sem modificador: '{value}'"


class TestPromptTemplates:
    """Testa que os templates de prompt estao bem formados."""

    def test_system_prompt_is_english(self):
        assert "Art Director" in STYLE_GENERATION_PROMPT_SYSTEM

    def test_template_has_all_placeholders(self):
        required_placeholders = [
            "{business_name}",
            "{specialization}",
            "{colors_formatted}",
            "{tema_principal}",
            "{contexto_visual_sugerido}",
            "{emocoes_associadas}",
        ]
        for placeholder in required_placeholders:
            assert placeholder in STYLE_GENERATION_PROMPT_TEMPLATE, \
                f"Placeholder '{placeholder}' faltando no template"

    def test_template_mentions_memory_colors(self):
        assert "memory color" in STYLE_GENERATION_PROMPT_TEMPLATE.lower()

    def test_template_forbids_hex(self):
        assert "NEVER hex codes" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_requires_json_output(self):
        assert "JSON" in STYLE_GENERATION_PROMPT_TEMPLATE


class TestStyleDirections:
    """Testa o mapeamento de preferencias de estilo do onboarding."""

    def test_all_onboarding_styles_mapped(self):
        expected_ids = ["minimalista", "colorido", "elegante", "moderno", "rustico", "ousado"]
        for style_id in expected_ids:
            assert style_id in STYLE_DIRECTIONS, f"Estilo '{style_id}' nao mapeado"

    def test_each_direction_has_required_fields(self):
        required = ["direction", "references", "typography", "lighting", "avoid"]
        for style_id, direction in STYLE_DIRECTIONS.items():
            for field in required:
                assert field in direction, f"Campo '{field}' faltando em '{style_id}'"

    def test_directions_are_distinct(self):
        all_refs = [d["references"] for d in STYLE_DIRECTIONS.values()]
        assert len(set(all_refs)) == len(all_refs), "Referencias duplicadas entre estilos"

    def test_default_direction_has_required_fields(self):
        required = ["direction", "references", "typography", "lighting", "avoid"]
        for field in required:
            assert field in DEFAULT_STYLE_DIRECTION

    def test_colorido_avoids_muted(self):
        assert "muted" in STYLE_DIRECTIONS["colorido"]["avoid"].lower()

    def test_elegante_references_luxury(self):
        refs = STYLE_DIRECTIONS["elegante"]["references"].lower()
        assert "vogue" in refs or "chanel" in refs or "luxury" in refs

    def test_rustico_has_warm_lighting(self):
        assert "golden hour" in STYLE_DIRECTIONS["rustico"]["lighting"]


class TestGetStyleDirection:
    """Testa _get_style_direction com mocks."""

    @patch("services.style_generation_service.CreatorProfile")
    def test_returns_default_when_no_style_ids(self, mock_model):
        mock_profile = Mock()
        mock_profile.visual_style_ids = []
        mock_model.objects.get.return_value = mock_profile

        result = _get_style_direction(Mock())
        assert "Direction:" in result
        assert DEFAULT_STYLE_DIRECTION["direction"] in result

    @patch("services.style_generation_service.CreatorProfile")
    def test_returns_mapped_style(self, mock_model):
        mock_profile = Mock()
        mock_profile.visual_style_ids = ["ousado", "minimalista"]
        mock_model.objects.get.return_value = mock_profile

        result = _get_style_direction(Mock())
        assert "Nike" in result or "bold" in result.lower() or "impactful" in result.lower()

    @patch("services.style_generation_service.CreatorProfile")
    def test_returns_default_for_unknown_style(self, mock_model):
        mock_profile = Mock()
        mock_profile.visual_style_ids = ["estilo_inexistente"]
        mock_model.objects.get.return_value = mock_profile

        result = _get_style_direction(Mock())
        assert DEFAULT_STYLE_DIRECTION["direction"] in result


class TestGatherMarketContext:
    """Testa _gather_market_context com mocks."""

    @patch("ClientContext.models.ClientContext")
    def test_returns_market_data_when_available(self, mock_model):
        mock_context = Mock()
        mock_context.market_panorama = "The vegan food market is growing 15% YoY"
        mock_context.market_tendencies = ["plant-based protein", "sustainable packaging"]
        mock_context.discovered_trends = ["oat milk surge"]
        mock_context.brand_communication_style = "Warm and educational"
        mock_context.competition_strategies = "Competitors focus on price"
        mock_context.competition_opportunities = "Premium positioning available"
        mock_context.target_audience_behaviors = "Health-conscious millennials"
        mock_context.target_audience_interests = ["wellness", "sustainability"]
        mock_model.objects.filter.return_value.first.return_value = mock_context

        market, comp, audience = _gather_market_context(Mock())

        assert "vegan food market" in market
        assert "plant-based protein" in market
        assert "Competitors focus on price" in comp
        assert "Health-conscious millennials" in audience

    @patch("ClientContext.models.ClientContext")
    def test_returns_defaults_when_no_context(self, mock_model):
        mock_model.objects.filter.return_value.first.return_value = None

        market, comp, audience = _gather_market_context(Mock())

        assert "No market data" in market
        assert "No competition data" in comp
        assert audience == ""

    @patch("ClientContext.models.ClientContext")
    def test_handles_empty_fields(self, mock_model):
        mock_context = Mock()
        mock_context.market_panorama = ""
        mock_context.market_tendencies = []
        mock_context.discovered_trends = []
        mock_context.brand_communication_style = ""
        mock_context.competition_strategies = ""
        mock_context.competition_opportunities = ""
        mock_context.target_audience_behaviors = ""
        mock_context.target_audience_interests = []
        mock_model.objects.filter.return_value.first.return_value = mock_context

        market, comp, audience = _gather_market_context(Mock())

        assert "No market data" in market
        assert "No competition data" in comp
        assert audience == ""


class TestGatherPreviousStyles:
    """Testa _gather_previous_styles com mocks."""

    @patch("services.style_generation_service.GeneratedVisualStyle")
    def test_returns_previous_styles(self, mock_model):
        mock_style = Mock()
        mock_style.name = "Estilo Anterior"
        mock_style.style_data = {
            "aesthetic": "Bold geometric design with overlapping shapes and vivid colors",
            "colors": {"background": "deep navy", "primary": "bright coral"},
            "lighting": "dramatic side lighting with deep shadows",
        }

        mock_model.objects.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self, key: [mock_style]
        )

        result = _gather_previous_styles(Mock())

        assert "Estilo Anterior" in result
        assert "DIFFERENT" in result

    @patch("services.style_generation_service.GeneratedVisualStyle")
    def test_returns_creative_message_when_no_history(self, mock_model):
        mock_model.objects.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self, key: []
        )

        result = _gather_previous_styles(Mock())

        assert "first generation" in result
        assert "creative" in result.lower()


class TestFormatContentTypeContext:
    """Testa _format_content_type_context."""

    def test_empty_type_returns_empty(self):
        assert _format_content_type_context(None, None) == ""
        assert _format_content_type_context("", None) == ""

    def test_polemica_has_bold_guidance(self):
        result = _format_content_type_context("Polemica", 85)
        assert "Polemica" in result
        assert "attention-grabbing" in result or "contrast" in result.lower()
        assert "HIGH" in result

    def test_educativo_has_clarity_guidance(self):
        result = _format_content_type_context("Educativo", 60)
        assert "Educativo" in result
        assert "structured" in result.lower() or "readability" in result.lower()
        assert "MEDIUM" in result

    def test_low_score_moderate(self):
        result = _format_content_type_context("Futuro", 30)
        assert "MODERATE" in result
        assert "clarity" in result.lower() or "brand" in result.lower()


class TestPromptHasRationale:
    """Testa que o prompt inclui campo rationale e secoes de contexto."""

    def test_rationale_in_template_output(self):
        assert "rationale" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_system_prompt_mentions_reasoning(self):
        prompt_lower = STYLE_GENERATION_PROMPT_SYSTEM.lower()
        assert "reason" in prompt_lower or "analyze" in prompt_lower

    def test_template_has_audience_section(self):
        assert "TARGET AUDIENCE" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_has_market_section(self):
        assert "MARKET INTELLIGENCE" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_has_competition_section(self):
        assert "COMPETITION" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_has_previous_styles_section(self):
        assert "PREVIOUS STYLES" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_has_differentiation_rule(self):
        assert "DIFFERENTIATE" in STYLE_GENERATION_PROMPT_TEMPLATE


class TestGenerateStyleIntegration:
    """Testa generate_style com mock do ai_service."""

    @pytest.fixture
    def mock_ai_service(self):
        service = Mock()
        service.generate_text.return_value = json.dumps({
            "name": "Tech Futurista Azul",
            "aesthetic": "Futuristic tech design with geometric patterns",
            "colors": {
                "background": "deep midnight navy",
                "primary": "bright cobalt blue",
                "accent": "vivid coral",
                "text": "pure white",
            },
            "lighting": "cool ambient neon glow",
            "typography": "sleek sans-serif, thin weight",
            "composition": "title centered, geometric elements scattered",
            "mood": "innovative, cutting-edge",
            "references": ["sci-fi movie UI", "Apple product page"],
        })
        return service

    @pytest.fixture
    def semantic_analysis(self):
        return {
            "tema_principal": "Inteligencia Artificial nos negocios",
            "contexto_visual_sugerido": "Abstract neural network visualization",
            "objetos_relevantes": ["neural networks", "data streams", "circuits"],
            "emocoes_associadas": ["innovation", "excitement", "progress"],
            "sensacao_geral": "futuristic and innovative",
            "tons_de_cor_sugeridos": ["blue", "purple", "white"],
        }

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="Migration conflitante tendencies_data no banco de teste")
    def test_generate_style_creates_record(self, mock_ai_service, semantic_analysis):
        from django.contrib.auth.models import User
        from CreatorProfile.models import CreatorProfile, GeneratedVisualStyle

        user = User.objects.create_user("testuser", "test@test.com", "pass123")
        CreatorProfile.objects.create(
            user=user,
            business_name="TechCorp",
            specialization="Tecnologia",
            business_description="Empresa de tecnologia",
            voice_tone="Inovador",
        )

        from services.style_generation_service import generate_style
        style = generate_style(
            user=user,
            semantic_analysis=semantic_analysis,
            ai_service=mock_ai_service,
        )

        assert isinstance(style, GeneratedVisualStyle)
        assert style.name == "Tech Futurista Azul"
        assert style.user == user
        assert style.style_data["colors"]["background"] == "deep midnight navy"
        assert style.times_used == 1
        assert not style.is_favorite
        mock_ai_service.generate_text.assert_called_once()

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="Migration conflitante tendencies_data no banco de teste")
    def test_generate_style_with_source_post(self, mock_ai_service, semantic_analysis):
        from django.contrib.auth.models import User
        from CreatorProfile.models import CreatorProfile, GeneratedVisualStyle

        user = User.objects.create_user("testuser2", "test2@test.com", "pass123")
        CreatorProfile.objects.create(
            user=user,
            business_name="DesignCo",
            specialization="Design",
            business_description="Empresa de design",
            voice_tone="Criativo",
        )

        from services.style_generation_service import generate_style
        style = generate_style(
            user=user,
            semantic_analysis=semantic_analysis,
            ai_service=mock_ai_service,
            source_post_id=42,
        )

        assert style.source_post_id == 42

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="Migration conflitante tendencies_data no banco de teste")
    def test_generate_style_with_invalid_ai_response(self, semantic_analysis):
        from django.contrib.auth.models import User
        from CreatorProfile.models import CreatorProfile, GeneratedVisualStyle

        user = User.objects.create_user("testuser3", "test3@test.com", "pass123")
        CreatorProfile.objects.create(
            user=user,
            business_name="FallbackCo",
            specialization="Geral",
            business_description="Empresa geral",
            voice_tone="Neutro",
        )

        bad_ai = Mock()
        bad_ai.generate_text.return_value = "sorry I cannot generate JSON right now"

        from services.style_generation_service import generate_style
        style = generate_style(
            user=user,
            semantic_analysis=semantic_analysis,
            ai_service=bad_ai,
        )

        assert isinstance(style, GeneratedVisualStyle)
        assert style.name == "Minimalista Profissional"
        assert "warm ivory" in style.style_data["colors"]["background"]


class TestGatherPreviousStylesWithFeedback:
    """Testa _gather_previous_styles com feedback signals."""

    @patch("services.style_generation_service.GeneratedVisualStyle")
    def test_separates_by_feedback_signal(self, mock_model):
        accepted = Mock()
        accepted.name = "Aceito"
        accepted.feedback_signal = "accepted"
        accepted.style_data = {
            "aesthetic": "Bold design",
            "colors": {"background": "deep navy", "primary": "coral"},
            "lighting": "dramatic",
        }

        rejected = Mock()
        rejected.name = "Rejeitado"
        rejected.feedback_signal = "rejected"
        rejected.style_data = {
            "aesthetic": "Minimal design",
            "colors": {"background": "ivory", "primary": "blue"},
            "lighting": "soft",
        }

        pending = Mock()
        pending.name = "Pendente"
        pending.feedback_signal = "pending"
        pending.style_data = {
            "aesthetic": "Clean design",
            "colors": {"background": "white", "primary": "green"},
            "lighting": "flat",
        }

        mock_model.objects.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self, key: [accepted, rejected, pending]
        )

        result = _gather_previous_styles(Mock())

        assert "LIKED" in result
        assert "REJECTED" in result
        assert "no feedback" in result
        assert "Aceito" in result
        assert "Rejeitado" in result
        assert "Pendente" in result

    @patch("services.style_generation_service.GeneratedVisualStyle")
    def test_all_pending_keeps_original_behavior(self, mock_model):
        style = Mock()
        style.name = "Pendente"
        style.feedback_signal = "pending"
        style.style_data = {
            "aesthetic": "Clean design",
            "colors": {"background": "white", "primary": "green"},
            "lighting": "flat",
        }

        mock_model.objects.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self, key: [style]
        )

        result = _gather_previous_styles(Mock())

        assert "DIFFERENT" in result
        assert "LIKED" not in result


class TestGatherFavoriteStyles:
    """Testa _gather_favorite_styles."""

    @patch("services.style_generation_service.GeneratedVisualStyle")
    def test_returns_favorites(self, mock_model):
        fav = Mock()
        fav.name = "Estilo Favorito"
        fav.style_data = {
            "aesthetic": "Beautiful editorial",
            "colors": {"primary": "coral", "accent": "gold"},
            "mood": "elegant, warm",
        }

        mock_model.objects.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self, key: [fav]
        )

        result = _gather_favorite_styles(Mock())

        assert "Estilo Favorito" in result
        assert "DNA" in result

    @patch("services.style_generation_service.GeneratedVisualStyle")
    def test_returns_message_when_no_favorites(self, mock_model):
        mock_model.objects.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self, key: []
        )

        result = _gather_favorite_styles(Mock())

        assert "No favorite" in result


class TestGatherPerformanceData:
    """Testa _gather_performance_data."""

    @patch("services.style_generation_service.GeneratedVisualStyle")
    def test_returns_top_performers(self, mock_model):
        style = Mock()
        style.name = "Top Performer"
        style.engagement_score = 8.5
        style.style_data = {"aesthetic": "Striking bold design"}

        mock_model.objects.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self, key: [style]
        )

        result = _gather_performance_data(Mock())

        assert "Top Performer" in result
        assert "8.5" in result

    @patch("services.style_generation_service.GeneratedVisualStyle")
    def test_returns_empty_when_no_data(self, mock_model):
        mock_model.objects.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self, key: []
        )

        result = _gather_performance_data(Mock())

        assert result == ""


class TestNewPromptSections:
    """Testa que o template tem as novas secoes."""

    def test_template_has_favorite_styles_section(self):
        assert "FAVORITE STYLES" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_has_performance_section(self):
        assert "TOP PERFORMING STYLES" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_has_favorite_dna_rule(self):
        assert "share DNA" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_has_favorite_placeholder(self):
        assert "{favorite_styles}" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_has_performance_placeholder(self):
        assert "{performance_data}" in STYLE_GENERATION_PROMPT_TEMPLATE
