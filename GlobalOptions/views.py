from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    CustomFont,
    CustomProfession,
    CustomSpecialization,
    CustomSpecializationForProfession,
    PredefinedFont,
    PredefinedProfession,
    PredefinedSpecialization,
)
from .serializers import (
    CustomFontSerializer,
    CustomProfessionSerializer,
    CustomSpecializationSerializer,
    PredefinedFontSerializer,
    PredefinedSpecializationSerializer,
)


# =============================================================================
# DRY: Response Helpers
# =============================================================================

def success_response(data, message=None, status_code=status.HTTP_200_OK):
    """DRY: Padroniza respostas de sucesso."""
    response = {'success': True, 'data': data}
    if message:
        response['message'] = message
    return Response(response, status=status_code)


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """DRY: Padroniza respostas de erro."""
    response = {'success': False, 'message': message}
    if errors:
        response['errors'] = errors
    return Response(response, status=status_code)


def server_error_response(action, exception):
    """DRY: Padroniza respostas de erro de servidor."""
    return error_response(
        f'Erro ao {action}: {str(exception)}',
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# =============================================================================
# DRY: Profession Lookup Helper
# =============================================================================

def find_profession(profession_id):
    """DRY: Busca profissão em CustomProfession ou PredefinedProfession.

    Returns:
        tuple: (profession, is_custom) ou (None, None) se não encontrar
    """
    try:
        return CustomProfession.objects.get(id=profession_id, is_active=True), True
    except CustomProfession.DoesNotExist:
        pass

    try:
        return PredefinedProfession.objects.get(id=profession_id, is_active=True), False
    except PredefinedProfession.DoesNotExist:
        return None, None



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_professions(request):
    """Retorna todas as profissões disponíveis (predefinidas + customizadas)."""
    try:
        predefined = PredefinedProfession.objects.filter(is_active=True)
        custom = CustomProfession.objects.filter(is_active=True)

        all_professions = [
            {'id': p.id, 'name': p.name, 'is_custom': False, 'is_predefined': True}
            for p in predefined
        ] + [
            {'id': p.id, 'name': p.name, 'is_custom': True, 'is_predefined': False}
            for p in custom
        ]

        all_professions.sort(key=lambda x: x['name'])
        return success_response(all_professions)

    except Exception as e:
        return server_error_response('buscar profissões', e)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profession_specializations(request, profession_id):
    """Retorna todas as especializações de uma profissão específica."""
    try:
        profession, is_custom = find_profession(profession_id)

        if profession is None:
            from django.http import Http404
            raise Http404("Profissão não encontrada")

        # Buscar especializações baseado no tipo de profissão
        predefined_specializations = []
        custom_specializations = []
        custom_specializations_for_profession = []

        if is_custom:
            # Para profissões customizadas, buscar apenas especializações customizadas
            custom_specializations = CustomSpecialization.objects.filter(
                profession=profession, is_active=True
            )
            custom_specializations_for_profession = CustomSpecializationForProfession.objects.filter(
                profession_name=profession.name, is_active=True
            )
        else:
            # Para profissões predefinidas, buscar especializações predefinidas e customizadas
            predefined_specializations = PredefinedSpecialization.objects.filter(
                profession=profession, is_active=True
            )
            # Para profissões predefinidas, não buscar especializações customizadas por enquanto
            # custom_specializations = CustomSpecialization.objects.filter(
            #     profession=profession, is_active=True
            # )
            custom_specializations_for_profession = CustomSpecializationForProfession.objects.filter(
                profession_name=profession.name, is_active=True
            )

        # Combinar as duas listas
        all_specializations = list(predefined_specializations) + list(
            custom_specializations) + list(custom_specializations_for_profession)

        # Serializar todas as especializações
        serialized_specializations = []

        for spec in all_specializations:
            if isinstance(spec, PredefinedSpecialization):
                serialized_spec = PredefinedSpecializationSerializer(spec).data
                serialized_spec['is_custom'] = False
            elif isinstance(spec, CustomSpecialization):
                serialized_spec = CustomSpecializationSerializer(spec).data
                serialized_spec['is_custom'] = True
            else:  # CustomSpecializationForProfession
                serialized_spec = {
                    'id': spec.id,
                    'name': spec.name,
                    'profession_name': spec.profession_name,
                    'created_by': spec.created_by.id if spec.created_by else None,
                    'usage_count': spec.usage_count,
                    'is_active': spec.is_active,
                    'created_at': spec.created_at.isoformat() if spec.created_at else None,
                }
                serialized_spec['is_custom'] = True

            serialized_specializations.append(serialized_spec)

        return success_response({
            'profession': {
                'id': profession.id,
                'name': profession.name,
                'is_custom': is_custom
            },
            'specializations': serialized_specializations
        })

    except Exception as e:
        return server_error_response('buscar especializações', e)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_fonts(request):
    """Retorna todas as fontes disponíveis (predefinidas + customizadas)."""
    try:
        predefined = PredefinedFont.objects.filter(is_active=True)
        custom = CustomFont.objects.filter(is_active=True)

        return success_response({
            'predefined': PredefinedFontSerializer(predefined, many=True).data,
            'custom': CustomFontSerializer(custom, many=True).data
        })

    except Exception as e:
        return server_error_response('buscar fontes', e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_profession(request):
    """Cria uma nova profissão customizada."""
    try:
        serializer = CustomProfessionSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return error_response('Dados inválidos.', serializer.errors)

        with transaction.atomic():
            name = serializer.validated_data['name'].strip()

            # DRY: Usa helper para verificar duplicidade
            if PredefinedProfession.objects.filter(name__iexact=name, is_active=True).exists():
                return error_response('Já existe uma profissão com este nome.')

            if CustomProfession.objects.filter(name__iexact=name, is_active=True).exists():
                return error_response('Já existe uma profissão customizada com este nome.')

            profession = serializer.save()

            return success_response(
                CustomProfessionSerializer(profession).data,
                'Profissão criada com sucesso!',
                status.HTTP_201_CREATED
            )

    except Exception as e:
        return server_error_response('criar profissão', e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_specialization(request):
    """Cria uma nova especialização customizada."""
    try:
        serializer = CustomSpecializationSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return error_response('Dados inválidos.', serializer.errors)

        with transaction.atomic():
            name = serializer.validated_data['name'].strip()
            profession = serializer.validated_data['profession']

            if CustomSpecialization.objects.filter(
                name__iexact=name, profession=profession, is_active=True
            ).exists():
                return error_response(
                    'Já existe uma especialização customizada com este nome para esta profissão.'
                )

            specialization = serializer.save()

            return success_response(
                CustomSpecializationSerializer(specialization).data,
                'Especialização criada com sucesso!',
                status.HTTP_201_CREATED
            )

    except Exception as e:
        return server_error_response('criar especialização', e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_font(request):
    """Cria uma nova fonte customizada."""
    try:
        serializer = CustomFontSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return error_response('Dados inválidos.', serializer.errors)

        with transaction.atomic():
            name = serializer.validated_data['name'].strip()

            if PredefinedFont.objects.filter(name__iexact=name, is_active=True).exists():
                return error_response('Já existe uma fonte com este nome.')

            if CustomFont.objects.filter(name__iexact=name, is_active=True).exists():
                return error_response('Já existe uma fonte customizada com este nome.')

            font = serializer.save()

            return success_response(
                CustomFontSerializer(font).data,
                'Fonte criada com sucesso!',
                status.HTTP_201_CREATED
            )

    except Exception as e:
        return server_error_response('criar fonte', e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_specialization_for_profession(request):
    """Cria uma nova especialização customizada para qualquer profissão."""
    try:
        name = request.data.get('name', '').strip()
        profession_id = request.data.get('profession')

        if not name or not profession_id:
            return error_response('Nome e profissão são obrigatórios.')

        with transaction.atomic():
            # DRY: Usa helper para buscar profissão
            profession, is_custom = find_profession(profession_id)

            if profession is None:
                return error_response('Profissão não encontrada ou inativa.')

            # Verificar duplicidade baseado no tipo de profissão
            if not is_custom:
                if PredefinedSpecialization.objects.filter(
                    name__iexact=name, profession=profession, is_active=True
                ).exists():
                    return error_response(
                        'Já existe uma especialização com este nome para esta profissão.'
                    )
            else:
                if CustomSpecialization.objects.filter(
                    name__iexact=name, profession=profession, is_active=True
                ).exists():
                    return error_response(
                        'Já existe uma especialização customizada com este nome para esta profissão.'
                    )

            if CustomSpecializationForProfession.objects.filter(
                name__iexact=name, profession_name__iexact=profession.name, is_active=True
            ).exists():
                return error_response(
                    'Já existe uma especialização customizada com este nome para esta profissão.'
                )

            specialization = CustomSpecializationForProfession.objects.create(
                name=name,
                profession_name=profession.name,
                created_by=request.user
            )

            return success_response(
                {
                    'id': specialization.id,
                    'name': specialization.name,
                    'profession_name': specialization.profession_name,
                    'created_by': specialization.created_by.id if specialization.created_by else None,
                    'usage_count': specialization.usage_count,
                    'is_active': specialization.is_active,
                    'created_at': specialization.created_at.isoformat() if specialization.created_at else None,
                },
                'Especialização criada com sucesso!',
                status.HTTP_201_CREATED
            )

    except Exception as e:
        return server_error_response('criar especialização', e)
