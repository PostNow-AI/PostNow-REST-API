# Proposta: Proteção da Branch Devel e Limpeza de Branches

**Data:** Fevereiro 2026
**Autor:** Equipe de Engenharia
**Status:** ✅ Aprovado e Executado (2026-02-26)
**Aprovado por:** MatheusBlanco (CTO)

---

## 1. Proteção da Branch `devel`

### Contexto

Atualmente apenas a branch `main` possui proteção configurada. A branch `devel` é usada como branch de desenvolvimento/integração, mas aceita commits diretos e merges sem revisão.

### Proposta

Configurar proteção na branch `devel` com as seguintes regras:

| Regra | Valor |
|-------|-------|
| Require pull request | ✅ Sim |
| Required approvals | 1 |
| Dismiss stale reviews | ✅ Sim |
| Enforce for admins | ✅ Sim |
| Allow force pushes | ❌ Não |

### Benefícios

- Code review obrigatório antes de integrar em devel
- Histórico mais limpo e rastreável
- Menos bugs chegando em devel
- Padrão consistente com main

### Impacto

- Features precisarão de aprovação antes de ir para devel
- Processo ligeiramente mais lento, mas mais seguro

### Comando para aplicar (após aprovação)

```bash
# REST-API
gh api repos/PostNow-AI/PostNow-REST-API/branches/devel/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

# UI
gh api repos/PostNow-AI/PostNow-UI/branches/devel/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

---

## 2. Limpeza de Branches Obsoletas

### Contexto

Existem branches que não recebem commits há mais de 60 dias. Manter branches obsoletas:
- Polui a lista de branches
- Dificulta encontrar branches ativas
- Pode causar confusão sobre o que está em desenvolvimento

### Branches Candidatas a Deleção

#### PostNow-REST-API

| Branch | Último Commit | Dias sem atividade | Recomendação |
|--------|---------------|-------------------|--------------|
| `docs/analytics-bandits` | 2025-12-17 | ~70 dias | ⚠️ Avaliar |
| `feat/Rogerio` | 2025-12-17 | ~70 dias | ⚠️ Avaliar |
| `feat/radar` | 2025-12-22 | ~65 dias | ⚠️ Avaliar |
| `feature/campaigns-mvp` | 2026-01-05 | ~52 dias | ⚠️ Avaliar |
| `carousel-mvp` | 2026-01-06 | ~51 dias | ⚠️ Avaliar |

#### PostNow-UI

| Branch | Último Commit | Dias sem atividade | Recomendação |
|--------|---------------|-------------------|--------------|
| `POC/Rogerio` | 2025-12-05 | ~83 dias | ⚠️ Avaliar |
| `feat/Rogerio` | 2025-12-17 | ~71 dias | ⚠️ Avaliar |
| `feat/radar` | 2026-01-06 | ~51 dias | ⚠️ Avaliar |

### Ações Possíveis

Para cada branch, o CTO pode decidir:

1. **Deletar** - Branch não é mais necessária
2. **Manter** - Trabalho ainda será retomado
3. **Arquivar** - Criar tag antes de deletar para preservar histórico

### Comando para deletar (após aprovação individual)

```bash
# Exemplo: deletar branch específica
gh api repos/PostNow-AI/PostNow-REST-API/git/refs/heads/NOME_DA_BRANCH --method DELETE

# ou via git
git push origin --delete NOME_DA_BRANCH
```

---

## 3. Checklist de Aprovação

### Proteção da devel

- [x] CTO aprova configurar proteção na `devel` do REST-API ✅ Executado
- [x] CTO aprova configurar proteção na `devel` do UI ✅ Executado

### Branches REST-API

- [x] `docs/analytics-bandits` - ✅ Deletada
- [x] `feat/Rogerio` - ✅ Deletada
- [x] `feat/radar` - ✅ Deletada
- [x] `feature/campaigns-mvp` - ✅ Deletada
- [x] `carousel-mvp` - ✅ Deletada

### Branches UI

- [x] `POC/Rogerio` - ✅ Deletada
- [x] `feat/Rogerio` - ✅ Deletada
- [x] `feat/radar` - ✅ Deletada

---

**Aprovação:**

| Nome | Cargo | Data | Assinatura |
|------|-------|------|------------|
| MatheusBlanco | CTO | 2026-02-26 | PR #35 aprovado |

---

*Documento gerado em Fevereiro/2026*
