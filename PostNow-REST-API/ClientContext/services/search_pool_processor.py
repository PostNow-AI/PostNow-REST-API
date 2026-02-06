"""
Search Pool Processor - Handles Google Search pool fetching and filtering.
Follows Single Responsibility Principle.
"""
import logging
import os
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

from asgiref.sync import sync_to_async

from ClientContext.utils.source_quality import allowed_domains, build_allowlist_query
from ClientContext.utils.url_validators import sanitize_query_for_allowlist
from ClientContext.services.url_processing_service import UrlProcessingService

logger = logging.getLogger(__name__)


class SearchPoolProcessor:
    """Handles fetching and processing search result pools."""

    def __init__(self, google_search_service, url_processor: Optional[UrlProcessingService] = None):
        self.google_search_service = google_search_service
        self.url_processor = url_processor or UrlProcessingService()

    async def fetch_and_filter_section(
        self,
        section: str,
        query: str,
        profile_data: dict,
        policy,
        used_keys_recent: set[str],
        used_keys_this_run: set[str]
    ) -> tuple[list[dict], set[str], dict]:
        """
        Fetch and filter search results for a section.

        Returns:
            tuple: (picked_items, updated_used_keys, metrics)
        """
        if not query:
            return [], used_keys_this_run, self._empty_metrics()

        # Get domain allowlist for section
        doms = allowed_domains(section)
        sanitized = sanitize_query_for_allowlist(query)
        allow_query = build_allowlist_query(
            sanitized or query, doms, max_domains=8
        ) if doms else query

        # 1. Fetch PT pool (primary)
        pt_pool = await self._fetch_pool_with_fallbacks(
            allow_query, query, doms, profile_data,
            policy.languages[0] if policy.languages else "lang_pt"
        )
        logger.info("[SOURCE_AUDIT] seção=%s stage=raw_pt count=%s", section, len(pt_pool))

        # Extract URLs and filter
        pt_urls = self._extract_urls(pt_pool)
        picked_items, updated_keys, metrics = self.url_processor.filter_and_dedupe_urls(
            urls=pt_urls,
            section=section,
            used_keys_recent=used_keys_recent,
            used_keys_this_run=used_keys_this_run,
            raw_pool=pt_pool,
            min_allowlist=policy.allowlist_min_coverage.get(section, 3),
            max_keep=12,
            max_items=6
        )

        metrics['raw_pt'] = len(pt_pool)
        metrics['raw_en'] = 0
        metrics['fallback_used'] = []

        # 2. Fallback to EN if coverage is low
        min_needed = policy.min_selected_by_section.get(section, 3)
        if len(picked_items) < min_needed and len(policy.languages) > 1:
            en_items, updated_keys, en_metrics = await self._fetch_en_fallback(
                section, allow_query, query, doms, policy,
                picked_items, updated_keys, used_keys_recent
            )
            picked_items.extend(en_items)
            metrics['raw_en'] = en_metrics.get('raw_en', 0)
            metrics['fallback_used'].append('en')
            metrics['denied_count'] += en_metrics.get('denied_count', 0)
            metrics['allowlist_count'] += en_metrics.get('allowlist_count', 0)

        # Log metrics
        self._log_metrics(section, policy, metrics, len(picked_items), min_needed, doms)

        return picked_items, updated_keys, metrics

    async def _fetch_pool_with_fallbacks(
        self,
        allow_query: str,
        original_query: str,
        doms: list,
        profile_data: dict,
        language: str
    ) -> list[dict]:
        """Fetch pool with fallback strategies."""
        pool = await self._fetch_pool(language, allow_query)

        # Fallback 1: Less restrictive query
        if doms and len(pool) < 5:
            fallback_base = (
                f"{profile_data.get('specialization', '')} "
                f"cultura organizacional gestão de processos {datetime.now().year}"
            )
            fb_query = build_allowlist_query(
                sanitize_query_for_allowlist(fallback_base),
                doms, max_domains=8
            )
            pool = await self._fetch_pool(language, fb_query)

        # Fallback 2: General query
        if doms and len(pool) < 5:
            pool = await self._fetch_pool(language, original_query)

        return pool

    async def _fetch_pool(self, language: str, query: str) -> list[dict]:
        """Fetch a pool of results for a language."""
        raw: list[dict] = []

        def _do_fetch():
            results = []
            for start in (1, 11, 21, 31, 41):
                try:
                    page = self.google_search_service.search(
                        query,
                        num_results=10,
                        start=start,
                        lr=language,
                        gl=os.getenv("GOOGLE_CSE_GL", "br"),
                    )
                except Exception:
                    page = []
                if page:
                    results.extend(page)
            return results

        return await sync_to_async(_do_fetch)()

    async def _fetch_en_fallback(
        self,
        section: str,
        allow_query: str,
        original_query: str,
        doms: list,
        policy,
        current_items: list[dict],
        used_keys: set[str],
        used_keys_recent: set[str]
    ) -> tuple[list[dict], set[str], dict]:
        """Fetch English fallback pool when PT coverage is low."""
        en_lang = policy.languages[1] if len(policy.languages) > 1 else "lang_en"

        en_pool = await self._fetch_pool(en_lang, allow_query)
        if doms and len(en_pool) < 5:
            en_pool = await self._fetch_pool(en_lang, original_query)

        logger.info("[SOURCE_AUDIT] seção=%s stage=raw_en count=%s", section, len(en_pool))

        en_urls = self._extract_urls(en_pool)
        new_items, updated_keys, metrics = self.url_processor.filter_and_dedupe_urls(
            urls=en_urls,
            section=section,
            used_keys_recent=used_keys_recent,
            used_keys_this_run=used_keys,
            raw_pool=en_pool,
            min_allowlist=2,
            max_keep=12,
            max_items=6 - len(current_items)  # Fill remaining slots
        )

        metrics['raw_en'] = len(en_pool)
        return new_items, updated_keys, metrics

    def _extract_urls(self, pool: list[dict]) -> list[str]:
        """Extract URLs from search result pool."""
        return [
            item.get("url")
            for item in pool
            if isinstance(item, dict) and isinstance(item.get("url"), str)
        ]

    def _empty_metrics(self) -> dict:
        return {
            'raw_pt': 0,
            'raw_en': 0,
            'denied_count': 0,
            'allowlist_count': 0,
            'fallback_used': []
        }

    def _log_metrics(
        self,
        section: str,
        policy,
        metrics: dict,
        selected_count: int,
        min_needed: int,
        doms: list
    ):
        """Log search metrics for auditing."""
        # Log selected domains
        if selected_count >= min_needed:
            logger.info(
                "[SOURCE_AUDIT] seção=%s stage=selected count=%s",
                section, selected_count
            )
        else:
            logger.info(
                "[LOW_SOURCE_COVERAGE] seção=%s picked=%s",
                section, selected_count
            )

        # Main metrics log
        logger.info(
            "[SOURCE_METRICS] policy=%s seção=%s raw_pt=%s raw_en=%s "
            "denied=%s allow=%s selected=%s min_needed=%s fallback=%s",
            policy.key, section,
            metrics.get('raw_pt', 0), metrics.get('raw_en', 0),
            metrics.get('denied_count', 0), metrics.get('allowlist_count', 0),
            selected_count, min_needed,
            ",".join(metrics.get('fallback_used', []))
        )

        # Warning for critical sections with low coverage
        if section in ("mercado", "tendencias", "concorrencia") and selected_count < min_needed:
            logger.warning(
                "[LOW_SOURCE_COVERAGE] policy=%s seção=%s selected=%s",
                policy.key, section, selected_count
            )

        # Allowlist ratio warning
        if doms and selected_count > 0:
            allow_ratio = metrics.get('allowlist_count', 0) / max(selected_count, 1)
            if allow_ratio < policy.allowlist_ratio_threshold:
                logger.warning(
                    "[LOW_ALLOWLIST_RATIO] policy=%s seção=%s ratio=%.2f",
                    policy.key, section, allow_ratio
                )
