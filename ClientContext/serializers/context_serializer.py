"""Serializer para mapeamento de dados de contexto JSON para Model."""

from typing import TYPE_CHECKING, Any, Dict

from ..utils.context_mapping import CONTEXT_FIELD_MAPPING

if TYPE_CHECKING:
    from ..models import ClientContext


class WeeklyContextDataSerializer:
    """Serializer para mapear dados JSON do contexto para o model ClientContext."""

    def __init__(self, context_data: Dict[str, Any]):
        """Inicializa o serializer com os dados de contexto.

        Args:
            context_data: Dicionario com dados de contexto da AI
        """
        self.context_data = context_data

    def update_client_context(self, client_context: "ClientContext") -> None:
        """Mapeia dados JSON para campos do model.

        Args:
            client_context: Instancia do ClientContext a ser atualizada
        """
        for section_key, fields in CONTEXT_FIELD_MAPPING.items():
            section_data = self.context_data.get(section_key, {})
            for json_key, (model_field, default) in fields.items():
                value = section_data.get(json_key, default)
                setattr(client_context, model_field, value)

    def to_dict(self) -> Dict[str, Any]:
        """Converte os dados mapeados para dicionario.

        Returns:
            Dicionario com campos do model como chaves
        """
        result = {}
        for section_key, fields in CONTEXT_FIELD_MAPPING.items():
            section_data = self.context_data.get(section_key, {})
            for json_key, (model_field, default) in fields.items():
                result[model_field] = section_data.get(json_key, default)
        return result
