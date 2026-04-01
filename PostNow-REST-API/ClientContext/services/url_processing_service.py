"""
URL Processing Service - Handles URL validation, recovery, and deduplication.
Follows Single Responsibility Principle.
"""
import logging
from urllib.parse import urlparse
from typing import Optional

from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.source_quality import is_denied, is_allowed, pick_candidates
from ClientContext.utils.url_validators import (
    is_blocked_filetype,
    coerce_url_to_str,
    recover_url,
    validate_url_permissive_async
)

logger = logging.getLogger(__name__)


class UrlProcessingService:
    """Handles all URL-related processing: validation, recovery, and deduplication."""

    def __init__(self, max_per_domain: int = 2):
        self.max_per_domain = max_per_domain

    def filter_and_dedupe_urls(
        self,
        urls: list[str],
        section: str,
        used_keys_recent: set[str],
        used_keys_this_run: set[str],
        raw_pool: list[dict],
        min_allowlist: int = 3,
        max_keep: int = 12,
        max_items: int = 6
    ) -> tuple[list[dict], set[str], dict]:
        """
        Filter URLs by quality rules and deduplicate.

        Returns:
            tuple: (picked_items, updated_used_keys, metrics)
        """
        picked_urls = pick_candidates(section, urls, min_allowlist=min_allowlist, max_keep=max_keep)

        picked_items = []
        per_domain: dict[str, int] = {}
        metrics = {
            'denied_count': 0,
            'allowlist_count': 0,
        }
        updated_keys = set(used_keys_this_run)

        for url in picked_urls:
            if not self._is_valid_url(url):
                continue

            if is_blocked_filetype(url) or is_denied(url):
                metrics['denied_count'] += 1
                continue

            if is_allowed(section, url):
                metrics['allowlist_count'] += 1

            url_key = normalize_url_key(url)
            if not url_key or url_key in used_keys_recent or url_key in updated_keys:
                continue

            # Domain limiting
            domain = urlparse(url).netloc.lower()
            per_domain[domain] = per_domain.get(domain, 0) + 1
            if per_domain[domain] > self.max_per_domain:
                per_domain[domain] -= 1
                continue

            # Find original item from pool
            item = self._find_item_by_url(raw_pool, url)
            if item:
                picked_items.append(item)
                updated_keys.add(url_key)

            if len(picked_items) >= max_items:
                break

        return picked_items, updated_keys, metrics

    async def validate_and_recover_url(
        self,
        ai_url: str,
        candidate_urls: list[str],
        real_urls_pool: list,
        used_keys_email: set[str],
        used_keys_recent: set[str],
        section: str
    ) -> Optional[str]:
        """
        Validate a URL from AI, recover if hallucinated, and ensure it's not a duplicate.

        Returns:
            str or None: Valid URL or None if should be skipped
        """
        ai_url_str = coerce_url_to_str(ai_url)
        ai_domain = self._extract_domain(ai_url_str)

        # Try to recover URL if AI hallucinated
        url_fonte = recover_url(ai_url, real_urls_pool)

        # Prefer Google Search URLs when available
        if candidate_urls:
            url_fonte = self._select_best_candidate(
                url_fonte, ai_domain, candidate_urls
            )

        # Check for recent usage
        url_key = normalize_url_key(url_fonte)
        if url_key and url_key in used_keys_recent:
            url_fonte = self._find_unused_alternative(
                candidate_urls, used_keys_recent, used_keys_email
            )
            if not url_fonte:
                logger.info(
                    "[DEDUP_DROP_SOURCE] seção=%s ai_url=%s",
                    section, ai_url_str
                )
                return None

        # Log recovery if URL changed
        if ai_url_str and url_fonte and url_fonte.strip() != ai_url_str.strip():
            logger.info(
                "[URL_RECOVERY] seção=%s ai_url=%s recovered_url=%s",
                section, ai_url_str, url_fonte
            )

        # Basic validation
        if not url_fonte or not url_fonte.startswith('http'):
            return None

        # Check email deduplication
        url_key = normalize_url_key(url_fonte)
        if url_key and (url_key in used_keys_email or url_key in used_keys_recent):
            url_fonte = self._find_unused_alternative(
                candidate_urls, used_keys_recent, used_keys_email
            )
            if not url_fonte:
                return None

        # HTTP validation with fallback
        if not await validate_url_permissive_async(url_fonte):
            url_fonte = await self._find_valid_alternative(
                url_fonte, ai_domain, candidate_urls,
                used_keys_email, used_keys_recent, section, ai_url_str
            )
            if not url_fonte:
                return None

        return url_fonte

    def prepare_candidate_urls(
        self,
        real_urls: list,
        section: str
    ) -> list[str]:
        """Extract and filter candidate URLs from search results."""
        candidates = []
        for item in (real_urls or []):
            url = coerce_url_to_str(item)
            if isinstance(item, dict) and not url:
                url = coerce_url_to_str(item.get('url'))

            if url and url.startswith('http'):
                if not is_blocked_filetype(url) and not is_denied(url):
                    candidates.append(url)

        return pick_candidates(section, candidates, min_allowlist=1, max_keep=10)

    # Private helper methods

    def _is_valid_url(self, url: str) -> bool:
        return bool(url and url.startswith('http'))

    def _extract_domain(self, url: str) -> str:
        try:
            return urlparse(url).netloc if url else ""
        except Exception:
            return ""

    def _find_item_by_url(self, pool: list[dict], url: str) -> Optional[dict]:
        return next(
            (x for x in pool if isinstance(x, dict) and x.get("url") == url),
            None
        )

    def _select_best_candidate(
        self,
        current_url: str,
        preferred_domain: str,
        candidates: list[str]
    ) -> str:
        """Select best URL, preferring same domain as AI suggested."""
        if not candidates:
            return current_url

        domain_matches = [
            u for u in candidates
            if preferred_domain and urlparse(u).netloc == preferred_domain
        ]
        preferred_pool = domain_matches or candidates

        if current_url not in preferred_pool:
            return preferred_pool[0]
        return current_url

    def _find_unused_alternative(
        self,
        candidates: list[str],
        used_recent: set[str],
        used_email: set[str]
    ) -> Optional[str]:
        """Find an alternative URL that hasn't been used."""
        for alt in candidates:
            key = normalize_url_key(alt)
            if not key or key in used_recent or key in used_email:
                continue
            return alt
        return None

    async def _find_valid_alternative(
        self,
        failed_url: str,
        ai_domain: str,
        candidates: list[str],
        used_email: set[str],
        used_recent: set[str],
        section: str,
        ai_url_str: str
    ) -> Optional[str]:
        """Find a valid alternative when primary URL fails validation."""
        # Build priority pool (same domain first)
        alt_pool = []
        if candidates:
            if ai_domain:
                alt_pool.extend([
                    u for u in candidates
                    if urlparse(u).netloc == ai_domain
                ])
            alt_pool.extend([u for u in candidates if u not in alt_pool])

        for alt in alt_pool:
            if alt == failed_url:
                continue
            key = normalize_url_key(alt)
            if key and (key in used_email or key in used_recent):
                continue
            if await validate_url_permissive_async(alt):
                logger.info(
                    "[URL_FALLBACK_PICKED] seção=%s ai_url=%s bad_url=%s alt_url=%s",
                    section, ai_url_str, failed_url, alt
                )
                return alt

        logger.warning(
            "[URL_DROPPED_404] seção=%s url=%s (ai_url=%s)",
            section, failed_url, ai_url_str
        )
        return None
