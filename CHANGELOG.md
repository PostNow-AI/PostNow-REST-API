# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- Feedback loop de estilos visuais em 3 níveis:
  - **Sinais implícitos:** FK `generated_style` no PostIdea, campo `feedback_signal` (accepted/rejected/pending), emissão de AnalyticsEvent
  - **Favoritos:** endpoints `GET /styles/` e `PATCH /styles/<id>/favorite/`, favoritos como referência forte no prompt de geração
  - **Performance:** `InstagramInsightsService`, model `EngagementMetrics`, management command `fetch_engagement_metrics`, `engagement_score` no prompt
- Campo `reuse_style_id` no `ImageGenerationRequestSerializer` para reutilizar estilo existente
- Prompt de estilo enriquecido com 3 novas seções: FAVORITE STYLES, TOP PERFORMING STYLES, feedback separado (liked/rejected/pending)
- 45 novos testes unitários para o feedback loop
- Sistema de enriquecimento de contexto em duas fases (PR #34)
- E-mail de Oportunidades de Conteúdo (Segunda-feira)
- E-mail de Inteligência de Mercado (Quarta-feira)
- Integração com Google Custom Search para fontes adicionais
- Análise aprofundada com Gemini AI
- Filtro de qualidade de fontes (denylist/allowlist + scoring)
- Validação de URLs (detecção de 404/soft-404)
- Deduplicação de URLs entre oportunidades
- Design visual unificado PostNow para e-mails
- **57 testes unitários** cobrindo segurança, validação e serviços
- Mockups HTML para validação visual (ver `docs/mockups/README.md`)
- Script de diagnóstico Mailjet (`scripts/diagnose_mailjet.py`)

### Changed
- Score de oportunidades agora exibido no formato X/100
- Refatoração do ContextEnrichmentService para seguir limite de 400 linhas
- Workflow de oportunidades agora usa batches (1-5) como market intelligence

### Fixed
- Validação de URL agora retorna `False` em caso de erro (antes retornava `True`)
- Corrigido problema N+1 query em 6 serviços (pré-carregamento de usuários)
- Filtro Django `__isnull=True` em vez de `=None` para queries NULL
- Race condition entre workflows Phase 1 e Phase 1b (horários ajustados)
- Retry de contextos com status `failed` no enriquecimento
- Validação de `tendencies_data` vazio (`{}` vs `NULL`)
- Parse de JSON com regex (preserva "json" no conteúdo)
- Reset de `context_enrichment_status` ao gerar novo contexto semanal
- Tratamento de `User.DoesNotExist` em múltiplos serviços

### Security
- **Timing attack prevention**: `secrets.compare_digest()` para validação de tokens
- **XSS prevention**: Sanitização HTML em templates de e-mail (`html.escape`)
- **Header injection prevention**: Sanitização de subject de e-mail
- Autenticação adicionada em endpoint `manual_generate_client_context`
- Validação de batch number (1-100) em todos os endpoints

## [1.0.0] - 2026-02-26

### Added
- Sistema de Onboarding 2.0 com fluxo completo
- Integração Stripe para assinaturas e checkout
- Sistema de créditos para usuários
- Geração de conteúdo com IA (Gemini)
- Sistema de estilos visuais para posts
- E-mail semanal de contexto de mercado
- Workflows automatizados para geração de conteúdo
- Sistema de auditoria
- Integração com Google OAuth
- Templates de issues e PRs
- Guia de versionamento

### Security
- Configuração de ALLOWED_HOSTS para produção
- CORS configurado para domínios autorizados

---

## Tipos de mudanças

- `Added` para novas funcionalidades
- `Changed` para mudanças em funcionalidades existentes
- `Deprecated` para funcionalidades que serão removidas
- `Removed` para funcionalidades removidas
- `Fixed` para correções de bugs
- `Security` para correções de vulnerabilidades
