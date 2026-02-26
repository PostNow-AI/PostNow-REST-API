# Guia de Versionamento - PostNow

Este documento define as convenções de versionamento, branching e releases para os repositórios da PostNow.

## Índice

- [Semantic Versioning](#semantic-versioning)
- [Estratégia de Branching](#estratégia-de-branching)
- [Convenção de Commits](#convenção-de-commits)
- [Workflow de Desenvolvimento](#workflow-de-desenvolvimento)
- [Releases](#releases)
- [Exemplos Práticos](#exemplos-práticos)

---

## Semantic Versioning

Utilizamos [Semantic Versioning 2.0.0](https://semver.org/) no formato `MAJOR.MINOR.PATCH`:

```
v1.2.3
│ │ └── PATCH: correções de bugs (backward compatible)
│ └──── MINOR: novas funcionalidades (backward compatible)
└────── MAJOR: mudanças que quebram compatibilidade (breaking changes)
```

### Quando incrementar cada número

| Tipo | Quando usar | Exemplo |
|------|-------------|---------|
| **MAJOR** | Breaking changes na API, mudanças incompatíveis | Remover endpoint, mudar estrutura de response |
| **MINOR** | Nova funcionalidade backward compatible | Novo endpoint, novo campo opcional |
| **PATCH** | Bug fixes, melhorias de performance | Corrigir validação, otimizar query |

### Sufixos de pré-release

```
1.0.0-alpha.1    # Desenvolvimento inicial
1.0.0-beta.1     # Testes internos
1.0.0-rc.1       # Release candidate (quase pronto)
1.0.0            # Versão estável
```

---

## Estratégia de Branching

Utilizamos um fluxo **main/devel** com feature branches:

```
main (produção)
  │
  └── devel (desenvolvimento)
        │
        ├── feat/nova-funcionalidade
        ├── fix/corrigir-bug
        ├── refactor/melhorar-codigo
        └── hotfix/correcao-urgente (vai direto para main)
```

### Branches

| Branch | Propósito | Merge para |
|--------|-----------|------------|
| `main` | Produção (sempre deployável) | - |
| `devel` | Desenvolvimento e integração | `main` (quando estável) |
| `feat/*` | Novas funcionalidades | `devel` |
| `fix/*` | Correções de bugs | `devel` |
| `refactor/*` | Refatorações | `devel` |
| `hotfix/*` | Correções urgentes em produção | `main` (e depois `devel`) |

### Nomenclatura de branches

```bash
# Features
feat/adicionar-login-social
feat/contexto-semanal-2.0
feat/insta-api

# Fixes
fix/corrigir-validacao-email
fix/onboarding-data-persistence

# Refatorações
refactor/solid-dry-cto-review

# Hotfixes (urgente, vai direto para main)
hotfix/corrigir-falha-pagamento

# Outros
Dashboard-2.0
onboarding-2.1
```

---

## Convenção de Commits

Utilizamos **Gitmoji + Conventional Commits**:

```
<tipo>: <emoji> <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos de commit com Gitmoji

| Tipo | Emoji | Código | Descrição | Versão |
|------|-------|--------|-----------|--------|
| `feat` | ✨ | `:sparkles:` | Nova funcionalidade | MINOR |
| `fix` | 🐛 | `:bug:` | Correção de bug | PATCH |
| `docs` | 📝 | `:memo:` | Documentação | - |
| `style` | 🎨 | `:art:` | Formatação/estrutura de código | - |
| `refactor` | ♻️ | `:recycle:` | Refatoração | - |
| `perf` | ⚡ | `:zap:` | Melhoria de performance | PATCH |
| `test` | ✅ | `:white_check_mark:` | Testes | - |
| `chore` | 🔧 | `:wrench:` | Configurações | - |
| `ci` | 👷 | `:construction_worker:` | CI/CD | - |
| `build` | 📦 | `:package:` | Build/dependências | - |
| `revert` | ⏪ | `:rewind:` | Reverter mudanças | - |
| `wip` | 🚧 | `:construction:` | Trabalho em progresso | - |
| `remove` | 🔥 | `:fire:` | Remover código/arquivos | - |

### Exemplos de commits (padrão da equipe)

```bash
# Feature
feat: :sparkles: Adds fallback email sending to admin users

# Bug fix
fix: :bug: Strips html from text

# Documentação
docs: :memo: Updates .env.example

# Refatoração
refactor: :art: Formats code for proper format

# CI/CD
chore: :construction_worker: Adds devel workflow

# Remover código
refactor: :fire: Removes unused files
```

### Breaking Changes

Para breaking changes, adicione `!` após o tipo:

```bash
feat!: :sparkles: Remove deprecated endpoint /api/v1/old

BREAKING CHANGE: endpoint removido, usar /api/v2/new
```

---

## Workflow de Desenvolvimento

### 1. Criar branch a partir de devel

```bash
git checkout devel
git pull origin devel
git checkout -b feat/minha-feature
```

### 2. Desenvolver e commitar

```bash
# Commits pequenos e frequentes
git add .
git commit -m "feat: :sparkles: Implementa funcionalidade X"
```

### 3. Abrir Pull Request para devel

```bash
git push origin feat/minha-feature
# Abrir PR: feat/minha-feature → devel
```

### 4. Code Review

- Mínimo 1 aprovação obrigatória
- CI deve passar (UI: lint, typecheck, test, build)
- Resolver conflitos se houver

### 5. Merge para devel

- Squash merge para manter histórico limpo
- Feature integrada em devel

### 6. Release para main

Quando devel estiver estável:

```bash
git checkout main
git merge devel
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --tags
```

---

## Releases

### Fluxo de Release

```
feat/X ──┐
feat/Y ──┼──► devel ──► main ──► tag v1.x.0 ──► Release automática
fix/Z  ──┘
```

### Criando uma release

1. **Garantir que devel está estável**
2. **Merge devel → main**:
```bash
git checkout main
git pull origin main
git merge devel
```

3. **Criar tag**:
```bash
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags
```

4. **Release automática**: O workflow cria a release no GitHub automaticamente com changelog.

### Hotfix (correção urgente)

```bash
# 1. Branch a partir de main
git checkout main
git checkout -b hotfix/corrigir-bug-critico

# 2. Fix
git commit -m "fix: :bug: Corrige bug crítico em produção"

# 3. PR direto para main
git push origin hotfix/corrigir-bug-critico
# Abrir PR: hotfix/corrigir-bug-critico → main

# 4. Após merge, criar tag
git checkout main
git pull
git tag -a v1.2.1 -m "Hotfix v1.2.1"
git push origin v1.2.1

# 5. Sincronizar hotfix com devel
git checkout devel
git merge main
git push origin devel
```

---

## Exemplos Práticos

### Cenário 1: Nova feature

```bash
# 1. Criar branch a partir de devel
git checkout devel
git pull origin devel
git checkout -b feat/exportar-pdf

# 2. Desenvolver e commitar
git commit -m "feat: :sparkles: Adiciona botão de exportar PDF"
git commit -m "feat: :sparkles: Implementa geração de PDF"
git commit -m "test: :white_check_mark: Adiciona testes unitários"

# 3. Push e PR para devel
git push origin feat/exportar-pdf
# Abrir PR: feat/exportar-pdf → devel

# 4. Após review e merge, feature está em devel
# 5. Quando for fazer release, merge devel → main + tag
```

### Cenário 2: Bug fix normal

```bash
# 1. Branch a partir de devel
git checkout devel
git checkout -b fix/validacao-email

# 2. Fix
git commit -m "fix: :bug: Corrige validação de email duplicado"

# 3. PR para devel
git push origin fix/validacao-email
# Abrir PR: fix/validacao-email → devel
```

### Cenário 3: Hotfix urgente em produção

```bash
# 1. Branch direto de main (não de devel!)
git checkout main
git checkout -b hotfix/falha-pagamento

# 2. Fix urgente
git commit -m "fix: :bug: Corrige falha crítica no pagamento"

# 3. PR direto para main (bypass devel)
git push origin hotfix/falha-pagamento
# Abrir PR: hotfix/falha-pagamento → main

# 4. Após merge, tag de patch
git tag -a v1.2.1 -m "Hotfix v1.2.1"
git push origin v1.2.1

# 5. Não esquecer de sincronizar com devel!
git checkout devel
git merge main
git push origin devel
```

---

## Sincronização entre Repositórios

Para manter **PostNow-REST-API** e **PostNow-UI** sincronizados:

| API Version | UI Version | Notas |
|-------------|------------|-------|
| v1.0.0 | v1.0.0 | Release inicial |
| v1.1.0 | v1.1.0 | Nova feature X |
| v1.1.0 | v1.2.0 | UI-only: melhorias visuais |
| v1.2.0 | v1.3.0 | API: novo endpoint Y |

**Regra**: O número MAJOR deve ser igual para garantir compatibilidade.

---

## Checklist de Release

- [ ] Todas as features/fixes em devel estão testadas
- [ ] CI passando em devel
- [ ] Merge devel → main feito
- [ ] Tag criada com padrão `v{MAJOR}.{MINOR}.{PATCH}`
- [ ] Release automática gerada no GitHub
- [ ] Deploy em produção verificado
- [ ] devel sincronizado com main (se houve hotfix)
- [ ] Comunicar equipe sobre a release

---

## Branch Protection

### main
- ✅ PR obrigatório
- ✅ 1 aprovação mínima
- ✅ Dismiss stale reviews
- ✅ CI obrigatório (UI)
- ❌ Force push bloqueado

### devel
- ✅ PR obrigatório
- ✅ 1 aprovação mínima

---

## Referências

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Gitmoji](https://gitmoji.dev/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
