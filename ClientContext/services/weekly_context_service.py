import html
import json
import logging
import re
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from AuditSystem.services import AuditService
from ClientContext.models import ClientContext
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.mailjet_service import MailjetService
from services.semaphore_service import SemaphoreService
from services.get_creator_profile_data import get_creator_profile_data
from services.trends_discovery_service import TrendsDiscoveryService
from services.user_validation_service import UserValidationService

logger = logging.getLogger(__name__)

# DRY: Mapeamento centralizado JSON -> Model fields
CONTEXT_FIELD_MAPPING = {
    'mercado': {
        'panorama': ('market_panorama', ''),
        'tendencias': ('market_tendencies', []),
        'desafios': ('market_challenges', []),
        'fontes': ('market_sources', []),
    },
    'concorrencia': {
        'principais': ('competition_main', []),
        'estrategias': ('competition_strategies', ''),
        'oportunidades': ('competition_opportunities', ''),
        'fontes': ('competition_sources', []),
    },
    'publico': {
        'perfil': ('target_audience_profile', ''),
        'comportamento_online': ('target_audience_behaviors', ''),
        'interesses': ('target_audience_interests', []),
        'fontes': ('target_audience_sources', []),
    },
    'tendencias': {
        'temas_populares': ('tendencies_popular_themes', []),
        'hashtags': ('tendencies_hashtags', []),
        'keywords': ('tendencies_keywords', []),
        'fontes': ('tendencies_sources', []),
    },
    'sazonalidade': {
        'datas_relevantes': ('seasonal_relevant_dates', []),
        'eventos_locais': ('seasonal_local_events', []),
        'fontes': ('seasonal_sources', []),
    },
    'marca': {
        'presenca_online': ('brand_online_presence', ''),
        'reputacao': ('brand_reputation', ''),
        'tom_comunicacao_atual': ('brand_communication_style', ''),
        'fontes': ('brand_sources', []),
    },
}


