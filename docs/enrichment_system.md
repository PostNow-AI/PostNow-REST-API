# PR #34: Two-Phase Context Enrichment System

**Data:** 2026-02-27
**Autor:** Claude Code + Equipe
**Status:** Pronto para Produção

---

## Resumo Executivo

Este PR implementa um sistema de enriquecimento de contexto em duas fases, substituindo o e-mail semanal único por dois e-mails especializados:

- **Segunda-feira:** E-mail de Oportunidades de Conteúdo (enriquecido)
- **Quarta-feira:** E-mail de Inteligência de Mercado (enriquecido)

### Métricas do PR

| Métrica | Valor |
|---------|-------|
| Commits | 21 |
| Arquivos modificados | 37 |
| Linhas adicionadas | +5.527 |
| Testes automatizados | 57 |
| Rodadas de análise de qualidade | 10 |

---

## Arquitetura

```
DOMINGO (Fase 1)
├── 06:00 UTC - WeeklyContextService
│   └── Gera contexto semanal com Gemini AI
│   └── Salva em ClientContext
│
└── 09:00 UTC - OpportunitiesGenerationService (Fase 1b)
    └── Transforma contexto em oportunidades ranqueadas
    └── Salva em tendencies_data

SEGUNDA-FEIRA (Fase 2a)
└── 10:00 UTC - Oportunidades
    ├── ContextEnrichmentService
    │   └── Busca fontes via Google Custom Search
    │   └── Gera análise aprofundada com AI
    └── OpportunitiesEmailService
        └── Envia e-mail com oportunidades enriquecidas

QUARTA-FEIRA (Fase 2b)
└── 10:00 UTC - Inteligência de Mercado
    ├── MarketIntelligenceEnrichmentService
    │   └── Enriquece seções (mercado, concorrência, público)
    └── MarketIntelligenceEmailService
        └── Envia e-mail de inteligência de mercado
```

---

## Novos Endpoints

| Endpoint | Método | Descrição | Auth |
|----------|--------|-----------|------|
| `/client-context/generate-opportunities/` | GET | Gera oportunidades (Fase 1b) | Bearer Token |
| `/client-context/enrich-and-send-opportunities-email/` | GET | Enriquece + envia e-mail de segunda | Bearer Token |
| `/client-context/send-market-intelligence-email/` | GET | Enriquece + envia e-mail de quarta | Bearer Token |

### Endpoint Deprecated

| Endpoint | Status | Alternativa |
|----------|--------|-------------|
| `/client-context/send-weekly-context-email/` | **410 Gone** | Usar novos endpoints acima |

---

## Migração de Banco de Dados

### Nova migração: `0004_add_enrichment_fields.py`

```python
# Campos adicionados ao ClientContext
tendencies_data = JSONField(null=True)           # Dados de oportunidades
context_enrichment_status = CharField(max_length=20, default='pending')
context_enrichment_date = DateTimeField(null=True)
context_enrichment_error = TextField(default='')
```

**Tipo:** AddField only (não destrutiva)
**Rollback:** `python manage.py migrate ClientContext 0003`

### Comando de migração

```bash
python manage.py migrate ClientContext
```

---

## Variáveis de Ambiente

### Obrigatórias (já existentes)

| Variável | Descrição |
|----------|-----------|
| `CRON_SECRET` | Token de autenticação para endpoints batch |
| `API_BASE_URL` | URL base da API (usado nos workflows) |

### Opcionais (novas)

| Variável | Descrição | Default |
|----------|-----------|---------|
| `GOOGLE_CSE_API_KEY` | API key do Google Custom Search | - |
| `GOOGLE_CSE_ID` | ID do Search Engine | - |

**Nota:** Se Google CSE não estiver configurado, o sistema funciona normalmente mas sem fontes enriquecidas.

### Configuração do Google Custom Search

