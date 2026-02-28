# Trabalho Próximo Sugerido

**Última atualização:** 2026-02-28

---

## Prioridade 1: Pós-Merge (Configuração de Produção)

### PRs Pendentes de Review
- [ ] PR #38 - Bugfix onboarding (backend)
- [ ] PR #29 - Bugfix onboarding (frontend)
- [ ] PR #37 - Two-phase enrichment + quality fixes

### Segurança
- [ ] Gerar nova `SECRET_KEY` para produção
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- [ ] Configurar `ALLOWED_HOSTS` com domínios reais
- [ ] Verificar `DEBUG=False` em produção

### Stripe
- [ ] Configurar `STRIPE_WEBHOOK_SECRET` de produção
- [ ] Atualizar Price IDs para live mode
- [ ] Testar webhook com `stripe listen --forward-to`

---

## Prioridade 2: Qualidade de Código

### Testes E2E
- [ ] Implementar testes E2E para fluxo de onboarding
  - Framework: Cypress ou Playwright
  - Cenários: Create novo + Edit existente
  - Coverage: Steps 1-2 completos

### TypeScript no Frontend
- [ ] Adicionar `tsc --noEmit` no pre-commit hook
- [ ] Configurar TypeScript strict mode gradualmente
- [ ] Resolver warnings existentes

### Dependências
- [ ] Frontend: `npm audit fix` (7 vulnerabilidades)
- [ ] Backend: Atualizar dependências com vulnerabilidades conhecidas

---

## Prioridade 3: Pendências do Plano Original

### Validação com Mensagens de Erro (ContactInfoStep)
- [ ] Validar Instagram: `^[a-zA-Z0-9._]{1,30}$`
- [ ] Validar Website: URL válida
- [ ] Mostrar mensagens em vermelho abaixo dos campos
- [ ] Adicionar classe `border-red-500` quando há erro

### Arquitetura de Visual Styles
- [ ] Decidir arquitetura: Frontend-first vs Backend-first
- [ ] Implementar single source of truth
- [ ] Remover duplicação de dados (ver `ANALISE_PR24_VISUAL_STYLES.md`)

---

## Prioridade 4: Débito Técnico

### Backend
- [ ] Implementar rate limiting no checkout
- [ ] Adicionar retry com exponential backoff nas chamadas Stripe
- [ ] Centralizar validação de status do Stripe em enum/constante
- [ ] Migrar emails assíncronos para Celery (evitar asyncio em Django)

### Frontend
- [ ] Resolver vulnerabilidades high/moderate do Dependabot
- [ ] Otimizar bundle size (lazy loading de componentes)

---

## Prioridade 5: Melhorias Futuras

### Testes
- [ ] Testar concorrência (múltiplas requisições simultâneas)
- [ ] Testar timeout em chamadas Stripe
- [ ] Adicionar testes de integração com Stripe em sandbox

### Monitoramento
- [ ] Dashboard de métricas de assinaturas
- [ ] Alertas para falhas de webhook
- [ ] Logs estruturados para debugging

### UX
- [ ] Adicionar indicador de progresso no onboarding
- [ ] Implementar auto-save nos steps do onboarding
- [ ] Melhorar feedback visual durante uploads

---

## Referências

### PRs Ativos
- PR #38: https://github.com/PostNow-AI/PostNow-REST-API/pull/38
- PR #37: https://github.com/PostNow-AI/PostNow-REST-API/pull/37
- PR #29: https://github.com/PostNow-AI/PostNow-UI/pull/29

### Documentação
- `docs/FIX_ONBOARDING_STEP_TRACKING.md` - Bugs corrigidos neste sprint
- `docs/ENTREGA_CTO_SPRINT_BUGFIX_ONBOARDING.md` - Entrega consolidada
- `docs/ANALISE_PR24_VISUAL_STYLES.md` - Análise arquitetural
- `docs/SUBSCRIPTION_SYSTEM.md` - Sistema de assinaturas

---

## Histórico de Atualizações

| Data | Mudança |
|------|---------|
| 2026-02-28 | Adicionado PRs #38, #29, #37 pendentes; Testes E2E; TypeScript checks |
| 2026-02-10 | Versão inicial com pendências do sprint Onboarding 2.0 |
