"""Testes para color_extraction — conversão HEX → memory colors."""

import pytest

from services.color_extraction import (
    hex_to_memory_color,
    format_colors_for_prompt,
    _hex_to_rgb,
    _rgb_to_hsl,
    _match_memory_color,
)


class TestHexToRgb:
    def test_basic_colors(self):
        assert _hex_to_rgb("#FF0000") == (255, 0, 0)
        assert _hex_to_rgb("#00FF00") == (0, 255, 0)
        assert _hex_to_rgb("#0000FF") == (0, 0, 255)

    def test_black_white(self):
        assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert _hex_to_rgb("#000000") == (0, 0, 0)

    def test_without_hash(self):
        assert _hex_to_rgb("FF0000") == (255, 0, 0)


class TestRgbToHsl:
    def test_pure_red(self):
        h, s, l = _rgb_to_hsl(255, 0, 0)
        assert h == pytest.approx(0.0, abs=1.0)
        assert s == pytest.approx(1.0, abs=0.01)
        assert l == pytest.approx(0.5, abs=0.01)

    def test_pure_white(self):
        h, s, l = _rgb_to_hsl(255, 255, 255)
        assert l == pytest.approx(1.0, abs=0.01)

    def test_pure_black(self):
        h, s, l = _rgb_to_hsl(0, 0, 0)
        assert l == pytest.approx(0.0, abs=0.01)

    def test_gray(self):
        h, s, l = _rgb_to_hsl(128, 128, 128)
        assert s == pytest.approx(0.0, abs=0.01)


class TestHexToMemoryColor:
    """Testa conversão de hex para memory colors descritivos."""

    def test_pure_white(self):
        assert hex_to_memory_color("#FFFFFF") == "pure white"

    def test_pure_black(self):
        assert hex_to_memory_color("#000000") == "pure black"

    def test_terracotta(self):
        """#E07A5F era 'salmon' no CSS3 — agora deve ser terracotta."""
        result = hex_to_memory_color("#E07A5F")
        assert "terracotta" in result

    def test_dark_green_not_gray(self):
        """#7C9070 era 'gray' no CSS3 — agora deve ter 'green'."""
        result = hex_to_memory_color("#7C9070")
        assert "green" in result or "forest" in result

    def test_wine_not_saddlebrown(self):
        """#722F37 era 'saddlebrown' no CSS3 — agora deve ser wine/burgundy."""
        result = hex_to_memory_color("#722F37")
        assert "wine" in result or "burgundy" in result

    def test_midnight_navy_not_black(self):
        """#1A1A2E era 'black' no CSS3 — agora deve ter navy."""
        result = hex_to_memory_color("#1A1A2E")
        assert "navy" in result or "midnight" in result

    def test_gold(self):
        result = hex_to_memory_color("#D4AF37")
        assert "gold" in result

    def test_hot_pink(self):
        result = hex_to_memory_color("#FF1493")
        assert "pink" in result or "hot" in result

    def test_scarlet_red(self):
        result = hex_to_memory_color("#FF0000")
        assert "scarlet" in result or "red" in result

    def test_butter_yellow(self):
        result = hex_to_memory_color("#FFEAA7")
        assert "butter" in result or "yellow" in result

    def test_lilac(self):
        result = hex_to_memory_color("#DDA0DD")
        assert "lilac" in result or "lavender" in result

    def test_empty_hex(self):
        assert hex_to_memory_color("") == "neutral gray"
        assert hex_to_memory_color(None) == "neutral gray"

    def test_invalid_hex(self):
        assert hex_to_memory_color("not-a-color") == "neutral gray"

    def test_without_hash_prefix(self):
        result = hex_to_memory_color("FF0000")
        assert "scarlet" in result or "red" in result

    def test_returns_string(self):
        """Todas as cores devem retornar string não vazia."""
        test_colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
        ]
        for hex_code in test_colors:
            result = hex_to_memory_color(hex_code)
            assert isinstance(result, str)
            assert len(result) > 0
            assert "#" not in result  # nunca retorna hex


class TestFormatColorsForPrompt:
    def test_basic_palette(self):
        result = format_colors_for_prompt(["#FF0000", "#00FF00"])
        assert "- " in result
        lines = result.strip().split("\n")
        assert len(lines) == 2

    def test_empty_palette(self):
        assert format_colors_for_prompt([]) == "- neutral colors"
        assert format_colors_for_prompt(None) == "- neutral colors"

    def test_palette_with_nones(self):
        result = format_colors_for_prompt(["#FF0000", None, "#0000FF", None, None])
        lines = result.strip().split("\n")
        assert len(lines) == 2  # apenas as 2 cores válidas

    def test_no_hex_in_output(self):
        """O output nunca deve conter códigos hex."""
        result = format_colors_for_prompt(["#FF6B6B", "#4ECDC4", "#1A1A2E"])
        assert "#" not in result

    def test_five_color_palette(self):
        palette = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
        result = format_colors_for_prompt(palette)
        lines = result.strip().split("\n")
        assert len(lines) == 5
        for line in lines:
            assert line.startswith("- ")
