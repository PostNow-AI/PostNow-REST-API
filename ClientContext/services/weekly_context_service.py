import json
import logging
import asyncio
import re
import requests
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from google.genai import types

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from AuditSystem.services import AuditService
from ClientContext.models import ClientContext
from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.policy_resolver import resolve_policy
from ClientContext.utils.source_quality import pick_candidates, is_denied, is_allowed, allowed_domains, build_allowlist_query
from ClientContext.utils.text_utils import is_blocked_filetype, sanitize_query_for_allowlist, extract_json_block
from ClientContext.utils.url_validation import coerce_url_to_str, recover_url, validate_url_permissive_async
from ClientContext.services.opportunity_ranking_service import OpportunityRankingService
from services.get_creator_profile_data import get_creator_profile_data
from services.prompt_utils import build_optimized_search_queries
from services.user_validation_service import UserValidationService
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from AuditSystem.services import AuditService
from services.google_search_service import GoogleSearchService
from services.mailjet_service import MailjetService
from services.semaphore_service import SemaphoreService
from ClientContext.utils.weekly_context import generate_weekly_context_email_template
# from utils.static_events import get_niche_events

logger = logging.getLogger(__name__)


class WeeklyContextService:
    def __init__(self):
        self.user_validation_service = UserValidationService()
        self.semaphore_service = SemaphoreService()
        self.ai_service = AiService()
        self.prompt_service = AIPromptService()
        self.audit_service = AuditService()
        self.mailjet_service = MailjetService()
        self.google_search_service = GoogleSearchService()
        self.opportunity_ranking_service = OpportunityRankingService()
        self.dedupe_lookback_weeks = 4

    @sync_to_async
    def _get_eligible_users(self, offset: int, limit: int) -> list[dict[str, Any]]:
        """Get a batch of users eligible for weekly context generation"""
        if limit is None:
            return list(
                User.objects.filter(
                    usersubscription__status='active',
                    is_active=True
                ).distinct().values('id', 'email', 'username')[offset:]
            )

        return list(
            User.objects.filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().values('id', 'email', 'username')[offset:offset + limit]
        )

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
            limit = None  # Process all users

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

            processed_count = sum(
                1 for r in results if r.get('status') == 'success')
            failed_count = sum(
                1 for r in results if r.get('status') == 'failed')
            skipped_count = sum(
                1 for r in results if r.get('status') == 'skipped')

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'status': 'completed',
                'processed': processed_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'total_users': total,
                'duration_seconds': duration,
                'details': results,
            }

            return result

        except Exception as e:
            return {
                'status': 'error',
                'processed': 0,
                'total_users': total,
                'message': f'Error processing users: {str(e)}',
            }

    async def _process_user_context(self, user_id: int) -> Dict[str, Any]:
        """Process weekly context generation for a single user."""
        # Placeholder for actual context generation logic
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
                return {'user_id': user_id,
                        'status': 'skipped',
                        'reason': validation_result['reason']}

            # _generate_context_for_user is async now, so we await it directly
            # RETORNA UMA TUPLA: (json_str, search_results_dict)
            context_result = await self._generate_context_for_user(user)
            logger.info(
                f"Context Result Type: {type(context_result)}")  # DEBUG

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
            # Garantir que todas as seções críticas sejam dicionários
            for section in ['mercado', 'concorrencia', 'publico', 'tendencias', 'sazonalidade', 'marca']:
                if section in context_data:
                    if isinstance(context_data[section], list):
                        # Se for lista, tenta pegar o primeiro item se for dict
                        if context_data[section] and isinstance(context_data[section][0], dict):
                            context_data[section] = context_data[section][0]
                        else:
                            # Se for lista de strings ou vazia, transforma em dict vazio ou adapta
                            context_data[section] = {}
                    elif not isinstance(context_data[section], dict):
                        context_data[section] = {}

            # --- NOVO: Agregação e Ranking de Oportunidades ---
            # Agora passando o mapa de URLs reais para recuperação
            recent_used_url_keys = await self._get_recent_url_keys(user)
            ranked_opportunities = await self.opportunity_ranking_service.aggregate_and_rank_opportunities(
                context_data,
                search_results_map,
                recent_used_url_keys=recent_used_url_keys
            )
            # Injetar estrutura rankeada no contexto para o template usar
            context_data['ranked_opportunities'] = ranked_opportunities

            client_context, created = await sync_to_async(ClientContext.objects.get_or_create)(user=user)

            # Update the context fields (Mantendo compatibilidade com campos antigos onde possível)
            # Para o novo motor, vamos salvar o JSON completo das oportunidades rankeadas
            # num campo JSONField genérico ou adaptado. Como não temos um campo 'ranked_opportunities' no model,
            # vamos salvar em 'market_opportunities' que é JSON, mas estruturado diferente.
            # Ideal seria criar campo novo, mas por agora vamos usar 'market_opportunities' para armazenar TUDO.

            # Salvar TODAS as oportunidades (raw) em market_opportunities para persistência total
            client_context.market_opportunities = context_data.get(
                'mercado', {}).get('fontes_analisadas', [])

            # Salvar as Rankeadas (Top Picks) em 'market_tendencies' (campo JSON pouco usado) ou 'tendencies_data'
            # Vamos usar 'tendencies_data' para armazenar o JSON final rankeado que o email vai usar.
            client_context.tendencies_data = ranked_opportunities

            # --- Helper: extrair dados do novo formato de oportunidades ---
            def _extract_from_opportunities(section_data):
                """Extrai textos legíveis do formato fontes_analisadas/oportunidades."""
                fontes_analisadas = section_data.get('fontes_analisadas', [])
                all_opps = []
                all_titles = []
                for fonte in fontes_analisadas:
                    all_titles.append(fonte.get('titulo_original', ''))
                    for opp in fonte.get('oportunidades', []):
                        all_opps.append(opp)
                return fontes_analisadas, all_opps, all_titles

            # === MERCADO ===
            mercado = context_data.get('mercado', {})
            mercado_raw, mercado_opps, mercado_titles = _extract_from_opportunities(mercado)
            # Panorama: sintetizar um resumo coerente dos textos analisados
            if mercado.get('panorama'):
                client_context.market_panorama = mercado['panorama']
            else:
                # Tentar extrair textos da seção mercado OU dos ranked_opportunities de origem mercado
                textos = [o.get('texto_base_analisado', '') for o in mercado_opps if o.get('texto_base_analisado')]
                if not textos and ranked_opportunities:
                    for section in ranked_opportunities.values():
                        if isinstance(section, dict):
                            for item in section.get('items', []):
                                if item.get('origem_secao') == 'mercado' and item.get('texto_base_analisado'):
                                    textos.append(item['texto_base_analisado'])
                if textos:
                    client_context.market_panorama = (
                        f"Esta semana, as análises de mercado destacam: {textos[0]}"
                        + (f" Além disso, {textos[1]}" if len(textos) > 1 else "")
                        + (f" Outro ponto relevante: {textos[2]}" if len(textos) > 2 else "")
                    )
                else:
                    client_context.market_panorama = ''
            # Tendências: títulos das ideias do mercado (com fallback para ranked)
            all_mercado_opps = list(mercado_opps)
            if not all_mercado_opps and ranked_opportunities:
                for section in ranked_opportunities.values():
                    if isinstance(section, dict):
                        for item in section.get('items', []):
                            if item.get('origem_secao') == 'mercado':
                                all_mercado_opps.append(item)
            client_context.market_tendencies = mercado.get('tendencias', []) or \
                [o.get('titulo_ideia', '') for o in all_mercado_opps if o.get('titulo_ideia')]
            # Desafios: filtrar oportunidades do tipo Polêmica/Newsjacking
            client_context.market_challenges = mercado.get('desafios', []) or \
                [o.get('titulo_ideia', '') for o in all_mercado_opps if o.get('tipo') in ('Polêmica', 'Newsjacking')]
            client_context.market_sources = mercado.get('fontes', [])
            client_context.market_opportunities = mercado_raw

            # === CONCORRÊNCIA ===
            concorrencia = context_data.get('concorrencia', {})
            conc_raw, conc_opps, conc_titles = _extract_from_opportunities(concorrencia)
            # Principais: extrair nomes das ferramentas/empresas dos títulos
            if concorrencia.get('principais'):
                client_context.competition_main = concorrencia['principais']
            else:
                # Títulos de artigos geralmente têm formato "Nome: Descrição" ou são o nome direto
                nomes = []
                for t in conc_titles:
                    if ':' in t:
                        nomes.append(t.split(':')[0].strip())
                    elif ' - ' in t:
                        nomes.append(t.split(' - ')[0].strip())
                    else:
                        nomes.append(t)
                client_context.competition_main = nomes
            # Estratégias: sintetizar um texto coerente
            client_context.competition_strategies = concorrencia.get('estrategias', '') or \
                '. '.join([o.get('gatilho_criativo', '') for o in conc_opps[:3] if o.get('gatilho_criativo')])
            # Oportunidades: títulos das ideias
            client_context.competition_opportunities = concorrencia.get('oportunidades', '') or \
                ', '.join([o.get('titulo_ideia', '') for o in conc_opps[:3] if o.get('titulo_ideia')])
            client_context.competition_benchmark = conc_raw
            client_context.competition_sources = concorrencia.get('fontes', [])

            # === PÚBLICO ===
            publico = context_data.get('publico', {})
            client_context.target_audience_profile = publico.get('perfil', '')
            client_context.target_audience_behaviors = publico.get('comportamento_online', '')
            client_context.target_audience_interests = publico.get('interesses', [])
            client_context.target_audience_sources = publico.get('fontes', [])

            # === TENDÊNCIAS ===
            tendencias = context_data.get('tendencias', {})
            tend_raw, tend_opps, tend_titles = _extract_from_opportunities(tendencias)
            client_context.tendencies_popular_themes = tendencias.get('temas_populares', []) or \
                [o.get('titulo_ideia', '') for o in tend_opps if o.get('titulo_ideia')]
            # Gerar hashtags a partir dos tipos e temas das oportunidades
            if tendencias.get('hashtags'):
                client_context.tendencies_hashtags = tendencias['hashtags']
            else:
                hashtags = set()
                # Adicionar tipos como hashtags (mais relevantes que palavras aleatórias)
                STOP_WORDS = {'para', 'como', 'será', 'pode', 'vai', 'que', 'por', 'uma', 'seu', 'sobre', 'mais', 'isso', 'este', 'esta', 'com', 'não', 'dos', 'das'}
                for o in tend_opps + mercado_opps + conc_opps:
                    tipo = o.get('tipo', '')
                    if tipo:
                        hashtags.add(f"#{tipo.replace(' ', '')}")
                    # Extrair apenas substantivos relevantes (palavras maiores de 5 chars)
                    titulo = o.get('titulo_ideia', '')
                    for word in titulo.split():
                        clean = word.strip('?!.,;:()[]{}"\'-').lower()
                        if len(clean) > 5 and clean.isalpha() and clean not in STOP_WORDS:
                            hashtags.add(f"#{clean.capitalize()}")
                client_context.tendencies_hashtags = sorted(list(hashtags))[:12]

            # Gerar keywords a partir dos títulos das oportunidades
            if tendencias.get('keywords'):
                client_context.tendencies_keywords = tendencias['keywords']
            else:
                keywords = [o.get('titulo_ideia', '') for o in tend_opps if o.get('titulo_ideia')]
                client_context.tendencies_keywords = keywords[:8]
            client_context.tendencies_sources = tendencias.get('fontes', [])

            # === SAZONALIDADE ===
            sazonalidade = context_data.get('sazonalidade', {})
            client_context.seasonal_relevant_dates = sazonalidade.get('datas_relevantes', [])
            client_context.seasonal_local_events = sazonalidade.get('eventos_locais', [])
            client_context.seasonal_sources = sazonalidade.get('fontes', [])

            # === MARCA ===
            marca = context_data.get('marca', {})
            client_context.brand_online_presence = marca.get('presenca_online', '')
            client_context.brand_reputation = marca.get('reputacao', '')
            client_context.brand_communication_style = marca.get('tom_comunicacao_atual', '')
            client_context.brand_sources = marca.get('fontes', [])

            client_context.weekly_context_error = None
            client_context.weekly_context_error_date = None

            await sync_to_async(client_context.save)()

            # --- HISTÓRICO: Salvar cópia no histórico ---
            from ClientContext.models import ClientContextHistory

            await sync_to_async(ClientContextHistory.objects.create)(
                user=user,
                original_context=client_context,
                # Copiar todos os campos
                market_panorama=client_context.market_panorama,
                market_tendencies=client_context.market_tendencies,
                market_challenges=client_context.market_challenges,
                market_opportunities=client_context.market_opportunities,
                market_sources=client_context.market_sources,
                competition_main=client_context.competition_main,
                competition_strategies=client_context.competition_strategies,
                competition_benchmark=client_context.competition_benchmark,
                competition_opportunities=client_context.competition_opportunities,
                competition_sources=client_context.competition_sources,
                target_audience_profile=client_context.target_audience_profile,
                target_audience_behaviors=client_context.target_audience_behaviors,
                target_audience_interests=client_context.target_audience_interests,
                target_audience_sources=client_context.target_audience_sources,
                tendencies_popular_themes=client_context.tendencies_popular_themes,
                tendencies_hashtags=client_context.tendencies_hashtags,
                tendencies_data=client_context.tendencies_data,
                tendencies_keywords=client_context.tendencies_keywords,
                tendencies_sources=client_context.tendencies_sources,
                seasonal_relevant_dates=client_context.seasonal_relevant_dates,
                seasonal_local_events=client_context.seasonal_local_events,
                seasonal_sources=client_context.seasonal_sources,
                brand_online_presence=client_context.brand_online_presence,
                brand_reputation=client_context.brand_reputation,
                brand_communication_style=client_context.brand_communication_style,
                brand_sources=client_context.brand_sources
            )
            logger.info(f"Saved context history for user {user.id}")

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
            await self._store_user_error(user, str(e))
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

        # 2. Histórico Anti-Repetição
        excluded_topics = await self._get_recent_topics(user)
        used_url_keys_recent = await self._get_recent_url_keys(user)
        # Também evita duplicar links dentro do mesmo e-mail (entre seções)
        used_url_keys_this_run: set[str] = set()

        # 3. Executar Buscas (Paralelas ou Sequenciais)
        search_tasks = []
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

    async def _store_user_error(self, user, error_message: str):
        """Store error message in user model for retry processing."""
        client_context, created = await sync_to_async(ClientContext.objects.get_or_create)(user=user)

        # Update the error fields
        client_context.weekly_context_error = error_message
        client_context.weekly_context_error_date = timezone.now()
        await sync_to_async(client_context.save)()

        logger.error(
            f"Updated existing ClientContext for user {user.id} with error: {error_message}")

        subject = "Falha na Geração de Contexto Semanal"
        html_content = f"""
        <h1>Falha na Geração de Contexto Semanal</h1>
        <p>Ocorreu um erro durante o processo de geração de contexto semanal para o usuário {user.email}.</p>
        <pre>{error_message or 'Erro interno de servidor'}</pre>
        """
        await self.mailjet_service.send_fallback_email_to_admins(
            subject, html_content)

    async def _get_recent_topics(self, user: User) -> list:
        """Recupera tópicos abordados nas últimas 4 semanas para evitar repetição."""
        from ClientContext.models import ClientContextHistory
        from datetime import timedelta
        from django.utils import timezone

        one_month_ago = timezone.now() - timedelta(weeks=4)

        history = await sync_to_async(lambda: list(ClientContextHistory.objects.filter(
            user=user,
            created_at__gte=one_month_ago
        ).values_list('tendencies_popular_themes', flat=True)))()

        # Flatten list
        topics = []
        for item in history:
            if item:  # item pode ser lista ou string JSON
                if isinstance(item, list):
                    topics.extend(item)
                elif isinstance(item, str):
                    try:
                        topics.extend(json.loads(item))
                    except:
                        pass
        return list(set(topics))  # Únicos

    async def _get_recent_url_keys(self, user: User) -> set[str]:
        """
        Recupera chaves (domain+path) usadas recentemente a partir do histórico.
        Janela: `self.dedupe_lookback_weeks` semanas.
        """
        from ClientContext.models import ClientContextHistory
        from datetime import timedelta
        from django.utils import timezone

        now = timezone.now()
        since = now - timedelta(days=max(self.dedupe_lookback_weeks, 1) * 7)

        histories = await sync_to_async(lambda: list(
            ClientContextHistory.objects.filter(
                user=user, created_at__gte=since)
            .order_by("-created_at")
            .values("tendencies_data")
        ))()

        used: set[str] = set()
        for h in histories:
            data = h.get("tendencies_data") or {}
            if not isinstance(data, dict):
                continue
            for group in data.values():
                if not isinstance(group, dict):
                    continue
                for item in (group.get("items") or []):
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url_fonte")
                    if isinstance(url, str) and url.startswith("http"):
                        k = normalize_url_key(url)
                        if k:
                            used.add(k)

        return used
