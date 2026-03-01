# Relatório de Conformidade de Versionamento

**Data:** 01/03/2026
**Versão:** v1.0.1

---

## Status de Conformidade

| Aspecto | Status |
|---------|--------|
| Entregas Atuais (PRs) | Conforme |
| Conventional Commits | Conforme |
| Branch Naming | Conforme |
| Documentação | Conforme |

---

## Versão Atual

- **Versão:** v1.0.1 (PATCH)
- **Tipo:** Bug Fixes
- **Mudanças:** 5 correções de bugs no onboarding

---

## Padrões Implementados

### 1. Branch Naming Convention

Padrão obrigatório para novos branches:

```
feature/*  - Novas funcionalidades
fix/*      - Correções de bugs
docs/*     - Documentação
refactor/* - Refatoração de código
test/*     - Testes
chore/*    - Manutenção
hotfix/*   - Correções urgentes
```

**Nota:** `feat/*` está deprecado. Use `feature/*`.

### 2. Conventional Commits

Formato obrigatório para commits:

```
type(scope): description
type(scope): :emoji: description
type: description
```

Tipos válidos:
- `feat` - Nova funcionalidade
- `fix` - Correção de bug
- `docs` - Documentação
- `style` - Formatação
- `refactor` - Refatoração
- `perf` - Performance
- `test` - Testes
- `build` - Build
- `ci` - CI/CD
- `chore` - Manutenção
- `revert` - Reverter commit

### 3. Gitmoji (Opcional)

Emojis comuns:
- `:sparkles:` - Nova feature
- `:bug:` - Bug fix
- `:memo:` - Documentação
- `:recycle:` - Refactoring
- `:white_check_mark:` - Testes
- `:bookmark:` - Release

---

## Ferramentas Instaladas

### Scripts

| Script | Descrição |
|--------|-----------|
| `scripts/release.sh` | Cria releases automatizados |
| `scripts/commit-msg` | Hook de validação de commits |
| `scripts/install-hooks.sh` | Instala git hooks |

### GitHub Actions

| Workflow | Descrição |
|----------|-----------|
| `branch-validation.yml` | Valida nomes de branches em PRs |

---

## Próximos Passos

1. [ ] Instalar hooks localmente: `./scripts/install-hooks.sh`
2. [ ] Ativar branch protection em `main`
3. [ ] Arquivar branches antigos não conformes
4. [ ] Após merge dos PRs, criar tag: `git tag -a v1.0.1 -m "Release v1.0.1"`

---

## Histórico de Releases

| Versão | Data | Tipo | Descrição |
|--------|------|------|-----------|
| v1.0.1 | 2026-03-01 | PATCH | Bugfix onboarding step tracking |
| v1.0.0 | - | MAJOR | Release inicial |
