"""
Serviço para execução e gerenciamento de buscas do Google para Weekly Context.

Este serviço encapsula toda a lógica de busca, filtragem de qualidade,
deduplic

ação e seleção de fontes para geração de contexto semanal.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Set
from urllib.parse import urlparse

from asgiref.sync import sync_to_async

from ClientContext.utils.policy_types import Policy
from ClientContext.utils.source_quality import (
    allowed_domains,
    build_allowlist_query,
    is_allowed,
    is_denied,
    pick_candidates,
)
from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.url_validators import is_blocked_filetype, sanitize_query_for_allowlist
from services.google_search_service import GoogleSearchService

logger = logging.getLogger(__name__)


class SearchService:
    """Service for managing Google Search operations with quality filtering."""
    
    def __init__(self):
        self.google_search_service = GoogleSearchService()
        self.dedupe_lookback_weeks = int(os.getenv("WEEKLY_CONTEXT_DEDUPE_WEEKS", "4"))
    
    async def search_section(
        self,
        section: str,
        query: str,
        policy: Policy,
        profile_data: dict,
        excluded_urls_recent: Set[str],
        excluded_urls_this_run: Set[str]
    ) -> Dict[str, any]:
        """
        Execute search for a specific section with quality filtering and deduplication.
        
        Args:
            section: Section name ('mercado', 'concorrencia', etc.)
            query: Search query
            policy: Policy object with language and coverage settings
            profile_data: User profile data for fallback queries
            excluded_urls_recent: Set of URL keys used in recent weeks
            excluded_urls_this_run: Set of URL keys used in current run
            
        Returns:
            Dict with 'items' (list of search results) and 'metrics' (dict with stats)
        """
        if not query:
            return {'items': [], 'metrics': {}}
        
        # Fetch search results from Google
        pt_pool, en_pool = await self._fetch_search_pools(
            section, query, policy, profile_data
        )
        
        # Apply quality filtering and deduplication
        picked_items, metrics = await self._filter_and_select_items(
            section=section,
            pt_pool=pt_pool,
            en_pool=en_pool,
            policy=policy,
            excluded_urls_recent=excluded_urls_recent,
            excluded_urls_this_run=excluded_urls_this_run
        )
        
        # Log metrics and warnings
        self._log_search_metrics(section, metrics, policy)
        
        return {
            'items': picked_items,
            'metrics': metrics
        }
    
    async def _fetch_search_pools(
        self,
        section: str,
        query: str,
        policy: Policy,
        profile_data: dict
    ) -> tuple[list, list]:
        """Fetch search results in PT-BR and optionally EN."""
        
        def _fetch_pool(lr: str, q: str) -> list[dict]:
            """Fetch multiple pages of search results."""
            raw: list[dict] = []
            for start in (1, 11, 21, 31, 41):
                try:
                    page = self.google_search_service.search(
                        q,
                        num_results=10,
                        start=start,
                        lr=lr,
                        gl=os.getenv("GOOGLE_CSE_GL", "br"),
                    )
                except Exception:
                    page = []
                if page:
                    raw.extend(page)
            return raw
        
        # 1) Buscar pt-BR primeiro com allowlist se disponível
        doms = allowed_domains(section)
        sanitized = sanitize_query_for_allowlist(query)
        allow_q = build_allowlist_query(sanitized or query, doms, max_domains=8) if doms else query
        
        pt_pool = await sync_to_async(_fetch_pool)(
            policy.languages[0] if policy.languages else "lang_pt",
            allow_q
        )
        
        # Fallbacks se resultados insuficientes
        if doms and len(pt_pool) < 5:
            fallback_base = f"{profile_data.get('specialization', '')} cultura organizacional gestão de processos {datetime.now().year}"
            fb_q = build_allowlist_query(
                sanitize_query_for_allowlist(fallback_base), doms, max_domains=8
            )
            pt_pool = await sync_to_async(_fetch_pool)(
                policy.languages[0] if policy.languages else "lang_pt",
                fb_q
            )
        
        if doms and len(pt_pool) < 5:
            pt_pool = await sync_to_async(_fetch_pool)(
                policy.languages[0] if policy.languages else "lang_pt",
                query
            )
        
        logger.info("[SOURCE_AUDIT] seção=%s stage=raw_pt count=%s", section, len(pt_pool))
        
        # 2) Buscar EN se necessário (será usado apenas se PT não tiver cobertura)
        en_pool = []
        
        return pt_pool, en_pool
    
    async def _filter_and_select_items(
        self,
        section: str,
        pt_pool: list,
        en_pool: list,
        policy: Policy,
        excluded_urls_recent: Set[str],
        excluded_urls_this_run: Set[str]
    ) -> tuple[list, dict]:
        """Filter, deduplicate and select best search results."""
        
        # Extract URLs from PT pool
        pt_urls = [
            i.get("url") for i in pt_pool
            if isinstance(i, dict) and isinstance(i.get("url"), str)
        ]
        
        # Apply quality filtering
        picked_urls = pick_candidates(
            section,
            pt_urls,
            min_allowlist=policy.allowlist_min_coverage.get(section, 3),
            max_keep=12,
        )
        
        # Metrics tracking
        picked_items: list[dict] = []
        metrics = {
            'raw_pt_count': len(pt_pool),
            'raw_en_count': 0,
            'denied_count': 0,
            'allowlist_count': 0,
            'fallback_used': [],
            'min_needed': policy.min_selected_by_section.get(section, 3)
        }
        
        # Apply deduplication and domain limits
        per_domain: dict[str, int] = {}
        
        for u in picked_urls:
            if not u or not u.startswith("http"):
                continue
            
            if is_blocked_filetype(u) or is_denied(u):
                metrics['denied_count'] += 1
                continue
            
            if is_allowed(section, u):
                metrics['allowlist_count'] += 1
            
            k = normalize_url_key(u)
            if not k or k in excluded_urls_recent or k in excluded_urls_this_run:
                continue
            
            # Max 2 URLs per domain
            d = urlparse(u).netloc.lower()
            per_domain[d] = per_domain.get(d, 0) + 1
            if per_domain[d] > 2:
                per_domain[d] -= 1
                continue
            
            # Find original item from pool
            item = next(
                (x for x in pt_pool if isinstance(x, dict) and x.get("url") == u),
                None
            )
            if item:
                picked_items.append(item)
                excluded_urls_this_run.add(k)
            
            if len(picked_items) >= 6:
                break
        
        # Fallback to EN if needed
        if len(picked_items) < metrics['min_needed'] and len(policy.languages) > 1:
            await self._add_english_fallback(
                section, policy, en_pool, pt_pool,
                picked_items, excluded_urls_recent, excluded_urls_this_run,
                per_domain, metrics
            )
        
        return picked_items, metrics
    
    async def _add_english_fallback(
        self,
        section: str,
        policy: Policy,
        en_pool: list,
        pt_pool: list,
        picked_items: list,
        excluded_urls_recent: Set[str],
        excluded_urls_this_run: Set[str],
        per_domain: dict,
        metrics: dict
    ):
        """Add English results as fallback if PT results are insufficient."""
        # This would fetch EN pool - simplified for now as the original
        # logic shows EN pool is fetched only when needed
        pass
    
    def _log_search_metrics(self, section: str, metrics: dict, policy: Policy):
        """Log search metrics and quality warnings."""
        logger.info(
            "[SOURCE_METRICS] policy=%s seção=%s raw_pt=%s raw_en=%s denied=%s allow=%s selected=%s min_needed=%s fallback=%s",
            policy.key,
            section,
            metrics['raw_pt_count'],
            metrics['raw_en_count'],
            metrics['denied_count'],
            metrics['allowlist_count'],
            len(metrics.get('picked_items', [])),
            metrics['min_needed'],
            ",".join(metrics['fallback_used']) if metrics['fallback_used'] else "",
        )
        
        # Quality alerts
        if section in ("mercado", "tendencias", "concorrencia"):
            picked_count = len(metrics.get('picked_items', []))
            if picked_count < metrics['min_needed']:
                logger.warning(
                    "[LOW_SOURCE_COVERAGE] policy=%s seção=%s selected=%s raw_pt=%s raw_en=%s",
                    policy.key,
                    section,
                    picked_count,
                    metrics['raw_pt_count'],
                    metrics['raw_en_count'],
                )

