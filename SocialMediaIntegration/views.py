"""
SocialMediaIntegration Views

API endpoints for Instagram integration and scheduled posts.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from AuditSystem.services import AuditService

from .models import (
    InstagramAccount,
    PublishingLog,
    ScheduledPost,
    ScheduledPostStatus,
)
from .serializers import (
    CalendarEventSerializer,
    InstagramAccountListSerializer,
    InstagramAccountSerializer,
    PublishingLogSerializer,
    ScheduledPostCreateSerializer,
    ScheduledPostDetailSerializer,
    ScheduledPostListSerializer,
    ScheduledPostUpdateSerializer,
)
from .services import InstagramPublishService, ScheduledPostProcessor

logger = logging.getLogger(__name__)


# ============================================================
# Instagram Account Views
# ============================================================

class InstagramAccountListView(generics.ListAPIView):
    """List user's Instagram accounts."""
    permission_classes = [IsAuthenticated]
    serializer_class = InstagramAccountListSerializer

    def get_queryset(self):
        return InstagramAccount.objects.filter(user=self.request.user)


class InstagramAccountDetailView(generics.RetrieveAPIView):
    """Get details of an Instagram account."""
    permission_classes = [IsAuthenticated]
    serializer_class = InstagramAccountSerializer

    def get_queryset(self):
        return InstagramAccount.objects.filter(user=self.request.user)


class InstagramAccountDisconnectView(APIView):
    """Disconnect an Instagram account."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            account = InstagramAccount.objects.get(
                id=pk,
                user=request.user
            )

            # Check for pending posts
            pending_posts = ScheduledPost.objects.filter(
                instagram_account=account,
                status__in=['draft', 'scheduled']
            ).count()

            if pending_posts > 0:
                return Response({
                    'error': 'Existem posts agendados para esta conta. '
                             f'Cancele os {pending_posts} posts antes de desconectar.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update status
            account.status = 'disconnected'
            account.access_token = ''
            account.save()

            AuditService.log_post_operation(
                user=request.user,
                action='instagram_disconnected',
                post_id=str(account.id),
                status='success',
                details={'username': account.instagram_username}
            )

            return Response({
                'message': f'Conta @{account.instagram_username} desconectada.'
            })

        except InstagramAccount.DoesNotExist:
            return Response({
                'error': 'Conta não encontrada.'
            }, status=status.HTTP_404_NOT_FOUND)


# ============================================================
# Scheduled Posts Views
# ============================================================

class ScheduledPostListView(generics.ListCreateAPIView):
    """List and create scheduled posts."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ScheduledPost.objects.filter(
            user=self.request.user
        ).select_related('instagram_account', 'post_idea')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(scheduled_for__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_for__lte=end_date)

        return queryset.order_by('-scheduled_for')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ScheduledPostCreateSerializer
        return ScheduledPostListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        scheduled_post = serializer.save()

        AuditService.log_post_operation(
            user=request.user,
            action='scheduled_post_created',
            post_id=str(scheduled_post.id),
            status='success',
            details={
                'scheduled_for': str(scheduled_post.scheduled_for),
                'instagram_username': scheduled_post.instagram_account.instagram_username
            }
        )

        response_serializer = ScheduledPostDetailSerializer(scheduled_post)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


class ScheduledPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete scheduled posts."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ScheduledPost.objects.filter(
            user=self.request.user
        ).select_related('instagram_account', 'post_idea').prefetch_related(
            'publishing_logs'
        )

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ScheduledPostUpdateSerializer
        return ScheduledPostDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if post can be updated
        if instance.status not in ['draft', 'scheduled', 'failed']:
            return Response({
                'error': 'Este post não pode ser editado.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ScheduledPostUpdateSerializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # If updating a failed post, reset to scheduled
        if instance.status == 'failed':
            instance.status = ScheduledPostStatus.SCHEDULED
            instance.last_error = None
            instance.save(update_fields=['status', 'last_error', 'updated_at'])

        AuditService.log_post_operation(
            user=request.user,
            action='scheduled_post_updated',
            post_id=str(instance.id),
            status='success',
            details={'updated_fields': list(request.data.keys())}
        )

        response_serializer = ScheduledPostDetailSerializer(instance)
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Can only delete draft, scheduled, or failed posts
        if instance.status not in ['draft', 'scheduled', 'failed', 'cancelled']:
            return Response({
                'error': 'Posts publicados não podem ser excluídos.'
            }, status=status.HTTP_400_BAD_REQUEST)

        post_id = instance.id
        instance.delete()

        AuditService.log_post_operation(
            user=request.user,
            action='scheduled_post_deleted',
            post_id=str(post_id),
            status='success',
            details={}
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class ScheduledPostCancelView(APIView):
    """Cancel a scheduled post."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = ScheduledPost.objects.get(
                id=pk,
                user=request.user
            )

            if post.status not in ['draft', 'scheduled']:
                return Response({
                    'error': 'Apenas posts agendados podem ser cancelados.'
                }, status=status.HTTP_400_BAD_REQUEST)

            post.status = ScheduledPostStatus.CANCELLED
            post.save(update_fields=['status', 'updated_at'])

            AuditService.log_post_operation(
                user=request.user,
                action='scheduled_post_cancelled',
                post_id=str(post.id),
                status='success',
                details={}
            )

            return Response({
                'message': 'Post cancelado com sucesso.',
                'status': post.status
            })

        except ScheduledPost.DoesNotExist:
            return Response({
                'error': 'Post não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)


class ScheduledPostPublishNowView(APIView):
    """Publish a scheduled post immediately."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = ScheduledPost.objects.get(
                id=pk,
                user=request.user
            )

            if post.status not in ['draft', 'scheduled', 'failed']:
                return Response({
                    'error': 'Este post não pode ser publicado.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check account
            if not post.instagram_account.is_token_valid:
                return Response({
                    'error': 'O token da conta Instagram expirou. '
                             'Por favor, reconecte sua conta.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Publish immediately
            publish_service = InstagramPublishService()
            result = publish_service.publish_post(post)

            if result.success:
                AuditService.log_post_operation(
                    user=request.user,
                    action='scheduled_post_published_now',
                    post_id=str(post.id),
                    status='success',
                    details={'media_id': result.media_id}
                )

                return Response({
                    'message': 'Post publicado com sucesso!',
                    'media_id': result.media_id,
                    'permalink': result.permalink
                })
            else:
                return Response({
                    'error': result.error_message,
                    'error_code': result.error_code
                }, status=status.HTTP_400_BAD_REQUEST)

        except ScheduledPost.DoesNotExist:
            return Response({
                'error': 'Post não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)


class ScheduledPostRetryView(APIView):
    """Retry a failed post."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = ScheduledPost.objects.get(
                id=pk,
                user=request.user
            )

            if post.status != 'failed':
                return Response({
                    'error': 'Apenas posts com falha podem ser retentados.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not post.can_retry:
                return Response({
                    'error': f'Número máximo de tentativas atingido '
                             f'({post.retry_count}/{post.max_retries}).'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Reset to scheduled
            post.status = ScheduledPostStatus.SCHEDULED
            post.last_error = None
            post.save(update_fields=['status', 'last_error', 'updated_at'])

            AuditService.log_post_operation(
                user=request.user,
                action='scheduled_post_retry',
                post_id=str(post.id),
                status='success',
                details={'retry_count': post.retry_count}
            )

            return Response({
                'message': 'Post agendado para nova tentativa.',
                'retry_count': post.retry_count
            })

        except ScheduledPost.DoesNotExist:
            return Response({
                'error': 'Post não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)


class ScheduledPostCalendarView(APIView):
    """Get scheduled posts as calendar events."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get date range from params
        start = request.query_params.get('start')
        end = request.query_params.get('end')

        queryset = ScheduledPost.objects.filter(
            user=request.user
        ).select_related('instagram_account')

        if start:
            queryset = queryset.filter(scheduled_for__gte=start)
        if end:
            queryset = queryset.filter(scheduled_for__lte=end)

        events = []
        for post in queryset:
            # Calculate end time (Instagram posts are instantaneous)
            end_time = post.scheduled_for + timedelta(minutes=5)

            events.append({
                'id': post.id,
                'title': post.caption_preview,
                'start': post.scheduled_for,
                'end': end_time,
                'status': post.status,
                'status_display': post.get_status_display(),
                'media_type': post.media_type,
                'instagram_username': post.instagram_account.instagram_username,
                'thumbnail_url': post.media_urls[0] if post.media_urls else None
            })

        serializer = CalendarEventSerializer(events, many=True)
        return Response(serializer.data)


class ScheduledPostStatsView(APIView):
    """Get statistics for scheduled posts."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        stats = {
            'pending': ScheduledPost.objects.filter(
                user=user,
                status='scheduled',
                scheduled_for__lte=now
            ).count(),
            'scheduled_future': ScheduledPost.objects.filter(
                user=user,
                status='scheduled',
                scheduled_for__gt=now
            ).count(),
            'published_today': ScheduledPost.objects.filter(
                user=user,
                status='published',
                published_at__gte=today_start
            ).count(),
            'failed': ScheduledPost.objects.filter(
                user=user,
                status='failed'
            ).count(),
            'total_published': ScheduledPost.objects.filter(
                user=user,
                status='published'
            ).count(),
        }

        return Response(stats)


# ============================================================
# Cron Views (for GitHub Actions)
# ============================================================

@csrf_exempt
@require_http_methods(['POST'])
def cron_publish_scheduled(request):
    """
    Cron endpoint to process scheduled posts.

    Called by GitHub Actions every 5 minutes.
    Requires CRON_SECRET for authentication.

    Note: POST-only to comply with REST standards (state-modifying operation).
    """
    # Verify cron secret
    auth_header = request.headers.get('Authorization', '')
    expected = f"Bearer {settings.CRON_SECRET}"

    if auth_header != expected:
        return JsonResponse({
            'error': 'Unauthorized'
        }, status=401)

    try:
        processor = ScheduledPostProcessor(batch_size=10)
        result = processor.process_pending_posts()

        return JsonResponse({
            'success': True,
            'processed': result.total_processed,
            'successful': result.successful,
            'failed': result.failed,
            'skipped': result.skipped,
            'results': result.results
        })

    except Exception as e:
        logger.exception("Erro no cron de publicação")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def cron_retry_failed(request):
    """
    Cron endpoint to retry failed posts.

    Called by GitHub Actions.

    Note: POST-only to comply with REST standards (state-modifying operation).
    """
    auth_header = request.headers.get('Authorization', '')
    expected = f"Bearer {settings.CRON_SECRET}"

    if auth_header != expected:
        return JsonResponse({
            'error': 'Unauthorized'
        }, status=401)

    try:
        processor = ScheduledPostProcessor(batch_size=10)
        result = processor.process_retries()

        return JsonResponse({
            'success': True,
            'processed': result.total_processed,
            'successful': result.successful,
            'failed': result.failed,
            'skipped': result.skipped
        })

    except Exception as e:
        logger.exception("Erro no cron de retry")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(['GET'])
def cron_stats(request):
    """Get publishing statistics for monitoring."""
    auth_header = request.headers.get('Authorization', '')
    expected = f"Bearer {settings.CRON_SECRET}"

    if auth_header != expected:
        return JsonResponse({
            'error': 'Unauthorized'
        }, status=401)

    try:
        processor = ScheduledPostProcessor()
        stats = processor.get_stats()

        return JsonResponse({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.exception("Erro ao obter stats")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================
# Instagram OAuth Views
# ============================================================

class InstagramConnectView(APIView):
    """
    GET: Generate Instagram OAuth authorization URL.
    Initiates the connection process with Meta OAuth.

    In MOCK mode (INSTAGRAM_MOCK_MODE=true), returns a fake OAuth URL
    that redirects directly to the callback with a test code.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Generate authorization URL for Instagram OAuth"""
        import os
        import secrets

        # Check for mock mode
        mock_mode = os.getenv('INSTAGRAM_MOCK_MODE', 'false').lower() == 'true'
        redirect_uri = os.getenv('META_REDIRECT_URI', 'http://localhost:5173/auth/instagram/callback')

        if mock_mode:
            # In mock mode, redirect directly to callback with a fake code
            mock_code = 'MOCK_AUTH_CODE_FOR_TESTING'
            mock_url = f"{redirect_uri}?code={mock_code}&state=mock_state"

            logger.info(f"Instagram OAuth (MOCK MODE) initiated for user {request.user.id}")

            return Response({
                'url': mock_url,
                'state': 'mock_state',
                'mock_mode': True,
                'message': 'Modo de teste ativo - redirecionando para callback simulado'
            })

        # Get Meta App credentials from environment
        app_id = os.getenv('META_APP_ID')

        if not app_id:
            return Response({
                'error': 'META_APP_ID not configured',
                'message': 'Configuração do Meta App não encontrada. Ative INSTAGRAM_MOCK_MODE=true para testar.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state in session for validation
        request.session['instagram_oauth_state'] = state
        request.session['instagram_oauth_user_id'] = request.user.id

        # Build OAuth URL
        # Instagram Basic Display API scopes
        scopes = 'instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments,instagram_business_content_publish'

        oauth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth"
            f"?client_id={app_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scopes}"
            f"&response_type=code"
            f"&state={state}"
        )

        logger.info(f"Instagram OAuth initiated for user {request.user.id}")

        return Response({
            'url': oauth_url,
            'state': state,
            'message': 'Redirecione para a URL para conectar o Instagram'
        })


class InstagramCallbackView(APIView):
    """
    POST: Process OAuth callback from Meta.
    Exchanges authorization code for access token.

    In MOCK mode (INSTAGRAM_MOCK_MODE=true), creates a fake Instagram
    account for testing purposes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Process OAuth callback with authorization code"""
        import os
        import requests

        code = request.data.get('code')
        if not code:
            return Response({
                'error': 'Missing authorization code',
                'message': 'Código de autorização não fornecido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for mock mode
        mock_mode = os.getenv('INSTAGRAM_MOCK_MODE', 'false').lower() == 'true'

        if mock_mode and code == 'MOCK_AUTH_CODE_FOR_TESTING':
            # Create a mock Instagram account for testing
            mock_ig_user_id = f"mock_{request.user.id}_17841400000000000"

            account, created = InstagramAccount.objects.update_or_create(
                user=request.user,
                instagram_user_id=mock_ig_user_id,
                defaults={
                    'instagram_username': f'postnow_test_{request.user.id}',
                    'instagram_name': f'PostNow Test Account',
                    'profile_picture_url': 'https://via.placeholder.com/150',
                    'facebook_page_id': 'mock_page_123456789',
                    'facebook_page_name': 'PostNow Test Page',
                    'access_token': 'MOCK_ACCESS_TOKEN_FOR_TESTING',
                    'token_expires_at': timezone.now() + timedelta(days=60),
                    'status': 'connected',
                }
            )

            logger.info(f"Instagram MOCK account {'created' if created else 'updated'} for user {request.user.id}")

            AuditService.log_account_operation(
                user=request.user,
                action='instagram_connected_mock',
                status='success',
                details={'username': account.instagram_username, 'account_id': account.id, 'mock_mode': True}
            )

            serializer = InstagramAccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Get Meta App credentials
        app_id = os.getenv('META_APP_ID')
        app_secret = os.getenv('META_APP_SECRET')
        redirect_uri = os.getenv('META_REDIRECT_URI', 'http://localhost:5173/auth/instagram/callback')

        if not app_id or not app_secret:
            return Response({
                'error': 'Meta App credentials not configured',
                'message': 'Credenciais do Meta App não configuradas. Ative INSTAGRAM_MOCK_MODE=true para testar.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Exchange code for access token
            token_url = 'https://graph.facebook.com/v18.0/oauth/access_token'
            token_response = requests.get(token_url, params={
                'client_id': app_id,
                'client_secret': app_secret,
                'redirect_uri': redirect_uri,
                'code': code
            })

            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                return Response({
                    'error': 'Token exchange failed',
                    'message': 'Falha ao trocar código por token',
                    'details': token_response.json()
                }, status=status.HTTP_400_BAD_REQUEST)

            token_data = token_response.json()
            access_token = token_data.get('access_token')

            # Get Instagram Business Account
            # First, get Facebook Pages
            pages_url = f'https://graph.facebook.com/v18.0/me/accounts'
            pages_response = requests.get(pages_url, params={
                'access_token': access_token
            })

            if pages_response.status_code != 200:
                return Response({
                    'error': 'Failed to get Facebook pages',
                    'message': 'Falha ao obter páginas do Facebook'
                }, status=status.HTTP_400_BAD_REQUEST)

            pages_data = pages_response.json()
            pages = pages_data.get('data', [])

            if not pages:
                return Response({
                    'error': 'No Facebook pages found',
                    'message': 'Nenhuma página do Facebook encontrada. Conecte uma página ao seu Instagram Business.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get Instagram Business Account from first page
            page = pages[0]
            page_id = page['id']
            page_access_token = page['access_token']
            page_name = page.get('name', '')

            ig_account_url = f'https://graph.facebook.com/v18.0/{page_id}'
            ig_response = requests.get(ig_account_url, params={
                'fields': 'instagram_business_account',
                'access_token': page_access_token
            })

            if ig_response.status_code != 200:
                return Response({
                    'error': 'Failed to get Instagram account',
                    'message': 'Falha ao obter conta do Instagram'
                }, status=status.HTTP_400_BAD_REQUEST)

            ig_data = ig_response.json()
            ig_account = ig_data.get('instagram_business_account')

            if not ig_account:
                return Response({
                    'error': 'No Instagram Business account',
                    'message': 'Nenhuma conta Instagram Business conectada à página do Facebook'
                }, status=status.HTTP_400_BAD_REQUEST)

            ig_user_id = ig_account['id']

            # Get Instagram profile info
            profile_url = f'https://graph.facebook.com/v18.0/{ig_user_id}'
            profile_response = requests.get(profile_url, params={
                'fields': 'username,name,profile_picture_url',
                'access_token': page_access_token
            })

            profile_data = profile_response.json()
            username = profile_data.get('username', '')
            name = profile_data.get('name', '')
            profile_picture = profile_data.get('profile_picture_url', '')

            # Create or update Instagram account
            account, created = InstagramAccount.objects.update_or_create(
                user=request.user,
                instagram_user_id=ig_user_id,
                defaults={
                    'instagram_username': username,
                    'instagram_name': name,
                    'profile_picture_url': profile_picture,
                    'facebook_page_id': page_id,
                    'facebook_page_name': page_name,
                    'access_token': page_access_token,  # In production, encrypt this!
                    'token_expires_at': timezone.now() + timedelta(days=60),
                    'status': 'connected',
                }
            )

            logger.info(f"Instagram account {'created' if created else 'updated'}: @{username} for user {request.user.id}")

            # Log audit
            AuditService.log_generic(
                user=request.user,
                action='instagram_connected',
                status='success',
                details={'username': username, 'account_id': account.id}
            )

            # Return serialized account
            serializer = InstagramAccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except requests.RequestException as e:
            logger.exception("Instagram OAuth request failed")
            return Response({
                'error': 'OAuth request failed',
                'message': f'Erro na requisição OAuth: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception("Instagram OAuth callback failed")
            return Response({
                'error': str(e),
                'message': 'Erro ao processar callback do Instagram'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
