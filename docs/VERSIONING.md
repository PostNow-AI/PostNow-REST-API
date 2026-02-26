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

Utilizamos **GitHub Flow** adaptado para deploy contínuo:

```
main (produção)
  │
  ├── feature/nova-funcionalidade
  ├── fix/corrigir-bug
  ├── hotfix/correcao-urgente
  └── release/v1.2.0
```

### Branches

| Branch | Propósito | Merge para |
|--------|-----------|------------|
| `main` | Produção (sempre deployável) | - |
| `feature/*` | Novas funcionalidades | `main` |
| `fix/*` | Correções de bugs | `main` |
| `hotfix/*` | Correções urgentes em produção | `main` |
| `release/*` | Preparação de release | `main` |

### Nomenclatura de branches

```bash
# Features
feature/adicionar-login-social
feature/PN-123-nova-dashboard    # Com ticket

# Fixes
fix/corrigir-validacao-email
fix/PN-456-erro-checkout

# Hotfixes (urgente)
hotfix/corrigir-falha-pagamento

# Releases
release/v1.2.0
```

---

## Convenção de Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos de commit

| Tipo | Descrição | Impacto na versão |
|------|-----------|-------------------|
| `feat` | Nova funcionalidade | MINOR |
| `fix` | Correção de bug | PATCH |
| `docs` | Documentação | - |
| `style` | Formatação (não afeta código) | - |
| `refactor` | Refatoração sem mudança de comportamento | - |
| `perf` | Melhoria de performance | PATCH |
| `test` | Adicionar/corrigir testes | - |
| `chore` | Manutenção (deps, configs) | - |
| `ci` | Mudanças em CI/CD | - |

### Breaking Changes

Para breaking changes, adicione `!` após o tipo ou `BREAKING CHANGE:` no rodapé:

```bash
feat!: remover endpoint deprecated /api/v1/old

# ou

feat: novo sistema de autenticação

BREAKING CHANGE: tokens antigos não são mais aceitos
```

### Exemplos de commits

```bash
# Feature simples
feat(auth): adicionar login com Google

# Fix com ticket
fix(checkout): corrigir cálculo de desconto

Closes #123

# Refatoração
refactor(api): extrair lógica de validação para utils

# Breaking change
feat(api)!: migrar endpoints para v2

BREAKING CHANGE: todos os endpoints agora usam /api/v2/
Endpoints v1 serão removidos em 30 dias.
```

---

## Workflow de Desenvolvimento

### 1. Criar branch a partir de main

```bash
git checkout main
git pull origin main
git checkout -b feature/minha-feature
```

### 2. Desenvolver e commitar

```bash
# Commits pequenos e frequentes
git add .
git commit -m "feat(modulo): implementar funcionalidade X"
```

### 3. Abrir Pull Request

```bash
git push origin feature/minha-feature
# Abrir PR no GitHub
```

### 4. Code Review

- Mínimo 1 aprovação
- CI deve passar (se configurado)
- Resolver conflitos se houver

### 5. Merge e Deploy

- Squash merge para manter histórico limpo
- Deploy automático via Vercel

---

## Releases

### Criando uma release

1. **Criar branch de release**:
```bash
git checkout main
git pull origin main
git checkout -b release/v1.2.0
```

2. **Atualizar versão** (se aplicável):

Para **PostNow-UI** (package.json):
```bash
npm version minor  # ou major/patch
```

Para **PostNow-REST-API**, criar/atualizar `VERSION` na raiz:
```bash
echo "1.2.0" > VERSION
```

3. **Criar tag e release no GitHub**:
```bash
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

4. **Criar Release no GitHub**:
   - Ir em Releases > Draft new release
   - Selecionar a tag
   - Gerar release notes automaticamente
   - Publicar

### Changelog automático

O GitHub gera changelogs baseado nos commits. Para isso funcionar bem:
- Use Conventional Commits
- PRs devem ter títulos descritivos

---

## Exemplos Práticos

### Cenário 1: Nova feature

```bash
# 1. Criar branch
git checkout -b feature/adicionar-exportar-pdf

# 2. Desenvolver e commitar
git commit -m "feat(export): adicionar botão de exportar PDF"
git commit -m "feat(export): implementar geração de PDF"
git commit -m "test(export): adicionar testes unitários"

# 3. Push e PR
git push origin feature/adicionar-exportar-pdf
# Abrir PR: "feat: adicionar exportação para PDF"

# 4. Após merge, se for release:
git checkout main
git pull
git tag -a v1.3.0 -m "Release v1.3.0 - Exportação PDF"
git push origin v1.3.0
```

### Cenário 2: Bug fix urgente (hotfix)

```bash
# 1. Criar branch de hotfix
git checkout main
git checkout -b hotfix/corrigir-falha-login

# 2. Fix rápido
git commit -m "fix(auth): corrigir timeout no login social"

# 3. PR com label "hotfix" e merge rápido
git push origin hotfix/corrigir-falha-login

# 4. Tag de patch
git checkout main
git pull
git tag -a v1.2.1 -m "Hotfix v1.2.1"
git push origin v1.2.1
```

### Cenário 3: Breaking change (major release)

```bash
# 1. Branch de release
git checkout -b release/v2.0.0

# 2. Commits com breaking changes
git commit -m "feat(api)!: migrar para novo formato de response

BREAKING CHANGE: estrutura de response alterada.
Antes: { data: [...] }
Agora: { items: [...], meta: {...} }"

# 3. Atualizar documentação de migração
git commit -m "docs: adicionar guia de migração v1 para v2"

# 4. Release
git tag -a v2.0.0 -m "Release v2.0.0 - Nova API"
git push origin v2.0.0
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

**Dica**: Use o mesmo número de versão MAJOR para garantir compatibilidade.

---

## Checklist de Release

- [ ] Todos os PRs da release foram merged
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Versão atualizada (package.json ou VERSION)
- [ ] Tag criada com padrão `v{MAJOR}.{MINOR}.{PATCH}`
- [ ] Release notes geradas no GitHub
- [ ] Deploy em produção verificado
- [ ] Comunicar equipe sobre a release

---

## Referências

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Keep a Changelog](https://keepachangelog.com/)
