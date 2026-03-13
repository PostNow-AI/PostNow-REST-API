"""Testes para image_text_validator — validação de texto em imagens geradas."""

from unittest.mock import Mock, patch

from services.image_text_validator import (
    validate_image_text,
    build_correction_prompt,
    generate_image_with_validation,
    _find_text_errors,
    _find_closest_line,
    IMAGE_GEN_CONFIG_4_5,
)


class TestValidateImageText:
    """Testes para validate_image_text."""

    def test_empty_image_bytes_returns_valid(self):
        result = validate_image_text(b"", ["test"], Mock())
        assert result["valid"] is True

    def test_empty_expected_texts_returns_valid(self):
        result = validate_image_text(b"fake_image", [], Mock())
        assert result["valid"] is True

    def test_none_image_bytes_returns_valid(self):
        result = validate_image_text(None, ["test"], Mock())
        assert result["valid"] is True

    def test_none_expected_texts_returns_valid(self):
        result = validate_image_text(b"fake_image", None, Mock())
        assert result["valid"] is True

    @patch("services.image_text_validator._extract_text_from_image")
    def test_no_text_in_image_returns_valid(self, mock_extract):
        mock_extract.return_value = "NO_TEXT"
        result = validate_image_text(b"img", ["test"], Mock())
        assert result["valid"] is True
        assert result["extracted_text"] == ""

    @patch("services.image_text_validator._extract_text_from_image")
    def test_matching_text_returns_valid(self, mock_extract):
        mock_extract.return_value = "SUPREN VEG"
        result = validate_image_text(b"img", ["SUPREN VEG"], Mock())
        assert result["valid"] is True
        assert result["extracted_text"] == "SUPREN VEG"

    @patch("services.image_text_validator._extract_text_from_image")
    def test_mismatched_text_returns_invalid(self, mock_extract):
        mock_extract.return_value = "SUPREN VGE"
        result = validate_image_text(b"img", ["SUPREN VEG"], Mock())
        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["expected"] == "SUPREN VEG"
        assert result["errors"][0]["found"] == "SUPREN VGE"

    @patch("services.image_text_validator._extract_text_from_image")
    def test_extraction_failure_returns_valid(self, mock_extract):
        mock_extract.side_effect = Exception("API error")
        result = validate_image_text(b"img", ["test"], Mock())
        assert result["valid"] is True


class TestFindTextErrors:
    """Testes para _find_text_errors."""

    def test_all_words_present_no_errors(self):
        errors = _find_text_errors("SUPREN VEG ALIMENTOS", ["SUPREN VEG"])
        assert errors == []

    def test_case_insensitive_matching(self):
        errors = _find_text_errors("supren veg", ["SUPREN VEG"])
        assert errors == []

    def test_missing_word_reports_error(self):
        errors = _find_text_errors("SUPREN VGE", ["SUPREN VEG"])
        assert len(errors) == 1
        assert errors[0]["expected"] == "SUPREN VEG"

    def test_empty_expected_text_ignored(self):
        errors = _find_text_errors("SOME TEXT", [""])
        assert errors == []

    def test_multiple_expected_texts(self):
        extracted = "SUPREN VEG\nCOMIDA SAUDAVEL"
        errors = _find_text_errors(extracted, ["SUPREN VEG", "COMIDA SAUDAVEL"])
        assert errors == []

    def test_partial_match_reports_error(self):
        extracted = "SUPREN VGE\nCOMIDA SAUDAVEL"
        errors = _find_text_errors(extracted, ["SUPREN VEG", "COMIDA SAUDAVEL"])
        assert len(errors) == 1
        assert errors[0]["expected"] == "SUPREN VEG"


class TestFindClosestLine:
    """Testes para _find_closest_line."""

    def test_exact_match(self):
        result = _find_closest_line("SUPREN VEG\nOUTRA LINHA", "SUPREN VEG")
        assert result == "SUPREN VEG"

    def test_partial_match_returns_best(self):
        result = _find_closest_line("SUPREN VGE\nALGO DIFERENTE", "SUPREN VEG")
        assert result == "SUPREN VGE"

    def test_no_match_returns_none(self):
        result = _find_closest_line("TOTALMENTE DIFERENTE", "SUPREN VEG")
        assert result is None

    def test_best_score_wins(self):
        result = _find_closest_line(
            "WORD1\nWORD1 WORD2\nWORD1 WORD2 WORD3",
            "WORD1 WORD2 WORD3"
        )
        assert result == "WORD1 WORD2 WORD3"


