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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_professions(request):
    """Retorna todas as profissões disponíveis (predefinidas + customizadas)."""
    try:
        # Buscar profissões predefinidas ativas
        predefined_professions = PredefinedProfession.objects.filter(
            is_active=True)

        # Buscar profissões customizadas ativas
        custom_professions = CustomProfession.objects.filter(is_active=True)

        # Combinar e ordenar por nome
        all_professions = []

        # Adicionar predefinidas
        for prof in predefined_professions:
            all_professions.append({
                'id': prof.id,
                'name': prof.name,
                'is_custom': False,
                'is_predefined': True
            })

        # Adicionar customizadas
        for prof in custom_professions:
            all_professions.append({
                'id': prof.id,
                'name': prof.name,
                'is_custom': True,
                'is_predefined': False
            })

        # Ordenar por nome
        all_professions.sort(key=lambda x: x['name'])

        return Response({
            'success': True,
            'data': all_professions
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erro ao buscar profissões: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profession_specializations(request, profession_id):
    """Retorna todas as especializações de uma profissão específica."""
    try:
        # Tentar buscar em ambas as tabelas
        profession = None
        is_custom = None

        # Tentar buscar na profissão customizada
        try:
            profession = CustomProfession.objects.get(
                id=profession_id, is_active=True)
            is_custom = True
        except CustomProfession.DoesNotExist:
            pass

        # Se não encontrou na customizada, tentar na predefinida
        if profession is None:
            try:
                profession = PredefinedProfession.objects.get(
                    id=profession_id, is_active=True)
                is_custom = False
            except PredefinedProfession.DoesNotExist:
                pass

        # Se não encontrou em nenhuma, retornar 404
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
                    'created_by_username': spec.created_by.username if spec.created_by else None,
                    'usage_count': spec.usage_count,
                    'is_active': spec.is_active,
                    'created_at': spec.created_at.isoformat() if spec.created_at else None,
                }
                serialized_spec['is_custom'] = True

            serialized_specializations.append(serialized_spec)

        return Response({
            'success': True,
            'data': {
                'profession': {
                    'id': profession.id,
                    'name': profession.name,
                    'is_custom': is_custom
                },
                'specializations': serialized_specializations
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erro ao buscar especializações: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_fonts(request):
    """Retorna todas as fontes disponíveis (predefinidas + customizadas)."""
    try:
        # Buscar fontes predefinidas ativas
        predefined_fonts = PredefinedFont.objects.filter(is_active=True)

        # Buscar fontes customizadas ativas
        custom_fonts = CustomFont.objects.filter(is_active=True)

        # Serializar
        predefined_serializer = PredefinedFontSerializer(
            predefined_fonts, many=True)
        custom_serializer = CustomFontSerializer(custom_fonts, many=True)

        return Response({
            'success': True,
            'data': {
                'predefined': predefined_serializer.data,
                'custom': custom_serializer.data
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erro ao buscar fontes: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_profession(request):
    """Cria uma nova profissão customizada."""
    try:
        serializer = CustomProfessionSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            with transaction.atomic():
                # Verificar se já existe uma profissão com o mesmo nome
                name = serializer.validated_data['name'].strip()

                # Verificar em profissões predefinidas
                if PredefinedProfession.objects.filter(name__iexact=name, is_active=True).exists():
                    return Response({
                        'success': False,
                        'message': 'Já existe uma profissão com este nome.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Verificar em profissões customizadas
                if CustomProfession.objects.filter(name__iexact=name, is_active=True).exists():
                    return Response({
                        'success': False,
                        'message': 'Já existe uma profissão customizada com este nome.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Criar a profissão
                profession = serializer.save()

                return Response({
                    'success': True,
                    'message': 'Profissão criada com sucesso!',
                    'data': CustomProfessionSerializer(profession).data
                }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': 'Dados inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erro ao criar profissão: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_specialization(request):
    """Cria uma nova especialização customizada."""
    try:
        serializer = CustomSpecializationSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            with transaction.atomic():
                # Verificar se já existe uma especialização com o mesmo nome para a profissão
                name = serializer.validated_data['name'].strip()
                profession = serializer.validated_data['profession']

                # Verificar se já existe uma especialização com o mesmo nome para esta profissão
                # Como estamos criando uma especialização customizada, só precisamos verificar nas customizadas
                if CustomSpecialization.objects.filter(
                    name__iexact=name,
                    profession=profession,
                    is_active=True
                ).exists():
                    return Response({
                        'success': False,
                        'message': 'Já existe uma especialização customizada com este nome para esta profissão.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Criar a especialização
                specialization = serializer.save()

                return Response({
                    'success': True,
                    'message': 'Especialização criada com sucesso!',
                    'data': CustomSpecializationSerializer(specialization).data
                }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': 'Dados inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erro ao criar especialização: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_font(request):
    """Cria uma nova fonte customizada."""
    try:
        serializer = CustomFontSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            with transaction.atomic():
                # Verificar se já existe uma fonte com o mesmo nome
                name = serializer.validated_data['name'].strip()

                # Verificar em fontes predefinidas
                if PredefinedFont.objects.filter(name__iexact=name, is_active=True).exists():
                    return Response({
                        'success': False,
                        'message': 'Já existe uma fonte com este nome.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Verificar em fontes customizadas
                if CustomFont.objects.filter(name__iexact=name, is_active=True).exists():
                    return Response({
                        'success': False,
                        'message': 'Já existe uma fonte customizada com este nome.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Criar a fonte
                font = serializer.save()

                return Response({
                    'success': True,
                    'message': 'Fonte criada com sucesso!',
                    'data': CustomFontSerializer(font).data
                }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': 'Dados inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erro ao criar fonte: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_specialization_for_profession(request):
    """Cria uma nova especialização customizada para qualquer profissão."""
    try:
        name = request.data.get('name', '').strip()
        profession_id = request.data.get('profession')

        if not name or not profession_id:
            return Response({
                'success': False,
                'message': 'Nome e profissão são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Buscar a profissão (pode ser predefinida ou customizada)
            # Priorizar profissões customizadas para evitar conflitos de ID
            profession = None
            try:
                profession = CustomProfession.objects.get(
                    id=profession_id, is_active=True)
            except CustomProfession.DoesNotExist:
                try:
                    profession = PredefinedProfession.objects.get(
                        id=profession_id, is_active=True)
                except PredefinedProfession.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Profissão não encontrada ou inativa.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Verificar se já existe uma especialização com o mesmo nome para a profissão
            # Só verificar em PredefinedSpecialization se a profissão for predefinida
            if isinstance(profession, PredefinedProfession):
                # É uma profissão predefinida
                if PredefinedSpecialization.objects.filter(
                    name__iexact=name,
                    profession=profession,
                    is_active=True
                ).exists():
                    return Response({
                        'success': False,
                        'message': 'Já existe uma especialização com este nome para esta profissão.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Só verificar em CustomSpecialization se a profissão for customizada
            if isinstance(profession, CustomProfession):
                if CustomSpecialization.objects.filter(
                    name__iexact=name,
                    profession=profession,
                    is_active=True
                ).exists():
                    return Response({
                        'success': False,
                        'message': 'Já existe uma especialização customizada com este nome para esta profissão.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            if CustomSpecializationForProfession.objects.filter(
                name__iexact=name,
                profession_name__iexact=profession.name,
                is_active=True
            ).exists():
                return Response({
                    'success': False,
                    'message': 'Já existe uma especialização customizada com este nome para esta profissão.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Criar a especialização
            specialization = CustomSpecializationForProfession.objects.create(
                name=name,
                profession_name=profession.name,
                created_by=request.user
            )

            return Response({
                'success': True,
                'message': 'Especialização criada com sucesso!',
                'data': {
                    'id': specialization.id,
                    'name': specialization.name,
                    'profession_name': specialization.profession_name,
                    'created_by': specialization.created_by.id if specialization.created_by else None,
                    'created_by_username': specialization.created_by.username if specialization.created_by else None,
                    'usage_count': specialization.usage_count,
                    'is_active': specialization.is_active,
                    'created_at': specialization.created_at.isoformat() if specialization.created_at else None,
                }
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erro ao criar especialização: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
