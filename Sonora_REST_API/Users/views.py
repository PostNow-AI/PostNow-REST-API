
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.http import JsonResponse
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

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
    return JsonResponse({
        'message': 'Google OAuth callback received',
        'note': 'This endpoint is for Google redirects only. Use POST /api/v1/auth/google/ for actual authentication',
        'code': request.GET.get('code', 'No code provided'),
    })


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
