"""
Opportunity Aggregator - Handles opportunity grouping and ranking.
Follows Single Responsibility Principle.
"""
import logging
from typing import Optional
from urllib.parse import urlparse

from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.url_validators import coerce_url_to_str
from ClientContext.services.url_processing_service import UrlProcessingService

logger = logging.getLogger(__name__)


# Type category mapping
TYPE_CATEGORIES = {
    'polemica': {
        'keywords': ['Polêmica', 'Debate'],
        'display': '🔥 Polêmica & Debate'
    },
    'educativo': {
        'keywords': ['Educativo', 'How-to'],
        'display': '🧠 Educativo & Utilidade'
    },
    'newsjacking': {
        'keywords': ['Newsjacking', 'Urgência', 'Atualidade'],
        'display': '📰 Newsjacking (Urgente)'
    },
    'entretenimento': {
        'keywords': ['Entretenimento', 'Meme'],
        'display': '😂 Entretenimento & Conexão'
    },
    'estudo_caso': {
        'keywords': ['Estudo de Caso'],
        'display': '💼 Estudo de Caso'
    },
    'futuro': {
        'keywords': ['Futuro', 'Tendência'],
        'display': '🔮 Futuro & Tendências'
    },
}

EMOJI_CHARS = ['🔥', '🧠', '📰', '😂', '💼', '🔮']


class OpportunityAggregator:
    """Aggregates and ranks opportunities from multiple sections."""

    def __init__(
        self,
        url_processor: Optional[UrlProcessingService] = None,
        top_per_category: int = 3
    ):
        self.url_processor = url_processor or UrlProcessingService()
        self.top_per_category = top_per_category

    async def aggregate_and_rank(
        self,
        context_data: dict,
        search_results_map: dict,
        recent_used_url_keys: Optional[set[str]] = None
    ) -> dict:
        """
        Aggregate opportunities from all sections, group by type, and rank.

        Returns:
            dict: Grouped and ranked opportunities
        """
        recent_used_url_keys = recent_used_url_keys or set()
        used_url_keys_email: set[str] = set()

        # 1. Collect opportunities from all sections
        all_opportunities = await self._collect_opportunities(
            context_data,
            search_results_map,
            recent_used_url_keys,
            used_url_keys_email
        )

        # 2. Group by type
        grouped = self._group_by_type(all_opportunities)

        # 3. Sort and select top items
        return self._select_top_items(grouped)

    async def _collect_opportunities(
        self,
        context_data: dict,
        search_results_map: dict,
        recent_used_url_keys: set[str],
        used_url_keys_email: set[str]
    ) -> list[dict]:
        """Collect and validate opportunities from all sections."""
        all_opportunities = []
        sections = ['mercado', 'tendencias', 'concorrencia']

        for section in sections:
            section_data = context_data.get(section, {})
            real_urls = search_results_map.get(section, [])

            # Prepare candidate URLs
            candidate_urls = self.url_processor.prepare_candidate_urls(real_urls, section)

            # Process sources with new schema
            if isinstance(section_data, dict) and 'fontes_analisadas' in section_data:
                section_ops = await self._process_section_sources(
                    section=section,
                    fontes=section_data['fontes_analisadas'],
                    real_urls=real_urls,
                    candidate_urls=candidate_urls,
                    recent_used_url_keys=recent_used_url_keys,
                    used_url_keys_email=used_url_keys_email
                )
                all_opportunities.extend(section_ops)

        return all_opportunities

    async def _process_section_sources(
        self,
        section: str,
        fontes: list,
        real_urls: list,
        candidate_urls: list[str],
        recent_used_url_keys: set[str],
        used_url_keys_email: set[str]
    ) -> list[dict]:
        """Process sources from a single section."""
        opportunities = []

        for fonte in fontes:
            ai_url = fonte.get('url_original', '')

            # Validate and recover URL
            url_fonte = await self.url_processor.validate_and_recover_url(
                ai_url=ai_url,
                candidate_urls=candidate_urls,
                real_urls_pool=real_urls,
                used_keys_email=used_url_keys_email,
                used_keys_recent=recent_used_url_keys,
                section=section
            )

            if not url_fonte:
                continue

            # Mark URL as used
            url_key = normalize_url_key(url_fonte)
            if url_key:
                used_url_keys_email.add(url_key)

            # Extract opportunities from this source
            for op in fonte.get('oportunidades', []):
                op['url_fonte'] = url_fonte
                op['origem_secao'] = section
                opportunities.append(op)

        return opportunities

    def _group_by_type(self, opportunities: list[dict]) -> dict:
        """Group opportunities by their type category."""
        grouped = {}

        for op in opportunities:
            key, display_title = self._categorize_type(op.get('tipo', 'Outros'))

            if key not in grouped:
                grouped[key] = {
                    'titulo': display_title,
                    'items': []
                }

            # Ensure score is integer
            op['score'] = self._parse_score(op.get('score', 0))
            grouped[key]['items'].append(op)

        return grouped

    def _categorize_type(self, raw_type: str) -> tuple[str, str]:
        """Categorize a type string into a standard category."""
        # Clean type (remove emojis)
        clean_type = raw_type
        for emoji in EMOJI_CHARS:
            clean_type = clean_type.replace(emoji, '').strip()

        # Match against known categories
        for key, config in TYPE_CATEGORIES.items():
            for keyword in config['keywords']:
                if keyword in clean_type:
                    return key, config['display']

        # Default category
        return 'outros', '⚡ Outras Oportunidades'

    def _parse_score(self, score) -> int:
        """Safely parse score to integer."""
        try:
            return int(score)
        except (ValueError, TypeError):
            return 0

    def _select_top_items(self, grouped: dict) -> dict:
        """Sort and select top items from each category."""
        final = {}

        for key, group in grouped.items():
            # Sort by score descending
            sorted_items = sorted(
                group['items'],
                key=lambda x: x['score'],
                reverse=True
            )
            # Keep top N
            group['items'] = sorted_items[:self.top_per_category]
            final[key] = group

        return final
