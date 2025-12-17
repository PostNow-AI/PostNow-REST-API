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

from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

from ClientContext.models import ClientContext
from ClientContext.utils.url_dedupe import normalize_url_key
from ClientContext.utils.policy_resolver import resolve_policy
from ClientContext.utils.source_quality import pick_candidates, is_denied, is_allowed, allowed_domains, build_allowlist_query
from services.user_validation_service import UserValidationService
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from AuditSystem.services import AuditService
from services.google_search_service import GoogleSearchService
from services.mailjet_service import MailjetService
from ClientContext.utils.weekly_context import generate_weekly_context_email_template
# from utils.static_events import get_niche_events

logger = logging.getLogger(__name__)


def _is_blocked_filetype(url: str) -> bool:
    u = (url or "").lower()
    return u.endswith((".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"))


def _sanitize_query_for_allowlist(query: str) -> str:
    """
    Remove operadores de site do query original (que pode conter site:-site:),
    para não conflitar com a injeção de allowlist.
    """
    if not query:
        return ""
    q = re.sub(r"(?i)(-?site:[^\\s]+)", " ", query)
    q = re.sub(r"\\s+", " ", q).strip()
    # Evitar queries muito longas (CSE é sensível a tamanho)
    return q[:220]


def extract_json_block(text: str) -> str:
    """
    Extrai o primeiro bloco JSON válido de uma string usando contagem de chaves.
    Suporta objetos {} e listas [].
    """
    text = text.strip()
    
    # Encontrar o primeiro caractere de início
    start_idx = -1
    stack = []
    
    for i, char in enumerate(text):
        if char == '{':
            if start_idx == -1:
                start_idx = i
            stack.append('{')
        elif char == '}':
            if stack and stack[-1] == '{':
                stack.pop()
                if not stack and start_idx != -1:
                    return text[start_idx:i+1]
        elif char == '[':
            if start_idx == -1:
                start_idx = i
            stack.append('[')
        elif char == ']':
            if stack and stack[-1] == '[':
                stack.pop()
                if not stack and start_idx != -1:
                    return text[start_idx:i+1]
                    
    # Fallback: Tentar regex simples se a lógica de pilha falhar (ex: json malformado)
    match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
    if match:
        return match.group(0)
        
    return "{}"