class TestBuildCorrectionPrompt:
    """Testes para build_correction_prompt."""

    def test_single_error(self):
        original = ["Generate an image with text SUPREN VEG"]
        errors = [{"expected": "SUPREN VEG", "found": "SUPREN VGE"}]
        result = build_correction_prompt(original, errors)
        assert len(result) == 1
        assert "SUPREN VGE" in result[0]
        assert "SUPREN VEG" in result[0]
        assert "Generate an image" in result[0]

    def test_multiple_errors(self):
        original = ["original prompt text"]
        errors = [
            {"expected": "SUPREN VEG", "found": "SUPREN VGE"},
            {"expected": "ALIMENTOS", "found": "ALMNETOS"},
        ]
        result = build_correction_prompt(original, errors)
        assert "SUPREN VGE" in result[0]
        assert "ALMNETOS" in result[0]

    def test_correction_prepended_to_original(self):
        original = ["ORIGINAL PROMPT HERE"]
        errors = [{"expected": "A", "found": "B"}]
        result = build_correction_prompt(original, errors)
        assert result[0].endswith("ORIGINAL PROMPT HERE")


class TestGenerateImageWithValidation:
    """Testes para generate_image_with_validation."""

    def _mock_ai(self, image_bytes=b"fake_image"):
        ai = Mock()
        ai.generate_image.return_value = image_bytes
        return ai

    def test_no_expected_texts_skips_validation(self):
        ai = self._mock_ai()
        result = generate_image_with_validation(
            ai, ["prompt"], None, Mock(), IMAGE_GEN_CONFIG_4_5,
        )
        assert result == b"fake_image"
        ai.generate_image.assert_called_once()

    def test_none_image_result_returns_none(self):
        ai = Mock()
        ai.generate_image.return_value = None
        result = generate_image_with_validation(
            ai, ["prompt"], None, Mock(), IMAGE_GEN_CONFIG_4_5,
            expected_texts=["test"],
        )
        assert result is None

    @patch("services.image_text_validator.validate_image_text")
    def test_valid_text_returns_image_without_retry(self, mock_validate):
        mock_validate.return_value = {"valid": True, "extracted_text": "OK", "errors": []}
        ai = self._mock_ai()

        result = generate_image_with_validation(
            ai, ["prompt"], None, Mock(), IMAGE_GEN_CONFIG_4_5,
            expected_texts=["test"],
        )

        assert result == b"fake_image"
        ai.generate_image.assert_called_once()

    @patch("services.image_text_validator.validate_image_text")
    def test_invalid_text_triggers_retry(self, mock_validate):
        mock_validate.return_value = {
            "valid": False,
            "extracted_text": "SUPREN VGE",
            "errors": [{"expected": "SUPREN VEG", "found": "SUPREN VGE"}],
        }
        ai = Mock()
        ai.generate_image.side_effect = [b"bad_image", b"good_image"]

        result = generate_image_with_validation(
            ai, ["prompt"], None, Mock(), IMAGE_GEN_CONFIG_4_5,
            expected_texts=["SUPREN VEG"],
        )

        assert result == b"good_image"
        assert ai.generate_image.call_count == 2

    @patch("services.image_text_validator.validate_image_text")
    def test_retry_failure_keeps_previous_image(self, mock_validate):
        mock_validate.return_value = {
            "valid": False,
            "extracted_text": "BAD",
            "errors": [{"expected": "GOOD", "found": "BAD"}],
        }
        ai = Mock()
        ai.generate_image.side_effect = [b"first_image", None]

        result = generate_image_with_validation(
            ai, ["prompt"], None, Mock(), IMAGE_GEN_CONFIG_4_5,
            expected_texts=["GOOD"],
        )

        assert result == b"first_image"

    @patch("services.image_text_validator.validate_image_text")
    def test_retry_uses_correction_prompt(self, mock_validate):
        mock_validate.return_value = {
            "valid": False,
            "extracted_text": "VGE",
            "errors": [{"expected": "VEG", "found": "VGE"}],
        }
        ai = Mock()
        ai.generate_image.side_effect = [b"img1", b"img2"]

        generate_image_with_validation(
            ai, ["original prompt"], None, Mock(), IMAGE_GEN_CONFIG_4_5,
            expected_texts=["VEG"],
        )

        retry_call = ai.generate_image.call_args_list[1]
        retry_prompt = retry_call[0][0]
        assert "VGE" in retry_prompt[0]
        assert "VEG" in retry_prompt[0]
        assert "original prompt" in retry_prompt[0]
