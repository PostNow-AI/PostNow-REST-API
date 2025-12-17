# Analytics + Bandits (Decisão → Eventos → Recompensa → Política)

Este documento descreve a implementação de **Analytics de produto** + **contextual bandit** no PostNow.

- **Código (backend)**: https://github.com/PostNow-AI/PostNow-REST-API/tree/feat/Rogerio
- **Código (frontend)**: https://github.com/PostNow-AI/PostNow-UI/tree/feat/Rogerio

## Propósito

O objetivo é habilitar um ciclo de aprendizado **interno** (sem depender de métricas externas como Instagram) para otimizar decisões do produto usando sinais observáveis:

- **Decisão**: o backend escolhe uma ação (ex.: pré-gerar imagem vs sob demanda)
- **Eventos**: a UI reporta o comportamento real do usuário
- **Recompensa**: um job offline agrega eventos e calcula um score/reward
- **Política**: outro job recalcula os parâmetros da política (ex.: Thompson Sampling)

Começamos pelo caso:

- **Imagem pré-gerar vs sob demanda**: reduzir gasto desnecessário de crédito sem degradar UX.

## Como isso funciona (visão geral)

### 1) Decisão (backend)

No momento da criação de uma `PostIdea`, o backend registra uma `Decision` com:

- `decision_type=image_pregen`
- `action=pre_generate|on_demand`
- `policy_id` (ex.: `image_pregen_bandit_v0` ou `image_pregen_bandit_v1`)
- `context` (inclui `post_type`, `objective`, e o `bucket` derivado)

### 2) Eventos (frontend → backend)

A UI emite eventos mínimos de produto e envia para o backend via endpoint autenticado.

### 3) Recompensa (job offline)

Um comando agrega `AnalyticsEvent` por `decision_id` e cria `DecisionOutcome` com:

- `reward`: score numérico
- `success`: boolean (heurística simples: houve download?)
- `metrics`: contagens por evento + penalidade de custo

### 4) Política (job offline)

Outro comando recalcula `BanditArmStat` (alpha/beta por bucket/ação), habilitando **Thompson Sampling**.

## Componentes no backend

- `Analytics/models.py`
  - `AnalyticsEvent`, `Decision`, `DecisionOutcome`, `BanditArmStat`
- `Analytics/views.py` + `Analytics/serializers.py`
  - endpoint de eventos
- `Analytics/services/image_pregen_policy.py`
  - políticas v0/v1 e registro de decisão
- `Analytics/management/commands/build_bandit_dataset.py`
  - agrega eventos → outcomes
- `Analytics/management/commands/rebuild_bandit_stats.py`
  - outcomes → stats
- `Analytics/management/commands/purge_analytics_events.py`
  - retenção/expurgo

## Endpoint de eventos (contrato)

- **Endpoint**: `POST /api/v1/analytics/events/`
- **Auth**: usuário autenticado (JWT/cookie via `dj_rest_auth`)

### Payload mínimo

Campos principais:

- `event_name` (controlado)
- `occurred_at` (opcional)
- `client_session_id` (UUID persistente no browser)
- `request_id` (opcional)
- `resource_type` / `resource_id` (ex.: `PostIdea` / `<id>`)
- `decision_id` / `policy_id` (quando existir)
- `context` / `properties` (JSON pequeno)

## Lista de eventos mínimos (UI)

- `idea_view_opened`
- `idea_copy_clicked`
- `idea_regenerate_clicked`
- `image_generate_clicked`
- `image_regenerate_clicked`
- `image_download_clicked`
- `image_download_succeeded`
- `image_download_failed`
- `post_save_clicked`

## Privacidade e anti-PII

Regras práticas:

- **Não enviar** `content` do post nem `prompt` livre.
- Enviar somente **tamanhos**, **flags** e campos estruturados (ex.: `content_len`, `has_html`).
- `context/properties` são validados e têm limites (tamanho/chaves); chaves sensíveis são bloqueadas no serializer.

## Políticas

### `image_pregen_bandit_v0` (default)

- Exploração determinística 50/50 (por dia, por usuário + bucket) para evitar flapping.

### `image_pregen_bandit_v1` (Thompson Sampling)

- Escolhe a ação com base em `BanditArmStat` (Beta-Binomial por bucket/ação).

### Variáveis de ambiente

- `IMAGE_PREGEN_POLICY_ID`
  - `image_pregen_bandit_v0` (default)
  - `image_pregen_bandit_v1` (Thompson)

## Runbook (operação)

### 1) Começar seguro

- Não configure nada (fica em `image_pregen_bandit_v0`).

### 2) Habilitar Thompson (v1)

- Garanta que os jobs offline estão rodando regularmente.
- Sete `IMAGE_PREGEN_POLICY_ID=image_pregen_bandit_v1`.

### 3) Rollback

- Voltar `IMAGE_PREGEN_POLICY_ID=image_pregen_bandit_v0`.

## Jobs offline

### Agregar eventos → outcomes

```bash
python manage.py build_bandit_dataset --decision-type image_pregen
```

### Recalcular stats (alpha/beta)

```bash
python manage.py rebuild_bandit_stats --policy-id image_pregen_bandit_v1
```

## Como validar (CTO / E2E)

1) Rodar backend + frontend em dev.
2) Criar um post no IdeaBank marcando “incluir imagem”.
3) Verificar que uma `Decision(image_pregen)` foi registrada para a `PostIdea`.
4) Abrir a ideia no UI e gerar sinais:
   - “Gerar imagem” (se não veio pré-gerada)
   - “Baixar” (para sinal de sucesso)
5) Rodar os jobs:

```bash
python manage.py build_bandit_dataset --decision-type image_pregen
python manage.py rebuild_bandit_stats --policy-id image_pregen_bandit_v1
```

6) Confirmar que `BanditArmStat` mudou para o(s) bucket(s) observados.

## Retenção

Recomendação inicial:

- Eventos brutos: 30–90 dias.
- Agregados (`DecisionOutcome`, `BanditArmStat`): manter por mais tempo.

Comando:

```bash
python manage.py purge_analytics_events --days 90 --dry-run
python manage.py purge_analytics_events --days 90
```

## Riscos e mitigação

- **Custo aumentar por pré-geração agressiva**
  - Mitigação: reward penaliza custo (crédito) e v0 como fallback.
- **Dados crescerem rápido**
  - Mitigação: retenção + índices.
- **Vazamento de PII**
  - Mitigação: validações + guideline “sem prompt/content”.
- **Jobs offline não rodarem**
  - Mitigação: manter v0 como default e só habilitar v1 após cron/rotina.

## O que ainda não está no escopo (mas a base suporta)

- Reward com métricas externas (Instagram/Meta).
- Bandits de texto (variação de prompts/params).
- Bandit de estilo visual.
- RL para scheduling/retries.
