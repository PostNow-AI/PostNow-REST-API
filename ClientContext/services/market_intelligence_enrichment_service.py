"""
Serviço de enriquecimento para Inteligência de Mercado.

Enriquece cada seção do contexto (mercado, concorrência, público, etc)
com fontes adicionais via Google Search, similar ao ContextEnrichmentService.

Fluxo:
    QUARTA → Enriquecer seções + Enviar email de Inteligência de Mercado
"""
import logging
from typing import Any, Dict, List, Optional, Set

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from ClientContext.models import ClientContext
from ClientContext.utils.search_utils import fetch_and_filter_sources
from services.google_search_service import GoogleSearchService

logger = logging.getLogger(__name__)

# Mapeamento de seções para queries de busca
SECTION_SEARCH_CONFIG = {
    'mercado': {
        'field': 'market_panorama',
        'query_template': '{business_sector} mercado tendências {year}',
        'section_type': 'mercado',
    },
    'concorrencia': {
        'field': 'competition_strategies',
        'query_template': '{business_sector} concorrentes estratégias {year}',
        'section_type': 'concorrencia',
    },
    'publico': {
        'field': 'target_audience_profile',
        'query_template': '{target_audience} comportamento digital {year}',
        'section_type': 'tendencias',
    },
    'tendencias': {
        'field': 'tendencies_popular_themes',
        'query_template': '{business_sector} tendências redes sociais {year}',
        'section_type': 'tendencias',
    },
    'calendario': {
        'field': 'seasonal_relevant_dates',
        'query_template': 'datas comemorativas marketing {month} {year}',
        'section_type': 'mercado',
    },
}


