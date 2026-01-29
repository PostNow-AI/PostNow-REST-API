"""
Social Media Integration Views
Instagram connection, status, sync, metrics, and notifications endpoints.
"""

from datetime import datetime, timedelta

from AuditSystem.services import AuditService
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    InstagramAccount,
    InstagramConnectionAttempt,
    InstagramMetrics,
    InstagramNotification,
)
from .serializers import (
    InstagramAccountSerializer,
    InstagramCallbackSerializer,
    InstagramMetricsSerializer,
    InstagramNotificationSerializer,
)
from .services.instagram_oauth_service import InstagramOAuthService
from .services.instagram_service import InstagramGraphService
from .services.notification_service import InstagramNotificationService
from .services.token_refresh_service import TokenRefreshService
from .utils.encryption import encrypt_token


class InstagramConnectView(APIView):
    """
    GET: Generate Instagram OAuth authorization URL.
    Initiates the connection process.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Generate authorization URL for Instagram OAuth"""
        try:
            # Track connection attempt
            attempt = InstagramConnectionAttempt.objects.create(
                user=request.user,
                step='initiated',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self._get_client_ip(request)
            )

            # Generate OAuth URL
            oauth_service = InstagramOAuthService()
            auth_data = oauth_service.get_authorization_url(request.user.id)

            # Update attempt
            attempt.step = 'oauth_started'
            attempt.save()

            # Log action
            AuditService.log_generic(
                user=request.user,
                action='instagram_connect_initiated',
                status='success',
                details={'attempt_id': attempt.id}
            )

            return Response({
                'authorization_url': auth_data['authorization_url'],
                'state': auth_data['state'],
                'expires_in': auth_data['expires_in'],
                'message': 'Clique no link para conectar seu Instagram'
            })

        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Erro ao gerar URL de conexão'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class InstagramCallbackView(APIView):
    """
    POST: Handle Instagram OAuth callback.
    Exchanges authorization code for access token and saves account.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Process OAuth callback and save Instagram account"""
        serializer = InstagramCallbackSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']
        state = serializer.validated_data['state']

        try:
            # Track callback received
            attempt = InstagramConnectionAttempt.objects.filter(
                user=request.user
            ).order_by('-started_at').first()

            if attempt:
                attempt.step = 'oauth_callback'
                attempt.save()

            # Exchange code for token
            oauth_service = InstagramOAuthService()
            token_data = oauth_service.exchange_code_for_token(
                code, state, request.user)

            # Validate business account
            account_info = oauth_service.validate_business_account(
                token_data['access_token'],
                token_data['instagram_user_id']
            )

            # Get full profile data
            graph_service = InstagramGraphService()
            profile_data = graph_service.get_user_profile(
                token_data['instagram_user_id'],
                token_data['access_token']
            )

            # Calculate expiration
            expires_in_seconds = token_data.get(
                'expires_in', 5184000)  # 60 days
            expires_at = timezone.now() + timedelta(seconds=expires_in_seconds)

            # Create or update Instagram account
            instagram_account, created = InstagramAccount.objects.update_or_create(
                instagram_user_id=token_data['instagram_user_id'],
                defaults={
                    'user': request.user,
                    'username': account_info['username'],
                    'account_type': account_info['account_type'],
                    'profile_picture_url': account_info.get('profile_picture_url'),
                    'followers_count': profile_data.get('followers_count', 0),
                    'following_count': profile_data.get('following_count', 0),
                    'media_count': profile_data.get('media_count', 0),
                    'access_token': encrypt_token(token_data['access_token']),
                    'token_type': token_data.get('token_type', 'Bearer'),
                    'expires_at': expires_at,
                    'connection_status': 'connected',
                    'is_active': True,
                    'sync_error_message': None,
                }
            )

            # Update connection attempt
            if attempt:
                attempt.step = 'completed'
                attempt.completed_at = timezone.now()
                attempt.duration_seconds = int(
                    (attempt.completed_at - attempt.started_at).total_seconds()
                )
                attempt.save()

            # Send notification for first connection
            if created:
                InstagramNotificationService.notify_first_connection(
                    user=request.user,
                    instagram_username=instagram_account.username
                )

                # Achievement unlocked notification
                InstagramNotificationService.notify_achievement_unlocked(
                    request.user)

            # Log success
            AuditService.log_generic(
                user=request.user,
                action='instagram_account_connected',
                status='success',
                details={
                    'instagram_username': instagram_account.username,
                    'account_type': instagram_account.account_type,
                    'is_new_connection': created
                }
            )

            # Serialize and return
            account_serializer = InstagramAccountSerializer(instagram_account)

            return Response({
                'success': True,
                'message': f'Instagram @{instagram_account.username} conectado com sucesso!',
                'account': account_serializer.data,
                'is_first_connection': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except ValueError as e:
            # User-friendly error
            if attempt:
                attempt.step = 'error'
                attempt.error_message = str(e)
                attempt.save()

            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Unexpected error
            AuditService.log_generic(
                user=request.user,
                action='instagram_connection_error',
                status='error',
                details={'error': str(e)}
            )

            if attempt:
                attempt.step = 'error'
                attempt.error_message = str(e)
                attempt.save()

            return Response({
                'error': 'Erro ao conectar Instagram. Tente novamente.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstagramAccountStatusView(APIView):
    """
    GET: Get current Instagram connection status for the user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return Instagram connection status"""
        try:
            # Get user's active Instagram account
            account = InstagramAccount.objects.filter(
                user=request.user,
                is_active=True
            ).first()

            if not account:
                return Response({
                    'is_connected': False,
                    'connection_status': 'disconnected',
                    'account_info': None,
                    'last_sync': None,
                    'next_sync_available': None,
                    'expires_in_days': None,
                    'has_errors': False,
                    'error_message': None
                })

            # Check for next sync availability (15 min cooldown)
            last_sync = account.last_synced_at
            next_sync_available = None
            if last_sync:
                next_sync_available = last_sync + timedelta(minutes=15)

            # Serialize account
            account_serializer = InstagramAccountSerializer(account)

            response_data = {
                'is_connected': True,
                'connection_status': account.connection_status,
                'account_info': account_serializer.data,
                'last_sync': account.last_synced_at,
                'next_sync_available': next_sync_available,
                'expires_in_days': account.days_until_expiration(),
                'has_errors': account.connection_status == 'error',
                'error_message': account.sync_error_message
            }

            return Response(response_data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstagramSyncView(APIView):
    """
    POST: Manually sync Instagram data (profile + metrics).
    Has 15-minute cooldown to prevent rate limiting.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Sync Instagram account data"""
        try:
            # Get user's account
            account = InstagramAccount.objects.filter(
                user=request.user,
                is_active=True
            ).first()

            if not account:
                return Response({
                    'error': 'Nenhuma conta Instagram conectada'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check cooldown (15 minutes)
            if account.last_synced_at:
                time_since_last_sync = timezone.now() - account.last_synced_at
                cooldown_minutes = 15

                if time_since_last_sync < timedelta(minutes=cooldown_minutes):
                    minutes_remaining = cooldown_minutes - \
                        int(time_since_last_sync.total_seconds() / 60)
                    return Response({
                        'error': f'Aguarde {minutes_remaining} minutos antes de sincronizar novamente',
                        'next_sync_available': account.last_synced_at + timedelta(minutes=cooldown_minutes)
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Get valid token (auto-refresh if needed)
            try:
                access_token = TokenRefreshService.get_valid_token(account)
            except ValueError as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Sync data
            graph_service = InstagramGraphService()

            # Get updated profile data
            profile_data = graph_service.get_user_profile(
                account.instagram_user_id,
                access_token
            )

            # Get insights
            insights_data = graph_service.get_account_insights(
                account.instagram_user_id,
                access_token,
                period='day'
            )

            # Calculate follower growth
            old_followers = account.followers_count
            new_followers = profile_data.get('followers_count', 0)
            followers_growth = new_followers - old_followers

            # Update account
            account.followers_count = new_followers
            account.following_count = profile_data.get('following_count', 0)
            account.media_count = profile_data.get('media_count', 0)
            account.profile_picture_url = profile_data.get(
                'profile_picture_url')
            account.last_synced_at = timezone.now()
            account.connection_status = 'connected'
            account.sync_error_message = None
            account.save()

            # Save metrics for today
            today = timezone.now().date()
            metrics, created = InstagramMetrics.objects.update_or_create(
                account=account,
                date=today,
                defaults={
                    'impressions': insights_data.get('impressions', 0),
                    'reach': insights_data.get('reach', 0),
                    'profile_views': insights_data.get('profile_views', 0),
                    'engagement': insights_data.get('engagement', 0),
                    'followers_count': new_followers,
                    'media_count': account.media_count,
                    'raw_metrics': insights_data
                }
            )

            # Send success notification
            if followers_growth > 0:
                InstagramNotificationService.notify_sync_success(
                    user=request.user,
                    instagram_username=account.username,
                    new_followers=followers_growth
                )

            # Log success
            AuditService.log_generic(
                user=request.user,
                action='instagram_sync_success',
                status='success',
                details={
                    'instagram_username': account.username,
                    'followers_growth': followers_growth
                }
            )

            return Response({
                'success': True,
                'message': 'Dados sincronizados com sucesso!',
                'account': InstagramAccountSerializer(account).data,
                'metrics': InstagramMetricsSerializer(metrics).data,
                'followers_growth': followers_growth
            })

        except ValueError as e:
            # User-friendly errors (rate limit, invalid token, etc.)
            account.connection_status = 'error'
            account.sync_error_message = str(e)
            account.save()

            # Determine error type and send notification
            error_str = str(e).lower()
            if 'rate limit' in error_str or 'muitas' in error_str:
                error_type = 'rate_limit'
            elif 'token' in error_str or 'reconecte' in error_str:
                error_type = 'invalid_token'
            else:
                error_type = 'generic'

            InstagramNotificationService.notify_sync_error(
                user=request.user,
                instagram_username=account.username,
                error_type=error_type
            )

            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Unexpected error
            AuditService.log_generic(
                user=request.user,
                action='instagram_sync_error',
                status='error',
                details={'error': str(e)}
            )

            return Response({
                'error': 'Erro ao sincronizar dados. Tente novamente.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstagramMetricsView(generics.ListAPIView):
    """
    GET: List Instagram metrics for a date range.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InstagramMetricsSerializer

    def get_queryset(self):
        """Filter metrics by user's account and date range"""
        # Get user's account
        account = InstagramAccount.objects.filter(
            user=self.request.user,
            is_active=True
        ).first()

        if not account:
            return InstagramMetrics.objects.none()

        # Get date range from query params
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        queryset = InstagramMetrics.objects.filter(account=account)

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end)
            except ValueError:
                pass

        return queryset.order_by('-date')


class InstagramDisconnectView(APIView):
    """
    DELETE: Disconnect Instagram account.
    Soft delete - marks as inactive.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """Disconnect Instagram account"""
        try:
            account = InstagramAccount.objects.filter(
                user=request.user,
                is_active=True
            ).first()

            if not account:
                return Response({
                    'error': 'Nenhuma conta Instagram conectada'
                }, status=status.HTTP_404_NOT_FOUND)

            # Soft delete
            username = account.username
            account.is_active = False
            account.connection_status = 'disconnected'
            account.save()

            # Log action
            AuditService.log_generic(
                user=request.user,
                action='instagram_disconnected',
                status='success',
                details={'instagram_username': username}
            )

            return Response({
                'success': True,
                'message': f'Instagram @{username} desconectado com sucesso'
            })

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstagramNotificationsView(generics.ListAPIView):
    """
    GET: List Instagram notifications.
    PATCH: Mark notifications as read.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InstagramNotificationSerializer

    def get_queryset(self):
        """Get user's Instagram notifications"""
        # Option to filter only unread
        unread_only = self.request.query_params.get(
            'unread', 'false').lower() == 'true'

        queryset = InstagramNotification.objects.filter(user=self.request.user)

        if unread_only:
            queryset = queryset.filter(is_read=False)

        return queryset.order_by('-created_at')

    def patch(self, request):
        """Mark notifications as read"""
        notification_ids = request.data.get('notification_ids', [])

        if notification_ids:
            # Mark specific notifications
            notifications = InstagramNotification.objects.filter(
                id__in=notification_ids,
                user=request.user,
                is_read=False
            )
            count = notifications.count()
            for notification in notifications:
                notification.mark_as_read()
        else:
            # Mark all as read
            count = InstagramNotificationService.mark_all_as_read(request.user)

        return Response({
            'success': True,
            'marked_as_read': count
        })


class InstagramHealthCheckView(APIView):
    """
    GET: Health check for Instagram integration system.
    Admin only.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Check system health"""
        try:
            # Check active accounts
            active_accounts = InstagramAccount.objects.filter(
                is_active=True).count()

            # Check expiring tokens
            threshold = timezone.now() + timedelta(days=7)
            expiring_soon = InstagramAccount.objects.filter(
                is_active=True,
                expires_at__lte=threshold,
                expires_at__gt=timezone.now()
            ).count()

            # Check accounts with errors
            error_accounts = InstagramAccount.objects.filter(
                is_active=True,
                connection_status='error'
            ).count()

            # Test Instagram API connectivity (optional)
            api_status = 'unknown'
            try:
                # Simple test - this would need a test account token
                api_status = 'reachable'
            except:
                api_status = 'unreachable'

            health_data = {
                'status': 'healthy' if error_accounts == 0 else 'degraded',
                'active_accounts': active_accounts,
                'tokens_expiring_soon': expiring_soon,
                'accounts_with_errors': error_accounts,
                'instagram_api_status': api_status,
                'checked_at': timezone.now()
            }

            return Response(health_data)

        except Exception as e:
            return Response({
                'status': 'down',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
