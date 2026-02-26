# Proposta: Implementação de Versionamento Profissional

**Data:** Fevereiro 2026
**Autor:** Equipe de Engenharia
**Status:** Aguardando aprovação

---

## Sumário Executivo

Esta proposta apresenta um plano de implementação gradual de versionamento semântico para os repositórios **PostNow-REST-API** e **PostNow-UI**, visando maior rastreabilidade, previsibilidade de releases e comunicação clara entre equipes.

A implementação foi projetada para **zero interrupção** no fluxo atual de trabalho, com adoção incremental ao longo de 4 semanas.

---

## 1. Diagnóstico: Cenário Atual

### 1.1 Estado dos Repositórios

| Aspecto | PostNow-REST-API | PostNow-UI |
|---------|------------------|------------|
| **Branch principal** | `main` | `main` |
| **Branches secundárias** | Nenhuma | Nenhuma |
| **Versionamento** | Inexistente | `0.0.0` (não utilizado) |
| **Tags de release** | Nenhuma | Nenhuma |
| **Padrão de commits** | Parcialmente Conventional Commits | Parcialmente Conventional Commits |
| **Deploy** | Vercel (automático) | Vercel (automático) |
| **CI/CD** | GitHub Actions (crons) | Nenhum |

### 1.2 Problemas Identificados

1. **Sem rastreabilidade de versões**
   - Impossível saber qual versão está em produção
   - Difícil identificar quando um bug foi introduzido
   - Rollback manual e arriscado

2. **Comunicação entre equipes prejudicada**
   - Backend e Frontend sem sincronização clara
   - QA não sabe o que testar em cada release
   - Stakeholders sem visibilidade de progresso

3. **Ausência de changelog**
   - Clientes não sabem das novidades
   - Suporte não tem referência de mudanças
   - Marketing não consegue comunicar updates

4. **Risco operacional**
   - Sem processo formal de release
   - Commits diretos na main sem revisão obrigatória
   - Sem ambiente de staging estruturado

### 1.3 Pontos Positivos (já implementados)

- Deploy automático funcionando
- Equipe já utiliza parcialmente Conventional Commits
- Workflows de automação bem estruturados
- Documentação de versionamento criada (`docs/VERSIONING.md`)

---

## 2. Solução Proposta

### 2.1 Visão Geral

Implementar **Semantic Versioning (SemVer)** com **GitHub Flow** simplificado, aproveitando a infraestrutura existente e adotando práticas incrementalmente.

```
ANTES                           DEPOIS
─────                           ──────
main ─────────────────►         main (v1.2.3) ──────────────►
     commits diretos                    │
                                        ├── feature/nova-func
                                        ├── fix/correcao
                                        └── release/v1.3.0
```

### 2.2 Benefícios Esperados

| Benefício | Impacto |
|-----------|---------|
| **Rastreabilidade** | Saber exatamente o que está em produção |
| **Rollback simplificado** | Reverter para qualquer versão anterior |
| **Comunicação clara** | Changelog automático para stakeholders |
| **Qualidade** | Code review obrigatório antes do merge |
| **Previsibilidade** | Releases planejadas e documentadas |
| **Compatibilidade** | API e UI sincronizadas por versão MAJOR |

---

## 3. Plano de Implementação

### Fase 1: Fundação (Semana 1) ✅ CONCLUÍDA

**Objetivo:** Documentar padrões sem alterar fluxo atual

| Tarefa | Status | Responsável |
|--------|--------|-------------|
| Criar `docs/VERSIONING.md` em ambos repos | ✅ Feito | Engenharia |
| Criar arquivo `VERSION` (REST-API) | ✅ Feito | Engenharia |
| Atualizar `package.json` com v1.0.0 (UI) | ✅ Feito | Engenharia |
| Adicionar scripts de release (UI) | ✅ Feito | Engenharia |

**Resultado:** Documentação disponível, equipe pode consultar.

---

### Fase 2: Tags e Releases (Semana 2)

**Objetivo:** Marcar versão atual e criar primeira release oficial

#### Tarefas

| # | Tarefa | Descrição |
|---|--------|-----------|
| 2.1 | Criar tag v1.0.0 | Marcar estado atual como versão inicial |
| 2.2 | Criar Release no GitHub | Documentar funcionalidades existentes |
| 2.3 | Configurar Release Notes automático | Template para PRs |

#### Comandos a executar

```bash
# PostNow-REST-API
git tag -a v1.0.0 -m "Release v1.0.0 - Versão inicial oficial

Funcionalidades:
- Sistema de autenticação OAuth
- Geração de conteúdo com IA
- Sistema de créditos e assinaturas
- Campanhas de onboarding
- Relatórios de auditoria
- Integração com Stripe"

git push origin v1.0.0

# PostNow-UI
git tag -a v1.0.0 -m "Release v1.0.0 - Versão inicial oficial

Funcionalidades:
- Dashboard completo
- Editor de conteúdo
- Gerenciamento de perfil
- Sistema de assinaturas
- Tema claro/escuro"

git push origin v1.0.0
```

#### Template de Release Notes (criar em `.github/`)

```markdown
## O que há de novo

### Funcionalidades
-

### Correções
-

### Melhorias
-

## Compatibilidade
- API: v1.x.x
- UI: v1.x.x
```

---

### Fase 3: Branch Protection (Semana 2-3)

**Objetivo:** Garantir qualidade com code review obrigatório

#### Configuração no GitHub (Settings > Branches > Branch protection rules)

