import asyncio

from AuditSystem.services import AuditService
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import (
    api_view,
)
from rest_framework.response import Response

from ClientContext.services.retry_client_context import RetryClientContext
from ClientContext.services.weekly_context_email_service import (
    WeeklyContextEmailService,
)
from ClientContext.services.weekly_context_service import WeeklyContextService


@csrf_exempt
@api_view(['GET'])
def generate_client_context(request):
    """Generate client context view."""

    # Verify it's from Cronjob (security check)
    auth_header = request.headers.get('Authorization', '')
    expected_auth = f"Bearer {settings.CRON_SECRET}"

    if auth_header != expected_auth:
        return Response({
            'error': 'Unauthorized'
        }, status=status.HTTP_401_UNAUTHORIZED)
    try:
        # Get batch number from query params (default to 1)
        batch_number = int(request.GET.get('batch', 1))
        batch_size = 5  # Process 5 users per batch, to avoid vercel timeouts

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


@csrf_exempt
@api_view(['GET'])
def retry_generate_client_context(request):
    """Retry generate client context view."""
    # Verify it's from Cronjob (security check)
    auth_header = request.headers.get('Authorization', '')
    expected_auth = f"Bearer {settings.CRON_SECRET}"

    if auth_header != expected_auth:
        return Response({
            'error': 'Unauthorized'
        }, status=status.HTTP_401_UNAUTHORIZED)
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
            retry_context_service = RetryClientContext()
            result = loop.run_until_complete(
                retry_context_service.process_all_users_context()
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
@api_view(['POST'])
def send_weekly_context_test_email(request):
    """Send a test weekly context email to the authenticated user."""

    auth_header = request.headers.get('Authorization', '')
    expected_auth = f"Bearer {settings.CRON_SECRET}"

    if auth_header != expected_auth:
        return Response({
            'error': 'Unauthorized'
        }, status=status.HTTP_401_UNAUTHORIZED)
    try:
        # Get optional test data from request
        test_context_data = request.data.get('context_data', None)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            email_service = WeeklyContextEmailService()
            result = loop.run_until_complete(
                email_service.send_weekly_context_test_email(
                    user=request.user,
                    test_context_data=test_context_data
                )
            )

            AuditService.log_system_operation(
                user=request.user,
                action='weekly_context_test_email_sent',
                status='success' if result['status'] == 'success' else 'failure',
                resource_type='WeeklyContextEmail',
                details=result
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            AuditService.log_system_operation(
                user=request.user,
                action='weekly_context_test_email_failed',
                status='error',
                resource_type='WeeklyContextEmail',
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
