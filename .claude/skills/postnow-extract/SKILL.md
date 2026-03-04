---
name: postnow-extract
description: Extrai funções de views para utils ou services. Use quando CTO pedir para mover código.
argument-hint: <função> <destino: utils|services>
disable-model-invocation: true
---

# PostNow Extract

Extraio funções de views.py para o local apropriado seguindo padrões do CTO.

## Argumentos

- `$0` - Nome da função a extrair
- `$1` - Destino: `utils` ou `services`

Exemplo: `/postnow-extract format_date utils`

## Quando usar cada destino

### `utils/` - Funções auxiliares
- Formatação de dados
- Validações genéricas
- Manipulação de strings/datas
- Helpers reutilizáveis
- Funções puras (sem side effects)

### `services/` - Lógica de negócio
- Processamento de dados
- Regras de negócio
- Integrações com APIs externas
- Operações de banco complexas
- Classes com estado

## Processo de Extração

1. **Localizo** a função `$0` no arquivo origem
2. **Analiso** dependências (imports, outras funções)
3. **Crio/atualizo** arquivo em `$1/`
4. **Movo** a função com seus imports
5. **Atualizo** imports no arquivo origem
6. **Verifico** que não quebrou nada

## Verificação Pós-Extração

Após mover, executo:
```bash
python -c "from <module>.$1.<arquivo> import $0; print('OK')"
```

Se falhar, reverto e reporto o erro.

## Estrutura Criada

### Para utils/
```python
# utils/nome_utils.py
"""Utilitários para [descrição]."""

def funcao_extraida(args):
    """Descrição da função."""
    ...
```

### Para services/
```python
# services/nome_service.py
"""Service para [descrição]."""

class NomeService:
    """Gerencia [descrição]."""

    def metodo(self, args):
        ...
```

## Dicas

- Se a função usa `self`, provavelmente é `services`
- Se a função é pura (sem side effects), provavelmente é `utils`
- Se tem mais de 50 linhas, considere dividir antes de extrair
