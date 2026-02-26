"""Utilitarios do modulo ClientContext."""

from .context_mapping import CONTEXT_FIELD_MAPPING
from .json_parser import extract_json_block, parse_ai_json_response, safe_json_loads
from .history_utils import get_recent_topics, get_recent_url_keys
from .data_extraction import (
    extract_from_opportunities,
    normalize_section_structure,
    generate_hashtags_from_opportunities,
    generate_keywords_from_opportunities,
)

__all__ = [
    'CONTEXT_FIELD_MAPPING',
    'parse_ai_json_response',
    'extract_json_block',
    'safe_json_loads',
    # History utils
    'get_recent_topics',
    'get_recent_url_keys',
    # Data extraction utils
    'extract_from_opportunities',
    'normalize_section_structure',
    'generate_hashtags_from_opportunities',
    'generate_keywords_from_opportunities',
]
