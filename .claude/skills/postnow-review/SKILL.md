---
name: postnow-review
description: Revisa código seguindo padrões do CTO PostNow (MatheusBlanco). Use ANTES de criar PRs para evitar revisões.
allowed-tools: Read, Grep, Glob
---

# PostNow Code Review

Reviso o código seguindo os padrões do CTO para evitar feedback nos PRs.

## Como usar

```
/postnow-review [arquivo ou diretório]
```

Exemplos:
- `/postnow-review` - Revisa arquivos modificados (git diff)
- `/postnow-review views.py` - Revisa arquivo específico
- `/postnow-review app/` - Revisa diretório

## O que verifico

### 1. Organização de Código
- [ ] Funções em views.py têm < 50 linhas?
- [ ] Funções auxiliares estão em `utils/`?
- [ ] Lógica de negócio está em `services/`?
- [ ] Views são enxutas (recebe, processa, retorna)?

### 2. Padrões Django
- [ ] Import do User: `from django.contrib.auth.models import User`?
- [ ] URLs são semânticas (não genéricas como `/api/data/`)?

### 3. Código Limpo
- [ ] Imports não utilizados removidos?
- [ ] Sem `except: pass` sem comentário?
- [ ] Imports organizados (stdlib, django, third-party, local)?

### 4. Documentação
- [ ] Não criou doc por PR/bugfix?
- [ ] Atualizou doc existente ao invés de criar novo?

## Processo de Review

1. Identifico os arquivos a revisar (modificados ou especificados)
2. Leio cada arquivo
3. Verifico cada item do checklist
4. Reporto problemas encontrados com:
   - Arquivo e linha
   - Problema específico
   - Sugestão de correção
5. Sugiro uso de outras skills quando aplicável:
   - `/postnow-extract` para mover funções
   - `/postnow-imports` para corrigir imports

## Exemplo de Output

```
## Review: app/views.py

### Problemas encontrados

1. **Linha 45-120**: Função `create_post` muito grande (75 linhas)
   - Extrair lógica para `services/post_service.py`
   - Use: `/postnow-extract create_post services`

2. **Linha 12**: Import do User incorreto
   - Atual: `from django.conf import settings`
   - Correto: `from django.contrib.auth.models import User`
   - Use: `/postnow-imports app/views.py`

3. **Linha 30-42**: Função auxiliar `format_date` em views
   - Mover para `utils/date_utils.py`
   - Use: `/postnow-extract format_date utils`

### Checklist
- [x] URLs semânticas
- [ ] Funções < 50 linhas (1 violação)
- [ ] Helpers em utils (1 violação)
- [ ] Import User correto (1 violação)
```

## Referência

Consulte as regras completas em:
`/postnow-review/../cto-standards/rules.md`
