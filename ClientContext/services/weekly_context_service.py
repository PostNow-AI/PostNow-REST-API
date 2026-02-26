"""Servico de orquestracao para geracao de contexto semanal."""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from google.genai import types

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from AuditSystem.services import AuditService
from ..utils.url_dedupe import normalize_url_key
from ..utils.policy_resolver import resolve_policy
from ..utils.source_quality import pick_candidates, is_denied, is_allowed, allowed_domains, build_allowlist_query
from ..utils.text_utils import is_blocked_filetype, sanitize_query_for_allowlist, extract_json_block
from ..utils.history_utils import get_recent_topics, get_recent_url_keys
from ..utils.data_extraction import normalize_section_structure
from .opportunity_ranking_service import OpportunityRankingService
from .context_error_service import ContextErrorService
from .context_stats_service import ContextStatsService
from .context_persistence_service import ContextPersistenceService
from services.get_creator_profile_data import get_creator_profile_data
from services.prompt_utils import build_optimized_search_queries
from services.user_validation_service import UserValidationService
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.google_search_service import GoogleSearchService
from services.semaphore_service import SemaphoreService
# from utils.static_events import get_niche_events

logger = logging.getLogger(__name__)


class WeeklyContextService:
    """Service for generating weekly context for users.

    Supports dependency injection for testing and flexibility (DIP).
    """

    def __init__(
        self,
        user_validation_service: Optional[UserValidationService] = None,
        semaphore_service: Optional[SemaphoreService] = None,
        ai_service: Optional[AiService] = None,
        prompt_service: Optional[AIPromptService] = None,
        audit_service: Optional[AuditService] = None,
        google_search_service: Optional[GoogleSearchService] = None,
        opportunity_ranking_service: Optional[OpportunityRankingService] = None,
        error_service: Optional[ContextErrorService] = None,
        stats_service: Optional[ContextStatsService] = None,
        persistence_service: Optional[ContextPersistenceService] = None,
    ):
        self.user_validation_service = user_validation_service or UserValidationService()
        self.semaphore_service = semaphore_service or SemaphoreService()
        self.ai_service = ai_service or AiService()
        self.prompt_service = prompt_service or AIPromptService()
        self.audit_service = audit_service or AuditService()
        self.google_search_service = google_search_service or GoogleSearchService()
        self.opportunity_ranking_service = opportunity_ranking_service or OpportunityRankingService()
        self.error_service = error_service or ContextErrorService()
        self.stats_service = stats_service or ContextStatsService()
        self.persistence_service = persistence_service or ContextPersistenceService()
        self.dedupe_lookback_weeks = 4

    @sync_to_async
    def _get_eligible_users(self, offset: int, limit: int) -> list[dict[str, Any]]:
        """Get a batch of users eligible for weekly context generation."""
        queryset = User.objects.filter(
            usersubscription__status='active',
            is_active=True
        ).distinct().values('id', 'email', 'username')

        if limit is None:
            return list(queryset[offset:])
        return list(queryset[offset:offset + limit])

    async def process_single_user(self, user_data: dict) -> Dict[str, Any]:
        """Wrapper method to process a single user from the user data."""
        user_id = user_data.get('id') or user_data.get('user_id')
        if not user_data:
            return {'status': 'failed', 'reason': 'no_user_data'}
        if not user_id:
            return {'status': 'failed', 'reason': 'no_user_id', 'user_data': user_data}

        return await self._process_user_context(user_id)

    async def process_all_users_context(self, batch_number: int, batch_size: int) -> Dict[str, Any]:
        """Process weekly context gen for all eligible users."""
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size

        if batch_size == 0:
            offset = 0
            limit = None

        eligible_users = await self._get_eligible_users(offset=offset, limit=limit)
        total = len(eligible_users)

        if total == 0:
            return {
                'status': 'completed',
                'processed': 0,
                'total_users': 0,
                'message': 'No eligible users found',
            }

        try:
            results = await self.semaphore_service.process_concurrently(
                users=eligible_users,
                function=self.process_single_user
            )

            end_time = timezone.now()
            stats = self.stats_service.calculate_batch_results(results, start_time, end_time)

            return self.stats_service.build_completion_result(stats, total, details=results)

        except Exception as e:
            return {
                'status': 'error',
                'processed': 0,
                'total_users': total,
                'message': f'Error processing users: {str(e)}',
            }

    async def _process_user_context(self, user_id: int) -> Dict[str, Any]:
        """Process weekly context generation for a single user."""
        user = await sync_to_async(User.objects.get)(id=user_id)

        try:
            user_data = await self.user_validation_service.get_user_data(user_id)
            if not user_data:
                return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

            await sync_to_async(self.audit_service.log_context_generation)(
                user=user,
                action='weekly_context_generation_started',
                status='info',
            )

            validation_result = await self.user_validation_service.validate_user_eligibility(user_data)

            if validation_result['status'] != 'eligible':
                return {
                    'user_id': user_id,
                    'status': 'skipped',
                    'reason': validation_result['reason']
                }

            # _generate_context_for_user is async now, so we await it directly
            # RETORNA UMA TUPLA: (json_str, search_results_dict)
            context_result = await self._generate_context_for_user(user)

            search_results_map = {}
            json_str = ""

            if isinstance(context_result, tuple):
                json_str = context_result[0]
                search_results_map = context_result[1]
            else:
                json_str = context_result

            # Robust JSON parsing from the full string
            try:
                context_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON Parse Error Main: {e}")
                # Tentar extrair o bloco principal novamente com a função robusta
                clean_context = extract_json_block(json_str)
                try:
                    context_data = json.loads(clean_context)
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse extracted JSON Main: {e2}")
                    raise ValueError("Invalid JSON format from AI synthesis")

            # --- CORREÇÃO DE ESTRUTURA ---
            # Garantir que todas as seções críticas sejam dicionários (movido para utils)
            context_data = normalize_section_structure(context_data)

            # --- NOVO: Agregação e Ranking de Oportunidades ---
            # Usar função utilitária para obter URLs recentes (movido para utils)
            recent_used_url_keys = await get_recent_url_keys(user, self.dedupe_lookback_weeks)
            ranked_opportunities = await self.opportunity_ranking_service.aggregate_and_rank_opportunities(
                context_data,
                search_results_map,
                recent_used_url_keys=recent_used_url_keys
            )
            # Injetar estrutura rankeada no contexto para o template usar
            context_data['ranked_opportunities'] = ranked_opportunities

            # --- PERSISTÊNCIA: Usar serviço dedicado (SRP) ---
            client_context = await self.persistence_service.save_context(
                user=user,
                context_data=context_data,
                ranked_opportunities=ranked_opportunities
            )

            # --- HISTÓRICO: Salvar cópia no histórico ---
            await self.persistence_service.save_context_history(user, client_context)

            await sync_to_async(self.audit_service.log_context_generation)(
                user=user,
                action='context_generated',
                status='success',
            )

            return {
                'user_id': user_id,
                'status': 'success',
            }

        except Exception as e:
            await self.error_service.store_error(user, str(e))
            await sync_to_async(self.audit_service.log_context_generation)(
                user=user,
                action='weekly_context_generation_failed',
                status='error',
                details=str(e)
            )

            return {
                'user_id': user_id,
                'status': 'failed',
                'error': str(e),
            }

    async def _generate_context_for_user(self, user: User) -> tuple:
        """
        Generate context for a specific user.
        Retorna: (json_string_completo, dict_urls_reais_por_secao)
        """
        self.prompt_service.set_user(user)

        # 1. Preparar Prompts e Queries
        profile_data = await sync_to_async(get_creator_profile_data)(user)
        queries = build_optimized_search_queries(profile_data)

        # Policy (auto/override) para controlar thresholds/idiomas e auditar comportamento
        decision = resolve_policy(profile_data)
        policy = decision.policy
        logger.info(
            "[POLICY] key=%s source=%s override=%s reason=%s languages=%s min_selected=%s allow_ratio_threshold=%.2f",
            policy.key,
            decision.source,
            decision.override_value or "",
            decision.reason,
            ",".join(policy.languages),
            policy.min_selected_by_section,
            policy.allowlist_ratio_threshold,
        )

        # 2. Histórico Anti-Repetição (usando funções utilitárias)
        excluded_topics = await get_recent_topics(user, self.dedupe_lookback_weeks)
        used_url_keys_recent = await get_recent_url_keys(user, self.dedupe_lookback_weeks)
        # Também evita duplicar links dentro do mesmo e-mail (entre seções)
        used_url_keys_this_run: set[str] = set()

        # 3. Executar Buscas (Paralelas ou Sequenciais)
        sections = ['mercado', 'concorrencia', 'publico',
                    'tendencias', 'sazonalidade', 'marca']

        # Executar buscas
        search_results = {}
        for section in sections:
            # Sazonalidade precisa de parser especial no futuro, mas por enquanto busca normal
            query = queries.get(section, '')
            urls = []
            if query:
                def _fetch_pool(lr: str, q: str) -> list[dict]:
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

                # 1) Buscar pt-BR primeiro (preferência). Tentar primeiro com restrição de allowlist (se existir).
                doms = allowed_domains(section)
                sanitized = sanitize_query_for_allowlist(query)
                allow_q = build_allowlist_query(
                    sanitized or query, doms, max_domains=8) if doms else query
                pt_pool = await sync_to_async(_fetch_pool)(policy.languages[0] if policy.languages else "lang_pt", allow_q)
                if doms and len(pt_pool) < 5:
                    # fallback 1: query genérica (menos restritiva) ainda dentro da allowlist
                    fallback_base = f"{profile_data.get('specialization', '')} cultura organizacional gestão de processos {datetime.now().year}"
                    fb_q = build_allowlist_query(sanitize_query_for_allowlist(
                        fallback_base), doms, max_domains=8)
                    pt_pool = await sync_to_async(_fetch_pool)(policy.languages[0] if policy.languages else "lang_pt", fb_q)
                if doms and len(pt_pool) < 5:
                    # fallback 2: busca geral
                    pt_pool = await sync_to_async(_fetch_pool)(policy.languages[0] if policy.languages else "lang_pt", query)
                logger.info(
                    "[SOURCE_AUDIT] seção=%s stage=raw_pt count=%s", section, len(pt_pool))
                pt_urls = [i.get("url") for i in pt_pool if isinstance(
                    i, dict) and isinstance(i.get("url"), str)]
                picked_urls = pick_candidates(
                    section,
                    pt_urls,
                    min_allowlist=policy.allowlist_min_coverage.get(
                        section, 3),
                    max_keep=12,
                )
                picked_items: list[dict] = []
                raw_pt_count = len(pt_pool)
                raw_en_count = 0
                denied_count = 0
                allowlist_count = 0
                fallback_used = []
                min_needed = policy.min_selected_by_section.get(section, 3)

                # Aplicar dedupe (histórico + dentro do run) e limite por domínio
                per_domain: dict[str, int] = {}
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
                    # recuperar item original
                    item = next((x for x in pt_pool if isinstance(
                        x, dict) and x.get("url") == u), None)
                    if item:
                        picked_items.append(item)
                        used_url_keys_this_run.add(k)
                    if len(picked_items) >= 6:
                        break

                # 2) Fallback en se cobertura baixa
                if len(picked_items) < min_needed and len(policy.languages) > 1:
                    en_pool = await sync_to_async(_fetch_pool)(policy.languages[1], allow_q)
                    if doms and len(en_pool) < 5:
                        en_pool = await sync_to_async(_fetch_pool)(policy.languages[1], query)
                    logger.info(
                        "[SOURCE_AUDIT] seção=%s stage=raw_en count=%s", section, len(en_pool))
                    raw_en_count = len(en_pool)
                    fallback_used.append("en")
                    en_urls = [i.get("url") for i in en_pool if isinstance(
                        i, dict) and isinstance(i.get("url"), str)]
                    en_picked = pick_candidates(
                        section, en_urls, min_allowlist=2, max_keep=12)
                    for u in en_picked:
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
                        item = next((x for x in en_pool if isinstance(
                            x, dict) and x.get("url") == u), None)
                        if item:
                            picked_items.append(item)
                            used_url_keys_this_run.add(k)
                        if len(picked_items) >= 6:
                            break

                if len(picked_items) < min_needed:
                    logger.info(
                        "[LOW_SOURCE_COVERAGE] seção=%s picked=%s lookback_weeks=%s",
                        section,
                        len(picked_items),
                        self.dedupe_lookback_weeks,
                    )
                else:
                    # Log dos domínios finais usados por seção
                    domains = []
                    for it in picked_items:
                        u = it.get("url") if isinstance(it, dict) else None
                        if isinstance(u, str) and u.startswith("http"):
                            domains.append(urlparse(u).netloc.lower())
                    logger.info(
                        "[SOURCE_AUDIT] seção=%s stage=selected count=%s domains=%s",
                        section,
                        len(picked_items),
                        sorted(list(set(domains)))[:10],
                    )

                logger.info(
                    "[SOURCE_METRICS] policy=%s seção=%s raw_pt=%s raw_en=%s denied=%s allow=%s selected=%s min_needed=%s fallback=%s",
                    policy.key,
                    section,
                    raw_pt_count,
                    raw_en_count,
                    denied_count,
                    allowlist_count,
                    len(picked_items),
                    min_needed,
                    ",".join(fallback_used) if fallback_used else "",
                )

                # Alertas simples de qualidade
                if section in ("mercado", "tendencias", "concorrencia") and len(picked_items) < min_needed:
                    logger.warning(
                        "[LOW_SOURCE_COVERAGE] policy=%s seção=%s selected=%s raw_pt=%s raw_en=%s",
                        policy.key,
                        section,
                        len(picked_items),
                        raw_pt_count,
                        raw_en_count,
                    )

                # Ratio de allowlist (quando há allowlist definida para a seção)
                if doms and len(picked_items) > 0:
                    allow_ratio = allowlist_count / max(len(picked_items), 1)
                    if allow_ratio < policy.allowlist_ratio_threshold:
                        logger.warning(
                            "[LOW_ALLOWLIST_RATIO] policy=%s seção=%s ratio=%.2f allow=%s selected=%s domains_allowlist=%s",
                            policy.key,
                            section,
                            allow_ratio,
                            allowlist_count,
                            len(picked_items),
                            len(doms),
                        )

                urls = picked_items
            search_results[section] = urls

        # 4. Contexto Cruzado (Cross-Context Synthesis)
        # O Público precisa saber o que está rolando no Mercado e Tendências
        context_borrowed_for_audience = search_results.get(
            'mercado', []) + search_results.get('tendencias', [])

        # 5. Gerar Síntese com IA (Sequencial para garantir coerência ou paralelo?)
        # Vamos fazer sequencial para simplicidade e controle de erro, mas construindo um JSON unificado
        final_json_parts = []

        for section in sections:
            borrowed = context_borrowed_for_audience if section == 'publico' else None

            prompt_list = self.prompt_service._build_synthesis_prompt(
                section_name=section,
                query=queries.get(section, ''),
                urls=search_results.get(section, []),
                profile_data=profile_data,
                excluded_topics=excluded_topics,
                context_borrowed=borrowed
            )

            # Chamar Gemini

            # Configuração "limpa" para síntese (sem Google Search Tools)
            # para evitar conflito com o texto já fornecido e prevenir erros de Grounding
            synthesis_config = types.GenerateContentConfig(
                response_modalities=["TEXT"],
                temperature=0.7,
                top_p=0.9,
                max_output_tokens=4096,
                response_mime_type="application/json"
            )

            try:
                # O método generate_text espera uma lista de prompts, não string única
                ai_response = await sync_to_async(self.ai_service.generate_text)(
                    prompt_list,
                    user,
                    config=synthesis_config
                )
                # Limpar JSON markdown se houver
                if isinstance(ai_response, dict):
                    ai_text = ai_response.get('text', '')
                else:
                    ai_text = str(ai_response)

                # Usar a nova função robusta para extrair o JSON
                clean_json = extract_json_block(ai_text)
                final_json_parts.append(f'"{section}": {clean_json}')

            except Exception as e:
                logger.error(f"Error generating section {section}: {e}")
                final_json_parts.append(f'"{section}": {{}}')  # Fallback vazio

        # Montar JSON Final
        full_json_str = "{" + ", ".join(final_json_parts) + "}"
        return full_json_str, search_results

    # NOTE: _get_recent_topics e _get_recent_url_keys foram movidos para
    # ClientContext/utils/history_utils.py conforme feedback do CTO (SOLID/DRY)
