"""
Context Persistence Service - Handles saving context data to database.
Follows Single Responsibility Principle.
"""
import logging
from django.contrib.auth.models import User
from django.utils import timezone
from asgiref.sync import sync_to_async

from ClientContext.models import ClientContext, ClientContextHistory

logger = logging.getLogger(__name__)


class ContextPersistenceService:
    """Handles all database persistence for weekly context."""

    async def save_context(
        self,
        user: User,
        context_data: dict,
        ranked_opportunities: dict
    ) -> ClientContext:
        """
        Save context data to ClientContext model.

        Args:
            user: The user to save context for
            context_data: Parsed context data from AI
            ranked_opportunities: Aggregated and ranked opportunities

        Returns:
            ClientContext: The saved context instance
        """
        client_context, created = await sync_to_async(
            ClientContext.objects.get_or_create
        )(user=user)

        # Update fields from context data
        self._update_market_fields(client_context, context_data, ranked_opportunities)
        self._update_competition_fields(client_context, context_data)
        self._update_audience_fields(client_context, context_data)
        self._update_trends_fields(client_context, context_data)
        self._update_seasonal_fields(client_context, context_data)
        self._update_brand_fields(client_context, context_data)

        # Clear any previous errors
        client_context.weekly_context_error = None
        client_context.weekly_context_error_date = None

        await sync_to_async(client_context.save)()
        return client_context

    async def save_to_history(
        self,
        user: User,
        client_context: ClientContext
    ) -> ClientContextHistory:
        """
        Save a copy of the context to history.

        Args:
            user: The user
            client_context: The context to copy to history

        Returns:
            ClientContextHistory: The created history record
        """
        history = await sync_to_async(ClientContextHistory.objects.create)(
            user=user,
            original_context=client_context,
            # Copy all fields
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
        return history

    async def store_error(self, user: User, error_msg: str):
        """Store an error message in the user's context."""
        client_context, _ = await sync_to_async(
            ClientContext.objects.get_or_create
        )(user=user)
        client_context.weekly_context_error = error_msg
        client_context.weekly_context_error_date = timezone.now()
        await sync_to_async(client_context.save)()

    # Private field update methods

    def _update_market_fields(
        self,
        ctx: ClientContext,
        data: dict,
        ranked_opportunities: dict
    ):
        """Update market-related fields."""
        mercado = data.get('mercado', {})
        ctx.market_panorama = mercado.get('panorama', '')
        ctx.market_opportunities = mercado.get('fontes_analisadas', [])
        ctx.market_sources = mercado.get('fontes', [])
        # Store ranked opportunities in tendencies_data
        ctx.tendencies_data = ranked_opportunities

    def _update_competition_fields(self, ctx: ClientContext, data: dict):
        """Update competition-related fields."""
        concorrencia = data.get('concorrencia', {})
        ctx.competition_main = concorrencia.get('principais', [])
        ctx.competition_strategies = "Ver oportunidades rankeadas."
        ctx.competition_benchmark = concorrencia.get('fontes_analisadas', [])
        ctx.competition_sources = concorrencia.get('fontes', [])

    def _update_audience_fields(self, ctx: ClientContext, data: dict):
        """Update audience-related fields."""
        publico = data.get('publico', {})
        ctx.target_audience_profile = publico.get('perfil', '')
        ctx.target_audience_behaviors = publico.get('comportamento_online', '')
        ctx.target_audience_interests = publico.get('interesses', [])
        ctx.target_audience_sources = publico.get('fontes', [])

    def _update_trends_fields(self, ctx: ClientContext, data: dict):
        """Update trends-related fields."""
        tendencias = data.get('tendencias', {})
        ctx.tendencies_hashtags = tendencias.get('hashtags', [])
        ctx.tendencies_sources = tendencias.get('fontes', [])

    def _update_seasonal_fields(self, ctx: ClientContext, data: dict):
        """Update seasonal-related fields."""
        sazonalidade = data.get('sazonalidade', {})
        sazonal = data.get('sazonal', {})  # Legacy key
        ctx.seasonal_relevant_dates = sazonalidade.get('datas_relevantes', [])
        ctx.seasonal_local_events = sazonal.get('eventos_locais', [])
        ctx.seasonal_sources = sazonal.get('fontes', [])

    def _update_brand_fields(self, ctx: ClientContext, data: dict):
        """Update brand-related fields."""
        marca = data.get('marca', {})
        ctx.brand_online_presence = marca.get('presenca_online', '')
        ctx.brand_reputation = marca.get('reputacao', '')
        ctx.brand_communication_style = marca.get('tom_comunicacao_atual', '')
        ctx.brand_sources = marca.get('fontes', [])
