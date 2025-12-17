from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import re
from urllib.parse import urlparse


# Denylist: fontes que tipicamente degradam o Weekly Context
# - PDFs / papers acadêmicos / repositórios institucionais
# - domínios que frequentemente retornam soft-404 / bloqueios / páginas genéricas
DENY_DOMAINS: set[str] = {
    "scielo.br",
    "www.scielo.br",
    "unesdoc.unesco.org",
    "www4.fag.edu.br",
    "cm-kls-content.s3.amazonaws.com",
    "sig.ufsb.edu.br",
    "sigaa.ufpi.br",
    "brasilescola.uol.com.br",
    "arinter.cps.sp.gov.br",
    "dokumen.pub",
    "www.dokumen.pub",
    "researchgate.net",
    "www.researchgate.net",
    "cdn.cebraspe.org.br",
    "sigaa.ufba.br",
    "ibipora.eloweb.net",
    "institutounicampo.com.br",
    "aspas.org.br",
    "br.linkedin.com",
    "www.studocu.com",
    "studocu.com",
    "fims.up.pt",
    "www.fims.up.pt",
    # LinkedIn Pulse tende a soft-404/article_not_found e gating
    "www.linkedin.com",
    "linkedin.com",
    # Redes sociais tendem a gating/irrelevância para fontes
    "www.instagram.com",
    "instagram.com",
    "www.facebook.com",
    "facebook.com",
    "www.tiktok.com",
    "tiktok.com",
}

# Deny por padrões de URL (independente do domínio)
# Objetivo: bloquear listagens/arquivos/downloads e páginas não-artigo que poluem a seleção
DENY_URL_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"(?i)\.(pdf|doc|docx|ppt|pptx|xls|xlsx)(\?|#|$)"),
    re.compile(r"(?i)/(tag|tags|categoria|category|search|busca)(/|\?|#|$)"),
    re.compile(r"(?i)/(embed|download|wp-content|wp-json)(/|\?|#|$)"),
    re.compile(r"(?i)/(home|inicio|sobre|contato)(/|\?|#|$)"),
)


# Allowlist leve (pode/DEVE evoluir com o tempo)
SECTION_ALLOWLIST: dict[str, set[str]] = {
    # Mercado: notícias e negócios
    "mercado": {
        "exame.com",
        "www.exame.com",
        "valor.globo.com",
        "infomoney.com.br",
        "www.infomoney.com.br",
        "istoedinheiro.com.br",
        "www.istoedinheiro.com.br",
        "economia.uol.com.br",
        "g1.globo.com",
        "sebrae.com.br",
        "www.sebrae.com.br",
        "cnnbrasil.com.br",
        "www.cnnbrasil.com.br",
        "www.meioemensagem.com.br",
        "meioemensagem.com.br",
        # en (premium)
        "www.mckinsey.com",
        "mckinsey.com",
        "www.hbr.org",
        "hbr.org",
        "www.shrm.org",
        "shrm.org",
        "www.reuters.com",
        "reuters.com",
    },
    # Tendências: tecnologia/gestão/trabalho
    "tendencias": {
        "www.gupy.io",
        "gupy.io",
        "www.totvs.com",
        "totvs.com",
        "www.startse.com",
        "startse.com",
        "endeavor.org.br",
        "www.endeavor.org.br",
        "sebrae.com.br",
        "www.sebrae.com.br",
        "www.meioemensagem.com.br",
        "meioemensagem.com.br",
        # en
        "www.mckinsey.com",
        "mckinsey.com",
        "www.hbr.org",
        "hbr.org",
        "www.gartner.com",
        "gartner.com",
        "www.shrm.org",
        "shrm.org",
    },
    # Concorrência: cases e campanhas (BR)
    "concorrencia": {
        "www.meioemensagem.com.br",
        "meioemensagem.com.br",
        "propmark.com.br",
        "www.propmark.com.br",
        "adnews.com.br",
        "www.adnews.com.br",
        "b9.com.br",
        "www.b9.com.br",
        "exame.com",
        "www.exame.com",
    },
    "publico": {
        "sebrae.com.br",
        "www.sebrae.com.br",
        "www.totvs.com",
        "totvs.com",
        "www.gupy.io",
        "gupy.io",
        "www.infomoney.com.br",
        "infomoney.com.br",
        "valor.globo.com",
        "exame.com",
        "www.exame.com",
    },
    "sazonalidade": {
        "www.sympla.com.br",
        "sympla.com.br",
        "www.eventbrite.com.br",
        "eventbrite.com.br",
        "www.feirasdobrasil.com.br",
        "feirasdobrasil.com.br",
    },
    "marca": {
        "www.reclameaqui.com.br",
        "reclameaqui.com.br",
        "www.instagram.com",
        "instagram.com",
        "www.facebook.com",
        "facebook.com",
        "exame.com",
        "www.exame.com",
        "valor.globo.com",
    },
}


