# Proposta: Implementação de Versionamento Profissional

**Data:** Fevereiro 2026
**Autor:** Equipe de Engenharia
**Status:** Aguardando aprovação

---

## Sumário Executivo

Esta proposta apresenta um plano para **formalizar e aprimorar** o sistema de versionamento já existente nos repositórios **PostNow-REST-API** e **PostNow-UI**, adicionando tags de release, changelog automático e proteção de branches.

A implementação foi projetada para **zero interrupção** no fluxo atual de trabalho.

---

## 1. Diagnóstico: Cenário Atual

### 1.1 Estado dos Repositórios

| Aspecto | PostNow-REST-API | PostNow-UI |
|---------|------------------|------------|
| **Branch principal** | `main` | `main` |
| **Branch de desenvolvimento** | `devel` | `devel` |
| **Feature branches** | 19 branches ativas | 10 branches ativas |
| **Padrão de commits** | Gitmoji + Conventional | Gitmoji + Conventional |
| **Tags de release** | Nenhuma | Nenhuma |
| **Deploy** | Vercel (automático) | Vercel (automático) |
| **CI/CD** | GitHub Actions (crons) | Nenhum |

### 1.2 Branches Existentes

#### PostNow-REST-API (22 branches)
```
Produção:     main
Desenvolvimento: devel (5 commits à frente da main)

Features ativas:
├── feat/Rogerio
├── feat/contexto-semanal-2.0
├── feat/devops
├── feat/insta-api
├── feat/prompt-improvements
├── feat/prompts
├── feat/radar
├── feat/visual-styles
├── feat/weekly-context-radar-api
├── feature/campaigns-mvp
└── Novo-Post-2.0

Refatorações:
├── refactor/solid-dry-cto-review
└── refactor/solid-dry-from-main

Outros:
├── carousel-mvp
├── docs/analytics-bandits
└── estilos-2.0
```

#### PostNow-UI (12 branches)
```
Produção:     main
Desenvolvimento: devel (1 commit à frente da main)

Features ativas:
├── feat/Rogerio
├── feat/insta-api
├── feat/radar
├── fix/onboarding-data-persistence
├── Dashboard-2.0
├── onboarding-2.0
├── onboarding-2.1
└── POC/Rogerio
```

### 1.3 Padrão de Commits Atual

A equipe já utiliza uma combinação de **Gitmoji** + **Conventional Commits**:

```bash
# Exemplos encontrados nos repositórios:
fix: :bug: Strips html from text
feat: :sparkles: Adds fallback email sending
docs: :memo: Updates .env.example
refactor: :art: Formats code for proper format
chore: :construction_worker: Adds devel workflow
```

### 1.4 O que já funciona bem

- ✅ Fluxo de branches estruturado (main → devel → feature)
- ✅ Feature branches com nomenclatura consistente
- ✅ Deploy automático via Vercel
- ✅ Padrão de commits parcialmente adotado
- ✅ Workflows de automação no REST-API

### 1.5 O que falta para completar

- ❌ **Tags de release** - Não há versionamento semântico
- ❌ **Changelog automático** - Não há histórico de mudanças
- ❌ **Branch protection** - Commits diretos na main são permitidos
- ❌ **CI no UI** - Sem validação automática de PRs
- ❌ **Documentação formal** - Fluxo não está documentado

---

## 2. Solução Proposta

### 2.1 Visão Geral

**Formalizar** o fluxo existente e adicionar as peças que faltam:

```
ATUAL                              PROPOSTO
─────                              ────────
main ◄── devel ◄── feature/*       main (v1.2.3) ◄── devel ◄── feature/*
                                        │
Sem tags                           Tags + Releases automáticas
Sem proteção                       Branch protection
Sem CI (UI)                        CI em todos os PRs
```

### 2.2 O que muda vs. O que permanece

| Aspecto | Permanece | Muda |
|---------|-----------|------|
| Branches main/devel | ✅ | - |
| Feature branches | ✅ | - |
| Deploy Vercel | ✅ | - |
| Padrão de commits | ✅ Gitmoji | Documentar formalmente |
| Tags de release | - | ✅ Adicionar v1.0.0+ |
| Branch protection | - | ✅ Ativar na main |
| CI no UI | - | ✅ Adicionar workflow |
| Changelog | - | ✅ Automático via releases |

### 2.3 Benefícios

| Benefício | Impacto |
|-----------|---------|
| **Rastreabilidade** | Saber exatamente qual versão está em produção |
| **Rollback** | `git checkout v1.2.3` em vez de procurar commit |
| **Changelog** | Gerado automaticamente a cada release |
| **Qualidade** | CI valida PRs antes do merge |

---

## 3. Plano de Implementação

### Fase 1: Documentação ✅

**Status:** PRs abertos aguardando aprovação

| Tarefa | PR |
|--------|-----|
| Guia de versionamento (REST-API) | #30 |
| Guia de versionamento (UI) | #26 |

**Conteúdo:**
- Formaliza o fluxo de branches existente
- Documenta o padrão de commits (Gitmoji + Conventional)
- Guia para criar releases

### Fase 2: Templates e CI/CD ✅

**Status:** PRs abertos aguardando aprovação

