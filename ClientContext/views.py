import asyncio
import logging

from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AuditSystem.services import AuditService
from IdeaBank.serializers import UserSerializer
from IdeaBank.services.weekly_feed_creation import WeeklyFeedCreationService

from ClientContext.models import ClientContext
from ClientContext.services.context_enrichment_service import ContextEnrichmentService
from ClientContext.services.market_intelligence_email_service import MarketIntelligenceEmailService
from ClientContext.services.market_intelligence_enrichment_service import MarketIntelligenceEnrichmentService
from ClientContext.services.opportunities_email_service import OpportunitiesEmailService
from ClientContext.services.opportunities_generation_service import OpportunitiesGenerationService
from ClientContext.services.retry_client_context import RetryClientContext
from ClientContext.services.weekly_context_service import WeeklyContextService
from ClientContext.utils.batch_validation import (
    SINGLE_CONTEXT_RATE_LIMIT_SECONDS,
    validate_batch_number,
    validate_batch_token,
)
from ClientContext.utils.context_helpers import (
    build_context_data,
    build_full_context_data,
    check_step_result,
)

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def generate_client_context(request):
    """Generate client context view."""

    # Validar token de autenticação
    if not validate_batch_token(request):
        return Response(
            {'error': 'Unauthorized'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        # Get batch number from query params (default to 1)
        batch_number = validate_batch_number(request.GET.get('batch', '1'))
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
    """Generate client context view (manual trigger for all users)."""

    # Validar token de autenticação
    if not validate_batch_token(request):
        return Response(
            {'error': 'Unauthorized'},
            status=status.HTTP_401_UNAUTHORIZED
        )

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
    """
    Generate context, opportunities and send emails for authenticated user.

    This endpoint performs the complete flow:
    1. Generate base context (WeeklyContextService)
    2. Generate ranked opportunities (OpportunitiesGenerationService)
    3. Enrich with external sources (ContextEnrichmentService)
    4. Send Opportunities email (OpportunitiesEmailService)
    5. Send Market Intelligence email (MarketIntelligenceEmailService)

    Rate limited to 1 request per 5 minutes per user.
    """
    user = request.user
    user_id = user.id

    if not user_id:
        return Response(
            {'error': 'User ID is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Rate limiting: 1 request per 5 minutes
    cache_key = f'single_context_gen_{user_id}'
    if cache.get(cache_key):
        logger.warning(f"Rate limit hit for user {user_id}")
        return Response(
            {
                'error': 'Rate limit exceeded',
                'message': 'Please wait 5 minutes before generating context again',
                'retry_after_seconds': SINGLE_CONTEXT_RATE_LIMIT_SECONDS
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # Set rate limit lock
    cache.set(cache_key, True, timeout=SINGLE_CONTEXT_RATE_LIMIT_SECONDS)

    # Track results for each step
    step_results = {
        'context': {'status': 'pending'},
        'opportunities': {'status': 'pending'},
        'enrichment': {'status': 'pending'},
        'opportunities_email': {'status': 'pending'},
        'market_email': {'status': 'pending'},
    }
    failed_steps = []

    try:
        serialized_user = UserSerializer(user).data

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        AuditService.log_system_operation(
            user=user,
            action='single_context_generation_started',
            status='info',
            resource_type='SingleContextGeneration',
        )

        try:
            # Step 1: Generate base context
            context_service = WeeklyContextService()
            context_result = loop.run_until_complete(
                context_service.process_single_user(user_data=serialized_user)
            )
            step_results['context'] = context_result if isinstance(context_result, dict) else {'status': 'success'}

            # Validate Step 1 result
            if not check_step_result(context_result, 'context'):
                failed_steps.append('context')
                logger.error(f"Context generation failed for user {user_id}: {context_result}")

            # Get the generated context
            try:
                client_context = ClientContext.objects.get(user_id=user_id)
            except ClientContext.DoesNotExist:
                # Clear rate limit on critical failure
                cache.delete(cache_key)
                return Response(
                    {
                        'status': 'failed',
                        'error': 'Context generation failed - no context created',
                        'failed_step': 'context',
                        'details': step_results
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            context_data = build_context_data(client_context)

            # Step 2: Generate opportunities (continue even if step 1 had issues)
            opportunities_service = OpportunitiesGenerationService()
            opportunities_result = loop.run_until_complete(
                opportunities_service.generate_user_opportunities(user, context_data)
            )
            step_results['opportunities'] = opportunities_result

            if not check_step_result(opportunities_result, 'opportunities'):
                failed_steps.append('opportunities')
                logger.warning(f"Opportunities generation failed for user {user_id}")

            # Reload context to get updated tendencies_data
            client_context.refresh_from_db()
            context_data['tendencies_data'] = client_context.tendencies_data

            # Step 3: Enrich opportunities
            enrichment_service = ContextEnrichmentService()
            enrichment_result = loop.run_until_complete(
                enrichment_service.enrich_user_context(user, context_data)
            )
            step_results['enrichment'] = enrichment_result

            if not check_step_result(enrichment_result, 'enrichment'):
                failed_steps.append('enrichment')
                logger.warning(f"Enrichment failed for user {user_id}")

            # Reload context to get enriched data
            client_context.refresh_from_db()
            context_data['tendencies_data'] = client_context.tendencies_data

            # Step 4: Send Opportunities email
            opportunities_email_service = OpportunitiesEmailService()
            opportunities_email_result = loop.run_until_complete(
                opportunities_email_service.send_to_user(user, context_data)
            )
            step_results['opportunities_email'] = opportunities_email_result

            opp_email_success = opportunities_email_result.get('status') in ('success', 'sent', 'skipped')
            if not opp_email_success:
                failed_steps.append('opportunities_email')
                logger.warning(f"Opportunities email failed for user {user_id}")

            # Step 5: Send Market Intelligence email
            full_context_data = build_full_context_data(client_context)
            market_email_service = MarketIntelligenceEmailService()
            market_email_result = loop.run_until_complete(
                market_email_service.send_to_user(user, full_context_data)
            )
            step_results['market_email'] = market_email_result

            market_email_success = market_email_result.get('status') in ('success', 'sent', 'skipped')
            if not market_email_success:
                failed_steps.append('market_email')
                logger.warning(f"Market intelligence email failed for user {user_id}")

            # Determine overall status
            if not failed_steps:
                overall_status = 'success'
                message = 'Context generated and emails sent successfully'
                http_status = status.HTTP_200_OK
            elif len(failed_steps) == len(step_results):
                overall_status = 'failed'
                message = 'All steps failed'
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            else:
                overall_status = 'partial_success'
                message = f'Completed with failures in: {", ".join(failed_steps)}'
                http_status = status.HTTP_200_OK  # Still 200 for partial success

            AuditService.log_system_operation(
                user=user,
                action='single_context_generation_completed',
                status=overall_status,
                resource_type='SingleContextGeneration',
                details={
                    'step_results': {k: v.get('status', 'unknown') for k, v in step_results.items()},
                    'failed_steps': failed_steps,
                }
            )

            weekly_feed_creation = WeeklyFeedCreationService()

            loop.run_until_complete(weekly_feed_creation.process_single_user(serialized_user))

            return Response({
                'status': overall_status,
                'message': message,
                'failed_steps': failed_steps if failed_steps else None,
                'emails_sent': {
                    'opportunities': opp_email_success,
                    'market_intelligence': market_email_success,
                },
                'details': {k: v.get('status', 'unknown') for k, v in step_results.items()},
            }, status=http_status)

        finally:
            loop.close()

    except Exception as e:
        # Clear rate limit on unexpected failure so user can retry
        cache.delete(cache_key)

        logger.exception(f"Unexpected error in generate_single_client_context for user {user_id}")
        AuditService.log_system_operation(
            user=request.user if hasattr(request, 'user') else None,
            action='single_context_generation_failed',
            status='error',
            resource_type='SingleContextGeneration',
            details={'error': str(e), 'step_results': step_results}
        )
        return Response(
            {
                'status': 'failed',
                'error': f'Failed to generate context: {str(e)}',
                'details': {k: v.get('status', 'unknown') for k, v in step_results.items()},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def retry_generate_client_context(request):
    """Retry generate client context view."""

    # Validar token de autenticação
    if not validate_batch_token(request):
        return Response(
            {'error': 'Unauthorized'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        # Get batch number from query params (default to 1)
        batch_number = validate_batch_number(request.GET.get('batch', '1'))
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
def generate_opportunities(request):
    """
    Generate content opportunities from context data (Phase 1b).

    SUNDAY - After context generation
    Transforms raw context into ranked opportunities for Monday email.

    Query params:
        batch: Batch number for processing (default: 1)
    """
    # Validar token de autenticação
    if not validate_batch_token(request):
        return Response(
            {'error': 'Unauthorized'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        batch_number = validate_batch_number(request.GET.get('batch', '1'))
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
    # Validar token de autenticação
    if not validate_batch_token(request):
        return Response(
            {'error': 'Unauthorized'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        batch_number = validate_batch_number(request.GET.get('batch', '1'))
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
                email_service.mail_opportunities(
                    batch_number=batch_number,
                    batch_size=batch_size
                )
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
    # Validar token de autenticação
    if not validate_batch_token(request):
        return Response(
            {'error': 'Unauthorized'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        batch_number = validate_batch_number(request.GET.get('batch', '1'))
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


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def test_enrichment_for_user(request):
    """
    Test enrichment pipeline for a specific user by email.

    Query Parameters:
        email: User email to test
        send_email: Whether to send email after enrichment (default: true)

    Requires CRON_SECRET authorization.
    """
    if not validate_batch_token(request):
        return Response(
            {'error': 'Unauthorized'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    email = request.query_params.get('email', '')
    send_email_flag = request.query_params.get('send_email', 'true').lower() == 'true'

    if not email:
        return Response(
            {'error': 'Email parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from django.contrib.auth.models import User

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': f'User not found: {email}'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        context = ClientContext.objects.get(user=user)
    except ClientContext.DoesNotExist:
        return Response(
            {'error': f'Context not found for user: {email}'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check opportunities
    tendencies = context.tendencies_data or {}
    total_opportunities = sum(
        len(data.get('items', []))
        for data in tendencies.values()
        if isinstance(data, dict) and 'items' in data
    )

    if total_opportunities == 0:
        return Response({
            'error': 'No opportunities to enrich',
            'message': 'Run generate-opportunities first'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Reset enrichment status
    old_status = context.context_enrichment_status
    context.context_enrichment_status = 'pending'
    context.context_enrichment_error = None
    context.save()

    result = {
        'user_id': user.id,
        'email': email,
        'opportunities_count': total_opportunities,
        'previous_status': old_status,
        'steps': {}
    }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Step 1: Enrichment
        enrichment_service = ContextEnrichmentService()
        context_data = {
            'user_id': user.id,
            'tendencies_data': context.tendencies_data,
        }

        enrichment_result = loop.run_until_complete(
            enrichment_service.enrich_user_context(user, context_data)
        )
        result['steps']['enrichment'] = enrichment_result

        # Collect enriched sources info
        context.refresh_from_db()
        tendencies = context.tendencies_data or {}
        sources_by_category = {}
        total_sources = 0

        for category, data in tendencies.items():
            if isinstance(data, dict) and 'items' in data:
                category_sources = []
                for item in data.get('items', []):
                    sources = item.get('enriched_sources', [])
                    category_sources.extend(sources)
                    total_sources += len(sources)
                if category_sources:
                    sources_by_category[category] = [
                        {'title': s.get('title', ''), 'url': s.get('url', '')}
                        for s in category_sources[:3]
                    ]

        result['enriched_sources'] = {
            'total': total_sources,
            'by_category': sources_by_category
        }

        # Step 2: Send email if requested
        if send_email_flag:
            email_service = OpportunitiesEmailService()
            email_result = loop.run_until_complete(
                email_service.send_email_to_user(user)
            )
            result['steps']['email'] = email_result

        result['status'] = 'success'
        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Error in test_enrichment_for_user: {e}")
        result['status'] = 'failed'
        result['error'] = str(e)
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        loop.close()