def allowed_domains(section: str) -> list[str]:
    return sorted(list(SECTION_ALLOWLIST.get(section, set())))


def build_allowlist_query(base_query: str, domains: Iterable[str], max_domains: int = 8) -> str:
    """
    Injeta restrição de sites no query para aumentar recall dentro da allowlist.
    Observação: o Google CSE tem limite de tamanho de query; por isso limitamos domínios.
    """
    doms = [d.strip() for d in domains if d and d.strip()]
    doms = doms[:max_domains]
    if not doms:
        return base_query
    sites = " OR ".join([f"site:{d}" for d in doms])
    return f"({sites}) {base_query}"


# Pequena lista de “premium global” para desempate
PREMIUM_DOMAINS: set[str] = {
    "www.mckinsey.com",
    "mckinsey.com",
    "www.hbr.org",
    "hbr.org",
    "www.gartner.com",
    "gartner.com",
}


def _domain_from_url(url: str) -> str:
    try:
        return (urlparse(url).netloc or "").lower()
    except Exception:
        return ""


def is_denied(url: str) -> bool:
    if _domain_from_url(url) in DENY_DOMAINS:
        return True
    u = (url or "").strip()
    if not u:
        return True
    return any(p.search(u) for p in DENY_URL_PATTERNS)


def is_allowed(section: str, url: str) -> bool:
    domain = _domain_from_url(url)
    allow = SECTION_ALLOWLIST.get(section, set())
    return domain in allow


def _looks_like_listing(url: str) -> bool:
    u = (url or "").lower()
    patterns = ("/tag/", "/tags/", "/categoria/", "/category/", "/search", "/busca", "/embed", "/home")
    return any(p in u for p in patterns) or u.endswith("/")


def score_source(section: str, url: str) -> int:
    """
    Score simples para priorização de fontes (sem ML/RL).
    """
    if not url:
        return -10_000
    if is_denied(url):
        return -10_000

    score = 0
    if is_allowed(section, url):
        score += 40
    domain = _domain_from_url(url)
    if domain in PREMIUM_DOMAINS:
        score += 10
    if _looks_like_listing(url):
        score -= 20
    return score


def pick_candidates(
    section: str,
    urls: Iterable[str],
    min_allowlist: int = 3,
    max_keep: int = 6,
) -> list[str]:
    """
    Aplica denylist/allowlist + scoring e retorna as melhores URLs.
    Estratégia:
    - Se houver cobertura suficiente na allowlist (>= min_allowlist), usa apenas allowlist
    - Caso contrário, usa geral (sem denylist) ordenado por score
    """
    clean: list[str] = [u for u in urls if u and u.startswith("http") and not is_denied(u)]
    allow = [u for u in clean if is_allowed(section, u)]

    base = allow if len(allow) >= min_allowlist else clean
    base_sorted = sorted(base, key=lambda u: score_source(section, u), reverse=True)
    return base_sorted[:max_keep]


