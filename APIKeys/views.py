from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserAPIKey
from .serializers import SetAPIKeySerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_api_key(request):
    """Set or update a user's API key for a specific provider."""
    serializer = SetAPIKeySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    provider = serializer.validated_data['provider']
    api_key = serializer.validated_data['api_key'].strip()

    if not api_key:
        return Response({'error': 'api_key é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    # Update or create the API key
    obj, created = UserAPIKey.objects.update_or_create(
        user=request.user,
        provider=provider,
        defaults={'api_key': api_key}
    )

    return Response({
        'success': True,
        'message': 'Chave da API salva com sucesso' if created else 'Chave da API atualizada com sucesso'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_api_key_status(request, provider):
    """Check if user has an API key for a specific provider."""
    has_key = UserAPIKey.objects.filter(
        user=request.user, provider=provider).exists()
    return Response({'has_key': has_key})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_api_key(request, provider):
    """Delete a user's API key for a specific provider."""
    try:
        api_key = UserAPIKey.objects.get(user=request.user, provider=provider)
        api_key.delete()
        return Response({'success': True, 'message': 'Chave da API removida com sucesso'})
    except UserAPIKey.DoesNotExist:
        return Response({'error': 'Chave da API não encontrada'}, status=status.HTTP_404_NOT_FOUND)