class MarketIntelligenceEnrichmentService:
    """
    Serviço para enriquecer dados de Inteligência de Mercado com fontes adicionais.
    """

    def __init__(self, google_search_service: Optional[GoogleSearchService] = None):
        self.google_search_service = google_search_service or GoogleSearchService()

    async def enrich_all_users(
        self,
        batch_number: int = 1,
        batch_size: int = 5
    ) -> Dict[str, Any]:
        """
        Enriquece dados de mercado para todos os usuários.

        Args:
            batch_number: Número do lote
            batch_size: Tamanho do lote

        Returns:
            Dict com resultados do processamento
        """
        offset = (batch_number - 1) * batch_size
        contexts = await self._get_contexts_to_enrich(offset, batch_size)

        if not contexts:
            return {
                'status': 'completed',
                'processed': 0,
                'message': 'No contexts to enrich',
            }

        processed = 0
        failed = 0
        results = []

        for context_data in contexts:
            try:
                user = await sync_to_async(User.objects.get)(id=context_data['user_id'])
                result = await self.enrich_user_context(user, context_data)
                results.append(result)
                if result.get('status') == 'success':
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error enriching market intelligence for user {context_data['user_id']}: {e}")
                failed += 1
                results.append({
                    'user_id': context_data['user_id'],
                    'status': 'failed',
                    'error': str(e)
                })

        return {
            'status': 'completed',
            'processed': processed,
            'failed': failed,
            'total': len(contexts),
            'details': results,
        }

    async def enrich_user_context(
        self,
        user: User,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enriquece o contexto de um usuário com fontes adicionais.

        Args:
            user: Instância do usuário
            context_data: Dados do contexto

        Returns:
            Dict com resultado do enriquecimento
        """
        try:
            from services.get_creator_profile_data import get_creator_profile_data
            profile_data = await sync_to_async(get_creator_profile_data)(user)

            used_url_keys: Set[str] = set()
            enriched_sources = {}

            # Enriquecer cada seção
            for section_name, config in SECTION_SEARCH_CONFIG.items():
                try:
                    sources = await self._enrich_section(
                        section_name,
                        config,
                        context_data,
                        profile_data,
                        used_url_keys
                    )
                    enriched_sources[f'{section_name}_enriched_sources'] = sources
                except Exception as e:
                    logger.warning(f"Failed to enrich section {section_name}: {e}")
                    enriched_sources[f'{section_name}_enriched_sources'] = []

            # Salvar fontes enriquecidas no contexto
            client_context = await sync_to_async(ClientContext.objects.get)(user=user)

            # Atualizar campos de fontes com as novas fontes enriquecidas
            if enriched_sources.get('mercado_enriched_sources'):
                existing = client_context.market_sources or []
                client_context.market_sources = self._merge_sources(
                    existing, enriched_sources['mercado_enriched_sources']
                )

            if enriched_sources.get('concorrencia_enriched_sources'):
                existing = client_context.competition_sources or []
                client_context.competition_sources = self._merge_sources(
                    existing, enriched_sources['concorrencia_enriched_sources']
                )

            if enriched_sources.get('publico_enriched_sources'):
                existing = client_context.target_audience_sources or []
                client_context.target_audience_sources = self._merge_sources(
                    existing, enriched_sources['publico_enriched_sources']
                )

            if enriched_sources.get('tendencias_enriched_sources'):
                existing = client_context.tendencies_sources or []
                client_context.tendencies_sources = self._merge_sources(
                    existing, enriched_sources['tendencias_enriched_sources']
                )

            if enriched_sources.get('calendario_enriched_sources'):
                existing = client_context.seasonal_sources or []
                client_context.seasonal_sources = self._merge_sources(
                    existing, enriched_sources['calendario_enriched_sources']
                )

            await sync_to_async(client_context.save)()

            total_sources = sum(len(v) for v in enriched_sources.values())
            logger.info(f"Enriched market intelligence for user {user.id} with {total_sources} sources")

            return {
                'user_id': user.id,
                'status': 'success',
                'sources_added': total_sources
            }

        except Exception as e:
            logger.error(f"Error enriching market intelligence for user {user.id}: {e}")
            return {
                'user_id': user.id,
                'status': 'failed',
                'error': str(e)
            }

    async def _enrich_section(
        self,
        section_name: str,
        config: Dict[str, str],
        context_data: Dict[str, Any],
        profile_data: Dict[str, Any],
        used_url_keys: Set[str]
    ) -> List[Dict[str, str]]:
        """
        Enriquece uma seção específica com fontes adicionais.

        Args:
            section_name: Nome da seção
            config: Configuração da seção
            context_data: Dados do contexto
            profile_data: Dados do perfil do usuário
            used_url_keys: URLs já usadas (para deduplicação)

        Returns:
            Lista de fontes encontradas
        """
        # Construir query de busca
        now = timezone.now()
        query = config['query_template'].format(
            business_sector=profile_data.get('specialization', ''),
            target_audience=profile_data.get('target_audience', ''),
            year=now.year,
            month=now.strftime('%B'),
        )

        # Buscar e filtrar fontes
        sources = await fetch_and_filter_sources(
            self.google_search_service,
            query,
            config['section_type'],
            used_url_keys
        )

        return sources

    def _merge_sources(
        self,
        existing: List[Any],
        new_sources: List[Dict[str, str]]
    ) -> List[str]:
        """
        Mescla fontes existentes com novas fontes.

        Args:
            existing: Fontes existentes (podem ser strings ou dicts)
            new_sources: Novas fontes (dicts com url, title, snippet)

        Returns:
            Lista de URLs únicas
        """
        # Extrair URLs existentes
        existing_urls = set()
        for source in existing:
            if isinstance(source, str):
                existing_urls.add(source)
            elif isinstance(source, dict):
                existing_urls.add(source.get('url', ''))

        # Adicionar novas URLs
        result = list(existing_urls)
        for source in new_sources:
            url = source.get('url', '')
            if url and url not in existing_urls:
                result.append(url)
                existing_urls.add(url)

        return result[:10]  # Limitar a 10 fontes por seção

    @sync_to_async
    def _get_contexts_to_enrich(
        self,
        offset: int = 0,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Busca contextos para enriquecimento de inteligência de mercado.
        """
        return list(
            ClientContext.objects.filter(
                weekly_context_error__isnull=True,
            ).select_related('user').values(
                'id', 'user_id',
                'market_panorama', 'market_tendencies', 'market_challenges', 'market_sources',
                'competition_main', 'competition_strategies', 'competition_sources',
                'target_audience_profile', 'target_audience_sources',
                'tendencies_popular_themes', 'tendencies_sources',
                'seasonal_relevant_dates', 'seasonal_sources',
            )[offset:offset + limit]
        )
