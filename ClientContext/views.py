import asyncio

from AuditSystem.services import AuditService
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from IdeaBank.serializers import UserSerializer
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ClientContext.models import ClientContext
from ClientContext.services.context_enrichment_service import ContextEnrichmentService
from ClientContext.services.market_intelligence_email_service import MarketIntelligenceEmailService
from ClientContext.services.opportunities_email_service import OpportunitiesEmailService
from ClientContext.services.opportunities_generation_service import OpportunitiesGenerationService
from ClientContext.services.market_intelligence_enrichment_service import MarketIntelligenceEnrichmentService
from ClientContext.services.retry_client_context import RetryClientContext
from ClientContext.services.weekly_context_email_service import (
    WeeklyContextEmailService,
)
from ClientContext.services.weekly_context_service import WeeklyContextService


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def generate_client_context(request):
    """Generate client context view."""

    try:
        # Get batch number from query params (default to 1)
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 3  # Process 3 users per batch, to avoid vercel timeouts

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='weekly_context_generation_started',
            status='info',
            resource_type='WeeklyContextGeneration',
        )

        try:
            context_service = WeeklyContextService()
            result = loop.run_until_complete(
                context_service.process_all_users_context(
                    batch_number=batch_number, batch_size=batch_size)
            )
            AuditService.log_system_operation(
                user=None,
                action='weekly_context_generation_completed',
                status='success',
                resource_type='WeeklyContextGeneration',
            )
            return Response(result, status=status.HTTP_200_OK)
        finally:
            loop.close()

    except Exception as e:
        AuditService.log_system_operation(
            user=None,
            action='weekly_context_generation_failed',
            status='error',
            resource_type='WeeklyContextGeneration',
            details=str(e)
        )
        return Response(
            {'error': f'Failed to generate weekly context: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def manual_generate_client_context(request):
    """Generate client context view."""

    try:

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='weekly_context_generation_started',
            status='info',
            resource_type='WeeklyContextGeneration',
        )

        try:
            context_service = WeeklyContextService()
            result = loop.run_until_complete(
                context_service.process_all_users_context(
                    batch_number=1, batch_size=0)
            )
            AuditService.log_system_operation(
                user=None,
                action='weekly_context_generation_completed',
                status='success',
                resource_type='WeeklyContextGeneration',
            )
            return Response(result, status=status.HTTP_200_OK)
        finally:
            loop.close()

    except Exception as e:
        AuditService.log_system_operation(
            user=None,
            action='weekly_context_generation_failed',
            status='error',
            resource_type='WeeklyContextGeneration',
            details=str(e)
        )
        return Response(
            {'error': f'Failed to generate weekly context: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_single_client_context(request):
    """Generate single client context view."""

    try:
        user_id = request.user.id

        if not user_id:
            return Response(
                {'error': 'User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_data = User.objects.get(
            id=user_id,
        )

        serialized_user = UserSerializer(user_data).data

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='weekly_context_generation_started',
            status='info',
            resource_type='WeeklyContextGeneration',
        )

        try:
            context_service = WeeklyContextService()
            result = loop.run_until_complete(
                context_service.process_single_user(
                    user_data=serialized_user)
            )
            mail_context_service = WeeklyContextEmailService()

            context_data = ClientContext.objects.filter(
                user_id=user_id
            ).select_related('user').values(
                'id', 'user__id', 'user__email', 'user__first_name', 'market_panorama', 'market_tendencies', 'market_challenges', 'market_sources', 'competition_main', 'competition_strategies', 'competition_opportunities', 'competition_sources', 'target_audience_profile', 'target_audience_behaviors', 'target_audience_interests', 'target_audience_sources', 'tendencies_popular_themes', 'tendencies_hashtags', 'tendencies_keywords', 'tendencies_sources', 'tendencies_data', 'seasonal_relevant_dates', 'seasonal_local_events', 'seasonal_sources', 'brand_online_presence', 'brand_reputation', 'brand_communication_style', 'brand_sources', 'created_at', 'updated_at', 'user_id', 'weekly_context_error', 'weekly_context_error_date', 'context_enrichment_status', 'context_enrichment_date', 'context_enrichment_error'
            )
            
            if context_data.exists():
                loop.run_until_complete(mail_context_service.send_weekly_context_email(
                    user_data, context_data[0])
                )

            AuditService.log_system_operation(
                user=None,
                action='weekly_context_generation_completed',
                status='success',
                resource_type='WeeklyContextGeneration',
            )
            return Response(result, status=status.HTTP_200_OK)
        finally:
            loop.close()

    except Exception as e:
        AuditService.log_system_operation(
            user=None,
            action='weekly_context_generation_failed',
            status='error',
            resource_type='WeeklyContextGeneration',
            details=str(e)
        )
        return Response(
            {'error': f'Failed to generate weekly context: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def retry_generate_client_context(request):
    """Retry generate client context view."""

    try:
       # Get batch number from query params (default to 1)
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 2  # Process 2 users per batch, to avoid vercel timeouts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='weekly_context_generation_started',
            status='info',
            resource_type='WeeklyContextGeneration',
        )

        try:
            retry_context_service = RetryClientContext()
            result = loop.run_until_complete(
                retry_context_service.process_all_users_context(
                    batch_number=1, batch_size=0)
            )
            AuditService.log_system_operation(
                user=None,
                action='weekly_context_generation_completed',
                status='success',
                resource_type='WeeklyContextGeneration',
            )
            return Response(result, status=status.HTTP_200_OK)
        finally:
            loop.close()

    except Exception as e:
        AuditService.log_system_operation(
            user=None,
            action='weekly_context_generation_failed',
            status='error',
            resource_type='WeeklyContextGeneration',
            details=str(e)
        )
        return Response(
            {'error': f'Failed to generate weekly context: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def generate_opportunities(request):
    """
    Generate content opportunities from context data (Phase 1b).

    SUNDAY - After context generation
    Transforms raw context into ranked opportunities for Monday email.

    Query params:
        batch: Batch number for processing (default: 1)
    """
    try:
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 5  # Process 5 users per batch

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=None,
            action='opportunities_generation_started',
            status='info',
            resource_type='OpportunitiesGeneration',
            details={'batch': batch_number}
        )

        try:
            service = OpportunitiesGenerationService()
            result = loop.run_until_complete(
                service.generate_all_users_opportunities(
                    batch_number=batch_number,
                    batch_size=batch_size
                )
            )

            AuditService.log_system_operation(
                user=None,
                action='opportunities_generation_completed',
                status='success' if result['status'] == 'completed' else 'partial',
                resource_type='OpportunitiesGeneration',
                details=result
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            AuditService.log_system_operation(
                user=None,
                action='opportunities_generation_failed',
                status='error',
                resource_type='OpportunitiesGeneration',
                details={'error': str(e)}
            )
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            loop.close()

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def send_weekly_context_email(request):
    """
    [DISABLED] This endpoint has been replaced by:
    - send_market_intelligence_email (Wednesday)
    - enrich_and_send_opportunities_email (Monday)

    The weekly context generation (generate_client_context) is still active
    as it feeds the AI prompt service for content generation.
    """
    AuditService.log_system_operation(
        user=None,
        action='weekly_context_email_disabled',
        status='info',
        resource_type='WeeklyContextEmail',
        details={'message': 'Endpoint disabled. Use market_intelligence or opportunities endpoints.'}
    )

    return Response({
        'status': 'disabled',
        'message': 'This endpoint has been disabled.',
        'alternatives': [
            '/client-context/send-market-intelligence-email/ (Wednesday)',
            '/client-context/enrich-and-send-opportunities-email/ (Monday)',
        ]
    }, status=status.HTTP_410_GONE)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def enrich_and_send_opportunities_email(request):
    """
    Enrich context data (Phase 2) and send opportunities email.

    MONDAY EMAIL - Content Opportunities

    This endpoint:
    1. Fetches contexts pending enrichment
    2. Enriches each context with additional sources and analysis
    3. Sends the opportunities email with enriched data
    """
    try:
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 2  # Process 2 users per batch to avoid timeouts

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Phase 2: Enrich contexts
            AuditService.log_system_operation(
                user=None,
                action='context_enrichment_started',
                status='info',
                resource_type='ContextEnrichment',
            )

            enrichment_service = ContextEnrichmentService()
            enrichment_result = loop.run_until_complete(
                enrichment_service.enrich_all_users_context(
                    batch_number=batch_number,
                    batch_size=batch_size
                )
            )

            AuditService.log_system_operation(
                user=None,
                action='context_enrichment_completed',
                status='success',
                resource_type='ContextEnrichment',
                details=enrichment_result
            )

            # Send opportunities emails with enriched data
            email_service = OpportunitiesEmailService()
            email_result = loop.run_until_complete(
                email_service.mail_opportunities()
            )

            AuditService.log_system_operation(
                user=None,
                action='opportunities_email_sent',
                status='success' if email_result['status'] == 'completed' else 'failure',
                resource_type='OpportunitiesEmail',
                details=email_result
            )

            return Response({
                'status': 'completed',
                'enrichment': enrichment_result,
                'email': email_result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            AuditService.log_system_operation(
                user=None,
                action='enrich_and_send_opportunities_failed',
                status='error',
                resource_type='OpportunitiesEmail',
                details={'error': str(e)}
            )
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            loop.close()

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def send_market_intelligence_email(request):
    """
    Enrich and send market intelligence email.

    WEDNESDAY EMAIL - Market Intelligence

    Phase 1: Enrich each section with additional sources via Google Search
    Phase 2: Send email with enriched data

    Contains: Market overview, competition analysis, audience insights,
    trends, and seasonal calendar - all with enriched sources.

    Query params:
        batch: Batch number for processing (default: 1)
    """
    try:
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 5  # Process 5 users per batch

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Phase 1: Enrich market intelligence data
            enrichment_service = MarketIntelligenceEnrichmentService()
            enrichment_result = loop.run_until_complete(
                enrichment_service.enrich_all_users(
                    batch_number=batch_number,
                    batch_size=batch_size
                )
            )

            AuditService.log_system_operation(
                user=None,
                action='market_intelligence_enrichment_completed',
                status='success' if enrichment_result['status'] == 'completed' else 'partial',
                resource_type='MarketIntelligenceEnrichment',
                details=enrichment_result
            )

            # Phase 2: Send emails with enriched data
            email_service = MarketIntelligenceEmailService()
            result = loop.run_until_complete(
                email_service.send_all(
                    batch_number=batch_number,
                    batch_size=batch_size
                )
            )

            AuditService.log_system_operation(
                user=None,
                action='market_intelligence_email_sent',
                status='success' if result['status'] == 'completed' else 'failure',
                resource_type='MarketIntelligenceEmail',
                details=result
            )

            return Response({
                'status': 'completed',
                'enrichment': enrichment_result,
                'email': result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            AuditService.log_system_operation(
                user=None,
                action='market_intelligence_email_failed',
                status='error',
                resource_type='MarketIntelligenceEmail',
                details={'error': str(e)}
            )
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            loop.close()

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
