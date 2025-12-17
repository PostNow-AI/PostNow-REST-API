# Weekly Context (E-mail semanal de oportunidades)

Este repositório/branch contém a implementação e documentação do **Weekly Context**: um pipeline que pesquisa fontes recentes, gera oportunidades rankeadas com IA e envia um e-mail semanal com links válidos e sem repetição.

## Propósito (por que usamos isso)
- **Reduzir tempo de pesquisa** do usuário (pauta semanal pronta)
- **Aumentar qualidade e confiabilidade** (guardrails de fonte + links válidos)
- **Acelerar criação** (CTA para “Criar Post” direto no app)

## Onde está a documentação “atual” (o que usamos hoje)

- **Propósito + UX + critérios de qualidade (visão produto)**  
  `PostNow-REST-API/docs/WEEKLY_CONTEXT_PRODUCT.md`

- **Políticas + Override por cliente (Admin + logs + como operar)**  
  `PostNow-REST-API/docs/WEEKLY_CONTEXT_POLICIES.md`

- **Arquitetura do Weekly Context (pipeline end-to-end)**  
  `PostNow-REST-API/docs/WEEKLY_CONTEXT_ARCHITECTURE.md`  
  _Inclui também: pré‑requisitos de execução (env vars) e como lidar com quota 429 do Google CSE._

## Como validar rapidamente (CTO)

### Backend

- Rodar testes do módulo:
  - `venv/bin/python manage.py test ClientContext.tests -v 2`
- Rodar processo completo (gera e envia e-mail):
  - `venv/bin/python scripts/trigger_team_validation.py`

## Principais mudanças desta entrega

- Policy automática por cliente (resolver) e **override manual por cliente** via `CreatorProfile.weekly_context_policy_override`
- Telemetria e alertas em logs: `[POLICY]`, `[SOURCE_METRICS]`, `[LOW_SOURCE_COVERAGE]`, `[LOW_ALLOWLIST_RATIO]`
- Migração: `CreatorProfile/migrations/0010_creatorprofile_weekly_context_policy_override.py`

## Observações importantes

- A documentação antiga não reflete o sistema atual do Weekly Context e foi substituída por este guia.
