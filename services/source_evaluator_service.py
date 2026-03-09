"""
Source Evaluator Service - Avalia fontes usando IA.

Analisa se as fontes são relevantes para:
- O setor do cliente
- O tipo de conteúdo (polêmica, educativo, newsjacking, etc.)
- A qualidade e autoridade do conteúdo
"""
import json
import logging
import os
from typing import Any, Dict, List

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None

logger = logging.getLogger(__name__)

# Critérios de avaliação por tipo de conteúdo
EVALUATION_CRITERIA = {
    'polemica': {
        'description': 'Conteúdo polêmico/debate',
        'criteria': [
            'Apresenta opiniões divergentes ou controversas?',
            'Gera discussão ou debate?',
            'Aborda um problema ou crítica do setor?',
        ],
        'good_signals': ['debate', 'polêmica', 'crítica', 'problema', 'controvérsia', 'discorda'],
        'bad_signals': ['tutorial', 'como fazer', 'passo a passo', 'guia'],
    },
    'educativo': {
        'description': 'Conteúdo educativo/tutorial',
        'criteria': [
            'Ensina algo prático e aplicável?',
            'Tem passos claros ou dicas acionáveis?',
            'É um guia, tutorial ou how-to?',
        ],
        'good_signals': ['como', 'guia', 'tutorial', 'dicas', 'passo a passo', 'aprenda'],
        'bad_signals': ['polêmica', 'debate', 'crítica', 'opinião'],
    },
    'newsjacking': {
        'description': 'Notícia recente para aproveitar',
        'criteria': [
            'É uma notícia recente (últimos 7-30 dias)?',
            'Anuncia algo novo (lançamento, atualização, mudança)?',
            'O cliente pode "surfar" essa notícia?',
        ],
        'good_signals': ['anuncia', 'lança', 'novo', 'atualização', 'mudança', '2026', '2025'],
        'bad_signals': ['história', 'desde', 'há anos', 'tradicional'],
    },
    'entretenimento': {
        'description': 'Conteúdo de entretenimento/humor',
        'criteria': [
            'É divertido, viral ou bem-humorado?',
            'Tem potencial de engajamento alto?',
            'É leve e compartilhável?',
        ],
        'good_signals': ['viral', 'meme', 'engraçado', 'hilário', 'trend', 'bomba'],
        'bad_signals': ['sério', 'técnico', 'complexo', 'estudo'],
    },
    'estudo_caso': {
        'description': 'Estudo de caso/case de sucesso',
        'criteria': [
            'Conta uma história real de sucesso ou fracasso?',
            'Mostra resultados concretos (números, métricas)?',
            'É sobre uma empresa ou pessoa específica?',
        ],
        'good_signals': ['case', 'sucesso', 'faturou', 'cresceu', 'resultados', 'história'],
        'bad_signals': ['dicas genéricas', 'teoria', 'conceito'],
    },
    'futuro': {
        'description': 'Tendências e previsões futuras',
        'criteria': [
            'Fala sobre tendências ou previsões?',
            'Projeta o futuro do setor?',
            'Aborda inovações ou mudanças que virão?',
        ],
        'good_signals': ['tendência', 'futuro', 'previsão', 'vai mudar', '2026', '2027'],
        'bad_signals': ['passado', 'história', 'retrospectiva'],
    },
}


