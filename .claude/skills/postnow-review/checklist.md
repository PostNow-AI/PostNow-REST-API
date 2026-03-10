# Checklist de Review PostNow

Use este checklist para validar código antes de criar PR.

## Organização

| # | Item | Passa? |
|---|------|--------|
| 1 | Views têm < 50 linhas cada | |
| 2 | Funções auxiliares em `utils/` | |
| 3 | Lógica de negócio em `services/` | |
| 4 | Views apenas: request → service → response | |

## Django

| # | Item | Passa? |
|---|------|--------|
| 5 | `from django.contrib.auth.models import User` | |
| 6 | URLs semânticas (não `/api/data/`) | |
| 7 | Serializers para validação de dados | |

## Código Limpo

| # | Item | Passa? |
|---|------|--------|
| 8 | Sem imports não utilizados | |
| 9 | Sem `except: pass` sem comentário | |
| 10 | Imports ordenados | |

## Documentação

| # | Item | Passa? |
|---|------|--------|
| 11 | Não criou `docs/PR*.md` ou `docs/FIX*.md` | |
| 12 | Atualizou doc existente (se aplicável) | |

---

## Ações por Problema

| Problema | Ação |
|----------|------|
| Função > 50 linhas | `/postnow-extract [func] services` |
| Helper em views | `/postnow-extract [func] utils` |
| Import incorreto | `/postnow-imports [arquivo]` |
| Doc por PR | Deletar e atualizar doc geral |
