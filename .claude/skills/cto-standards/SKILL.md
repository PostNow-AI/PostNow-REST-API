---
name: cto-standards
description: Base de conhecimento com padrões de código do CTO PostNow (MatheusBlanco). Referência para outras skills.
user-invocable: false
---

# Padrões de Código do CTO PostNow

Este skill contém todas as regras e padrões extraídos do feedback do CTO nos PRs.

**Não é invocável diretamente** - serve como referência para outras skills.

## Regras Completas

Veja [rules.md](rules.md) para todas as regras detalhadas com exemplos.

## Resumo Rápido

### Organização
- Views < 50 linhas
- Helpers → `utils/`
- Lógica de negócio → `services/`

### Django
- `from django.contrib.auth.models import User` (não settings.AUTH_USER_MODEL)
- URLs semânticas

### Documentação
- NUNCA criar docs por PR/bugfix
- Atualizar docs existentes

### Código Limpo
- Remover imports não utilizados
- Ordenar imports
- Sem `except: pass` sem comentário
