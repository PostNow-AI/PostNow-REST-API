from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class WeeklyContextPolicy:
    """
    Policy versionada em código para controlar comportamento do Weekly Context.
    Mantemos deliberadamente simples (baixo risco operacional).
    """

    key: str

    # Idiomas (Google CSE lr), em ordem de preferência. Ex.: ["lang_pt", "lang_en"].
    languages: List[str]

    # Mínimo de fontes selecionadas por seção (mercado/tendencias/concorrencia/etc).
    min_selected_by_section: Dict[str, int]

    # Quando houver cobertura >= N na allowlist, prioriza-se somente allowlist (por seção).
    allowlist_min_coverage: Dict[str, int]

    # Threshold de alerta para proporção allowlist (quando houver allowlist).
    allowlist_ratio_threshold: float = 0.60


