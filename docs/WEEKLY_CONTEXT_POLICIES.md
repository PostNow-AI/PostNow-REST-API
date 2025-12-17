# Weekly Context Policies

## Visão geral
O Weekly Context usa **policies versionadas em código** para controlar:
- qualidade de fontes (allowlist/denylist + padrões de URL)
- idiomas de busca (pt-BR e en) e fallback
- thresholds mínimos por seção (quantas fontes precisamos)
- telemetria (logs/métricas) para detectar regressões

O objetivo é permitir que o sistema se adapte ao perfil do cliente sem criar lógica espalhada (if/else) por todo o pipeline.

## Onde a policy é aplicada
Durante a geração do contexto (pipeline):
1. Carregamos `CreatorProfile` (via `AIPromptService._get_creator_profile_data`)
2. Resolvemos a policy automaticamente (`policy_resolver.resolve_policy`)
3. Aplicamos a policy na busca/filtro de fontes antes da IA e no recovery pós-IA

## Policies disponíveis
As policies ficam em `ClientContext/utils/policy_registry.py`.

### `default`
Policy padrão: pt-BR primeiro, fallback en, thresholds típicos por seção.

### `business_strict`
Mais conservadora. Indicada quando detectamos termos regulados (jurídico, saúde, financeiro etc.).
- ratio allowlist mínimo mais alto (alerta mais rígido)

### `broad_discovery`
Mais permissiva quando o perfil está incompleto (descrição curta ou nicho vazio), para aumentar recall.

## Como o sistema escolhe a policy (resolver)
Arquivo: `ClientContext/utils/policy_resolver.py`

Heurística (explicável, sem ML):
- Se `specialization` vazio ou `business_description` muito curta -> `broad_discovery`
- Se detectar palavras-chave reguladas (jurídico/saúde/financeiro) -> `business_strict`
- Caso contrário -> `default`

O sistema registra logs:
- `[POLICY] key=... source=auto|override override=... reason=... languages=... min_selected=...`

## Override por cliente (manual)
Existe um campo opcional no `CreatorProfile` para forçar uma policy por cliente:
- `weekly_context_policy_override` (ex.: `default`, `business_strict`, `broad_discovery`)

### Quando usar
- Cliente VIP/enterprise com exigência de qualidade mais rígida
- Perfil com onboarding incompleto que está caindo em uma policy “permissiva”
- Casos em que a heurística automática não está escolhendo a policy ideal

### Como usar (Django Admin)
1. Acesse o Django Admin
2. Abra o `CreatorProfile` do cliente
3. Preencha `Override de Policy (Weekly Context)` com uma das chaves de policy
4. Salve

### Rollback
Para voltar ao modo automático, **limpe o campo** (deixe vazio) e salve.

## Telemetria e alertas
Logs por seção:
- `[SOURCE_AUDIT]`: contagens raw e domínios finais
- `[SOURCE_METRICS]`: raw_pt/raw_en/denied/allow/selected/fallback

Alertas:
- `[LOW_SOURCE_COVERAGE]`: seção crítica abaixo do mínimo da policy
- `[LOW_ALLOWLIST_RATIO]`: proporção de allowlist abaixo do threshold da policy

## Testes
Rodar:
```bash
cd PostNow-REST-API
venv/bin/python manage.py test ClientContext.tests -v 2
```

Cobertura:
- `ClientContext/tests/test_policy_resolver.py`
- `ClientContext/tests/test_source_quality.py`
- `ClientContext/tests/test_url_dedupe.py`

## Como criar uma policy nova
1. Adicione um novo `WeeklyContextPolicy` no `policy_registry.get_policies()`
2. Ajuste o `policy_resolver.resolve_policy()` se quiser mapear automaticamente para ela
3. Adicione testes cobrindo o caso novo

## Carimbo de validação (execução real)
Última validação executada nesta branch (manual, end-to-end):

- **Unit tests**:
  - `venv/bin/python manage.py test ClientContext.tests -v 2` ✅
- **Migrations**:
  - `venv/bin/python manage.py makemigrations AuditSystem ClientContext CreatorProfile` ✅
  - `venv/bin/python manage.py migrate --noinput` ✅
- **E2E (email)**:
  - `venv/bin/python scripts/trigger_team_validation.py` ✅
  - Cenário padrão: logs com `[POLICY] ... source=auto` ✅
  - Cenário override: set `weekly_context_policy_override=business_strict`, logs com `[POLICY] ... source=override` ✅
  - Rollback: limpar `weekly_context_policy_override` ✅


