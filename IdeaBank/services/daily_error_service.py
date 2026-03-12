"""Servico para gestao de erros de geracao diaria de ideias."""

import logging
from typing import Any, Dict, List

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)


class DailyErrorService:
    """Servico para gestao de erros de geracao diaria.

    Nota: Os campos daily_generation_error e daily_generation_error_date
    foram adicionados diretamente na tabela auth_user via migration raw SQL.
    Este servico encapsula o acesso a esses campos.
    """

    @sync_to_async
    def store_error(self, user: User, error_message: str) -> None:
        """Armazena erro para retry posterior.

        Args:
            user: Usuario que teve erro
            error_message: Mensagem de erro a armazenar
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_user SET daily_generation_error = %s, "
                "daily_generation_error_date = %s WHERE id = %s",
                [error_message, timezone.now(), user.id]
            )

        logger.error(f"Stored daily error for user {user.id}: {error_message}")

    @sync_to_async
    def clear_error(self, user: User) -> None:
        """Limpa erro apos sucesso.

        Args:
            user: Usuario para limpar erro
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_user SET daily_generation_error = NULL, "
                "daily_generation_error_date = NULL WHERE id = %s",
                [user.id]
            )

    @sync_to_async
    def get_users_with_errors(self, offset: int = 0, limit: int = None) -> List[Dict[str, Any]]:
        """Retorna usuarios com erro para retry.

        Args:
            offset: Posicao inicial na lista
            limit: Numero maximo de usuarios a retornar

        Returns:
            Lista de dicionarios com dados dos usuarios
        """
        queryset = User.objects.extra(
            where=["daily_generation_error IS NOT NULL"]
        ).filter(
            usersubscription__status='active',
            is_active=True
        ).distinct().values('id', 'email', 'username')

        if limit is None:
            return list(queryset[offset:])
        return list(queryset[offset:offset + limit])

    @sync_to_async
    def get_users_without_errors(self, offset: int = 0, limit: int = None) -> List[Dict[str, Any]]:
        """Retorna usuarios sem erro (elegiveis para processamento).

        Args:
            offset: Posicao inicial na lista
            limit: Numero maximo de usuarios a retornar

        Returns:
            Lista de dicionarios com dados dos usuarios
        """
        queryset = User.objects.extra(
            where=["daily_generation_error IS NULL"]
        ).filter(
            usersubscription__status='active',
            is_active=True
        ).distinct().values('id', 'email', 'username')

        if limit is None:
            return list(queryset[offset:])
        return list(queryset[offset:offset + limit])
