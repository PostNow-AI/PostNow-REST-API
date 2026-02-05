"""
GlobalOptions Views - Admin dashboard and global configuration endpoints.
Refactored to follow DRY principles.
"""
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from AuditSystem.models import AuditLog
from AuditSystem.services import AuditService
from CreditSystem.models import UserSubscription
from django.contrib.auth import get_user_model

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


# =============================================================================
# Response Helpers (DRY)
# =============================================================================

def success_response(data, status_code=status.HTTP_200_OK):
    """Build a success response."""
    return Response({'success': True, 'data': data}, status=status_code)


def error_response(message, status_code=status.HTTP_400_BAD_REQUEST, errors=None):
    """Build an error response."""
    response = {'success': False, 'message': message}
    if errors:
        response['errors'] = errors
    return Response(response, status=status_code)


def server_error_response(action, error):
    """Build a server error response."""
    return Response(
        {'success': False, 'message': f'Erro ao {action}: {str(error)}'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# =============================================================================
# Validation Helpers (DRY)
# =============================================================================

def check_duplicate_name(model, name, extra_filters=None):
    """Check if a name already exists in a model."""
    filters = {'name__iexact': name, 'is_active': True}
    if extra_filters:
        filters.update(extra_filters)
    return model.objects.filter(**filters).exists()


def find_profession(profession_id):
    """Find a profession by ID (custom or predefined)."""
    # Try custom first
    try:
        return CustomProfession.objects.get(id=profession_id, is_active=True), True
    except CustomProfession.DoesNotExist:
        pass

    # Try predefined
    try:
        return PredefinedProfession.objects.get(id=profession_id, is_active=True), False
    except PredefinedProfession.DoesNotExist:
        return None, None


# =============================================================================
# Dashboard Views
# =============================================================================

class DashboardStatsView(APIView):
    """Admin dashboard with aggregated metrics."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        period = self._parse_period(request)

        # Client stats (no period filter)
        client_stats = self._get_client_stats()

        # Email stats (with period filter)
        email_stats, series_daily = self._get_email_stats(period)

        return Response({
            'success': True,
            'data': {
                'clients': client_stats,
                'emails': email_stats,
                'series': {'daily': series_daily},
                'period': self._serialize_period(period),
                'generated_at': timezone.now().isoformat(),
            },
        })

    def _get_client_stats(self):
        """Get client statistics."""
        non_admin_users = User.objects.filter(is_superuser=False)

        active_ids = UserSubscription.objects.filter(
            status='active'
        ).values_list('user_id', flat=True).distinct()

        ever_subscribed_ids = UserSubscription.objects.values_list(
            'user_id', flat=True
        ).distinct()

        active = non_admin_users.filter(id__in=active_ids).count()
        never_subscribed = non_admin_users.exclude(id__in=ever_subscribed_ids).count()
        cancelled = non_admin_users.filter(
            id__in=ever_subscribed_ids
        ).exclude(id__in=active_ids).count()
        inactive_total = never_subscribed + cancelled

        return {
            'active': active,
            'inactive': {
                'never_subscribed': never_subscribed,
                'cancelled_or_expired': cancelled,
                'total': inactive_total,
            },
            'total': active + inactive_total,
        }

    def _get_email_stats(self, period):
        """Get email statistics with optional period filter."""
        sent_qs = AuditLog.objects.filter(action='email_sent', status='success')
        opened_qs = AuditLog.objects.filter(action='email_opened', status='success')

        if period:
            start_dt, end_dt = period
            sent_qs = sent_qs.filter(timestamp__gte=start_dt, timestamp__lte=end_dt)
            opened_qs = opened_qs.filter(timestamp__gte=start_dt, timestamp__lte=end_dt)

        sent = sent_qs.count()
        opened = opened_qs.count()
        rate = round((opened / sent * 100), 1) if sent > 0 else 0

        series = self._build_daily_series(sent_qs, opened_qs, period)

        return {'sent': sent, 'opened': opened, 'rate': rate}, series

    def _parse_period(self, request):
        """Parse period from request parameters."""
        preset = (request.query_params.get('preset') or '').strip()
        start_str = (request.query_params.get('start') or '').strip()
        end_str = (request.query_params.get('end') or '').strip()

        tz = timezone.get_current_timezone()
        today = timezone.localdate()

        if preset in {'7d', '30d'}:
            days = 7 if preset == '7d' else 30
            return self._to_day_range(today - timedelta(days=days - 1), today, tz)

        if start_str and end_str:
            try:
                start_date = date.fromisoformat(start_str)
                end_date = date.fromisoformat(end_str)
                if start_date <= end_date:
                    return self._to_day_range(start_date, end_date, tz)
            except ValueError:
                pass

        return None

    def _to_day_range(self, start_date, end_date, tz):
        start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
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
        sent_by_day = self._aggregate_by_day(sent_qs)
        opened_by_day = self._aggregate_by_day(opened_qs)

        if not period:
            all_days = sorted(set(sent_by_day.keys()) | set(opened_by_day.keys()))
            return [self._day_entry(d, sent_by_day, opened_by_day) for d in all_days]

        start_dt, end_dt = period
        start_date = timezone.localtime(start_dt).date()
        end_date = timezone.localtime(end_dt).date()

        days = []
        cursor = start_date
        while cursor <= end_date:
            days.append(self._day_entry(cursor.isoformat(), sent_by_day, opened_by_day))
            cursor += timedelta(days=1)
        return days

    def _aggregate_by_day(self, qs):
        return {
            row['day'].isoformat(): row['count']
            for row in qs.annotate(day=TruncDate('timestamp')).values('day').annotate(count=Count('id'))
        }

    def _day_entry(self, d, sent_by_day, opened_by_day):
        return {
            'date': d,
            'emails_sent': sent_by_day.get(d, 0),
            'emails_opened': opened_by_day.get(d, 0),
        }


class MailjetWebhookView(APIView):
    """Mailjet webhook for email events."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data
        events = payload if isinstance(payload, list) else [payload]

        audit_service = AuditService()
        opened_count = 0

        for event in events:
            if not isinstance(event, dict) or event.get('event') != 'open':
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

        return Response({
            'success': True,
            'processed': len(events),
            'opened_registered': opened_count,
        })


# =============================================================================
# Profession & Specialization Views
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_professions(request):
    """Return all available professions (predefined + custom)."""
    try:
        professions = []

        # Add predefined
        for prof in PredefinedProfession.objects.filter(is_active=True):
            professions.append(_serialize_profession(prof, is_custom=False))

        # Add custom
        for prof in CustomProfession.objects.filter(is_active=True):
            professions.append(_serialize_profession(prof, is_custom=True))

        # Sort by name
        professions.sort(key=lambda x: x['name'])
        return success_response(professions)

    except Exception as e:
        return server_error_response('buscar profissões', e)


def _serialize_profession(prof, is_custom):
    """Serialize a profession object (DRY helper)."""
    return {
        'id': prof.id,
        'name': prof.name,
        'is_custom': is_custom,
        'is_predefined': not is_custom
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profession_specializations(request, profession_id):
    """Return all specializations for a specific profession."""
    try:
        profession, is_custom = find_profession(profession_id)
        if profession is None:
            raise Http404("Profissão não encontrada")

        specializations = _get_specializations_for_profession(profession, is_custom)

        return success_response({
            'profession': {
                'id': profession.id,
                'name': profession.name,
                'is_custom': is_custom
            },
            'specializations': specializations
        })

    except Exception as e:
        return server_error_response('buscar especializações', e)


def _get_specializations_for_profession(profession, is_custom):
    """Get and serialize all specializations for a profession."""
    all_specs = []

    if is_custom:
        all_specs.extend(CustomSpecialization.objects.filter(
            profession=profession, is_active=True
        ))
    else:
        all_specs.extend(PredefinedSpecialization.objects.filter(
            profession=profession, is_active=True
        ))

    # Add custom specializations for profession name
    all_specs.extend(CustomSpecializationForProfession.objects.filter(
        profession_name=profession.name, is_active=True
    ))

    return [_serialize_specialization(spec) for spec in all_specs]


def _serialize_specialization(spec):
    """Serialize a specialization object (DRY helper)."""
    if isinstance(spec, PredefinedSpecialization):
        data = PredefinedSpecializationSerializer(spec).data
        data['is_custom'] = False
    elif isinstance(spec, CustomSpecialization):
        data = CustomSpecializationSerializer(spec).data
        data['is_custom'] = True
    else:  # CustomSpecializationForProfession
        data = {
            'id': spec.id,
            'name': spec.name,
            'profession_name': spec.profession_name,
            'created_by': spec.created_by.id if spec.created_by else None,
            'usage_count': spec.usage_count,
            'is_active': spec.is_active,
            'created_at': spec.created_at.isoformat() if spec.created_at else None,
            'is_custom': True
        }
    return data


# =============================================================================
# Font Views
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_fonts(request):
    """Return all available fonts (predefined + custom)."""
    try:
        predefined = PredefinedFontSerializer(
            PredefinedFont.objects.filter(is_active=True), many=True
        ).data
        custom = CustomFontSerializer(
            CustomFont.objects.filter(is_active=True), many=True
        ).data

        return success_response({'predefined': predefined, 'custom': custom})

    except Exception as e:
        return server_error_response('buscar fontes', e)


# =============================================================================
# Create Custom Resources Views
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_profession(request):
    """Create a new custom profession."""
    return _create_custom_resource(
        request,
        serializer_class=CustomProfessionSerializer,
        duplicate_checks=[
            (PredefinedProfession, 'Já existe uma profissão com este nome.'),
            (CustomProfession, 'Já existe uma profissão customizada com este nome.'),
        ],
        action='criar profissão'
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_font(request):
    """Create a new custom font."""
    return _create_custom_resource(
        request,
        serializer_class=CustomFontSerializer,
        duplicate_checks=[
            (PredefinedFont, 'Já existe uma fonte com este nome.'),
            (CustomFont, 'Já existe uma fonte customizada com este nome.'),
        ],
        action='criar fonte'
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_specialization(request):
    """Create a new custom specialization."""
    try:
        serializer = CustomSpecializationSerializer(
            data=request.data, context={'request': request}
        )

        if not serializer.is_valid():
            return error_response('Dados inválidos.', errors=serializer.errors)

        with transaction.atomic():
            name = serializer.validated_data['name'].strip()
            profession = serializer.validated_data['profession']

            if check_duplicate_name(CustomSpecialization, name, {'profession': profession}):
                return error_response(
                    'Já existe uma especialização customizada com este nome para esta profissão.'
                )

            specialization = serializer.save()
            return success_response(
                CustomSpecializationSerializer(specialization).data,
                status_code=status.HTTP_201_CREATED
            )

    except Exception as e:
        return server_error_response('criar especialização', e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_specialization_for_profession(request):
    """Create a custom specialization for any profession."""
    try:
        name = request.data.get('name', '').strip()
        profession_id = request.data.get('profession')

        if not name or not profession_id:
            return error_response('Nome e profissão são obrigatórios.')

        with transaction.atomic():
            profession, is_custom = find_profession(profession_id)
            if profession is None:
                return error_response('Profissão não encontrada ou inativa.')

            # Check duplicates based on profession type
            if not is_custom:
                if check_duplicate_name(PredefinedSpecialization, name, {'profession': profession}):
                    return error_response(
                        'Já existe uma especialização com este nome para esta profissão.'
                    )
            else:
                if check_duplicate_name(CustomSpecialization, name, {'profession': profession}):
                    return error_response(
                        'Já existe uma especialização customizada com este nome para esta profissão.'
                    )

            if CustomSpecializationForProfession.objects.filter(
                name__iexact=name,
                profession_name__iexact=profession.name,
                is_active=True
            ).exists():
                return error_response(
                    'Já existe uma especialização customizada com este nome para esta profissão.'
                )

            specialization = CustomSpecializationForProfession.objects.create(
                name=name,
                profession_name=profession.name,
                created_by=request.user
            )

            return success_response({
                'id': specialization.id,
                'name': specialization.name,
                'profession_name': specialization.profession_name,
                'created_by': specialization.created_by.id if specialization.created_by else None,
                'usage_count': specialization.usage_count,
                'is_active': specialization.is_active,
                'created_at': specialization.created_at.isoformat() if specialization.created_at else None,
            }, status_code=status.HTTP_201_CREATED)

    except Exception as e:
        return server_error_response('criar especialização', e)


def _create_custom_resource(request, serializer_class, duplicate_checks, action):
    """Generic helper for creating custom resources (DRY)."""
    try:
        serializer = serializer_class(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return error_response('Dados inválidos.', errors=serializer.errors)

        with transaction.atomic():
            name = serializer.validated_data['name'].strip()

            # Check all duplicate rules
            for model, message in duplicate_checks:
                if check_duplicate_name(model, name):
                    return error_response(message)

            resource = serializer.save()
            return success_response(
                serializer_class(resource).data,
                status_code=status.HTTP_201_CREATED
            )

    except Exception as e:
        return server_error_response(action, e)
