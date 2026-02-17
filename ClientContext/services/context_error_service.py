"""Servico para gestao de erros de contexto."""

import logging
from typing import Any, Dict, List

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from ClientContext.models import ClientContext

logger = logging.getLogger(__name__)


class ContextErrorService:
    """Servico para gestao de erros de geracao de contexto semanal."""

    @sync_to_async
    def store_error(self, user: User, error_message: str) -> None:
        """Armazena erro para retry posterior.

        Args:
            user: Usuario que teve erro
            error_message: Mensagem de erro a armazenar
        """
        client_context, _ = ClientContext.objects.get_or_create(user=user)
        client_context.weekly_context_error = error_message
        client_context.weekly_context_error_date = timezone.now()
        client_context.save()

        logger.error(
            f"Stored error for user {user.id}: {error_message}"
        )

    @sync_to_async
    def clear_error(self, user: User) -> None:
        """Limpa erro apos sucesso.

        Args:
            user: Usuario para limpar erro
        """
        try:
            client_context = ClientContext.objects.get(user=user)
            client_context.weekly_context_error = None
            client_context.weekly_context_error_date = None
            client_context.save()
        except ClientContext.DoesNotExist:
            pass

    @sync_to_async
    def get_users_with_errors(self, offset: int = 0, limit: int = None) -> List[Dict[str, Any]]:
        """Retorna usuarios com erro para retry.

        Args:
            offset: Posicao inicial na lista
            limit: Numero maximo de usuarios a retornar

        Returns:
            Lista de dicionarios com dados dos usuarios
        """
        queryset = User.objects.filter(
            usersubscription__status='active',
            is_active=True,
            client_context__weekly_context_error__isnull=False
        ).distinct().values('id', 'email', 'username')

        if limit is None:
            return list(queryset[offset:])
        return list(queryset[offset:offset + limit])
