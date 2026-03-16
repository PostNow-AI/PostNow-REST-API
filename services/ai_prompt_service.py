"""
AIPromptService - Coordenador de prompts para IA.

Delega a construção de prompts para módulos especializados em services/prompts/.

=============================================================================
NOTA IMPORTANTE SOBRE ARQUITETURA (NÃO REFATORAR SEM LER)
=============================================================================

Os prompts contêm "repetição" proposital de dados do perfil
(nome do negócio, setor, público-alvo, tom de voz, etc.) em cada prompt.

ISSO NÃO É VIOLAÇÃO DE DRY. Motivos:

1. Cada prompt é enviado INDEPENDENTEMENTE para a IA
2. A IA não "lembra" de chamadas anteriores
3. Cada prompt PRECISA ter o contexto completo para funcionar
4. São dados de contexto, não lógica duplicada

DRY se aplica a: lógica de código, funções, algoritmos
DRY NÃO se aplica a: dados de contexto em prompts independentes

=============================================================================
"""

import logging

from services.prompts.content_generation_prompts import (
    build_automatic_post_prompt as _build_automatic_post_prompt,
    build_campaign_prompts as _build_campaign_prompts,
    build_content_edit_prompt as _build_content_edit_prompt,
    build_content_prompts as _build_content_prompts,
    build_historical_analysis_prompt as _build_historical_analysis_prompt,
    build_image_edit_prompt as _build_image_edit_prompt,
    build_standalone_post_prompt as _build_standalone_post_prompt,
)
from services.prompts.context_discovery_prompts import (
    build_context_prompts as _build_context_prompts,
    build_synthesis_prompt as _build_synthesis_prompt,
    format_discovered_trends_for_prompt as _format_discovered_trends_for_prompt,
)
from services.prompts.image_prompts import (
    adapted_semantic_analysis_prompt as _adapted_semantic_analysis_prompt,
    image_generation_prompt as _image_generation_prompt,
    semantic_analysis_prompt as _semantic_analysis_prompt,
)

logger = logging.getLogger(__name__)


class AIPromptService:
    def __init__(self):
        self.user = None

    def set_user(self, user) -> None:
        """Set the user for whom the prompts will be generated."""
        self.user = user

    def build_context_prompts(self, discovered_trends: dict = None) -> list[str]:
        return _build_context_prompts(self.user, discovered_trends)

    def _build_synthesis_prompt(self, section_name: str, query: str, urls: list, profile_data: dict, excluded_topics: list = None, context_borrowed: list = None) -> list:
        return _build_synthesis_prompt(section_name, query, urls, self.user, excluded_topics, context_borrowed)

    def _format_discovered_trends_for_prompt(self, discovered_trends: dict = None) -> str:
        return _format_discovered_trends_for_prompt(discovered_trends)

    def build_content_prompts(self, context: dict, posts_quantity: str) -> list[str]:
        return _build_content_prompts(self.user, context, posts_quantity)

    def build_standalone_post_prompt(self, post_data: dict, context: dict) -> list[str]:
        return _build_standalone_post_prompt(self.user, post_data, context)

    def build_campaign_prompts(self, context: dict) -> list:
        return _build_campaign_prompts(self.user, context)

    def semantic_analysis_prompt(self, post_text: str) -> list[str]:
        return _semantic_analysis_prompt(post_text)

    def adapted_semantic_analysis_prompt(self, semantic_analysis: dict) -> list[str]:
        return _adapted_semantic_analysis_prompt(self.user, semantic_analysis)

    def image_generation_prompt(self, semantic_analysis: dict, generated_style=None) -> list[str]:
        return _image_generation_prompt(self.user, semantic_analysis, generated_style)

    def build_historical_analysis_prompt(self, post_data: dict) -> list[str]:
        return _build_historical_analysis_prompt(self.user, post_data)

    def build_automatic_post_prompt(self, analysis_data: dict = None) -> list[str]:
        return _build_automatic_post_prompt(self.user, analysis_data)

    def build_content_edit_prompt(self, current_content: str, instructions: str = None) -> list[str]:
        return _build_content_edit_prompt(current_content, instructions)

    def build_image_edit_prompt(self, user_prompt: str = None) -> list[str]:
        return _build_image_edit_prompt(user_prompt)
