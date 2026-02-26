"""Service for persisting context data to the database."""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

from ..models import ClientContext, ClientContextHistory
from ..utils.data_extraction import (
    extract_from_opportunities,
    generate_hashtags_from_opportunities,
    generate_keywords_from_opportunities,
)

logger = logging.getLogger(__name__)


@dataclass
class ContextSectionData:
    """Data class for a single context section."""
    raw: List[Dict]
    opportunities: List[Dict]
    titles: List[str]


class ContextPersistenceService:
    """Service responsible for persisting context data to the database.

    Separates the persistence logic from the generation logic (SRP).
    """

    async def save_context(
        self,
        user: User,
        context_data: Dict[str, Any],
        ranked_opportunities: Dict[str, Any]
    ) -> ClientContext:
        """
        Save the generated context to the database.

        Args:
            user: User instance
            context_data: Processed context data from AI
            ranked_opportunities: Ranked opportunities for email

        Returns:
            Updated ClientContext instance
        """
        client_context, created = await sync_to_async(
            ClientContext.objects.get_or_create
        )(user=user)

        # Extract data from each section
        mercado = self._extract_section(context_data, 'mercado')
        concorrencia = self._extract_section(context_data, 'concorrencia')
        tendencias = self._extract_section(context_data, 'tendencias')

        # Update all fields
        self._update_market_fields(client_context, context_data, mercado)
        self._update_competition_fields(client_context, context_data, concorrencia)
        self._update_audience_fields(client_context, context_data)
        self._update_tendencies_fields(client_context, context_data, tendencias, mercado)
        self._update_seasonal_fields(client_context, context_data)
        self._update_brand_fields(client_context, context_data)

        # Save ranked opportunities
        client_context.tendencies_data = ranked_opportunities

        # Clear error fields
        client_context.weekly_context_error = None
        client_context.weekly_context_error_date = None

        await sync_to_async(client_context.save)()

        return client_context

    async def save_context_history(
        self,
        user: User,
        client_context: ClientContext
    ) -> ClientContextHistory:
        """
        Save a copy of the context to history for tracking.

        Args:
            user: User instance
            client_context: Current ClientContext instance

        Returns:
            New ClientContextHistory instance
        """
        history = await sync_to_async(ClientContextHistory.objects.create)(
            user=user,
            original_context=client_context,
            # Market fields
            market_panorama=client_context.market_panorama,
            market_tendencies=client_context.market_tendencies,
            market_challenges=client_context.market_challenges,
            market_opportunities=client_context.market_opportunities,
            market_sources=client_context.market_sources,
            # Competition fields
            competition_main=client_context.competition_main,
            competition_strategies=client_context.competition_strategies,
            competition_benchmark=client_context.competition_benchmark,
            competition_opportunities=client_context.competition_opportunities,
            competition_sources=client_context.competition_sources,
            # Audience fields
            target_audience_profile=client_context.target_audience_profile,
            target_audience_behaviors=client_context.target_audience_behaviors,
            target_audience_interests=client_context.target_audience_interests,
            target_audience_sources=client_context.target_audience_sources,
            # Tendencies fields
            tendencies_popular_themes=client_context.tendencies_popular_themes,
            tendencies_hashtags=client_context.tendencies_hashtags,
            tendencies_data=client_context.tendencies_data,
            tendencies_keywords=client_context.tendencies_keywords,
            tendencies_sources=client_context.tendencies_sources,
            # Seasonal fields
            seasonal_relevant_dates=client_context.seasonal_relevant_dates,
            seasonal_local_events=client_context.seasonal_local_events,
            seasonal_sources=client_context.seasonal_sources,
            # Brand fields
            brand_online_presence=client_context.brand_online_presence,
            brand_reputation=client_context.brand_reputation,
            brand_communication_style=client_context.brand_communication_style,
            brand_sources=client_context.brand_sources,
        )

        logger.info(f"Saved context history for user {user.id}")
        return history

    def _extract_section(self, context_data: Dict, section_name: str) -> ContextSectionData:
        """Extract and parse a section's data."""
        section = context_data.get(section_name, {})
        raw, opps, titles = extract_from_opportunities(section)
        return ContextSectionData(raw=raw, opportunities=opps, titles=titles)

    def _update_market_fields(
        self,
        client_context: ClientContext,
        context_data: Dict,
        mercado: ContextSectionData
    ):
        """Update market-related fields."""
        section = context_data.get('mercado', {})

        # Panorama: usar campo direto OU sintetizar dos textos analisados
        client_context.market_panorama = section.get('panorama', '') or \
            '. '.join([o.get('texto_base_analisado', '') for o in mercado.opportunities[:3]
                      if o.get('texto_base_analisado')])

        # Tendências: títulos das ideias geradas
        client_context.market_tendencies = section.get('tendencias', []) or \
            [o.get('titulo_ideia', '') for o in mercado.opportunities if o.get('titulo_ideia')]

        # Desafios: filtrar oportunidades do tipo Polêmica como desafios
        client_context.market_challenges = section.get('desafios', []) or \
            [o.get('titulo_ideia', '') for o in mercado.opportunities
             if o.get('tipo') in ('Polêmica', 'Newsjacking')]

        client_context.market_sources = section.get('fontes', [])
        client_context.market_opportunities = mercado.raw

    def _update_competition_fields(
        self,
        client_context: ClientContext,
        context_data: Dict,
        concorrencia: ContextSectionData
    ):
        """Update competition-related fields."""
        section = context_data.get('concorrencia', {})

        # Principais: títulos das fontes analisadas
        client_context.competition_main = section.get('principais', []) or concorrencia.titles

        # Estratégias: sintetizar dos gatilhos criativos
        client_context.competition_strategies = section.get('estrategias', '') or \
            '. '.join([o.get('gatilho_criativo', '') for o in concorrencia.opportunities[:3]
                      if o.get('gatilho_criativo')])

        # Oportunidades: títulos das ideias
        client_context.competition_opportunities = section.get('oportunidades', '') or \
            ', '.join([o.get('titulo_ideia', '') for o in concorrencia.opportunities[:3]
                      if o.get('titulo_ideia')])

        client_context.competition_benchmark = concorrencia.raw
        client_context.competition_sources = section.get('fontes', [])

    def _update_audience_fields(self, client_context: ClientContext, context_data: Dict):
        """Update audience-related fields."""
        publico = context_data.get('publico', {})

        client_context.target_audience_profile = publico.get('perfil', '')
        client_context.target_audience_behaviors = publico.get('comportamento_online', '')
        client_context.target_audience_interests = publico.get('interesses', [])
        client_context.target_audience_sources = publico.get('fontes', [])

    def _update_tendencies_fields(
        self,
        client_context: ClientContext,
        context_data: Dict,
        tendencias: ContextSectionData,
        mercado: ContextSectionData
    ):
        """Update tendencies-related fields."""
        section = context_data.get('tendencias', {})

        # Temas populares
        client_context.tendencies_popular_themes = section.get('temas_populares', []) or \
            [o.get('titulo_ideia', '') for o in tendencias.opportunities if o.get('titulo_ideia')]

        # Hashtags
        if section.get('hashtags'):
            client_context.tendencies_hashtags = section['hashtags']
        else:
            all_opps = tendencias.opportunities + mercado.opportunities
            client_context.tendencies_hashtags = generate_hashtags_from_opportunities(all_opps)

        # Keywords
        if section.get('keywords'):
            client_context.tendencies_keywords = section['keywords']
        else:
            client_context.tendencies_keywords = generate_keywords_from_opportunities(
                tendencias.opportunities
            )

        client_context.tendencies_sources = section.get('fontes', [])

    def _update_seasonal_fields(self, client_context: ClientContext, context_data: Dict):
        """Update seasonal-related fields."""
        sazonalidade = context_data.get('sazonalidade', {})

        client_context.seasonal_relevant_dates = sazonalidade.get('datas_relevantes', [])
        client_context.seasonal_local_events = sazonalidade.get('eventos_locais', [])
        client_context.seasonal_sources = sazonalidade.get('fontes', [])

    def _update_brand_fields(self, client_context: ClientContext, context_data: Dict):
        """Update brand-related fields."""
        marca = context_data.get('marca', {})

        client_context.brand_online_presence = marca.get('presenca_online', '')
        client_context.brand_reputation = marca.get('reputacao', '')
        client_context.brand_communication_style = marca.get('tom_comunicacao_atual', '')
        client_context.brand_sources = marca.get('fontes', [])
