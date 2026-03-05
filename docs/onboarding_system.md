# Correção: Bugs no Sistema de Onboarding

**Data:** 2026-02-28
**Autor:** Análise técnica via Claude Code
**Status:** PR #38 - Aguardando review
**Tipo:** Bugfix (PATCH)

---

## Índice

- [Resumo Executivo](#resumo-executivo)
- [Bug 1: Campo step_3_completed Fantasma](#bug-1-campo-step_3_completed-fantasma)
- [Bug 2: Numeração Incorreta nos Logs](#bug-2-numeração-incorreta-nos-logs)
- [Bug 3: visual_style_ids Tipo Inconsistente](#bug-3-visual_style_ids-tipo-inconsistente)
- [Bug 4: Array de Cores Incompleto na Edição](#bug-4-array-de-cores-incompleto-na-edição)
- [Bug 5: Except Duplicado no Service](#bug-5-except-duplicado-no-service)
- [Testes](#testes)
- [Verificação](#verificação)
- [Impacto](#impacto)
- [Referências](#referências)

---

## Resumo Executivo

Correção de múltiplos bugs no sistema de onboarding, incluindo problemas de tracking de steps, tipos inconsistentes entre frontend e backend, e código duplicado.

| Métrica | Valor |
|---------|-------|
| Bugs corrigidos | 5 |
| Arquivos backend modificados | 3 |
| Arquivos frontend modificados | 3 |
| Testes adicionados | 10 |
| Risco de regressão | Baixo |

---

## Bug 1: Campo `step_3_completed` Fantasma

### Problema

```
HISTÓRICO DAS MIGRAÇÕES
───────────────────────

Migration 0002                    Migration 0005
     │                                 │
     ▼                                 ▼
┌─────────────────────┐         ┌─────────────────────┐
│ + step_1_completed  │         │ - step_3_completed  │  ← REMOVIDO
│ + step_2_completed  │         │                     │
│ + step_3_completed  │         └─────────────────────┘
└─────────────────────┘

MAS O CÓDIGO AINDA USAVA:
─────────────────────────
models.py:246  →  self.step_3_completed = self.step_2_completed
views.py:129   →  updated_profile.step_3_completed
views.py:138   →  updated_profile.step_3_completed
```

### Solução

**`CreatorProfile/models.py`**: Removida atribuição dinâmica de `step_3_completed`

**`CreatorProfile/views.py`**: Corrigidas referências para usar `step_2_completed`

---

## Bug 2: Numeração Incorreta nos Logs

### Problema

```
FLUXO ESPERADO                    FLUXO REAL (BUG)
──────────────                    ────────────────

Step1BusinessView                 Step1BusinessView
Log: step=1 ✓                     Log: step=2 ✗

Step2BrandingView                 Step2BrandingView
Log: step=2 ✓                     Log: step=3 ✗
```

### Solução

**`CreatorProfile/views.py`**: Corrigida numeração de steps nos logs de auditoria

```diff
- 'step': 2,
- 'step_completed': updated_profile.step_2_completed,
+ 'step': 1,
+ 'step_completed': updated_profile.step_1_completed,
```

---

## Bug 3: `visual_style_ids` Tipo Inconsistente

### Problema

```
FRONTEND                          BACKEND
────────                          ───────

useOnboardingStorage.ts           serializers.py
visual_style_ids: string[]        child=serializers.IntegerField()
     ↓                                 ↑
["1", "2", "3"]        ≠          [1, 2, 3]
```

O frontend armazenava e enviava `visual_style_ids` como strings, mas o backend esperava integers.

### Solução

**`PostNow-UI/src/features/Auth/Onboarding/hooks/useOnboardingStorage.ts`**:

```typescript
// Converter para integers - backend espera IntegerField()
visual_style_ids: data.visual_style_ids.map(id => parseInt(id, 10)).filter(id => !isNaN(id)),
```

**`PostNow-UI/src/features/Auth/Onboarding/services/index.ts`**:

```typescript
// Garantir conversão em camada de serviço também (defesa em profundidade)
const visualStyleIds = (data.visual_style_ids || []).map(id =>
  typeof id === 'string' ? parseInt(id, 10) : id
).filter(id => !isNaN(id));
```

---

## Bug 4: Array de Cores Incompleto na Edição

### Problema

```typescript
// OnboardingNew.tsx - Modo edição
colors: [
  initialData.color_1,
  initialData.color_2,
  initialData.color_3,
  initialData.color_4,
  initialData.color_5,
].filter((c): c is string => !!c),  // ← Remove cores vazias!
```

Se qualquer cor fosse `null`/`undefined`, o array ficava com menos de 5 cores, causando comportamento inconsistente.

### Solução

**`PostNow-UI/src/features/Auth/Onboarding/OnboardingNew.tsx`**:

```typescript
const defaultColors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFBE0B"];
colors: [
  initialData.color_1 || defaultColors[0],
  initialData.color_2 || defaultColors[1],
  initialData.color_3 || defaultColors[2],
  initialData.color_4 || defaultColors[3],
  initialData.color_5 || defaultColors[4],
],
```

**`PostNow-UI/src/features/Auth/Onboarding/hooks/useOnboardingStorage.ts`**:

Mesma lógica aplicada no `initializeWithData` para garantir consistência.

---

## Bug 5: Except Duplicado no Service

### Problema

```python
# CreatorProfile/services.py - Código duplicado
except CreatorProfile.DoesNotExist:
    return False
except CreatorProfile.DoesNotExist:  # ← DUPLICADO!
    return False
```

### Solução

**`CreatorProfile/services.py`**: Removido bloco except duplicado

---

## Testes

### Backend - Novos Testes Adicionados

| Classe | Testes | Descrição |
|--------|--------|-----------|
| `CreatorProfileStepTrackingTest` | 6 | Validação de step tracking |
| `CreatorProfileServiceTest` | 4 | Validação de serviços |
| **Total** | **10** | |

### Casos de Teste

```python
# Step Tracking
test_model_does_not_have_step_3_completed_field
test_onboarding_completes_with_only_two_steps
test_step_1_completion_tracked_correctly
test_step_2_completion_tracked_correctly
test_current_step_returns_correct_values
test_profile_loaded_from_db_has_no_step_3_attribute

# Service
test_complete_profile_updates_all_flags
test_update_profile_data_handles_visual_style_ids
test_update_profile_data_handles_empty_visual_style_ids
test_update_profile_data_strips_string_values
```

### Executar Testes

```bash
# Backend
python manage.py test CreatorProfile --settings=Sonora_REST_API.settings_test -v 2

# Resultado esperado: 37 tests OK
```

### Resultados (2026-02-28)

```
----------------------------------------------------------------------
Ran 37 tests in 0.037s

OK
```

---

## Verificação

### Backend

```bash
# Verificar que step_3 não é mais referenciado
grep -r "step_3" CreatorProfile/*.py | grep -v migrations | grep -v __pycache__
# Deve retornar vazio

# Verificar que except duplicado foi removido
grep -A2 "DoesNotExist" CreatorProfile/services.py
# Deve mostrar apenas um bloco except
```

### Frontend

```bash
# Verificar conversão de visual_style_ids
grep -A3 "visual_style_ids:" src/features/Auth/Onboarding/hooks/useOnboardingStorage.ts
# Deve mostrar conversão para parseInt

# Verificar fallback de cores
grep -B2 -A5 "defaultColors" src/features/Auth/Onboarding/OnboardingNew.tsx
# Deve mostrar array com 5 cores padrão
```

---

## Impacto

### Antes da Correção

| Bug | Comportamento |
|-----|---------------|
| step_3_completed | AttributeError potencial em alguns cenários |
| Logs incorretos | Métricas de funil desalinhadas |
| visual_style_ids | Erro de validação no backend |
| Cores | Array incompleto, comportamento inconsistente |
| Except duplicado | Código morto, warning do Python |

### Depois da Correção

| Bug | Comportamento |
|-----|---------------|
| step_3_completed | Completamente removido |
| Logs corretos | Métricas de funil alinhadas (step 1, 2) |
| visual_style_ids | Sempre enviado como integers |
| Cores | Sempre 5 cores com fallbacks |
| Except único | Código limpo |

### Compatibilidade

- **Backward compatible:** Sim
- **Database migration:** Não necessária
- **Frontend changes:** Correções de tipo e lógica
- **API changes:** Não (correções internas)

---

## Arquivos Modificados

### Backend (PostNow-REST-API)

| Arquivo | Mudança |
|---------|---------|
| `CreatorProfile/models.py` | Remove step_3_completed |
| `CreatorProfile/views.py` | Corrige logs e referências |
| `CreatorProfile/services.py` | Remove except duplicado |
| `CreatorProfile/tests.py` | +10 novos testes |

### Frontend (PostNow-UI)

| Arquivo | Mudança |
|---------|---------|
| `hooks/useOnboardingStorage.ts` | Converte visual_style_ids para int, garante 5 cores |
| `services/index.ts` | Atualiza tipo e conversão de visual_style_ids |
| `OnboardingNew.tsx` | Garante 5 cores com fallbacks na edição |

---

## Referências

### Pull Request

- **PR:** [#38](https://github.com/PostNow-AI/PostNow-REST-API/pull/38)
- **Branch:** `fix/onboarding-step-tracking`
- **Target:** `main`

### Commits

```
fix(onboarding): :bug: corrigir tracking de steps e bugs de edição
```

---

## Checklist de Aprovação

- [x] Bug 1: step_3_completed removido
- [x] Bug 2: Logs corrigidos
- [x] Bug 3: visual_style_ids corrigido
- [x] Bug 4: Array de cores corrigido
- [x] Bug 5: Except duplicado removido
- [x] Testes adicionados (10)
- [x] Testes passando (37/37)
- [x] Documentação atualizada
- [ ] Review aprovado
- [ ] Merge realizado
- [ ] Deploy em produção

---

**Aprovação:**

| Nome | Cargo | Data | Assinatura |
|------|-------|------|------------|
| | CTO | | |

---

*Documento gerado em Fevereiro/2026*
