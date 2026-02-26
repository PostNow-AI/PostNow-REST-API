# Proposta: Implementação de Versionamento Profissional

**Data:** Fevereiro 2026
**Autor:** Equipe de Engenharia
**Status:** Aguardando aprovação

---

## Sumário Executivo

Esta proposta apresenta um plano de implementação gradual de versionamento semântico para os repositórios **PostNow-REST-API** e **PostNow-UI**, visando maior rastreabilidade, previsibilidade de releases e comunicação clara entre equipes.

A implementação foi projetada para **zero interrupção** no fluxo atual de trabalho, com adoção incremental.

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

### 1.2 Problemas Identificados

1. **Sem rastreabilidade de versões**
   - Impossível saber qual versão está em produção
   - Difícil identificar quando um bug foi introduzido

2. **Comunicação entre equipes prejudicada**
   - Backend e Frontend sem sincronização clara
   - QA não sabe o que testar em cada release

3. **Ausência de changelog**
   - Clientes não sabem das novidades
   - Suporte não tem referência de mudanças

### 1.3 Pontos Positivos

- Deploy automático funcionando
- Equipe já utiliza parcialmente Conventional Commits
- Workflows de automação bem estruturados

---

## 2. Solução Proposta

### 2.1 Visão Geral

Implementar **Semantic Versioning (SemVer)** com **GitHub Flow**:

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

---

## 3. Plano de Implementação

### Fase 1: Documentação

**Status:** PRs abertos aguardando aprovação

| Tarefa | PR |
|--------|-----|
| Guia de versionamento (REST-API) | #30 |
| Guia de versionamento (UI) | #26 |

### Fase 2: Templates e CI/CD

**Status:** PRs abertos aguardando aprovação

| Tarefa | PR |
|--------|-----|
| Templates + Workflow release (REST-API) | #31 |
| Templates + CI + Workflow release (UI) | #27 |

### Fase 3: Tags e Releases

Após merge dos PRs anteriores:

```bash
# Criar primeira release oficial
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Fase 4: Branch Protection

Configurar no GitHub (Settings > Branches):

- Require pull request before merging
- Require 1 approval
- Require status checks to pass

### Fase 5: Adoção pela Equipe

- Comunicar padrão de commits
- Treinar equipe no novo fluxo
- Monitorar e ajustar conforme necessário

---

## 4. Cronograma

```
Semana 1              Semana 2              Semana 3
────────              ────────              ────────
    │                     │                     │
    ▼                     ▼                     ▼
┌────────────┐      ┌────────────┐      ┌────────────┐
│ Aprovar    │      │ Tags       │      │ Branch     │
│ PRs        │ ───► │ v1.0.0     │ ───► │ Protection │
│ pendentes  │      │            │      │            │
└────────────┘      └────────────┘      └────────────┘
```

---

## 5. Métricas de Sucesso

| Métrica | Antes | Meta |
|---------|-------|------|
| Versões taggeadas | 0 | 100% das releases |
| PRs com review | ~50% | 100% |
| Commits padronizados | ~60% | 100% |

---

## 6. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Resistência da equipe | Adoção gradual + treinamento |
| Atraso em entregas | Período de adaptação flexível |

---

## 7. Investimento

- **Tempo de configuração:** ~4 horas
- **Custo de infraestrutura:** $0 (GitHub Actions gratuito)

---

## 8. Próximos Passos

Após aprovação:

1. Merge dos PRs de documentação (#30, #26)
2. Merge dos PRs de templates/CI (#31, #27)
3. Criar tags v1.0.0 em ambos repos
4. Configurar branch protection
5. Comunicar equipe

---

## 9. PRs Relacionados

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