| Tarefa | PR |
|--------|-----|
| Templates + Workflow release (REST-API) | #31 |
| Templates + CI + Workflow release (UI) | #27 |

**Conteúdo:**
- Templates de PR e Issues
- Workflow de release automática
- CI para UI (lint, typecheck, test, build)

### Fase 3: Primeira Release

Após merge dos PRs anteriores:

```bash
# REST-API
git checkout main
git tag -a v1.0.0 -m "Release v1.0.0 - Versão inicial oficial"
git push origin v1.0.0

# UI
git checkout main
git tag -a v1.0.0 -m "Release v1.0.0 - Versão inicial oficial"
git push origin v1.0.0
```

O workflow de release criará automaticamente:
- Release no GitHub com changelog
- Lista de commits desde o início

### Fase 4: Branch Protection

Configurar no GitHub (Settings > Branches > Add rule):

**Para `main`:**
| Regra | Valor |
|-------|-------|
| Branch name pattern | `main` |
| Require pull request | ✅ |
| Required approvals | 1 |
| Dismiss stale reviews | ✅ |
| Require status checks | ✅ (UI: CI) |

**Para `devel` (opcional):**
| Regra | Valor |
|-------|-------|
| Branch name pattern | `devel` |
| Require pull request | ✅ |
| Required approvals | 1 |

### Fase 5: Comunicação

- Documentar o fluxo na wiki/README
- Comunicar padrão para a equipe
- Período de adaptação

---

## 4. Fluxo de Trabalho Proposto

### 4.1 Desenvolvimento Normal

```bash
# 1. Criar feature branch a partir de devel
git checkout devel
git pull origin devel
git checkout -b feat/minha-feature

# 2. Desenvolver e commitar (manter padrão atual)
git commit -m "feat: :sparkles: Adiciona nova funcionalidade"

# 3. Push e PR para devel
git push origin feat/minha-feature
# Abrir PR: feat/minha-feature → devel

# 4. Após review e merge, feature vai para devel
```

### 4.2 Release para Produção

```bash
# 1. Quando devel estiver pronto para produção
git checkout main
git merge devel

# 2. Criar tag de release
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --tags

# 3. Workflow cria release automaticamente no GitHub
```

### 4.3 Hotfix Urgente

```bash
# 1. Criar branch de hotfix a partir de main
git checkout main
git checkout -b hotfix/corrigir-bug-critico

# 2. Fix e commit
git commit -m "fix: :bug: Corrige bug crítico"

# 3. PR direto para main (urgente)
# Após merge, criar tag de patch
git tag -a v1.1.1 -m "Hotfix v1.1.1"
git push origin v1.1.1

# 4. Merge hotfix de volta para devel
git checkout devel
git merge main
```

---

## 5. Cronograma

```
Semana 1              Semana 2              Semana 3
────────              ────────              ────────
    │                     │                     │
    ▼                     ▼                     ▼
┌────────────┐      ┌────────────┐      ┌────────────┐
│ Aprovar    │      │ Tags       │      │ Branch     │
│ PRs #30,   │ ───► │ v1.0.0     │ ───► │ Protection │
│ #26, #31,  │      │ em ambos   │      │ main/devel │
│ #27        │      │ repos      │      │            │
└────────────┘      └────────────┘      └────────────┘
```

---

## 6. Métricas de Sucesso

| Métrica | Atual | Meta |
|---------|-------|------|
| Versões taggeadas | 0 | 100% das releases |
| PRs com review | Não obrigatório | 100% obrigatório |
| CI no UI | Não existe | 100% dos PRs validados |
| Changelog | Manual/inexistente | Automático |
| Documentação do fluxo | Informal | Formal |

---

## 7. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Resistência a branch protection | Baixa | Período de adaptação, começar só com main |
| CI quebrando PRs | Média | Revisar e ajustar workflow conforme necessário |
| Esquecer de criar tags | Média | Documentação + lembretes em releases importantes |

---

## 8. Investimento

- **Tempo de configuração:** ~2-3 horas (menor que o estimado inicialmente pois o fluxo já existe)
- **Custo de infraestrutura:** $0 (GitHub Actions gratuito)

---

## 9. Próximos Passos

Após aprovação:

1. ✅ Merge PR #30 (docs REST-API)
2. ✅ Merge PR #26 (docs UI)
3. ✅ Merge PR #31 (templates REST-API)
4. ✅ Merge PR #27 (templates + CI UI)
5. 🏷️ Criar tags v1.0.0 em ambos repos
6. 🔒 Configurar branch protection (main primeiro, devel depois)
7. 📢 Comunicar equipe

---

## 10. PRs Relacionados

### PostNow-REST-API
- [#30](https://github.com/PostNow-AI/PostNow-REST-API/pull/30) - Guia de versionamento
- [#31](https://github.com/PostNow-AI/PostNow-REST-API/pull/31) - Templates + Workflow release

### PostNow-UI
- [#26](https://github.com/PostNow-AI/PostNow-UI/pull/26) - Guia de versionamento
- [#27](https://github.com/PostNow-AI/PostNow-UI/pull/27) - Templates + CI + Workflow release

---

**Aprovação:**

| Nome | Cargo | Data | Assinatura |
|------|-------|------|------------|
| | CTO | | |

---

*Documento gerado em Fevereiro/2026*
