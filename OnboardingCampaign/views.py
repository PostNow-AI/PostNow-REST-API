import asyncio
import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from OnboardingCampaign.services.onboarding_email_service import OnboardingEmailService

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])  # No authentication required for cron
@permission_classes([AllowAny])  # Allow Vercel cron to access
def send_onboarding_emails_cron(request):
    """
    Vercel cron endpoint to send due onboarding emails.

    Called daily at 13:00 UTC (10:00 AM BRT) via Vercel cron job.

    This endpoint:
    1. Queries all OnboardingEmail records that are due (scheduled_for <= now)
    2. Checks if users still haven't completed onboarding
    3. Sends emails via Mailjet
    4. Marks emails as sent or cancels campaign if onboarding completed

    Returns:
        JSON response with send statistics
    """
    try:
        # Get optional user_id from query params for testing
        user_id = request.GET.get('user_id')
        if user_id:
            logger.info(
                f"Starting onboarding emails cron job for user {user_id}")
        else:
            logger.info("Starting onboarding emails cron job")

        # Run the send_onboarding_emails function
        service = OnboardingEmailService()
        result = service.send_onboarding_emails_sync(user_id=user_id)

        if result['success']:
            logger.info(
                f"Onboarding emails cron completed: "
                f"{result['sent']} sent, {result['failed']} failed, "
                f"{result['skipped']} skipped"
            )

            return Response({
                'status': 'success',
                'message': 'Onboarding emails processed',
                'sent': result['sent'],
                'failed': result['failed'],
                'skipped': result['skipped'],
                'total': result['total']
            }, status=status.HTTP_200_OK)
        else:
            logger.error(
                f"Onboarding emails cron failed: {result.get('error')}")
            return Response({
                'status': 'error',
                'message': 'Failed to process onboarding emails',
                'error': result.get('error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error in onboarding emails cron endpoint: {e}")
        return Response({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