| Regra | Valor | Motivo |
|-------|-------|--------|
| **Branch name pattern** | `main` | Proteger produção |
| **Require pull request** | ✅ Sim | Evitar commits diretos |
| **Required approvals** | 1 | Code review obrigatório |
| **Dismiss stale reviews** | ✅ Sim | Garantir review atualizado |
| **Require status checks** | ✅ Sim (quando CI existir) | Build deve passar |
| **Include administrators** | ✅ Sim | Todos seguem as regras |

#### Fluxo após configuração

```
Desenvolvedor           GitHub                  Main
     │                     │                      │
     ├── push branch ─────►│                      │
     │                     │                      │
     ├── abre PR ─────────►│                      │
     │                     │                      │
     │◄── review request ──┤                      │
     │                     │                      │
     │   [Code Review]     │                      │
     │                     │                      │
     │◄── aprovação ───────┤                      │
     │                     │                      │
     ├── merge ───────────►├─────────────────────►│
     │                     │                      │
     │                     │    [Auto Deploy]     │
```

---

### Fase 4: Conventional Commits (Semana 3)

**Objetivo:** Padronizar 100% dos commits para changelog automático

#### Ação: Comunicar padrão para equipe

Todos os novos commits devem seguir:

```
<tipo>(<escopo>): <descrição>

Tipos permitidos:
- feat:     nova funcionalidade
- fix:      correção de bug
- docs:     documentação
- style:    formatação
- refactor: refatoração
- perf:     performance
- test:     testes
- chore:    manutenção
```

#### Opcional: Instalar commitlint (validação automática)

```bash
# PostNow-UI
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# Criar commitlint.config.js
echo "module.exports = { extends: ['@commitlint/config-conventional'] };" > commitlint.config.js
```

---

### Fase 5: CI/CD para UI (Semana 3-4)

**Objetivo:** Adicionar validação automática no PostNow-UI

#### Criar `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npx tsc --noEmit

      - name: Test
        run: npm run test:run

      - name: Build
        run: npm run build
```

---

### Fase 6: Releases Automatizadas (Semana 4)

**Objetivo:** Automatizar criação de releases e changelog

#### Opção A: Release manual com script

```bash
# Adicionar ao package.json (UI)
"scripts": {
  "release": "npm version $1 -m 'chore(release): v%s' && git push --follow-tags"
}

# Uso
npm run release minor  # 1.0.0 -> 1.1.0
```

#### Opção B: GitHub Actions para release automática

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        id: changelog
        uses: metcalfc/changelog-generator@v4
        with:
          myToken: ${{ secrets.GITHUB_TOKEN }}

      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          body: ${{ steps.changelog.outputs.changelog }}
```

---

## 4. Cronograma Consolidado

```
Semana 1        Semana 2        Semana 3        Semana 4
────────        ────────        ────────        ────────
   │               │               │               │
   ▼               ▼               ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Fase 1   │  │ Fase 2   │  │ Fase 4   │  │ Fase 6   │
│ Docs ✅  │  │ Tags     │  │ Commits  │  │ Releases │
│          │  │ Release  │  │ Padrão   │  │ Auto     │
└──────────┘  │          │  │          │  │          │
              │ Fase 3   │  │ Fase 5   │  └──────────┘
              │ Branch   │  │ CI/CD    │
              │ Protect  │  │ UI       │
              └──────────┘  └──────────┘

───────────────────────────────────────────────────────►
                                              Sistema
                                            Versionado
```

---

## 5. Métricas de Sucesso

| Métrica | Antes | Meta |
|---------|-------|------|
| Versões taggeadas | 0 | 100% das releases |
| PRs com review | ~50% | 100% |
| Commits padronizados | ~60% | 100% |
| Tempo para rollback | Manual (~30min) | 1 comando (~2min) |
| Changelog disponível | Não | Sim, automático |

---

## 6. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Resistência da equipe | Média | Alto | Treinamento + adoção gradual |
| Atraso em entregas | Baixa | Médio | Fase inicial sem branch protection |
| Commits fora do padrão | Média | Baixo | Período de adaptação antes de bloquear |
| Conflitos de merge | Baixa | Baixo | Branches de vida curta |

---

## 7. Investimento

### Tempo de implementação

| Fase | Esforço |
|------|---------|
| Fase 1 (Docs) | ✅ Concluído |
| Fase 2 (Tags) | 1 hora |
| Fase 3 (Branch Protection) | 30 minutos |
| Fase 4 (Commits) | Comunicação + prática |
| Fase 5 (CI/CD) | 2-3 horas |
| Fase 6 (Releases) | 1-2 horas |

**Total estimado:** ~6 horas de configuração + período de adaptação da equipe

### Custo

- **Infraestrutura:** $0 (GitHub Actions gratuito para repos públicos/privados com limite)
- **Ferramentas:** $0 (todas open-source)

---

## 8. Próximos Passos

Após aprovação desta proposta:

1. **Imediato:** Criar tags v1.0.0 em ambos repositórios
2. **Semana 2:** Configurar branch protection na main
3. **Semana 2:** Comunicar padrão de commits para equipe
4. **Semana 3:** Implementar CI/CD no PostNow-UI
5. **Semana 4:** Automatizar releases

---

## 9. Conclusão

A implementação de versionamento semântico é um investimento de baixo custo com alto retorno em:

- **Qualidade:** Code review obrigatório reduz bugs em produção
- **Visibilidade:** Stakeholders sabem o que está sendo entregue
- **Operação:** Rollback e debugging simplificados
- **Profissionalismo:** Práticas alinhadas com padrões de mercado

A abordagem gradual garante **zero interrupção** no fluxo atual enquanto elevamos a maturidade do processo de desenvolvimento.

---

**Aprovação:**

| Nome | Cargo | Data | Assinatura |
|------|-------|------|------------|
| | CTO | | |
| | Tech Lead | | |

---

*Documento gerado em Fevereiro/2026*
