
import os
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

load_dotenv()

# Get base URL from environment or settings


def get_base_url():
    return os.getenv('BACKEND_BASE_URL', 'http://localhost:8000')


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = f"{get_base_url()}/api/v1/auth/google/callback/"
    client_class = OAuth2Client


@api_view(['GET'])
@permission_classes([AllowAny])
def google_callback(request):
    """
    Google OAuth callback endpoint - this is where Google redirects after authentication
    """

    code = request.GET.get('code')
    error = request.GET.get('error')
    frontend_url = os.getenv('FRONTEND_URL')

    # Handle OAuth errors (user denied access, etc.)
    if error:
        error_params = urlencode(
            {'error': error, 'error_description': 'Google authentication failed'})
        return redirect(f'{frontend_url}/auth/google/callback?{error_params}')

    if not code:
        error_params = urlencode(
            {'error': 'no_code', 'error_description': 'No authorization code received'})
        return redirect(f'{frontend_url}/auth/google/callback?{error_params}')

    try:
        # Process the OAuth code using the GoogleLogin view
        token_endpoint_url = urljoin(
            get_base_url(), reverse("google_login"))
        response = requests.post(url=token_endpoint_url, data={"code": code})

        if response.status_code == 200:
            # Parse the JWT tokens from the response
            token_data = response.json()
            # or 'access_token' depending on your setup
            access_token = token_data.get('access')
            refresh_token = token_data.get('refresh')  # or 'refresh_token'

            # Create redirect response with tokens in URL parameters
            success_params = urlencode({
                'success': 'true',
                'access_token': access_token,
                'refresh_token': refresh_token
            })
            redirect_response = redirect(
                f'{frontend_url}/auth/google/callback?{success_params}')

            # No need to set cookies - tokens are passed in URL
            return redirect_response
        else:
            # API error - redirect to frontend with error
            error_params = urlencode(
                {'error': 'auth_failed', 'error_description': 'Google authentication failed'})
            return redirect(f'{frontend_url}/auth/google/callback?{error_params}')

    except Exception as e:
        # Server error - redirect to frontend with error
        error_params = urlencode(
            {'error': 'server_error', 'error_description': str(e)})
        return redirect(f'{frontend_url}/auth/google/callback?{error_params}')


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    Google OAuth authentication endpoint - generates the Google OAuth URL
    """
    try:
        # Generate Google OAuth URL
        client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
        redirect_uri = f"{get_base_url()}/api/v1/auth/google/callback/"
        scope = "email profile"

        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + \
                   f"client_id={client_id}&" + \
                   f"redirect_uri={redirect_uri}&" + \
                   f"scope={scope}&" + \
                   "response_type=code&" + \
                   "access_type=offline"

        return Response({
            'auth_url': auth_url
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
