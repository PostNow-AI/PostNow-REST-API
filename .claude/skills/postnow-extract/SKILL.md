---
name: postnow-extract
description: Extrai funções de views para utils ou services. Use quando CTO pedir para mover código.
argument-hint: [função] [destino: utils|services]
---

# PostNow Extract

Extraio funções de views.py para o local apropriado seguindo padrões do CTO.

## Como usar

```
/postnow-extract <nome_função> <destino>
```

Exemplos:
- `/postnow-extract format_date utils` - Move helper para utils
- `/postnow-extract create_post services` - Move lógica para services
- `/postnow-extract` - Analiso o arquivo e sugiro extrações

## Quando usar cada destino

### `utils/` - Funções auxiliares
Use para:
- Formatação de dados
- Validações genéricas
- Manipulação de strings/datas
- Helpers reutilizáveis
- Funções puras (sem side effects)

### `services/` - Lógica de negócio
Use para:
- Processamento de dados
- Regras de negócio
- Integrações com APIs externas
- Operações de banco complexas
- Classes com estado

## Processo de Extração

1. **Identifico** a função no arquivo origem
2. **Determino** dependências (imports, outras funções)
3. **Crio/atualizo** arquivo destino com estrutura correta
4. **Movo** a função com seus imports necessários
5. **Atualizo** imports no arquivo origem
6. **Verifico** que não quebrou nada

## Estrutura Criada

### Para utils/
```python
# utils/nome_utils.py
"""
Utilitários para [descrição].
"""

def funcao_extraida(args):
    """Descrição da função."""
    ...
```

### Para services/
```python
# services/nome_service.py
"""
Service para [descrição].
"""

class NomeService:
    """Gerencia [descrição]."""

    def metodo_extraido(self, args):
        """Descrição do método."""
        ...
```

## Exemplo Completo

**Antes** (`views.py`):
```python
from django.http import JsonResponse

def my_view(request):
    # Helper que deveria estar em utils
    def format_response(data):
        return {'status': 'ok', 'data': data}

    # 60 linhas de lógica de negócio
    result = complex_business_logic()

    return JsonResponse(format_response(result))
```

**Depois**:

`utils/response_utils.py`:
```python
def format_response(data):
    """Formata resposta padrão da API."""
    return {'status': 'ok', 'data': data}
```

`services/my_service.py`:
```python
class MyService:
    def process(self):
        """Executa lógica de negócio."""
        # 60 linhas de lógica aqui
        return result
```

`views.py`:
```python
from django.http import JsonResponse
from .utils.response_utils import format_response
from .services.my_service import MyService

def my_view(request):
    service = MyService()
    result = service.process()
    return JsonResponse(format_response(result))
```

## Dicas

- Se a função usa `self`, provavelmente é `services`
- Se a função é pura (sem side effects), provavelmente é `utils`
- Se tem mais de 50 linhas, considere dividir antes de extrair
- Mantenha funções relacionadas no mesmo arquivo
