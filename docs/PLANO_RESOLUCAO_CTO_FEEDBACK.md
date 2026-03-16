# Plano de Resolucao - Feedback do CTO

**Data:** 2026-03-16
**Autor:** Rogerio + Claude
**Status:** Em execucao

---

## Resumo

14 comentarios do CTO (MatheusBlanco) sem resposta, distribuidos em 2 repos e 6 PRs.
Este documento detalha o plano de acao para resolver cada um.

---

## Fase 1: REST-API PR #42 — Prompts fora do lugar (URGENTE)

**Comentarios:**
1. `opportunities_generation_service.py`: "se e um prompt, deve ir no arquivo ai_prompt_service.py"
2. `ai_prompt_service.py`: "isso deve estar num arquivo proprio"

### 1.1 Mover prompts de oportunidades

Extrair de `ClientContext/services/opportunities_generation_service.py`:
- `_build_opportunities_prompt()` (linhas 201-332)
- `_format_context_for_prompt()` (linhas 334-398)
- `_format_discovered_trends()` (linhas 504-559)

Destino: novo modulo `services/prompts/opportunities_prompts.py`
O `OpportunitiesGenerationService` passa a importar e chamar desse modulo.

### 1.2 Quebrar ai_prompt_service.py (1.505 linhas)

Criar pacote `services/prompts/`:

| Novo arquivo | Conteudo |
|---|---|
| `services/prompts/__init__.py` | Re-exporta classes para compatibilidade |
| `services/prompts/context_discovery_prompts.py` | `_build_market_prompt`, `_build_competition_prompt`, `_build_trends_prompt`, `_build_seasonality_prompt`, `_build_brand_prompt`, `_build_synthesis_prompt` |
| `services/prompts/content_generation_prompts.py` | `build_content_prompts`, `build_standalone_post_prompt`, `build_campaign_prompts` |
| `services/prompts/opportunities_prompts.py` | `build_opportunities_prompt` + helpers do 1.1 |
| `services/ai_prompt_service.py` | Coordenador que importa dos modulos acima (~150 linhas) |

Manter `prompt_utils.py` e `prompt_logo.py` inalterados.

**Branch:** `integration/opportunity-flow`

---

## Fase 2: REST-API PR #39 — Funcoes grandes e utils duplicados (URGENTE)

**Comentarios:**
1. (hoje) `weekly_context_service.py`: "esse e o tipo de codigo que deveria estar em um arquivo proprio"
2. (13/03) Quebrar funcoes grandes em services menores
3. (13/03) Separar funcoes de `weekly_context.py` em arquivos distintos

### 2.1 Quebrar `_generate_context_for_user()` (275 linhas)

Extrair para metodos menores:

| Novo metodo | Responsabilidade |
|---|---|
| `_resolve_policy(user, profile)` | Logica de policy auto/override |
| `_execute_searches(sections, history, policy)` | Buscas pt-BR/en com fallbacks e deduplicacao |
| `_synthesize_with_ai(section, results)` | Sintese via Gemini por secao |

### 2.2 Finalizar extracao de `weekly_context.py` (1.043 linhas)

| Funcao | Destino |
|---|---|
| `generate_weekly_context_email_template()` | `ClientContext/utils/weekly_context_email.py` (novo) |
| `_render_json_as_bullets()`, `_format_text_data()` | `ClientContext/utils/email_helpers.py` (ja existe) |
| `_generate_ranked_opportunities_html()` | `ClientContext/utils/opportunities_email.py` (ja existe) |
| Remover duplicatas de templates que ja existem em arquivos proprios | |

### 2.3 Atualizar imports em `weekly_context_email_service.py`

**Branch:** branch do PR #39

---

## Fase 3: REST-API PR #12 — Excesso de comentarios (MEDIA)

**Comentario:** "tem mais comentario do que codigo aqui. se isso ja nao estiver documentado em um docs, fazer e tirar daqui"

### 3.1 Limpar comentarios redundantes

O projeto ja tem docs completos:
- `docs/WEEKLY_CONTEXT_ARCHITECTURE.md`
- `docs/WEEKLY_CONTEXT_POLICIES.md`
- `docs/WEEKLY_CONTEXT_PRODUCT.md`

Acoes:
- Remover comentarios que duplicam os docs (secoes numeradas 1-5, explicacoes de fallback/policy)
- Manter apenas comentarios de "porque" para decisoes nao-obvias
- Adicionar referencia `# See docs/WEEKLY_CONTEXT_ARCHITECTURE.md` no topo da classe

**Branch:** junto com Fase 2

---

## Fase 4: UI PR #15 — Code review do Dashboard 2.0 (ALTA)

**Comentarios:** 7 pontos (className, progress bar, hex colors, componente custom)

### 4.1 Simplificar classNames
Arquivos: `BottomNav.tsx`, `EmailSection.tsx`, `GeneralView.tsx`
- Onde nao ha condicional, juntar `cn()` multi-line em uma unica linha

### 4.2 Usar Progress bar existente
Arquivo: `EmailSection.tsx` (linhas 98-103)
- Substituir progress bar custom pelo `<Progress>` de `src/components/ui/progress.tsx`

### 4.3 Eliminar hex colors
Arquivo: `HeroMetricCard.tsx` (linhas 90-99)
- Substituir `colorMap` hex por CSS variables do tema (`--chart-1` a `--chart-5`)

### 4.4 Chart custom (baixa prioridade, CTO disse "pode ficar para depois")
Arquivo: `EngagementSection.tsx` (linhas 47-83)
- Substituir donut SVG por componente de biblioteca quando oportuno

**Branch:** nova branch a partir de main

---

## Fase 5: UI PR #14 — Bugs de QA do Onboarding (ALTA)

**Comentarios:** Rota bloqueada, validacao de campos, erro em screenshot

### 5.1 Rota visual-style-preferences
- Backend: criar endpoint publico GET-only para fixtures de estilos
- Frontend: atualizar `fetchVisualStylePreferences()` para endpoint publico

### 5.2 Validacao pre-submit
Arquivo: `OnboardingNew.tsx`
- Validar via Zod schema antes do submit (schema ja existe)
- Se erro: navegar stepper para o step com campo invalido + mensagem inline

### 5.3 Error handling
- Adicionar tratamento de erro amigavel no submit do onboarding

**Branch:** nova branch a partir de main (envolve backend + frontend)

---

## Fase 6: UI PR #33 — @ts-nocheck (MEDIA)

**Comentario:** "Mais de metade dos arquivos estao declarando @ts-nocheck"

### 6.1 Verificar estado atual
- Grep atual retorna 0 arquivos com `@ts-nocheck` — provavelmente ja resolvido
- Confirmar e responder o CTO no PR

**Branch:** verificar apenas

---

## Checklist de execucao

- [x] Fase 1.1: Mover prompts de oportunidades
- [x] Fase 1.2: Quebrar ai_prompt_service.py em modulos
- [ ] Fase 2.1: Quebrar _generate_context_for_user()
- [ ] Fase 2.2: Finalizar extracao de weekly_context.py
- [ ] Fase 2.3: Atualizar imports
- [ ] Fase 3.1: Limpar comentarios redundantes
- [ ] Fase 4.1: Simplificar classNames
- [ ] Fase 4.2: Usar Progress existente
- [ ] Fase 4.3: Eliminar hex colors
- [ ] Fase 5.1: Endpoint publico visual-style-preferences
- [ ] Fase 5.2: Validacao pre-submit onboarding
- [ ] Fase 5.3: Error handling onboarding
- [ ] Fase 6.1: Verificar @ts-nocheck
