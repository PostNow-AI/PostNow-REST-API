from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from AuditSystem.models import AuditLog
from AuditSystem.services import AuditService
from CreditSystem.models import UserSubscription

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

User = get_user_model()


class DashboardStatsView(APIView):
    """
    Dashboard administrativo (somente admin) com métricas agregadas.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        period = self._parse_period(request)

        # ===== Clientes (sem recorte por período) =====
        non_admin_users = User.objects.filter(is_superuser=False)

        active_subscriber_user_ids = UserSubscription.objects.filter(
            status='active'
        ).values_list('user_id', flat=True).distinct()

        ever_subscriber_user_ids = UserSubscription.objects.values_list(
            'user_id', flat=True
        ).distinct()

        active_clients = non_admin_users.filter(
            id__in=active_subscriber_user_ids).count()

        never_subscribed = non_admin_users.exclude(
            id__in=ever_subscriber_user_ids).count()

        cancelled_or_expired = non_admin_users.filter(id__in=ever_subscriber_user_ids).exclude(
            id__in=active_subscriber_user_ids
        ).count()

        inactive_total = never_subscribed + cancelled_or_expired
        total_clients = active_clients + inactive_total

        # ===== E-mails (com recorte por período) =====
        sent_qs = AuditLog.objects.filter(
            action='email_sent', status='success')
        opened_qs = AuditLog.objects.filter(
            action='email_opened', status='success')

        if period:
            start_dt, end_dt = period
            sent_qs = sent_qs.filter(
                timestamp__gte=start_dt, timestamp__lte=end_dt)
            opened_qs = opened_qs.filter(
                timestamp__gte=start_dt, timestamp__lte=end_dt)

        emails_sent = sent_qs.count()
        emails_opened = opened_qs.count()
        open_rate = round((emails_opened / emails_sent * 100),
                          1) if emails_sent > 0 else 0

        series_daily = self._build_daily_series(sent_qs, opened_qs, period)

        return Response(
            {
                'success': True,
                'data': {
                    'clients': {
                        'active': active_clients,
                        'inactive': {
                            'never_subscribed': never_subscribed,
                            'cancelled_or_expired': cancelled_or_expired,
                            'total': inactive_total,
                        },
                        'total': total_clients,
                    },
                    'emails': {
                        'sent': emails_sent,
                        'opened': emails_opened,
                        'rate': open_rate,
                    },
                    'series': {
                        'daily': series_daily,
                    },
                    'period': self._serialize_period(period),
                    'generated_at': timezone.now().isoformat(),
                },
            }
        )

    def _parse_period(self, request):
        """
        Aceita:
        - preset=7d|30d
        - start=YYYY-MM-DD & end=YYYY-MM-DD
        Retorna (start_dt, end_dt) timezone-aware ou None.
        """
        preset = (request.query_params.get('preset') or '').strip()
        start_str = (request.query_params.get('start') or '').strip()
        end_str = (request.query_params.get('end') or '').strip()

        tz = timezone.get_current_timezone()
        today = timezone.localdate()

        if preset in {'7d', '30d'}:
            days = 7 if preset == '7d' else 30
            start_date = today - timedelta(days=days - 1)
            end_date = today
            return self._to_day_range(start_date, end_date, tz)

        if start_str and end_str:
            try:
                start_date = date.fromisoformat(start_str)
                end_date = date.fromisoformat(end_str)
            except ValueError:
                return None

            if start_date > end_date:
                return None

            return self._to_day_range(start_date, end_date, tz)

        return None

    def _to_day_range(self, start_date: date, end_date: date, tz):
        start_dt = timezone.make_aware(
            datetime.combine(start_date, time.min), tz)
        end_dt = timezone.make_aware(datetime.combine(end_date, time.max), tz)
        return start_dt, end_dt

    def _serialize_period(self, period):
        if not period:
            return None
        start_dt, end_dt = period
        return {
            'start': timezone.localtime(start_dt).date().isoformat(),
            'end': timezone.localtime(end_dt).date().isoformat(),
        }

    def _build_daily_series(self, sent_qs, opened_qs, period):
        # Agregar por data local
        sent_by_day = {
            row['day'].isoformat(): row['count']
            for row in sent_qs.annotate(day=TruncDate('timestamp')).values('day').annotate(count=Count('id'))
        }
        opened_by_day = {
            row['day'].isoformat(): row['count']
            for row in opened_qs.annotate(day=TruncDate('timestamp')).values('day').annotate(count=Count('id'))
        }

        if period:
            start_dt, end_dt = period
            start_date = timezone.localtime(start_dt).date()
            end_date = timezone.localtime(end_dt).date()
        else:
            # Sem período: retornar somente dias existentes (ordenados)
            all_days = sorted(set(sent_by_day.keys()) |
                              set(opened_by_day.keys()))
            return [
                {
                    'date': d,
                    'emails_sent': sent_by_day.get(d, 0),
                    'emails_opened': opened_by_day.get(d, 0),
                }
                for d in all_days
            ]

        days = []
        cursor = start_date
        while cursor <= end_date:
            d = cursor.isoformat()
            days.append(
                {
                    'date': d,
                    'emails_sent': sent_by_day.get(d, 0),
                    'emails_opened': opened_by_day.get(d, 0),
                }
            )
            cursor += timedelta(days=1)
        return days


class MailjetWebhookView(APIView):
    """
    Webhook do Mailjet para registrar eventos (ex.: abertura).
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data
        events = payload if isinstance(payload, list) else [payload]

        audit_service = AuditService()
        opened_count = 0

        for event in events:
            if not isinstance(event, dict):
                continue

            if event.get('event') != 'open':
                continue

            opened_count += 1
            audit_service.log_email_operation(
                user=None,
                action='email_opened',
                status='success',
                details={
                    'email': event.get('email'),
                    'time': event.get('time'),
                    'MessageID': event.get('MessageID') or event.get('message_id'),
                    'mj_campaign_id': event.get('mj_campaign_id'),
                    'mj_contact_id': event.get('mj_contact_id'),
                    'ip': event.get('ip'),
                    'user_agent': event.get('useragent'),
                    'original_event': event,
                },
            )

        return Response(
            {
                'success': True,
                'processed': len(events),
                'opened_registered': opened_count,
            }
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
