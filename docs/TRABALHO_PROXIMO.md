# Trabalho Próximo Sugerido

## Prioridade 1: Pós-Merge (Configuração de Produção)

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

## Prioridade 2: Pendências do Plano Original

### Validação com Mensagens de Erro (ContactInfoStep)
- [ ] Validar Instagram: `^[a-zA-Z0-9._]{1,30}$`
- [ ] Validar Website: URL válida
- [ ] Mostrar mensagens em vermelho abaixo dos campos
- [ ] Adicionar classe `border-red-500` quando há erro

### Modo Edição do Onboarding
- [ ] Substituir modal antigo (`OnboardingForm.tsx`) pelo novo
- [ ] Inicializar com dados do backend
- [ ] Pular steps de autenticação
- [ ] Botão "Salvar Alterações" no final

---

## Prioridade 3: Débito Técnico

### Frontend
- [ ] Atualizar dependências (7 vulnerabilidades no GitHub)
- [ ] Resolver vulnerabilidades high/moderate do Dependabot

### Backend
- [ ] Implementar rate limiting no checkout
- [ ] Adicionar retry com exponential backoff nas chamadas Stripe
- [ ] Centralizar validação de status do Stripe em enum/constante

---

## Prioridade 4: Melhorias Futuras

### Testes
- [ ] Adicionar testes de integração E2E (Cypress/Playwright)
- [ ] Testar concorrência (múltiplas requisições simultâneas)
- [ ] Testar timeout em chamadas Stripe

### Monitoramento
- [ ] Dashboard de métricas de assinaturas
- [ ] Alertas para falhas de webhook
- [ ] Logs estruturados para debugging

---

## Referências

- PR Backend: https://github.com/PostNow-AI/PostNow-REST-API/pull/15
- PR Frontend: https://github.com/PostNow-AI/PostNow-UI/pull/14
- Documentação Técnica: `docs/SUBSCRIPTION_SYSTEM.md`
