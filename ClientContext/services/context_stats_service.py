"""Servico para calculos estatisticos de processamento."""

from datetime import datetime
from typing import Any, Dict, List


class ContextStatsService:
    """Servico para calcular estatisticas de processamento de contexto."""

    @staticmethod
    def calculate_batch_results(
        results: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calcula estatisticas do batch de processamento.

        Args:
            results: Lista de resultados do processamento
            start_time: Hora de inicio do processamento
            end_time: Hora de fim do processamento

        Returns:
            Dicionario com estatisticas calculadas
        """
        return {
            'processed': sum(1 for r in results if r.get('status') == 'success'),
            'failed': sum(1 for r in results if r.get('status') == 'failed'),
            'skipped': sum(1 for r in results if r.get('status') == 'skipped'),
            'duration_seconds': (end_time - start_time).total_seconds(),
        }

    @staticmethod
    def build_completion_result(
        stats: Dict[str, Any],
        total_users: int,
        details: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Constroi resultado final de processamento.

        Args:
            stats: Estatisticas calculadas
            total_users: Total de usuarios processados
            details: Detalhes de cada processamento (opcional)

        Returns:
            Dicionario com resultado completo
        """
        result = {
            'status': 'completed',
            'processed': stats['processed'],
            'failed': stats['failed'],
            'skipped': stats['skipped'],
            'total_users': total_users,
            'duration_seconds': stats['duration_seconds'],
        }

        if details is not None:
            result['details'] = details

        return result
