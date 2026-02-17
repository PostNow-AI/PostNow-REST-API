from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse


@dataclass(frozen=True)
class WeekKey:
    year: int
    week: int

    def __str__(self) -> str:
        return f"{self.year}-W{self.week:02d}"


def get_week_key(dt: datetime, tz_name: str = "America/Sao_Paulo") -> WeekKey:
    """
    Retorna a semana ISO (seg-dom) para um datetime, usando o fuso informado.
    dt pode ser aware ou naive; se naive, assume que já está no fuso desejado.
    """
    try:
        from zoneinfo import ZoneInfo  # py3.9+
    except Exception:  # pragma: no cover
        ZoneInfo = None  # type: ignore

    if ZoneInfo is not None:
        tz = ZoneInfo(tz_name)
        if dt.tzinfo is not None:
            local_dt = dt.astimezone(tz)
        else:
            local_dt = dt.replace(tzinfo=tz)
    else:  # fallback bem simples
        local_dt = dt

    iso_year, iso_week, _ = local_dt.isocalendar()
    return WeekKey(year=int(iso_year), week=int(iso_week))


def normalize_url_key(url: str) -> str:
    """
    Normaliza uma URL para uma chave estável de dedupe: domain+path.
    - Ignora querystring e fragment
    - Lowercase apenas no domínio (path preserva case, mas a chave é para comparação)
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        domain = (parsed.netloc or "").lower()
        path = parsed.path or "/"
        # Remover barra final (exceto raiz) para reduzir variações
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return f"{domain}{path}"
    except Exception:
        return ""


