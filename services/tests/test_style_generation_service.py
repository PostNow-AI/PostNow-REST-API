"""Testes para style_generation_service — geração de estilo visual via IA."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from services.style_generation_service import (
    _parse_style_json,
    _default_style,
    STYLE_GENERATION_PROMPT_SYSTEM,
    STYLE_GENERATION_PROMPT_TEMPLATE,
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
        """JSON parcial deve ter campos faltantes preenchidos."""
        partial = json.dumps({
            "name": "Meu Estilo",
            "aesthetic": "Bold colorful design",
            # faltam: colors, lighting, typography, composition
        })
        result = _parse_style_json(partial)
        assert result["name"] == "Meu Estilo"
        assert result["aesthetic"] == "Bold colorful design"
        assert "background" in result["colors"]
        assert result["lighting"]
        assert result["typography"]
        assert result["composition"]

    def test_complete_json_not_modified(self):
        """JSON completo não deve ser alterado."""
        original = self._valid_style_json(name="Teste Completo")
        result = _parse_style_json(original)
        assert result["name"] == "Teste Completo"
        assert result["lighting"] == "soft overcast nordic daylight"

    def test_json_with_extra_whitespace(self):
        raw = f"  \n\n  {self._valid_style_json()}  \n\n  "
        result = _parse_style_json(raw)
        assert result["name"] == "Editorial Minimalista"


class TestDefaultStyle:
    """Testa que o estilo default é válido e completo."""

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
        """Default não deve conter hex codes."""
        style_str = json.dumps(_default_style())
        assert "#" not in style_str

    def test_colors_are_descriptive(self):
        """Cores devem ser memory colors, não hex ou CSS3 genéricos."""
        colors = _default_style()["colors"]
        for key, value in colors.items():
            assert len(value) > 3, f"Cor '{key}' muito curta: '{value}'"
            assert " " in value, f"Cor '{key}' sem modificador: '{value}'"


class TestPromptTemplates:
    """Testa que os templates de prompt estão bem formados."""

    def test_system_prompt_is_english(self):
        assert "Senior Art Director" in STYLE_GENERATION_PROMPT_SYSTEM

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
        assert "NEVER use hex" in STYLE_GENERATION_PROMPT_TEMPLATE

    def test_template_requires_json_output(self):
        assert "JSON" in STYLE_GENERATION_PROMPT_TEMPLATE


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
            "tema_principal": "Inteligência Artificial nos negócios",
            "contexto_visual_sugerido": "Abstract neural network visualization",
            "objetos_relevantes": ["neural networks", "data streams", "circuits"],
            "emoções_associadas": ["innovation", "excitement", "progress"],
            "sensação_geral": "futuristic and innovative",
            "tons_de_cor_sugeridos": ["blue", "purple", "white"],
        }

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="Migration conflitante tendencies_data no banco de teste (pré-existente)")
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
    @pytest.mark.xfail(reason="Migration conflitante tendencies_data no banco de teste (pré-existente)")
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
    @pytest.mark.xfail(reason="Migration conflitante tendencies_data no banco de teste (pré-existente)")
    def test_generate_style_with_invalid_ai_response(self, semantic_analysis):
        """Quando a IA retorna JSON inválido, usa fallback."""
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
        assert style.name == "Minimalista Profissional"  # fallback
        assert "warm ivory" in style.style_data["colors"]["background"]
