
from urllib.parse import urlencode, urljoin

import requests
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.shortcuts import redirect
from django.urls import reverse
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserSubscriptionStatusSerializer

load_dotenv()


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:8000/api/v1/auth/google/callback/"
    client_class = OAuth2Client


@api_view(['GET'])
@permission_classes([AllowAny])
def google_callback(request):
    """
    Google OAuth callback endpoint - this is where Google redirects after authentication
    """

    code = request.GET.get('code')
    error = request.GET.get('error')

    # Handle OAuth errors (user denied access, etc.)
    if error:
        error_params = urlencode(
            {'error': error, 'error_description': 'Google authentication failed'})
        return redirect(f'http://localhost:5173/auth/google/callback?{error_params}')

    if not code:
        error_params = urlencode(
            {'error': 'no_code', 'error_description': 'No authorization code received'})
        return redirect(f'http://localhost:5173/auth/google/callback?{error_params}')

    try:
        # Process the OAuth code using the GoogleLogin view
        token_endpoint_url = urljoin(
            "http://localhost:8000", reverse("google_login"))
        response = requests.post(url=token_endpoint_url, data={"code": code})

        if response.status_code == 200:
            # Parse the JWT tokens from the response
            token_data = response.json()
            # or 'access_token' depending on your setup
            access_token = token_data.get('access')
            refresh_token = token_data.get('refresh')  # or 'refresh_token'

            # Create redirect response
            success_params = urlencode({'success': 'true'})
            redirect_response = redirect(
                f'http://localhost:5173/auth/google/callback?{success_params}')

            # Set JWT tokens as cookies
            if access_token:
                redirect_response.set_cookie(
                    'access',
                    access_token,
                    max_age=86400,  # 24 hours (1 day)
                    httponly=False,  # Frontend needs to access these
                    secure=False,   # Set to True in production with HTTPS
                    samesite='Strict'
                )

            if refresh_token:
                redirect_response.set_cookie(
                    'refresh',
                    refresh_token,
                    max_age=604800,  # 7 days
                    httponly=False,  # Frontend needs to access these
                    secure=False,   # Set to True in production with HTTPS
                    samesite='Strict'
                )

            return redirect_response
        else:
            # API error - redirect to frontend with error
            error_params = urlencode(
                {'error': 'auth_failed', 'error_description': 'Google authentication failed'})
            return redirect(f'http://localhost:5173/auth/google/callback?{error_params}')

    except Exception as e:
        # Server error - redirect to frontend with error
        error_params = urlencode(
            {'error': 'server_error', 'error_description': str(e)})
        return redirect(f'http://localhost:5173/auth/google/callback?{error_params}')


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    Google OAuth authentication endpoint
    Expected payload: {'access_token': 'google_access_token'} or {'code': 'authorization_code'}
    """
    access_token = request.data.get('access_token')
    auth_code = request.data.get('code')

    if not access_token and not auth_code:
        return Response(
            {'error': 'access_token or code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Use the GoogleLogin view properly through the class-based view approach
        view = GoogleLogin.as_view()
        return view(request)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_social_accounts(request):
    """
    List all social accounts connected to the current user
    """
    try:
        social_accounts = SocialAccount.objects.filter(user=request.user)
        accounts_data = []

        for account in social_accounts:
            accounts_data.append({
                'id': account.id,
                'provider': account.provider,
                'uid': account.uid,
                'extra_data': {
                    'email': account.extra_data.get('email'),
                    'name': account.extra_data.get('name'),
                    'picture': account.extra_data.get('picture')
                },
                'date_joined': account.date_joined.isoformat()
            })

        return Response({
            'social_accounts': accounts_data,
            'total_count': len(accounts_data)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Failed to retrieve social accounts: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def disconnect_social_account(request, account_id):
    """
    Disconnect a social account from the current user
    """
    try:
        social_account = SocialAccount.objects.get(
            id=account_id,
            user=request.user
        )

        provider = social_account.provider
        social_account.delete()

        return Response({
            'message': f'{provider.title()} account disconnected successfully',
            'disconnected_provider': provider
        }, status=status.HTTP_200_OK)

    except SocialAccount.DoesNotExist:
        return Response(
            {'error': 'Social account not found or does not belong to you'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to disconnect social account: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subscription_status(request):
    """Get user's subscription status."""
    try:
        profile = request.user.profile
        message = ""

        if not profile.subscribed:
            message = "Para acessar todas as funcionalidades, entre em contato com Rogério Resende: WhatsApp +55 61 99993-0263"

        data = {
            'subscribed': profile.subscribed,
            'subscription_date': profile.subscription_date,
            'message': message
        }

        serializer = UserSubscriptionStatusSerializer(data)
        return Response(serializer.data)

    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)
        data = {
            'subscribed': False,
            'subscription_date': None,
            'message': "Para acessar todas as funcionalidades, entre em contato com Rogério Resende: WhatsApp +55 61 99993-0263"
        }
        serializer = UserSubscriptionStatusSerializer(data)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Erro ao verificar status de assinatura: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
