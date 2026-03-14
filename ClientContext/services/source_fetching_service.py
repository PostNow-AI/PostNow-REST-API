"""Service para busca e filtragem de URLs por secao."""

import logging
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from asgiref.sync import sync_to_async

from ..utils.url_dedupe import normalize_url_key
from ..utils.source_quality import pick_candidates, is_denied, is_allowed, allowed_domains, build_allowlist_query
from ..utils.text_utils import is_blocked_filetype, sanitize_query_for_allowlist
from services.search_service import SearchService

logger = logging.getLogger(__name__)


class SourceFetchingService:
    """Busca e filtra URLs de fontes para cada secao do contexto semanal."""

    def __init__(self, search_service: Optional[SearchService] = None):
        self.search_service = search_service or SearchService()

    def _fetch_pool(self, lr: str, q: str) -> list[dict]:
        try:
            return self.search_service.search(
                q, num_results=10, lr=lr,
                gl=os.getenv("SERPER_GL", "br"),
            )
        except Exception:
            return []

    async def fetch_and_filter_section(
        self,
        section: str,
        query: str,
        profile_data: dict,
        policy,
        used_url_keys_recent: set,
        used_url_keys_this_run: set,
    ) -> list[dict]:
        if not query:
            return []

        doms = allowed_domains(section)
        sanitized = sanitize_query_for_allowlist(query)
        allow_q = build_allowlist_query(
            sanitized or query, doms, max_domains=8) if doms else query

        # 1) PT-BR (com fallback progressivo)
        pt_pool = await sync_to_async(self._fetch_pool)(
            policy.languages[0] if policy.languages else "lang_pt", allow_q)
        if doms and len(pt_pool) < 5:
            fallback_base = (
                f"{profile_data.get('specialization', '')} "
                f"cultura organizacional gestao de processos {datetime.now().year}"
            )
            fb_q = build_allowlist_query(
                sanitize_query_for_allowlist(fallback_base), doms, max_domains=8)
            pt_pool = await sync_to_async(self._fetch_pool)(
                policy.languages[0] if policy.languages else "lang_pt", fb_q)
        if doms and len(pt_pool) < 5:
            pt_pool = await sync_to_async(self._fetch_pool)(
                policy.languages[0] if policy.languages else "lang_pt", query)

        logger.info("[SOURCE_AUDIT] secao=%s stage=raw_pt count=%s", section, len(pt_pool))

        # Filtrar e dedupe
        pt_urls = [i.get("url") for i in pt_pool
                   if isinstance(i, dict) and isinstance(i.get("url"), str)]
        picked_urls = pick_candidates(
            section, pt_urls,
            min_allowlist=policy.allowlist_min_coverage.get(section, 3),
            max_keep=12,
        )
        picked_items, denied_count, allowlist_count = self._dedupe_and_filter(
            picked_urls, pt_pool, section, used_url_keys_recent, used_url_keys_this_run)

        raw_pt_count = len(pt_pool)
        raw_en_count = 0
        fallback_used = []
        min_needed = policy.min_selected_by_section.get(section, 3)

        # 2) Fallback EN se cobertura baixa
        if len(picked_items) < min_needed and len(policy.languages) > 1:
            en_pool = await sync_to_async(self._fetch_pool)(policy.languages[1], allow_q)
            if doms and len(en_pool) < 5:
                en_pool = await sync_to_async(self._fetch_pool)(policy.languages[1], query)
            logger.info("[SOURCE_AUDIT] secao=%s stage=raw_en count=%s", section, len(en_pool))
            raw_en_count = len(en_pool)
            fallback_used.append("en")
            en_urls = [i.get("url") for i in en_pool
                       if isinstance(i, dict) and isinstance(i.get("url"), str)]
            en_picked = pick_candidates(section, en_urls, min_allowlist=2, max_keep=12)
            en_items, en_denied, en_allow = self._dedupe_and_filter(
                en_picked, en_pool, section, used_url_keys_recent, used_url_keys_this_run)
            picked_items.extend(en_items)
            denied_count += en_denied
            allowlist_count += en_allow

        # Logging
        self._log_metrics(
            section, policy, picked_items, raw_pt_count, raw_en_count,
            denied_count, allowlist_count, min_needed, fallback_used, doms)

        return picked_items

    def _dedupe_and_filter(
        self, picked_urls, pool, section, used_url_keys_recent, used_url_keys_this_run,
    ) -> tuple[list[dict], int, int]:
        per_domain: dict[str, int] = {}
        picked_items: list[dict] = []
        denied_count = 0
        allowlist_count = 0

        for u in picked_urls:
            if not u or not u.startswith("http"):
                continue
            if is_blocked_filetype(u) or is_denied(u):
                denied_count += 1
                continue
            if is_allowed(section, u):
                allowlist_count += 1
            k = normalize_url_key(u)
            if not k or k in used_url_keys_recent or k in used_url_keys_this_run:
                continue
            d = urlparse(u).netloc.lower()
            per_domain[d] = per_domain.get(d, 0) + 1
            if per_domain[d] > 2:
                per_domain[d] -= 1
                continue
            item = next((x for x in pool if isinstance(x, dict) and x.get("url") == u), None)
            if item:
                picked_items.append(item)
                used_url_keys_this_run.add(k)
            if len(picked_items) >= 6:
                break

        return picked_items, denied_count, allowlist_count

    def _log_metrics(
        self, section, policy, picked_items, raw_pt_count, raw_en_count,
        denied_count, allowlist_count, min_needed, fallback_used, doms,
    ):
        if len(picked_items) < min_needed:
            logger.info(
                "[LOW_SOURCE_COVERAGE] secao=%s picked=%s",
                section, len(picked_items))
        else:
            domains = []
            for it in picked_items:
                u = it.get("url") if isinstance(it, dict) else None
                if isinstance(u, str) and u.startswith("http"):
                    domains.append(urlparse(u).netloc.lower())
            logger.info(
                "[SOURCE_AUDIT] secao=%s stage=selected count=%s domains=%s",
                section, len(picked_items), sorted(list(set(domains)))[:10])

        logger.info(
            "[SOURCE_METRICS] policy=%s secao=%s raw_pt=%s raw_en=%s denied=%s allow=%s selected=%s min_needed=%s fallback=%s",
            policy.key, section, raw_pt_count, raw_en_count,
            denied_count, allowlist_count, len(picked_items),
            min_needed, ",".join(fallback_used) if fallback_used else "")

        if section in ("mercado", "tendencias", "concorrencia") and len(picked_items) < min_needed:
            logger.warning(
                "[LOW_SOURCE_COVERAGE] policy=%s secao=%s selected=%s raw_pt=%s raw_en=%s",
                policy.key, section, len(picked_items), raw_pt_count, raw_en_count)

        if doms and len(picked_items) > 0:
            allow_ratio = allowlist_count / max(len(picked_items), 1)
            if allow_ratio < policy.allowlist_ratio_threshold:
                logger.warning(
                    "[LOW_ALLOWLIST_RATIO] policy=%s secao=%s ratio=%.2f allow=%s selected=%s",
                    policy.key, section, allow_ratio, allowlist_count, len(picked_items))