1. Acessar [Google Cloud Console](https://console.cloud.google.com)
2. Criar projeto ou selecionar existente
3. Habilitar "Custom Search API"
4. Criar credencial (API Key)
5. Acessar [Programmable Search Engine](https://cse.google.com)
6. Criar Search Engine
7. Copiar Search Engine ID
8. Configurar variáveis de ambiente

**Custos:**
- Free tier: 100 queries/dia (~16 usuários)
- Paid: $5 por 1000 queries

---

## GitHub Actions Workflows

### Removido

- `weekly-context-mailing.yml` - Substituído pelos novos workflows

### Modificado

- `weekly-context-generation.yml` - Horário alterado de 00:00 para 06:00 UTC

### Novos

| Workflow | Cron | Descrição |
|----------|------|-----------|
| `weekly-opportunities-generation.yml` | `0 9 * * 0` (Dom 09:00) | Gera oportunidades |
| `weekly-opportunities-mailing.yml` | `0 10 * * 1` (Seg 10:00) | Envia e-mail de oportunidades |
| `weekly-market-intelligence-mailing.yml` | `0 10 * * 3` (Qua 10:00) | Envia e-mail de inteligência |

Todos os workflows usam **5 batches** com `max-parallel: 2` para evitar timeouts.

---

## Correções de Segurança

| Vulnerabilidade | Correção | Arquivo |
|-----------------|----------|---------|
| Timing Attack | `secrets.compare_digest()` | `views.py` |
| XSS em e-mails | `html.escape()` em todos os templates | `*_email.py` |
| Header Injection | `_sanitize_subject()` | Email services |
| Endpoints sem auth | Token validation obrigatório | `views.py` |

---

## Testes Automatizados

| Categoria | Quantidade | Cobertura |
|-----------|------------|-----------|
| URL Validation | 19 | Sync/async, edge cases, erros |
| N+1 Query Fix | 12 | Pre-fetch, imports, services |
| Security | 26 | Timing attack, XSS, sanitização |
| **Total** | **57** | ✅ Todos passando |

### Executar testes

```bash
python manage.py test ClientContext.tests
```

---

## Checklist de Deploy

### Pré-deploy

- [ ] Verificar `CRON_SECRET` no GitHub Secrets
- [ ] Verificar `API_BASE_URL` no GitHub Secrets
- [ ] (Opcional) Configurar `GOOGLE_CSE_API_KEY` e `GOOGLE_CSE_ID`
- [ ] Revisar PR no GitHub

### Deploy

- [ ] Aprovar e fazer merge do PR
- [ ] Aguardar deploy automático (Vercel)
- [ ] Executar migração em produção:
  ```bash
  python manage.py migrate ClientContext
  ```

### Pós-deploy

- [ ] Verificar logs de erro no Vercel
- [ ] Testar endpoint manualmente:
  ```bash
  curl -X GET "https://api.postnow.com.br/api/v1/client-context/generate-opportunities/?batch=1" \
    -H "Authorization: Bearer $CRON_SECRET"
  ```
- [ ] Verificar que endpoint deprecated retorna 410

### Monitoramento (primeira semana)

| Dia | Horário (UTC) | Verificar |
|-----|---------------|-----------|
| Domingo | 06:00 | Logs de geração de contexto |
| Domingo | 09:00 | Logs de geração de oportunidades |
| Segunda | 10:00 | Envio de e-mails de Oportunidades |
| Quarta | 10:00 | Envio de e-mails de Inteligência de Mercado |

---

## Rollback

### Se migração falhar

```bash
python manage.py migrate ClientContext 0003
```

### Se bugs em produção

1. Reverter merge no GitHub
2. Redeploy automático via Vercel
3. Rollback de migração se necessário

### Degradação graceful

- Se Google CSE indisponível: E-mails enviados sem fontes extras
- Se Gemini falhar: Erro logado, usuário marcado para retry
- Se Mailjet falhar: Erro logado, não afeta outros usuários

---

## Estrutura de Arquivos

```
ClientContext/
├── services/
│   ├── opportunities_generation_service.py    # NOVO - Fase 1b
│   ├── context_enrichment_service.py          # NOVO - Fase 2 Segunda
│   ├── market_intelligence_enrichment_service.py  # NOVO - Fase 2 Quarta
│   ├── opportunities_email_service.py         # NOVO - E-mail Segunda
│   └── market_intelligence_email_service.py   # NOVO - E-mail Quarta
├── utils/
│   ├── opportunities_email.py      # NOVO - Template HTML
│   ├── market_intelligence_email.py # NOVO - Template HTML
│   ├── search_utils.py             # NOVO - Google Search
│   ├── source_quality.py           # NOVO - Scoring de fontes
│   ├── url_validation.py           # NOVO - Validação 404
│   └── url_dedupe.py               # NOVO - Deduplicação URLs
├── tests/
│   ├── test_url_validation.py      # NOVO - 19 testes
│   ├── test_services_n1_fix.py     # NOVO - 12 testes
│   └── test_security_fixes.py      # NOVO - 26 testes
└── migrations/
    └── 0004_add_enrichment_fields.py  # NOVO

services/
└── google_search_service.py        # NOVO - Integração Google CSE

docs/mockups/
├── README.md                       # NOVO - Documentação dos mockups
├── mock_email_monday_opportunities.html
└── mock_email_wednesday_market_intelligence.html
```

---

## Contato

Para dúvidas sobre esta implementação:
- Revisar código nos arquivos listados acima
- Consultar `docs/mockups/README.md` para visualização dos e-mails
- Verificar `CHANGELOG.md` para histórico completo de mudanças
