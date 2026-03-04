# Guia de Skills do Claude Code - PostNow

Este guia explica como usar as skills personalizadas do Claude Code criadas para seguir os padrões de código do CTO (MatheusBlanco).

---

## Skills Disponíveis

| Skill | Comando | Propósito |
|-------|---------|-----------|
| **postnow-review** | `/postnow-review [arquivo]` | Revisa código antes de PR |
| **postnow-extract** | `/postnow-extract <func> <destino>` | Extrai funções para local correto |
| **postnow-docs** | `/postnow-docs <feature>` | Atualiza documentação |
| **postnow-imports** | `/postnow-imports [arquivo]` | Organiza imports |
| **cto-standards** | *(não invocável)* | Base de conhecimento |

---

## Como Usar

### Pré-requisitos

1. Ter o Claude Code instalado
2. Estar no diretório do projeto PostNow

```bash
cd /path/to/PostNow-REST-API
claude
```

### 1. `/postnow-review` - Revisão de Código

**Quando usar:** Antes de criar um PR

```bash
# Revisar arquivos modificados no git
/postnow-review

# Revisar arquivo específico
/postnow-review ClientContext/views.py

# Revisar diretório
/postnow-review ClientContext/
```

**O que verifica:**
- Funções > 50 linhas
- Helpers em views.py (devem estar em utils/)
- Lógica de negócio em views.py (deve estar em services/)
- Import incorreto do User
- Imports não utilizados
- `except: pass` sem comentário
- Documentação por PR/FIX

**Exemplo de saída:**
```
## Review: ClientContext/views.py

### Problemas encontrados
1. **Linha 45**: Função _validate_token em views.py
   - Correção: Mover para utils/
   - Comando: `/postnow-extract _validate_token utils`

### Checklist
- [x] Imports organizados
- [ ] Funções < 50 linhas (1 violação)
```

---

### 2. `/postnow-extract` - Extração de Código

**Quando usar:** Quando o CTO pedir para mover código ou quando `/postnow-review` sugerir

```bash
# Extrair helper para utils
/postnow-extract _validate_email utils

# Extrair lógica de negócio para services
/postnow-extract process_payment services
```

**Destinos:**
- `utils` - Funções auxiliares, helpers, formatadores
- `services` - Lógica de negócio, integrações, processamento

**O que faz:**
1. Localiza a função no arquivo origem
2. Cria/atualiza arquivo em utils/ ou services/
3. Move a função com seus imports
4. Atualiza imports no arquivo origem
5. Verifica que não quebrou nada

---

### 3. `/postnow-imports` - Organização de Imports

**Quando usar:** Para organizar imports seguindo padrão Django

```bash
# Organizar imports de arquivo específico
/postnow-imports ClientContext/views.py

# Organizar imports de app inteira
/postnow-imports ClientContext/
```

**Ordem correta dos imports:**
```python
# 1. Standard library
import os
import json

# 2. Django
from django.http import JsonResponse
from django.views import View

# 3. Third-party
from rest_framework.views import APIView

# 4. Local
from .models import Post
from .services import PostService
```

**Também corrige:**
- Import incorreto do User
- Remove imports não utilizados

---

### 4. `/postnow-docs` - Documentação

**Quando usar:** Para documentar uma funcionalidade

```bash
# Documentar sistema de autenticação
/postnow-docs authentication

# Documentar sistema de email
/postnow-docs email_system
```

**Regras:**
- ❌ NUNCA cria `docs/PR*.md` ou `docs/FIX*.md`
- ✅ Atualiza documentação existente
- ✅ Cria doc geral se não existir

---

## Fluxo de Trabalho Recomendado

```
1. Desenvolve código
        │
        ▼
2. /postnow-review  ──► Detecta problemas
        │
        ├─► /postnow-extract func utils
        ├─► /postnow-extract func services
        └─► /postnow-imports arquivo.py
                │
                ▼
3. /postnow-review  ──► Confirma correções
        │
        ▼
4. git commit && git push
        │
        ▼
5. Criar PR (código já segue padrões!)
```

---

## Regras do CTO (Resumo)

### Organização de Código
| ❌ Errado | ✅ Correto |
|-----------|-----------|
| Helpers em views.py | Helpers em utils/ |
| Lógica em views.py | Lógica em services/ |
| Funções > 50 linhas | Funções pequenas e focadas |

### Padrões Django
| ❌ Errado | ✅ Correto |
|-----------|-----------|
| `settings.AUTH_USER_MODEL` | `from django.contrib.auth.models import User` |
| `/api/data/` | `/api/analytic-events/` |

### Documentação
| ❌ Errado | ✅ Correto |
|-----------|-----------|
| `docs/PR12_fix.md` | `docs/authentication.md` |
| `docs/FIX_bug.md` | Atualizar doc existente |

### Código Limpo
| ❌ Errado | ✅ Correto |
|-----------|-----------|
| `except: pass` | `except SpecificError: pass  # motivo` |
| Imports desorganizados | stdlib → Django → third-party → local |

---

## Troubleshooting

### Skill não encontrada
```
Unknown skill: postnow-review
```
**Solução:** Reinicie o Claude Code no diretório do projeto:
```bash
cd /path/to/PostNow-REST-API
claude
```

### Skill não detecta problemas conhecidos
**Solução:** Verifique se o arquivo foi salvo e tente novamente:
```bash
/postnow-review ClientContext/views.py
```

---

## Arquivos das Skills

As skills estão em:
```
.claude/skills/
├── postnow-review/
│   ├── SKILL.md
│   └── checklist.md
├── postnow-extract/
│   └── SKILL.md
├── postnow-docs/
│   └── SKILL.md
├── postnow-imports/
│   └── SKILL.md
└── cto-standards/
    ├── SKILL.md
    └── rules.md
```

Para ver todas as regras detalhadas:
```bash
cat .claude/skills/cto-standards/rules.md
```

---

## Contato

Dúvidas sobre as skills? Fale com a equipe de desenvolvimento.