class WeeklyContextService:
    def __init__(self):
        self.ai_service = AiService()
        self.prompt_service = AIPromptService()
        self.google_search_service = GoogleSearchService()
        self.mailjet_service = MailjetService()
        self.user_validation_service = UserValidationService()
        self.audit_service = AuditService()
        # Quantas semanas olhar para trás para evitar repetição de links (domínio+path)
        self.dedupe_lookback_weeks = int(os.getenv("WEEKLY_CONTEXT_DEDUPE_WEEKS", "4"))

    async def _process_user_context(self, user_id: int, bcc: list[str] = None) -> Dict[str, Any]:
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
            logger.info(f"Context Result Type: {type(context_result)}") # DEBUG
            
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
            ranked_opportunities = await self._aggregate_and_rank_opportunities(
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
            client_context.market_opportunities = context_data.get('mercado', {}).get('fontes_analisadas', [])
            
            # Salvar as Rankeadas (Top Picks) em 'market_tendencies' (campo JSON pouco usado) ou 'tendencies_data'
            # Vamos usar 'tendencies_data' para armazenar o JSON final rankeado que o email vai usar.
            client_context.tendencies_data = ranked_opportunities

            client_context.market_panorama = context_data.get(
                'mercado', {}).get('panorama', '') # Este campo pode vir vazio no novo schema, atenção
            
            # ... resto dos campos ...
            # Adaptar leitura dos campos antigos para não quebrar se vier vazio do novo schema
            
            client_context.market_sources = context_data.get(
                'mercado', {}).get('fontes', [])

            client_context.competition_main = context_data.get(
                'concorrencia', {}).get('principais', [])
            
            # Concorrência agora também usa schema de oportunidades, então 'acoes_taticas' pode não existir
            # Vamos tentar extrair algo genérico ou deixar vazio
            client_context.competition_strategies = "Ver oportunidades rankeadas."
                
            client_context.competition_benchmark = context_data.get(
                'concorrencia', {}).get('fontes_analisadas', []) # Salvar raw também
            
            client_context.competition_sources = context_data.get(
                'concorrencia', {}).get('fontes', [])

            client_context.target_audience_profile = context_data.get(
                'publico', {}).get('perfil', '')
            client_context.target_audience_behaviors = context_data.get(
                'publico', {}).get('comportamento_online', '')
            client_context.target_audience_interests = context_data.get(
                'publico', {}).get('interesses', [])
            client_context.target_audience_sources = context_data.get(
                'publico', {}).get('fontes', [])

            client_context.tendencies_hashtags = context_data.get(
                'tendencias', {}).get('hashtags', [])
            client_context.tendencies_sources = context_data.get(
                'tendencias', {}).get('fontes', [])

            client_context.seasonal_relevant_dates = context_data.get(
                'sazonalidade', {}).get('datas_relevantes', [])
            client_context.seasonal_local_events = context_data.get(
                'sazonal', {}).get('eventos_locais', [])
            client_context.seasonal_sources = context_data.get(
                'sazonal', {}).get('fontes', [])

            client_context.brand_online_presence = context_data.get(
                'marca', {}).get('presenca_online', '')
            client_context.brand_reputation = context_data.get(
                'marca', {}).get('reputacao', '')
            client_context.brand_communication_style = context_data.get(
                'marca', {}).get('tom_comunicacao_atual', '')
            client_context.brand_sources = context_data.get(
                'marca', {}).get('fontes', [])

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

            # Enviar Email (Passando o context_data COMPLETO, que agora tem 'ranked_opportunities')
            await self._send_email_async(user, context_data, bcc=bcc)

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

    async def _send_email_async(self, user: User, context_data: dict, bcc: list[str] = None):
        """Send email asynchronously."""
        # user_data from validation service returns (User, CreatorProfile) tuple
        user_tuple = await self.user_validation_service.get_user_data(user.id)
        
        if not user_tuple:
            logger.error(f"User data not found for email sending: {user.id}")
            return

        user_obj, profile_obj = user_tuple
        
        # Construct user_data dict expected by template
        user_data = {
            'business_name': profile_obj.business_name,
            'user_name': user_obj.first_name,
            'user__first_name': user_obj.first_name
        }
        
        # FIX: Remover to_email da lista de BCC se presente para evitar envio duplicado
        if bcc and user.email in bcc:
            bcc = [email for email in bcc if email != user.email]
        
        # Gerar HTML usando o novo template que suporta 'ranked_opportunities'
        html_content = generate_weekly_context_email_template(
            context_data, user_data)
            
        await self.mailjet_service.send_email(
            to_email=user.email,
            subject="Seu Contexto Semanal de Mercado",
            body=html_content,
            bcc=bcc
        )

    async def _generate_context_for_user(self, user: User) -> tuple:
        """
        Generate context for a specific user.
        Retorna: (json_string_completo, dict_urls_reais_por_secao)
        """
        self.prompt_service.set_user(user)
        
        # 1. Preparar Prompts e Queries
        profile_data = await sync_to_async(self.prompt_service._get_creator_profile_data)()
        queries = self.prompt_service._build_optimized_search_queries(profile_data)

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
        sections = ['mercado', 'concorrencia', 'publico', 'tendencias', 'sazonalidade', 'marca']
        
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
                sanitized = _sanitize_query_for_allowlist(query)
                allow_q = build_allowlist_query(sanitized or query, doms, max_domains=8) if doms else query
                pt_pool = await sync_to_async(_fetch_pool)(policy.languages[0] if policy.languages else "lang_pt", allow_q)
                if doms and len(pt_pool) < 5:
                    # fallback 1: query genérica (menos restritiva) ainda dentro da allowlist
                    fallback_base = f"{profile_data.get('specialization','')} cultura organizacional gestão de processos {datetime.now().year}"
                    fb_q = build_allowlist_query(_sanitize_query_for_allowlist(fallback_base), doms, max_domains=8)
                    pt_pool = await sync_to_async(_fetch_pool)(policy.languages[0] if policy.languages else "lang_pt", fb_q)
                if doms and len(pt_pool) < 5:
                    # fallback 2: busca geral
                    pt_pool = await sync_to_async(_fetch_pool)(policy.languages[0] if policy.languages else "lang_pt", query)
                logger.info("[SOURCE_AUDIT] seção=%s stage=raw_pt count=%s", section, len(pt_pool))
                pt_urls = [i.get("url") for i in pt_pool if isinstance(i, dict) and isinstance(i.get("url"), str)]
                picked_urls = pick_candidates(
                    section,
                    pt_urls,
                    min_allowlist=policy.allowlist_min_coverage.get(section, 3),
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
                    if _is_blocked_filetype(u) or is_denied(u):
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
                    item = next((x for x in pt_pool if isinstance(x, dict) and x.get("url") == u), None)
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
                    logger.info("[SOURCE_AUDIT] seção=%s stage=raw_en count=%s", section, len(en_pool))
                    raw_en_count = len(en_pool)
                    fallback_used.append("en")
                    en_urls = [i.get("url") for i in en_pool if isinstance(i, dict) and isinstance(i.get("url"), str)]
                    en_picked = pick_candidates(section, en_urls, min_allowlist=2, max_keep=12)
                    for u in en_picked:
                        if not u or not u.startswith("http"):
                            continue
                        if _is_blocked_filetype(u) or is_denied(u):
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
                        item = next((x for x in en_pool if isinstance(x, dict) and x.get("url") == u), None)
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
        context_borrowed_for_audience = search_results.get('mercado', []) + search_results.get('tendencias', [])

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
                temperature=0.7, # Criatividade balanceada
                top_p=0.9,
                max_output_tokens=2000,
                response_mime_type="application/json" # Forçar JSON
            )
            
            try:
                # O método generate_text espera uma lista de prompts, não string única
                ai_response = await sync_to_async(self.ai_service.generate_text)(
                    prompt_list, 
                    user, 
                    config=synthesis_config,
                    response_mime_type="application/json"
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
                final_json_parts.append(f'"{section}": {{}}') # Fallback vazio
        
        # Montar JSON Final
        full_json_str = "{" + ", ".join(final_json_parts) + "}"
        return full_json_str, search_results

    async def _store_user_error(self, user: User, error_msg: str):
        """Store error message in ClientContext."""
        from django.utils import timezone
        client_context, _ = await sync_to_async(ClientContext.objects.get_or_create)(user=user)
        client_context.weekly_context_error = error_msg
        client_context.weekly_context_error_date = timezone.now()
        await sync_to_async(client_context.save)()
        
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
            if item: # item pode ser lista ou string JSON
                if isinstance(item, list):
                    topics.extend(item)
                elif isinstance(item, str):
                    try:
                        topics.extend(json.loads(item))
                    except:
                        pass
        return list(set(topics)) # Únicos

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
            ClientContextHistory.objects.filter(user=user, created_at__gte=since)
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

    def _coerce_url_to_str(self, value: Any) -> str:
        """
        Normaliza valores vindos da IA para uma URL em string.
        A IA ocasionalmente retorna objetos/estruturas (dict/list) em vez de string.
        """
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        # Casos comuns de alucinação: {"url": "..."} / {"uri": "..."} / {"link": "..."}
        if isinstance(value, dict):
            for key in ("url", "uri", "link", "href", "original", "value"):
                v = value.get(key)
                if isinstance(v, str) and v.strip():
                    return v
            return ""
        if isinstance(value, list):
            # Pega o primeiro item útil
            for item in value:
                s = self._coerce_url_to_str(item)
                if s:
                    return s
            return ""
        # Fallback: representação em string (evitar crash)
        try:
            return str(value)
        except Exception:
            return ""

    def _recover_url(self, generated_url: Any, real_urls: List[str]) -> str:
        """
        Tenta recuperar uma URL alucinada encontrando a melhor correspondência
        entre as URLs reais fornecidas pelo Google Search.
        """
        generated_url = self._coerce_url_to_str(generated_url)
        if not generated_url:
            return ""
            
        generated_url = generated_url.strip().lower()
        # Normalizar a lista de URLs reais (GoogleSearchService retorna lista de dicts)
        real_urls_norm = []
        for real in (real_urls or []):
            real_s = self._coerce_url_to_str(real)
            if real_s:
                real_urls_norm.append(real_s)
        
        # 1. Correspondência Exata (case insensitive)
        for real in real_urls_norm:
            if real.strip().lower() == generated_url:
                return real
                
        # 2. Correspondência Parcial (Domínio e Path)
        # Se a IA inventou parâmetros mas acertou o path principal
        # Ex: real: forbes.com/artigo | generated: forbes.com/artigo?utm=...
        for real in real_urls_norm:
            real_clean = real.split('?')[0].lower()
            gen_clean = generated_url.split('?')[0]
            if real_clean in gen_clean or gen_clean in real_clean:
                return real
                
        # 3. Fallback Seguro: Se a IA inventou uma URL de um domínio que temos
        # Ex: IA inventou forbes.com/fake-news, mas temos forbes.com/real-news na lista
        # Nesses casos, melhor retornar a URL real do mesmo domínio (se houver apenas uma)
        # ou retornar vazio para não mandar 404.
        # Vamos ser conservadores: se não deu match acima, retorna a URL original da IA
        # e deixa a validação HTTP decidir (se for 404, cai fora).
        
        return generated_url

    async def _aggregate_and_rank_opportunities(
        self,
        context_data: dict,
        search_results_map: dict,
        recent_used_url_keys: Optional[set[str]] = None
    ) -> dict:
        """
        Agrega oportunidades de todas as seções (Mercado, Concorrência, Tendências),
        classifica por tipo e seleciona as Top 3 de cada categoria baseada no Score.
        Valida URLs usando requests HEAD/GET e tenta recuperação com URLs reais.
        """
        all_opportunities = []
        
        # 1. Coletar oportunidades de todas as seções que usam o novo schema
        # Dedupe por URL ao longo do e-mail inteiro (domain+path)
        used_url_keys_email: set[str] = set()
        recent_used_url_keys = recent_used_url_keys or set()

        for section in ['mercado', 'tendencias', 'concorrencia']:
            section_data = context_data.get(section, {})
            # Obter URLs reais para esta seção
            real_urls_for_section = search_results_map.get(section, [])
            candidate_urls = []
            for item in (real_urls_for_section or []):
                u = self._coerce_url_to_str(item)
                # GoogleSearchService retorna dict com chave 'url'
                if isinstance(item, dict) and not u:
                    u = self._coerce_url_to_str(item.get('url'))
                if u and u.startswith('http'):
                    if _is_blocked_filetype(u):
                        continue
                    if is_denied(u):
                        continue
                    candidate_urls.append(u)
            # Priorizar candidate_urls por allowlist/score (quando houver)
            candidate_urls = pick_candidates(section, candidate_urls, min_allowlist=1, max_keep=10)
            
            # Verificar se segue o novo schema com 'fontes_analisadas'
            if isinstance(section_data, dict) and 'fontes_analisadas' in section_data:
                for fonte in section_data['fontes_analisadas']:
                    # A IA pode retornar url_original como string OU como objeto.
                    url_original_ai = fonte.get('url_original', '')
                    url_original_ai_str = self._coerce_url_to_str(url_original_ai)
                    ai_domain = ""
                    try:
                        ai_domain = urlparse(url_original_ai_str).netloc if url_original_ai_str else ""
                    except Exception:
                        ai_domain = ""
                    
                    # Tentar RECUPERAR a URL se a IA alucinou
                    url_fonte = self._recover_url(url_original_ai, real_urls_for_section)
                    # Regra de qualidade: quando temos resultados do Google, preferir SEMPRE uma URL do Google,
                    # tentando primeiro manter o mesmo domínio sugerido pela IA (ex.: McKinsey).
                    if candidate_urls:
                        domain_candidates = [u for u in candidate_urls if ai_domain and urlparse(u).netloc == ai_domain]
                        preferred_pool = domain_candidates or candidate_urls
                        # Se a URL recuperada não estiver no pool do Google, escolhe a melhor candidata.
                        if url_fonte not in preferred_pool:
                            url_fonte = preferred_pool[0]

                    # Se a URL selecionada já foi usada recentemente e não temos alternativa válida, descarta a fonte
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
                            logger.info(
                                "[DEDUP_DROP_SOURCE] seção=%s ai_url=%s reused_url=%s",
                                section,
                                url_original_ai_str,
                                url_fonte,
                            )
                            continue

                    # Auditoria: log quando a URL é "recuperada" para uma URL real do Google Search
                    if url_original_ai_str and url_fonte and url_fonte.strip() and url_fonte.strip() != url_original_ai_str.strip():
                        logger.info(
                            "[URL_RECOVERY] seção=%s ai_url=%s recovered_url=%s",
                            section,
                            url_original_ai_str,
                            url_fonte
                        )
                    
                    # FIX: Validação básica de URL string
                    if not url_fonte or not url_fonte.startswith('http'):
                        continue 
                    
                    # FIX: Validação HTTP Permissiva
                    # Respeitar dedupe no e-mail: evita repetir domain+path
                    url_key = normalize_url_key(url_fonte)
                    if url_key and (url_key in used_url_keys_email or url_key in recent_used_url_keys):
                        # tenta pegar alternativa ainda não usada
                        for alt in candidate_urls:
                            ak = normalize_url_key(alt)
                            if ak and (ak in used_url_keys_email or ak in recent_used_url_keys):
                                continue
                            url_fonte = alt
                            break

                    if not await self._validate_url_permissive_async(url_fonte):
                        # Tentar substituir por uma URL real alternativa da busca (evita enviar 404/soft-404)
                        replaced = False
                        # Tenta primeiro candidatas do mesmo domínio
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
                            if await self._validate_url_permissive_async(alt):
                                logger.info(
                                    "[URL_FALLBACK_PICKED] seção=%s ai_url=%s bad_url=%s alt_url=%s",
                                    section,
                                    url_original_ai_str,
                                    url_fonte,
                                    alt,
                                )
                                url_fonte = alt
                                replaced = True
                                break

                        if not replaced:
                            logger.warning(
                                "[URL_DROPPED_404] seção=%s url=%s (ai_url=%s)",
                                section,
                                url_fonte,
                                url_original_ai_str
                            )
                            continue

                    # Marcar URL como usada no e-mail (após validação final)
                    final_key = normalize_url_key(url_fonte)
                    if final_key:
                        used_url_keys_email.add(final_key)

                    for op in fonte.get('oportunidades', []):
                        # Enriquecer oportunidade com dados da fonte para o display
                        op['url_fonte'] = url_fonte
                        op['origem_secao'] = section
                        all_opportunities.append(op)
        
        # 2. Agrupar por Tipo
        grouped_ops = {}
        for op in all_opportunities:
            # Normalizar tipo (remover emojis e espaços extras para chave)
            raw_type = op.get('tipo', 'Outros')
            # Extrair palavra chave do tipo (ex: "🔥 Polêmica" -> "Polêmica")
            clean_type = raw_type
            for emoji in ['🔥', '🧠', '📰', '😂', '💼', '🔮']:
                clean_type = clean_type.replace(emoji, '').strip()
            
            # Padronizar chaves para o template
            if 'Polêmica' in clean_type or 'Debate' in clean_type:
                key = 'polemica'
                display_title = '🔥 Polêmica & Debate'
            elif 'Educativo' in clean_type or 'How-to' in clean_type:
                key = 'educativo'
                display_title = '🧠 Educativo & Utilidade'
            elif 'Newsjacking' in clean_type or 'Urgência' in clean_type or 'Atualidade' in clean_type:
                key = 'newsjacking'
                display_title = '📰 Newsjacking (Urgente)'
            elif 'Entretenimento' in clean_type or 'Meme' in clean_type:
                key = 'entretenimento'
                display_title = '😂 Entretenimento & Conexão'
            elif 'Estudo de Caso' in clean_type:
                key = 'estudo_caso'
                display_title = '💼 Estudo de Caso'
            elif 'Futuro' in clean_type or 'Tendência' in clean_type:
                key = 'futuro'
                display_title = '🔮 Futuro & Tendências'
            else:
                key = 'outros'
                display_title = '⚡ Outras Oportunidades'
            
            if key not in grouped_ops:
                grouped_ops[key] = {
                    'titulo': display_title,
                    'items': []
                }
            
            # Tratamento de Score (garantir int)
            try:
                op['score'] = int(op.get('score', 0))
            except:
                op['score'] = 0
                
            grouped_ops[key]['items'].append(op)
            
        # 3. Ordenar e Filtrar (Top 3 por Tipo)
        final_structure = {}
        for key, group in grouped_ops.items():
            # Ordenar por Score Decrescente
            sorted_items = sorted(group['items'], key=lambda x: x['score'], reverse=True)
            # Pegar Top 3
            group['items'] = sorted_items[:3]
            final_structure[key] = group
            
        return final_structure

    async def _validate_url_permissive_async(self, url: str) -> bool:
        """
        Valida URL de forma permissiva. 
        Retorna True para qualquer coisa que NÃO seja um 404 confirmado.
        Timeouts e Erros de Conexão são considerados URLs Válidas (presunção de inocência).
        """
        def _is_soft_404(url_final: str, body_text: str) -> bool:
            if not body_text:
                return False
            low = body_text.lower()

            # LinkedIn Pulse: frequentemente redireciona para um "article_not_found" com status 200
            if "linkedin.com" in (url_final or ""):
                if "trk=article_not_found" in (url_final or ""):
                    return True
                if ("we can\u2019t find the page you\u2019re looking for" in low) or ("we can't find the page you're looking for" in low):
                    return True

            # Soft-404 genérico (tenta evitar falsos positivos)
            if "página não encontrada" in low or "pagina nao encontrada" in low:
                return True
            if "page not found" in low:
                return True

            return False

        def _check():
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                # Timeout curto de 3s
                response = requests.head(url, headers=headers, timeout=3, allow_redirects=True)
                if response.status_code == 404:
                    return False

                # Alguns sites retornam 200/302 no HEAD mas são soft-404 no GET (ex: LinkedIn)
                try:
                    get_resp = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
                    if get_resp.status_code == 404:
                        return False
                    if _is_soft_404(get_resp.url, get_resp.text or ""):
                        return False
                except requests.exceptions.RequestException:
                    # Se GET falhar (timeout/bloqueio), mantém a presunção de inocência,
                    # exceto quando o HEAD já indicou um erro forte (404 tratado acima).
                    return True

                return True
            except requests.exceptions.RequestException:
                # Se der timeout ou erro de conexão, assumimos que o link existe mas o site é chato
                # Tentar GET rápido só para ter certeza se não é 404 disfarçado?
                # Não, melhor ser rápido e permissivo.
                return True
            except Exception:
                # Qualquer outro erro, assume válido
                return True
        
        return await sync_to_async(_check)()
