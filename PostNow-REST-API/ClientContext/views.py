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
                'id', 'user__id', 'user__email', 'user__first_name', 'market_panorama', 'market_tendencies', 'market_challenges', 'market_sources', 'competition_main', 'competition_strategies', 'competition_opportunities', 'competition_sources', 'target_audience_profile', 'target_audience_behaviors', 'target_audience_interests', 'target_audience_sources', 'tendencies_popular_themes', 'tendencies_hashtags', 'tendencies_keywords', 'tendencies_sources', 'seasonal_relevant_dates', 'seasonal_local_events', 'seasonal_sources', 'brand_online_presence', 'brand_reputation', 'brand_communication_style', 'brand_sources', 'created_at', 'updated_at', 'user_id', 'weekly_context_error', 'weekly_context_error_date'
            )
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
def send_weekly_context_email(request):
    """Send weekly context email view."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            email_service = WeeklyContextEmailService()
            result = loop.run_until_complete(
                email_service.mail_weekly_context()
            )

            AuditService.log_system_operation(
                user=None,
                action='weekly_context_email_sent',
                status='success' if result['status'] == 'success' else 'failure',
                resource_type='WeeklyContextEmail',
                details=result
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            AuditService.log_system_operation(
                user=None,
                action='weekly_context_email_failed',
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


# Weekly Context Web Page Views
from datetime import datetime, timedelta
from rest_framework import generics
from ClientContext.models import ClientContextHistory
from ClientContext.serializers import WeeklyContextSerializer


class WeeklyContextCurrentView(generics.GenericAPIView):
    """
    GET /api/v1/client-context/weekly-context/
    Returns the most recent Weekly Context for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WeeklyContextSerializer

    def get(self, request):
        user = request.user
        
        try:
            latest_context = ClientContextHistory.objects.filter(
                user=user
            ).order_by('-created_at').first()
            
            if not latest_context:
                return Response({
                    'success': False,
                    'message': 'Nenhum contexto semanal encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            total_count = ClientContextHistory.objects.filter(user=user).count()
            has_previous = total_count > 1
            
            try:
                business_name = user.creator_profile.business_name or 'Sua Empresa'
            except:
                business_name = 'Sua Empresa'
            
            created_at = latest_context.created_at
            next_week = created_at + timedelta(days=7)
            week_range = f"{created_at.day}/{created_at.month} a {next_week.day}/{next_week.month}"
            
            ranked_opportunities = latest_context.tendencies_data or {}
            
            response_data = {
                'week_number': 0,
                'week_range': week_range,
                'created_at': latest_context.created_at,
                'business_name': business_name,
                'has_previous': has_previous,
                'has_next': False,
                'ranked_opportunities': ranked_opportunities
            }
            
            return Response({
                'success': True,
                'data': response_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erro ao buscar contexto: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WeeklyContextHistoryView(generics.GenericAPIView):
    """
    GET /api/v1/client-context/weekly-context/history/?offset=N
    Returns a specific Weekly Context by offset (0 = current, 1 = last week, etc.)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WeeklyContextSerializer

    def get(self, request):
        user = request.user
        offset = int(request.query_params.get('offset', 0))
        
        try:
            all_contexts = ClientContextHistory.objects.filter(
                user=user
            ).order_by('-created_at')
            
            total_count = all_contexts.count()
            
            if total_count == 0:
                return Response({
                    'success': False,
                    'message': 'Nenhum contexto semanal encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if offset < 0 or offset >= total_count:
                return Response({
                    'success': False,
                    'message': 'Offset inválido'
                }, status=status.HTTP_404_NOT_FOUND)
            
            context = all_contexts[offset]
            
            has_previous = offset < total_count - 1
            has_next = offset > 0
            
            try:
                business_name = user.creator_profile.business_name or 'Sua Empresa'
            except:
                business_name = 'Sua Empresa'
            
            created_at = context.created_at
            next_week = created_at + timedelta(days=7)
            week_range = f"{created_at.day}/{created_at.month} a {next_week.day}/{next_week.month}"
            
            ranked_opportunities = context.tendencies_data or {}
            
            response_data = {
                'week_number': offset,
                'week_range': week_range,
                'created_at': context.created_at,
                'business_name': business_name,
                'has_previous': has_previous,
                'has_next': has_next,
                'ranked_opportunities': ranked_opportunities
            }
            
            return Response({
                'success': True,
                'data': response_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erro ao buscar histórico: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
