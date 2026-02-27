# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- Sistema de enriquecimento de contexto em duas fases (PR #34)
- E-mail de Oportunidades de Conteúdo (Segunda-feira)
- E-mail de Inteligência de Mercado (Quarta-feira)
- Integração com Google Custom Search para fontes adicionais
- Análise aprofundada com Gemini AI
- Filtro de qualidade de fontes (denylist/allowlist + scoring)
- Validação de URLs (detecção de 404/soft-404)
- Deduplicação de URLs entre oportunidades
- Design visual unificado PostNow para e-mails
- 26 testes unitários para ContextEnrichmentService
- Scripts de geração de mockups para validação visual

### Changed
- Score de oportunidades agora exibido no formato X/100
- Refatoração do ContextEnrichmentService para seguir limite de 400 linhas

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