class WeeklyContextService:
    """Service for generating weekly context for users.

    Supports dependency injection for testing and flexibility (DIP).

    Fluxo melhorado (2026):
        1. Fase 0: TrendsDiscoveryService descobre tendências REAIS
        2. Fase 1: Contexto gerado com tendências como input
        3. Resultado: Temas validados com fontes verificáveis
    """

    def __init__(
        self,
        user_validation_service: Optional[UserValidationService] = None,
        semaphore_service: Optional[SemaphoreService] = None,
        ai_service: Optional[AiService] = None,
        prompt_service: Optional[AIPromptService] = None,
        audit_service: Optional[AuditService] = None,
        mailjet_service: Optional[MailjetService] = None,
        trends_discovery_service: Optional[TrendsDiscoveryService] = None,
    ):
        self.user_validation_service = user_validation_service or UserValidationService()
        self.semaphore_service = semaphore_service or SemaphoreService()
        self.ai_service = ai_service or AiService()
        self.prompt_service = prompt_service or AIPromptService()
        self.audit_service = audit_service or AuditService()
        self.mailjet_service = mailjet_service or MailjetService()
        self.trends_discovery_service = trends_discovery_service or TrendsDiscoveryService()

    @sync_to_async
    def _get_eligible_users(self, offset: int, limit: int) -> list[dict[str, Any]]:
        """Get a batch of users eligible for weekly context generation"""
        if limit is None:
            return list(
                User.objects.filter(
                    usersubscription__status='active',
                    is_active=True
                ).distinct().order_by('id').values('id', 'email', 'username')[offset:]
            )

        return list(
            User.objects.filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().order_by('id').values('id', 'email', 'username')[offset:offset + limit]
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
        """Process weekly context generation for a single user.

        Fluxo melhorado (2026):
            1. Fase 0: Descobrir tendências REAIS via Google Trends
            2. Fase 1: Gerar contexto com tendências como input
            3. Salvar tendências descobertas e contexto gerado
        """
        try:
            user = await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

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

            # FASE 0: Descobrir tendências REAIS antes de gerar contexto
            discovered_trends = await self._discover_trends_for_user(user)

            # FASE 1: Gerar contexto com tendências como input
            context_result = await sync_to_async(self._generate_context_for_user)(
                user, discovered_trends
            )
            # Remove markdown code block se presente (```json ... ```)
            context_json = re.sub(r'^```(?:json)?\s*', '', context_result.strip())
            context_json = re.sub(r'\s*```$', '', context_json).strip()

            context_data = json.loads(context_json).get(
                'contexto_pesquisado', {})

            client_context, created = await sync_to_async(ClientContext.objects.get_or_create)(user=user)

            # DRY: Usa mapeamento centralizado
            self._map_context_fields(client_context, context_data)

            # Salvar tendências descobertas para uso posterior
            client_context.discovered_trends = discovered_trends

            client_context.weekly_context_error = None
            client_context.weekly_context_error_date = None
            # Resetar status de enriquecimento para nova semana
            client_context.context_enrichment_status = 'pending'
            client_context.context_enrichment_error = None

            await sync_to_async(client_context.save)()

            await sync_to_async(self.audit_service.log_context_generation)(
                user=user,
                action='context_generated',
                status='success',
                details={
                    'discovered_trends_count': discovered_trends.get('validated_count', 0)
                }
            )

            return {
                'user_id': user_id,
                'status': 'success',
                'discovered_trends_count': discovered_trends.get('validated_count', 0),
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

    async def _discover_trends_for_user(self, user: User) -> Dict[str, Any]:
        """
        Fase 0: Descobre tendências REAIS para o setor do usuário.

        Usa Google Trends para descobrir o que está em alta e valida
        cada tendência buscando fontes reais no Google Search.

        Args:
            user: Instância do usuário

        Returns:
            Dict com tendências descobertas e validadas
        """
        try:
            # Buscar dados do perfil do usuário
            profile_data = await sync_to_async(get_creator_profile_data)(user)

            sector = profile_data.get('specialization', '')
            business_description = profile_data.get('business_description', '')
            location = profile_data.get('business_location', 'Brasil')

            if not sector:
                logger.warning(f"User {user.id} has no sector defined, skipping trend discovery")
                return {
                    'general_trends': [],
                    'sector_trends': [],
                    'rising_topics': [],
                    'validated_count': 0,
                    'discovery_metadata': {'error': 'no_sector_defined'}
                }

            # Executar descoberta de tendências (sync, pois pytrends é síncrono)
            discovered_trends = await sync_to_async(
                self.trends_discovery_service.discover_trends_for_sector
            )(
                sector=sector,
                business_description=business_description,
                location=location,
            )

            logger.info(
                f"Discovered {discovered_trends.get('validated_count', 0)} trends "
                f"for user {user.id} (sector: {sector})"
            )

            return discovered_trends

        except Exception as e:
            logger.error(f"Error discovering trends for user {user.id}: {e}")
            # Retornar estrutura vazia em caso de erro (não bloqueia o fluxo)
            return {
                'general_trends': [],
                'sector_trends': [],
                'rising_topics': [],
                'validated_count': 0,
                'discovery_metadata': {'error': str(e)}
            }

    def _map_context_fields(self, client_context: ClientContext, context_data: dict) -> None:
        """DRY: Map JSON context data to ClientContext model fields.

        Uses CONTEXT_FIELD_MAPPING to avoid repetitive field assignments.
        """
        for section_key, fields in CONTEXT_FIELD_MAPPING.items():
            section_data = context_data.get(section_key, {})
            for json_key, (model_field, default) in fields.items():
                value = section_data.get(json_key, default)
                setattr(client_context, model_field, value)

    def _generate_context_for_user(
        self,
        user: User,
        discovered_trends: Dict[str, Any] = None
    ) -> str:
        """AI service call to generate weekly context for a user.

        Args:
            user: Instância do usuário
            discovered_trends: Tendências descobertas pelo TrendsDiscoveryService

        Returns:
            String JSON com o contexto gerado
        """
        try:
            self.prompt_service.set_user(user)
            prompt = self.prompt_service.build_context_prompts(
                discovered_trends=discovered_trends
            )
            context_result = self.ai_service.generate_text(prompt, user)

            return context_result
        except Exception as e:
            raise Exception(
                f"Failed to generate context for user {user.id}: {str(e)}")

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
        # Sanitizar dados para prevenir XSS no email de admin
        safe_email = html.escape(str(user.email))
        safe_error = html.escape(str(error_message or 'Erro interno de servidor'))
        html_content = f"""
        <h1>Falha na Geração de Contexto Semanal</h1>
        <p>Ocorreu um erro durante o processo de geração de contexto semanal para o usuário {safe_email}.</p>
        <pre>{safe_error}</pre>
        """
        await self.mailjet_service.send_fallback_email_to_admins(
            subject, html_content)
