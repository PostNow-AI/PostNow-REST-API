"""
Pacote de prompts - módulos especializados por domínio.

Estrutura:
    - context_discovery_prompts: mercado, concorrência, tendências, sazonalidade, marca
    - content_generation_prompts: posts, campanhas, edição de conteúdo
    - image_prompts: análise semântica e geração de imagens
    - opportunities_prompts: oportunidades de conteúdo
"""

from services.prompts.context_discovery_prompts import (
    build_context_prompts,
    build_synthesis_prompt,
    format_discovered_trends_for_prompt,
)
from services.prompts.content_generation_prompts import (
    build_automatic_post_prompt,
    build_campaign_prompts,
    build_content_edit_prompt,
    build_content_prompts,
    build_historical_analysis_prompt,
    build_image_edit_prompt,
    build_standalone_post_prompt,
)
from services.prompts.image_prompts import (
    adapted_semantic_analysis_prompt,
    image_generation_prompt,
    semantic_analysis_prompt,
)
from services.prompts.opportunities_prompts import (
    build_opportunities_prompt,
    format_context_for_prompt,
    format_discovered_trends,
)

__all__ = [
    'build_context_prompts',
    'build_synthesis_prompt',
    'format_discovered_trends_for_prompt',
    'build_content_prompts',
    'build_standalone_post_prompt',
    'build_campaign_prompts',
    'build_historical_analysis_prompt',
    'build_automatic_post_prompt',
    'build_content_edit_prompt',
    'build_image_edit_prompt',
    'semantic_analysis_prompt',
    'adapted_semantic_analysis_prompt',
    'image_generation_prompt',
    'build_opportunities_prompt',
    'format_context_for_prompt',
    'format_discovered_trends',
]
