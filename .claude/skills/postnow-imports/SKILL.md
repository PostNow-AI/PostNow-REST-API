---
name: postnow-imports
description: Corrige imports Django e remove não utilizados. Use para organizar imports conforme padrões.
argument-hint: [arquivo.py]
---

# PostNow Imports

Organizo e corrijo imports seguindo padrões Django e do CTO.

## Argumentos

`$ARGUMENTS` - Arquivo(s) a corrigir

Exemplos:
- `/postnow-imports views.py`
- `/postnow-imports app/`
- `/postnow-imports` (arquivos modificados no git)

## O que corrijo

### 1. Import do User
```python
# ERRADO
from django.conf import settings
User = settings.AUTH_USER_MODEL

# CERTO
from django.contrib.auth.models import User
```

### 2. Imports não utilizados
Removo imports que não são usados no arquivo.

### 3. Ordem dos imports
Organizo na ordem:
1. Standard library (`os`, `json`, `datetime`)
2. Django (`django.*`)
3. Third-party (`rest_framework`, `celery`)
4. Local (`.models`, `.services`)

## Processo

1. **Leio** o arquivo `$ARGUMENTS`
2. **Identifico** todos os imports
3. **Analiso** quais são usados no código
4. **Corrijo** import do User se necessário
5. **Removo** imports não utilizados
6. **Reordeno** imports por categoria
7. **Aplico** mudanças

## Exemplo de Correção

**Antes:**
```python
from .models import Post
import json
from django.conf import settings
from rest_framework.views import APIView
import os  # não usado
```

**Depois:**
```python
import json

from django.contrib.auth.models import User

from rest_framework.views import APIView

from .models import Post
```

## Verificação

Após corrigir, confirmo que o arquivo ainda é válido:
```bash
python -m py_compile $ARGUMENTS
```

## Integração

- Use após `/postnow-extract` para limpar imports órfãos
- Use antes de `/postnow-review` para já ter imports corretos
