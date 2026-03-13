"""
Validação de texto renderizado em imagens geradas por IA.

Envia a imagem de volta ao Gemini para ler o texto renderizado,
compara com o esperado, e solicita regeneração se houver erros.
"""

import logging

from google.genai import types

logger = logging.getLogger(__name__)

VALIDATION_PROMPT = """
Look at this image carefully and extract ALL text that is rendered/written in the image.
Return ONLY the extracted text, exactly as it appears, one line per text block.
Do not add any explanation or commentary — just the text you see.
If there is no text, return "NO_TEXT".
"""

CORRECTION_INSTRUCTION = """
CRITICAL TEXT CORRECTION:
The previous image had text errors. The rendered text said "{wrong_text}"
but it MUST say "{correct_text}" — fix the spelling exactly.
Regenerate the image with the corrected text. Keep everything else the same.
"""


MAX_VALIDATION_RETRIES = 1

IMAGE_GEN_CONFIG_4_5 = types.GenerateContentConfig(
    temperature=0.7,
    top_p=0.9,
    response_modalities=["IMAGE"],
    image_config=types.ImageConfig(aspect_ratio="4:5"),
)


def generate_image_with_validation(
    ai_service,
    image_prompt: list[str],
    user_logo: str | None,
    user,
    config,
    expected_texts: list[str] | None = None,
) -> bytes | None:
    """
    Gera imagem e valida o texto renderizado, com retry automático.

    Se expected_texts for fornecido, extrai o texto da imagem gerada,
    compara com o esperado, e regenera com correção se houver erros.

    Returns:
        Bytes da imagem final (validada ou melhor tentativa), ou None.
    """
    image_result = ai_service.generate_image(image_prompt, user_logo, user, config)

    if not image_result or not expected_texts:
        return image_result

    for attempt in range(MAX_VALIDATION_RETRIES):
        validation = validate_image_text(image_result, expected_texts, ai_service)

        if validation["valid"]:
            logger.info("Image text validated OK (attempt %d)", attempt + 1)
            return image_result

        logger.info(
            "Text errors in image (attempt %d/%d): %s",
            attempt + 1,
            MAX_VALIDATION_RETRIES,
            validation["errors"],
        )

        corrected_prompt = build_correction_prompt(image_prompt, validation["errors"])
        retry_result = ai_service.generate_image(corrected_prompt, user_logo, user, config)

        if retry_result:
            image_result = retry_result
        else:
            logger.warning("Retry image generation returned None, keeping previous result")

    return image_result


def validate_image_text(
    image_bytes: bytes,
    expected_texts: list[str],
    ai_service,
) -> dict:
    """
    Valida o texto renderizado em uma imagem gerada.

    Args:
        image_bytes: Bytes da imagem PNG gerada
        expected_texts: Lista de textos que deveriam estar na imagem
        ai_service: Instância de AiService

    Returns:
        {
            "valid": bool,
            "extracted_text": str,
            "errors": [{"expected": str, "found": str}]
        }
    """
    if not image_bytes or not expected_texts:
        return {"valid": True, "extracted_text": "", "errors": []}

    try:
        extracted = _extract_text_from_image(image_bytes, ai_service)
    except Exception as e:
        logger.warning("Falha ao extrair texto da imagem: %s", e)
        return {"valid": True, "extracted_text": "", "errors": []}

    if extracted == "NO_TEXT":
        return {"valid": True, "extracted_text": "", "errors": []}

    errors = _find_text_errors(extracted, expected_texts)

    return {
        "valid": len(errors) == 0,
        "extracted_text": extracted,
        "errors": errors,
    }


def build_correction_prompt(
    original_prompt: list[str],
    errors: list[dict],
) -> list[str]:
    """
    Adiciona instrução de correção ao prompt original.

    Args:
        original_prompt: Prompt original que gerou a imagem
        errors: Lista de erros do validate_image_text

    Returns:
        Novo prompt com instrução de correção prepended
    """
    corrections = []
    for error in errors:
        corrections.append(
            CORRECTION_INSTRUCTION.format(
                wrong_text=error["found"],
                correct_text=error["expected"],
            )
        )

    correction_block = "\n".join(corrections)
    corrected_prompt = [correction_block + "\n\n" + original_prompt[0]]
    return corrected_prompt


def _extract_text_from_image(
    image_bytes: bytes,
    ai_service,
) -> str:
    """Envia imagem ao Gemini e pede para ler o texto."""
    contents = types.Content(
        role="user",
        parts=[
            types.Part.from_bytes(mime_type="image/png", data=image_bytes),
            types.Part.from_text(text=VALIDATION_PROMPT),
        ],
    )

    config = types.GenerateContentConfig(
        response_modalities=["TEXT"],
        temperature=0.1,
    )

    response_text = ""
    for chunk in ai_service.client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    ):
        if (
            hasattr(chunk, "candidates")
            and chunk.candidates
            and chunk.candidates[0].content
            and chunk.candidates[0].content.parts
        ):
            part = chunk.candidates[0].content.parts[0]
            if hasattr(part, "text") and part.text:
                response_text += part.text

    return response_text.strip()


def _find_text_errors(
    extracted: str,
    expected_texts: list[str],
) -> list[dict]:
    """
    Compara texto extraído com textos esperados.
    Usa matching fuzzy — procura cada palavra esperada no texto extraído.
    """
    errors = []
    extracted_upper = extracted.upper()

    for expected in expected_texts:
        expected_words = expected.upper().split()
        if len(expected_words) == 0:
            continue

        # Verifica se todas as palavras do texto esperado estão na imagem
        missing_words = [w for w in expected_words if w not in extracted_upper]

        if missing_words:
            # Tenta encontrar o que foi renderizado no lugar
            found_line = _find_closest_line(extracted, expected)
            if found_line and found_line.upper() != expected.upper():
                errors.append({
                    "expected": expected,
                    "found": found_line,
                })

    return errors


def _find_closest_line(extracted: str, expected: str) -> str | None:
    """Encontra a linha do texto extraído mais parecida com o esperado."""
    lines = extracted.strip().split("\n")
    expected_words = set(expected.upper().split())

    best_match = None
    best_score = 0

    for line in lines:
        line_words = set(line.upper().split())
        # Score = palavras em comum
        common = len(expected_words & line_words)
        if common > best_score:
            best_score = common
            best_match = line.strip()

    # Só retorna se tiver pelo menos 1 palavra em comum
    return best_match if best_score > 0 else None
