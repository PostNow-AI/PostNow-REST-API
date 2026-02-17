"""
Service for aggregating and ranking opportunities from Weekly Context data.
"""
import logging
from typing import Optional
from urllib.parse import urlparse

from ClientContext.utils.source_quality import is_denied, pick_candidates
from ClientContext.utils.text_utils import is_blocked_filetype
from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.url_validation import (
    coerce_url_to_str,
    recover_url,
    validate_url_permissive_async,
)

logger = logging.getLogger(__name__)


class OpportunityRankingService:
    """Service for aggregating and ranking content opportunities."""

    async def aggregate_and_rank_opportunities(
        self,
        context_data: dict,
        search_results_map: dict,
        recent_used_url_keys: Optional[set[str]] = None
    ) -> dict:
        """
        Aggregate opportunities from all sections (Mercado, Concorrência, Tendências),
        classify by type and select Top 3 of each category based on Score.
        Validates URLs using requests HEAD/GET and attempts recovery with real URLs.
        """
        all_opportunities = []
        used_url_keys_email: set[str] = set()
        recent_used_url_keys = recent_used_url_keys or set()

        for section in ['mercado', 'tendencias', 'concorrencia']:
            section_data = context_data.get(section, {})
            real_urls_for_section = search_results_map.get(section, [])
            candidate_urls = self._get_candidate_urls(section, real_urls_for_section)

            if isinstance(section_data, dict) and 'fontes_analisadas' in section_data:
                for fonte in section_data['fontes_analisadas']:
                    url_fonte = await self._process_fonte_url(
                        fonte,
                        section,
                        candidate_urls,
                        real_urls_for_section,
                        used_url_keys_email,
                        recent_used_url_keys
                    )

                    if not url_fonte:
                        continue

                    final_key = normalize_url_key(url_fonte)
                    if final_key:
                        used_url_keys_email.add(final_key)

                    for op in fonte.get('oportunidades', []):
                        op['url_fonte'] = url_fonte
                        op['origem_secao'] = section
                        all_opportunities.append(op)

        grouped_ops = self._group_by_type(all_opportunities)
        return self._sort_and_filter(grouped_ops)

    def _get_candidate_urls(self, section: str, real_urls_for_section: list) -> list:
        """Get and filter candidate URLs for a section."""
        candidate_urls = []
        for item in (real_urls_for_section or []):
            u = coerce_url_to_str(item)
            if isinstance(item, dict) and not u:
                u = coerce_url_to_str(item.get('url'))
            if u and u.startswith('http'):
                if is_blocked_filetype(u) or is_denied(u):
                    continue
                candidate_urls.append(u)
        return pick_candidates(section, candidate_urls, min_allowlist=1, max_keep=10)

    async def _process_fonte_url(
        self,
        fonte: dict,
        section: str,
        candidate_urls: list,
        real_urls_for_section: list,
        used_url_keys_email: set,
        recent_used_url_keys: set
    ) -> str:
        """Process and validate a fonte's URL, returning the final URL or empty string."""
        url_original_ai = fonte.get('url_original', '')
        url_original_ai_str = coerce_url_to_str(url_original_ai)

        ai_domain = ""
        try:
            ai_domain = urlparse(url_original_ai_str).netloc if url_original_ai_str else ""
        except Exception:
            ai_domain = ""

        url_fonte = recover_url(url_original_ai, real_urls_for_section)

        if candidate_urls:
            domain_candidates = [u for u in candidate_urls if ai_domain and urlparse(u).netloc == ai_domain]
            preferred_pool = domain_candidates or candidate_urls
            if url_fonte not in preferred_pool:
                url_fonte = preferred_pool[0]

        url_key_pre = normalize_url_key(url_fonte)
        if url_key_pre and url_key_pre in recent_used_url_keys:
            swapped = False
            for alt in candidate_urls:
                ak = normalize_url_key(alt)
                if not ak or ak in recent_used_url_keys:
                    continue
                url_fonte = alt
                swapped = True
                break
            if not swapped:
                logger.info("[DEDUP_DROP_SOURCE] seção=%s ai_url=%s reused_url=%s",
                           section, url_original_ai_str, url_fonte)
                return ""

        if url_original_ai_str and url_fonte and url_fonte.strip() != url_original_ai_str.strip():
            logger.info("[URL_RECOVERY] seção=%s ai_url=%s recovered_url=%s",
                       section, url_original_ai_str, url_fonte)

        if not url_fonte or not url_fonte.startswith('http'):
            return ""

        url_key = normalize_url_key(url_fonte)
        if url_key and (url_key in used_url_keys_email or url_key in recent_used_url_keys):
            for alt in candidate_urls:
                ak = normalize_url_key(alt)
                if ak and (ak in used_url_keys_email or ak in recent_used_url_keys):
                    continue
                url_fonte = alt
                break

        if not await validate_url_permissive_async(url_fonte):
            url_fonte = await self._try_fallback_url(
                url_fonte, candidate_urls, ai_domain,
                used_url_keys_email, recent_used_url_keys,
                section, url_original_ai_str
            )
            if not url_fonte:
                return ""

        return url_fonte

    async def _try_fallback_url(
        self,
        url_fonte: str,
        candidate_urls: list,
        ai_domain: str,
        used_url_keys_email: set,
        recent_used_url_keys: set,
        section: str,
        url_original_ai_str: str
    ) -> str:
        """Try to find a fallback URL when the primary one fails validation."""
        alt_pool = []
        if candidate_urls:
            if ai_domain:
                alt_pool.extend([u for u in candidate_urls if urlparse(u).netloc == ai_domain])
            alt_pool.extend([u for u in candidate_urls if u not in alt_pool])

        for alt in (alt_pool or candidate_urls):
            if alt == url_fonte:
                continue
            ak = normalize_url_key(alt)
            if ak and (ak in used_url_keys_email or ak in recent_used_url_keys):
                continue
            if await validate_url_permissive_async(alt):
                logger.info("[URL_FALLBACK_PICKED] seção=%s ai_url=%s bad_url=%s alt_url=%s",
                           section, url_original_ai_str, url_fonte, alt)
                return alt

        logger.warning("[URL_DROPPED_404] seção=%s url=%s (ai_url=%s)",
                      section, url_fonte, url_original_ai_str)
        return ""

    def _group_by_type(self, all_opportunities: list) -> dict:
        """Group opportunities by their type."""
        grouped_ops = {}

        type_mappings = {
            ('Polêmica', 'Debate'): ('polemica', '🔥 Polêmica & Debate'),
            ('Educativo', 'How-to'): ('educativo', '🧠 Educativo & Utilidade'),
            ('Newsjacking', 'Urgência', 'Atualidade'): ('newsjacking', '📰 Newsjacking (Urgente)'),
            ('Entretenimento', 'Meme'): ('entretenimento', '😂 Entretenimento & Conexão'),
            ('Estudo de Caso',): ('estudo_caso', '💼 Estudo de Caso'),
            ('Futuro', 'Tendência'): ('futuro', '🔮 Futuro & Tendências'),
        }

        for op in all_opportunities:
            raw_type = op.get('tipo', 'Outros')
            clean_type = raw_type
            for emoji in ['🔥', '🧠', '📰', '😂', '💼', '🔮']:
                clean_type = clean_type.replace(emoji, '').strip()

            key, display_title = 'outros', '⚡ Outras Oportunidades'
            for keywords, (k, title) in type_mappings.items():
                if any(kw in clean_type for kw in keywords):
                    key, display_title = k, title
                    break

            if key not in grouped_ops:
                grouped_ops[key] = {'titulo': display_title, 'items': []}

            try:
                op['score'] = int(op.get('score', 0))
            except (ValueError, TypeError):
                op['score'] = 0

            grouped_ops[key]['items'].append(op)

        return grouped_ops

    def _sort_and_filter(self, grouped_ops: dict) -> dict:
        """Sort by score and keep top 3 per type."""
        final_structure = {}
        for key, group in grouped_ops.items():
            sorted_items = sorted(group['items'], key=lambda x: x['score'], reverse=True)
            group['items'] = sorted_items[:3]
            final_structure[key] = group
        return final_structure
