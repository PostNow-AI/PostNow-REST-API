---
name: postnow-review
description: Revisa código seguindo padrões do CTO PostNow (MatheusBlanco). Use ANTES de criar PRs para evitar revisões.
argument-hint: [arquivo ou diretório]
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

# PostNow Code Review

Reviso o código seguindo os padrões do CTO para evitar feedback nos PRs.

## Arquivos a revisar

$ARGUMENTS

Se nenhum arquivo foi especificado, analiso os arquivos modificados listados abaixo.

## Contexto Git (automático)

**Arquivos modificados:**
!`git diff --name-only 2>/dev/null || echo "Nenhum arquivo modificado"`

**Branch atual:**
!`git branch --show-current 2>/dev/null || echo "N/A"`

## Checklist de Verificação

Leia o arquivo [checklist.md](checklist.md) para ver todos os itens.

### Resumo do checklist:

1. **Organização de Código**
   - Funções em views.py têm < 50 linhas?
   - Funções auxiliares estão em `utils/`?
   - Lógica de negócio está em `services/`?

2. **Padrões Django**
   - Import do User: `from django.contrib.auth.models import User`?
   - URLs são semânticas?

3. **Código Limpo**
   - Imports não utilizados removidos?
   - Sem `except: pass` sem comentário?
   - Imports organizados?

4. **Documentação**
   - Não criou doc por PR/bugfix?

## Processo

1. Identifico os arquivos a revisar
2. Leio cada arquivo
3. Verifico cada item do checklist
4. Reporto problemas com:
   - Arquivo e linha exata
   - Problema específico
   - Comando para corrigir (ex: `/postnow-extract func utils`)

## Referência

Regras completas em [../cto-standards/rules.md](../cto-standards/rules.md)

## Output esperado

```markdown
## Review: [arquivo]

### Problemas encontrados

1. **Linha X**: [problema]
   - Correção: [sugestão]
   - Comando: `/postnow-extract [func] [destino]`

### Checklist
- [x] URLs semânticas
- [ ] Funções < 50 linhas (N violações)
```
