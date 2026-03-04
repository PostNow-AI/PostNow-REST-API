---
name: postnow-imports
description: Corrige imports Django e remove não utilizados. Use para organizar imports conforme padrões.
---

# PostNow Imports

Organizo e corrijo imports seguindo padrões Django e do CTO.

## Como usar

```
/postnow-imports [arquivo]
```

Exemplos:
- `/postnow-imports` - Corrige todos os arquivos Python modificados
- `/postnow-imports views.py` - Corrige arquivo específico
- `/postnow-imports app/` - Corrige diretório

## O que corrijo

### 1. Import do User
```python
# ERRADO
from django.conf import settings
User = settings.AUTH_USER_MODEL

# ERRADO
from django.conf import settings
user_model = settings.AUTH_USER_MODEL

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

## Exemplo

**Antes:**
```python
from .models import Post
import json
from django.conf import settings
from rest_framework.views import APIView
from django.http import JsonResponse
import os
from .utils import unused_function  # não usado
from django.views import View

User = settings.AUTH_USER_MODEL

class MyView(APIView):
    def get(self, request):
        user = User.objects.get(id=1)
        data = json.loads(request.body)
        return JsonResponse({'user': user.username})
```

**Depois:**
```python
import json

from django.contrib.auth.models import User
from django.http import JsonResponse

from rest_framework.views import APIView

from .models import Post


class MyView(APIView):
    def get(self, request):
        user = User.objects.get(id=1)
        data = json.loads(request.body)
        return JsonResponse({'user': user.username})
```

## Mudanças feitas:
1. Removido `import os` (não usado)
2. Removido `from .utils import unused_function` (não usado)
3. Removido `from django.views import View` (não usado)
4. Corrigido import do User
5. Removido `from django.conf import settings` (só era usado para User)
6. Ordenado imports por categoria
7. Adicionado espaçamento entre categorias

## Processo

1. **Leio** o arquivo
2. **Identifico** todos os imports
3. **Analiso** quais são usados no código
4. **Corrijo** import do User se necessário
5. **Removo** imports não utilizados
6. **Reordeno** imports por categoria
7. **Aplico** mudanças

## Integração com outras skills

Use após `/postnow-extract` para limpar imports órfãos.

Use antes de `/postnow-review` para já ter imports corretos.
