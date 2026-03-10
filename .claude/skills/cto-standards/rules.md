# Regras do CTO PostNow (MatheusBlanco)

Extraídas dos PRs #12, #24 e #40.

---

## 1. Organização de Código

### Views devem ser enxutas
- Views NÃO devem conter funções auxiliares
- Views NÃO devem ter lógica de negócio complexa
- Views devem apenas: receber request, chamar service, retornar response

### Funções auxiliares vão em `utils/`
Exemplos de funções para utils:
- Formatação de dados
- Validações genéricas
- Manipulação de strings/datas
- Helpers reutilizáveis

```python
# ERRADO - helper dentro de views.py
def my_view(request):
    def format_date(d):  # ❌ Não faça isso
        return d.strftime('%Y-%m-%d')
    ...

# CERTO - helper em utils/
# utils/date_utils.py
def format_date(d):  # ✅ Correto
    return d.strftime('%Y-%m-%d')

# views.py
from .utils.date_utils import format_date
```

### Lógica de negócio vai em `services/`
Exemplos de código para services:
- Processamento de dados
- Regras de negócio
- Integrações com APIs externas
- Operações complexas de banco

```python
# ERRADO - lógica em views.py
def create_post_view(request):
    # 50 linhas de lógica de negócio ❌
    ...

# CERTO - lógica em services/
# services/post_service.py
class PostService:
    def create_post(self, data):
        # Lógica aqui ✅
        ...

# views.py
def create_post_view(request):
    service = PostService()
    result = service.create_post(request.data)
    return Response(result)
```

### Tamanho de funções
- Funções NÃO devem ter mais de 50 linhas
- Se passou de 50 linhas, extrair para funções menores
- Cada função deve ter UMA responsabilidade

---

## 2. Padrões Django

### Import do User
```python
# ERRADO
from django.conf import settings
User = settings.AUTH_USER_MODEL  # ❌

# CERTO
from django.contrib.auth.models import User  # ✅
```

### URLs semânticas
```python
# ERRADO
path('api/data/', ...)  # ❌ Genérico demais

# CERTO
path('api/analytic-events/', ...)  # ✅ Descritivo
path('api/user-preferences/', ...)  # ✅ Descritivo
```

---

## 3. Documentação

### NÃO criar docs por PR/bugfix
```
# ERRADO
docs/
├── PR12_fix_login.md  ❌
├── PR24_add_styles.md  ❌
└── FIX_email_bug.md  ❌

# CERTO
docs/
├── authentication.md  ✅ (doc geral de auth)
├── email_system.md  ✅ (doc geral de email)
└── visual_styles.md  ✅ (doc geral de estilos)
```

### Atualizar docs existentes
1. Buscar se já existe doc da funcionalidade
2. Atualizar seções relevantes
3. Só criar novo doc se for feature completamente nova

### Evitar poluição
- Documentação excessiva dificulta leitura
- Manter docs concisos e focados
- Preferir código auto-documentado

---

## 4. Código Limpo

### Imports
- Remover imports não utilizados
- Ordenar imports:
  1. Standard library
  2. Django
  3. Third-party
  4. Local

```python
# CERTO - ordenado
import os
import json

from django.http import JsonResponse
from django.views import View

from rest_framework.views import APIView

from .models import Post
from .services import PostService
```

### Exception handling
```python
# ERRADO
try:
    ...
except:
    pass  # ❌ Silencia erros sem explicação

# CERTO
try:
    ...
except SpecificException:
    pass  # Ignorado intencionalmente porque X ✅
```

---

## 5. Estrutura de Projeto

### Onde colocar cada coisa

| Tipo de código | Local |
|----------------|-------|
| Endpoints HTTP | `views.py` |
| Lógica de negócio | `services/` |
| Funções auxiliares | `utils/` |
| Modelos de dados | `models.py` |
| Serialização | `serializers.py` |
| Configuração de URLs | `urls.py` |

### Estrutura recomendada de app
```
app/
├── models.py
├── views.py
├── urls.py
├── serializers.py
├── services/
│   ├── __init__.py
│   └── feature_service.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── tests/
    └── test_feature.py
```

---

## Checklist Rápido

Antes de criar PR, verificar:

- [ ] Views têm < 50 linhas cada?
- [ ] Funções auxiliares estão em utils/?
- [ ] Lógica de negócio está em services/?
- [ ] Import do User está correto?
- [ ] URLs são semânticas?
- [ ] Não criei doc por PR/bugfix?
- [ ] Imports não utilizados removidos?
- [ ] Sem `except: pass` sem comentário?