class SourceEvaluatorService:
    """Serviço para avaliar fontes usando IA."""

    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.client = None
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        self.model = 'claude-3-5-haiku-20241022'

    def is_configured(self) -> bool:
        """Verifica se o serviço está configurado."""
        return bool(ANTHROPIC_AVAILABLE and self.api_key and self.client)

    def evaluate_sources(
        self,
        sources: List[Dict[str, Any]],
        opportunity_title: str,
        content_type: str,
        client_sector: str,
        max_sources: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Avalia fontes e retorna as mais relevantes.

        Args:
            sources: Lista de fontes com 'url', 'title', 'snippet', 'content'
            opportunity_title: Título da oportunidade de conteúdo
            content_type: Tipo de conteúdo (polemica, educativo, etc.)
            client_sector: Setor/nicho do cliente
            max_sources: Número máximo de fontes a retornar

        Returns:
            Lista das melhores fontes, ordenadas por relevância
        """
        if not sources:
            return []

        if not self.is_configured():
            logger.warning("SourceEvaluator: API não configurada, usando fallback")
            return self._evaluate_by_signals(sources, content_type, max_sources)

        try:
            return self._evaluate_with_ai(
                sources, opportunity_title, content_type, client_sector, max_sources
            )
        except Exception as e:
            logger.error(f"SourceEvaluator: Erro na avaliação IA: {e}")
            return self._evaluate_by_signals(sources, content_type, max_sources)

    def _build_sources_text(self, sources: List[Dict[str, Any]]) -> str:
        """Build formatted text of sources for the prompt."""
        parts = []
        for i, source in enumerate(sources, 1):
            content_preview = source.get('content', source.get('snippet', ''))[:300]
            parts.append(f"""
Fonte {i}:
- URL: {source.get('url', '')}
- Título: {source.get('title', '')}
- Conteúdo: {content_preview}...""")
        return '\n'.join(parts)

    def _build_evaluation_prompt(
        self,
        sources_text: str,
        criteria: Dict[str, Any],
        opportunity_title: str,
        client_sector: str,
        max_sources: int
    ) -> str:
        """Build the evaluation prompt for the AI."""
        criteria_list = '\n'.join(f'- {c}' for c in criteria['criteria'])
        return f"""Você é um avaliador de fontes para um criador de conteúdo.

CONTEXTO:
- Setor do cliente: {client_sector}
- Tipo de conteúdo desejado: {criteria['description']}
- Oportunidade: "{opportunity_title}"

CRITÉRIOS DE AVALIAÇÃO:
{criteria_list}

FONTES PARA AVALIAR:
{sources_text}

TAREFA:
Avalie cada fonte e selecione as {max_sources} MELHORES para esse tipo de conteúdo.

Responda APENAS com um JSON válido no formato:
{{
  "selected": [
    {{"index": 1, "score": 85, "reason": "Motivo em 1 linha"}}
  ]
}}

Selecione apenas fontes realmente relevantes. Se nenhuma for boa, retorne lista vazia."""

    def _parse_ai_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse AI response and extract selected sources."""
        # Remove code markers if present
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]

        result = json.loads(response_text)
        return result.get('selected', [])

    def _evaluate_with_ai(
        self,
        sources: List[Dict[str, Any]],
        opportunity_title: str,
        content_type: str,
        client_sector: str,
        max_sources: int
    ) -> List[Dict[str, Any]]:
        """Avalia fontes usando Claude."""
        criteria = EVALUATION_CRITERIA.get(content_type, EVALUATION_CRITERIA['educativo'])
        sources_text = self._build_sources_text(sources)
        prompt = self._build_evaluation_prompt(
            sources_text, criteria, opportunity_title, client_sector, max_sources
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            selected_indices = self._parse_ai_response(response.content[0].text.strip())

            selected_sources = []
            for item in selected_indices[:max_sources]:
                idx = item.get('index', 0) - 1
                if 0 <= idx < len(sources):
                    source = sources[idx].copy()
                    source['ai_score'] = item.get('score', 50)
                    source['ai_reason'] = item.get('reason', '')
                    selected_sources.append(source)

            logger.info(f"SourceEvaluator: IA selecionou {len(selected_sources)}/{len(sources)}")
            return selected_sources

        except json.JSONDecodeError:
            logger.warning("SourceEvaluator: Falha ao parsear JSON da IA")
            return self._evaluate_by_signals(sources, content_type, max_sources)

    def _evaluate_by_signals(
        self,
        sources: List[Dict[str, Any]],
        content_type: str,
        max_sources: int
    ) -> List[Dict[str, Any]]:
        """Fallback: Avalia fontes por sinais textuais (sem IA)."""
        criteria = EVALUATION_CRITERIA.get(content_type, EVALUATION_CRITERIA['educativo'])
        good_signals = criteria.get('good_signals', [])
        bad_signals = criteria.get('bad_signals', [])

        scored_sources = []
        for source in sources:
            text = (
                source.get('title', '') + ' ' +
                source.get('snippet', '') + ' ' +
                source.get('content', '')[:500]
            ).lower()

            score = 50
            for signal in good_signals:
                if signal.lower() in text:
                    score += 10
            for signal in bad_signals:
                if signal.lower() in text:
                    score -= 10

            score = max(0, min(100, score))
            scored_source = source.copy()
            scored_source['signal_score'] = score
            scored_sources.append(scored_source)

        scored_sources.sort(key=lambda x: x.get('signal_score', 0), reverse=True)
        return scored_sources[:max_sources]

    def evaluate_single_source(
        self,
        source: Dict[str, Any],
        content_type: str,
        client_sector: str
    ) -> Dict[str, Any]:
        """Avalia uma única fonte rapidamente."""
        result = self.evaluate_sources(
            sources=[source],
            opportunity_title="",
            content_type=content_type,
            client_sector=client_sector,
            max_sources=1
        )
        return result[0] if result else source
