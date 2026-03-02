# Checklist Pré-PR - PostNow

Este documento define o processo padronizado para garantir PRs de qualidade antes de solicitar review.

**Baseado em:** Análise de 71 PRs + Feedbacks do CTO + Documentação existente + Cursor Rules

---

## 🥇 REGRA DE OURO (Verificar ANTES de tudo)

```
┌─────────────────────────────────────────────────────────────────┐
│                      🥇 REGRA DE OURO                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Para CADA tarefa nova, SEMPRE criar branch nova a partir       │
│  da branch base ATUALIZADA:                                     │
│                                                                 │
│  git checkout devel                                             │
│  git pull origin devel                                          │
│  git checkout -b <tipo>/<descricao>                             │
│                                                                 │
│  ⚠️  NUNCA reutilizar branch antiga                             │
│  ⚠️  NUNCA criar branch sem antes fazer pull                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Para IAs:** Antes de iniciar qualquer tarefa, verificar:
1. `git branch` - Em qual branch estamos?
2. `git pull origin devel` - Branch base está atualizada?
3. Se for tarefa nova → criar branch nova com `git checkout -b <tipo>/<descricao>`

---

## ⚠️ IMPORTANTE: Escolha o Checklist pelo Tipo de Branch

| Tipo de Branch | Checklist a usar | Documentação |
|----------------|------------------|--------------|
| `fix/` | [Checklist FIX](#checklist-fix-bugfix) | ❌ Não criar (atualizar existente se necessário) |
| `feat/` | [Checklist FEAT](#checklist-feat-feature) | ✅ Doc da funcionalidade (não do PR) |
| `hotfix/` | [Checklist HOTFIX](#checklist-hotfix-urgente) | ❌ Não criar |
| `refactor/` | [Checklist REFACTOR](#checklist-refactor) | ❌ Não criar |
| `docs/` | [Checklist DOCS](#checklist-docs) | N/A (é a própria mudança) |
| `chore/` | [Checklist CHORE](#checklist-chore) | ❌ Não criar |

---

## Checklist FIX (Bugfix)

**Use para:** Correções de bugs, ajustes de comportamento

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHECKLIST FIX - BUGFIX                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ BRANCH & COMMITS                                                │
│ [ ] Branch: fix/<descricao>                                     │
│ [ ] Commit: fix(escopo): descrição                              │
│                                                                 │
│ CÓDIGO                                                          │
│ [ ] Apenas o código necessário foi alterado                     │
│ [ ] Sem bare excepts                                            │
│ [ ] Sem prints de debug                                         │
│ [ ] Sem imports não utilizados                                  │
│                                                                 │
│ TESTES                                                          │
│ [ ] python -m flake8 .                                          │
│ [ ] python manage.py test                                       │
│ [ ] Bug específico foi testado manualmente                      │
│                                                                 │
│ INTEGRAÇÃO                                                      │
│ [ ] Branch atualizada com devel                                 │
│ [ ] Sem conflitos                                               │
│                                                                 │
│ PR                                                              │
│ [ ] Template preenchido                                         │
│ [ ] Self-review feito                                           │
│                                                                 │
│ DOCUMENTAÇÃO                                                    │
│ [ ] ❌ NÃO criar doc nova (ENTREGA_*.md)                        │
│ [ ] Se necessário, atualizar doc EXISTENTE da funcionalidade    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Checklist FEAT (Feature)

**Use para:** Novas funcionalidades, novos endpoints, novas telas

```
┌─────────────────────────────────────────────────────────────────┐
│                   CHECKLIST FEAT - FEATURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ BRANCH & COMMITS                                                │
│ [ ] Branch: feat/<descricao>                                    │
│ [ ] Commits: feat(escopo): descrição                            │
│ [ ] Commits pequenos e frequentes                               │
│                                                                 │
│ CÓDIGO                                                          │
│ [ ] Funções < 50 linhas                                         │
│ [ ] Lógica complexa em services/ dedicados                      │
│ [ ] Funções auxiliares em utils/                                │
│ [ ] Sem bare excepts (usar Exception + logger)                  │
│ [ ] Sem imports não utilizados                                  │
│ [ ] Sem prints de debug                                         │
│ [ ] Type hints em funções públicas                              │
│                                                                 │
│ PERFORMANCE                                                     │
│ [ ] Queries otimizadas (select_related/prefetch_related)        │
│ [ ] Sem N+1 queries                                             │
│                                                                 │
│ SEGURANÇA                                                       │
│ [ ] Sem secrets hardcoded                                       │
│ [ ] Permissions adequadas nas views                             │
│ [ ] Validação de input do usuário                               │
│                                                                 │
│ TESTES                                                          │
│ [ ] python -m flake8 .                                          │
│ [ ] python -m black . --check                                   │
│ [ ] python manage.py test                                       │
│ [ ] Testes unitários para nova funcionalidade                   │
│                                                                 │
│ INTEGRAÇÃO                                                      │
│ [ ] Branch atualizada com devel                                 │
│ [ ] Sem conflitos de merge                                      │
│ [ ] Migrations não conflitam                                    │
│                                                                 │
│ PR                                                              │
│ [ ] Template preenchido                                         │
│ [ ] PRs relacionadas linkadas (frontend)                        │
│ [ ] Self-review feito                                           │
│                                                                 │
│ DOCUMENTAÇÃO                                                    │
│ [ ] Doc da FUNCIONALIDADE (não do PR)                           │
│ [ ] Ex: CONTEXT_EMAIL.md, não ENTREGA_PR40.md                   │
│                                                                 │
│ PÓS-PUSH                                                        │
│ [ ] Vercel Preview funcionando                                  │
│ [ ] CodeQL/GitGuardian sem alertas                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Checklist HOTFIX (Urgente)

**Use para:** Correções urgentes em produção

```
┌─────────────────────────────────────────────────────────────────┐
│                  CHECKLIST HOTFIX - URGENTE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ BRANCH & COMMITS                                                │
│ [ ] Branch: hotfix/<descricao>                                  │
│ [ ] Commit: fix(escopo): descrição                              │
│                                                                 │
│ CÓDIGO (mínimo necessário)                                      │
│ [ ] Apenas a correção, nada mais                                │
│ [ ] Sem bare excepts                                            │
│                                                                 │
│ TESTES                                                          │
│ [ ] Teste manual do fix                                         │
│ [ ] python manage.py test (se possível)                         │
│                                                                 │
│ PR                                                              │
│ [ ] Marcar como URGENTE                                         │
│ [ ] Descrever o problema e a solução                            │
│                                                                 │
│ DOCUMENTAÇÃO                                                    │
│ [ ] ❌ NÃO criar doc                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Checklist REFACTOR

**Use para:** Refatoração sem mudança de comportamento

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHECKLIST REFACTOR                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ BRANCH & COMMITS                                                │
│ [ ] Branch: refactor/<descricao>                                │
│ [ ] Commit: refactor(escopo): descrição                         │
│                                                                 │
│ CÓDIGO                                                          │
│ [ ] Comportamento NÃO mudou (só estrutura)                      │
│ [ ] Funções < 50 linhas                                         │
│ [ ] Lógica em services/utils apropriados                        │
│ [ ] Sem bare excepts                                            │
│ [ ] Sem imports não utilizados                                  │
│                                                                 │
│ TESTES                                                          │
│ [ ] python -m flake8 .                                          │
│ [ ] python manage.py test (TODOS devem passar)                  │
│ [ ] Nenhum teste quebrou                                        │
│                                                                 │
│ INTEGRAÇÃO                                                      │
│ [ ] Branch atualizada com devel                                 │
│ [ ] Sem conflitos                                               │
│                                                                 │
│ PR                                                              │
│ [ ] Template preenchido                                         │
│ [ ] Self-review feito                                           │
│                                                                 │
│ DOCUMENTAÇÃO                                                    │
│ [ ] ❌ NÃO criar doc nova                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Checklist DOCS

**Use para:** Apenas documentação

```
┌─────────────────────────────────────────────────────────────────┐
│                      CHECKLIST DOCS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ BRANCH & COMMITS                                                │
│ [ ] Branch: docs/<descricao>                                    │
│ [ ] Commit: docs(escopo): descrição                             │
│                                                                 │
│ CONTEÚDO                                                        │
│ [ ] Markdown válido                                             │
│ [ ] Links funcionando                                           │
│ [ ] Texto em português                                          │
│                                                                 │
│ PR                                                              │
│ [ ] Template preenchido                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Checklist CHORE

**Use para:** Manutenção, dependências, configs

```
┌─────────────────────────────────────────────────────────────────┐
│                      CHECKLIST CHORE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ BRANCH & COMMITS                                                │
│ [ ] Branch: chore/<descricao>                                   │
│ [ ] Commit: chore(escopo): descrição                            │
│                                                                 │
│ VERIFICAÇÕES                                                    │
│ [ ] Build funciona                                              │
│ [ ] Testes passam                                               │
│ [ ] Sem vulnerabilidades novas (npm audit / pip audit)          │
│                                                                 │
│ PR                                                              │
│ [ ] Template preenchido                                         │
│ [ ] Listar dependências alteradas                               │
│                                                                 │
│ DOCUMENTAÇÃO                                                    │
│ [ ] ❌ NÃO criar doc                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Índice - Detalhes por Fase

- [Fase 1: Branch](#fase-1-branch)
- [Fase 2: Commits](#fase-2-commits)
- [Fase 3: Código](#fase-3-código)
- [Fase 4: Performance](#fase-4-performance)
- [Fase 5: Testes Locais](#fase-5-testes-locais)
- [Fase 6: Integração](#fase-6-integração)
- [Fase 7: PR](#fase-7-pr)
- [Fase 8: Pós-Push](#fase-8-pós-push)
- [Fase 9: Pós-Merge](#fase-9-pós-merge)
- [Comandos Úteis](#comandos-úteis)
- [Padrões Django (Cursor Rules)](#padrões-django-cursor-rules)
- [Feedbacks Recorrentes do CTO](#feedbacks-recorrentes-do-cto)

---

## Fase 1: Branch

### Criar branch corretamente

```bash
# Atualizar branch base (backend usa devel)
git checkout devel
git pull origin devel

# Criar feature branch
git checkout -b <tipo>/<descricao>
```

### Nomenclatura obrigatória

| Prefixo | Uso | Impacto na versão |
|---------|-----|-------------------|
| `feat/` | Nova funcionalidade | MINOR |
| `fix/` | Correção de bug | PATCH |
| `hotfix/` | Correção urgente em produção | PATCH |
| `docs/` | Documentação | - |
| `refactor/` | Refatoração sem mudança de comportamento | - |
| `chore/` | Manutenção (deps, configs) | - |
| `release/` | Preparação de release | - |

### Exemplos

```bash
feat/adicionar-login-social
fix/corrigir-validacao-email
hotfix/corrigir-falha-pagamento
docs/atualizar-readme
refactor/extrair-logica-auth
refactor/solid-dry-cto-review
```

---

## Fase 2: Commits

### Formato (Conventional Commits)

```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos de commit

| Tipo | Descrição | Impacto na versão |
|------|-----------|-------------------|
| `feat` | Nova funcionalidade | MINOR |
| `fix` | Correção de bug | PATCH |
| `docs` | Documentação | - |
| `style` | Formatação (não afeta código) | - |
| `refactor` | Refatoração sem mudança de comportamento | - |
| `perf` | Melhoria de performance | PATCH |
| `test` | Adicionar/corrigir testes | - |
| `chore` | Manutenção (deps, configs) | - |
| `ci` | Mudanças em CI/CD | - |

### Exemplos

```bash
feat(auth): adicionar login com Google
fix(checkout): corrigir cálculo de desconto
refactor(api): extrair lógica de validação para utils
docs(readme): atualizar instruções de instalação
perf(queries): otimizar listagem com prefetch_related

# Breaking change
feat(api)!: migrar endpoints para v2

BREAKING CHANGE: todos os endpoints agora usam /api/v2/
```

---

## Fase 3: Código

### Padrões obrigatórios (Feedbacks do CTO)

| Evitar | Fazer |
|--------|-------|
| Funções > 50-100 linhas | Quebrar em funções menores |
| Lógica misturada em um arquivo | Criar **service** dedicado |
| Funções auxiliares soltas | Mover para **utils/** |
| `except: pass` (bare except) | `except Exception as exc: logger.debug()` |
| Imports não utilizados | Remover antes do PR |
| Prints de debug | Usar **logging** apropriado |
| Código comentado | Remover (Git tem histórico) |
| Hardcoded secrets | Usar **os.environ** ou **.env** |
| Funções sem type hints | Adicionar **type hints** |

### Estrutura de arquivos esperada

```
App/
├── models.py          # Modelos Django
├── views.py           # Views thin (delegam para services)
├── urls.py            # Rotas
├── serializers.py     # Serializers DRF
├── permissions.py     # Permissions customizadas
├── exceptions.py      # Exceções customizadas
├── services/          # Lógica de negócios
│   ├── __init__.py
│   └── nome_service.py
├── utils/             # Funções auxiliares
│   ├── __init__.py
│   └── nome_utils.py
└── tests/             # Testes
    └── test_*.py
```

### Padrão de Services

```python
from typing import Optional, List
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class NomeService:
    """Docstring explicando responsabilidade."""

    def __init__(self, user):
        self.user = user

    def metodo_publico(self, param: str) -> Optional[dict]:
        """Métodos pequenos e focados com type hints."""
        try:
            return self._processar(param)
        except Exception as exc:
            logger.error("Erro ao processar: %s", exc)
            raise

    def _metodo_privado(self) -> List[str]:
        """Métodos auxiliares com underscore."""
        pass
```

### Padrão de Exception Handling

```python
# Em exceptions.py - usar o unified handler existente
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    """Handler unificado de exceções."""
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code

    return response
```

```python
# Em views/services - NUNCA usar bare except
# ERRADO
try:
    fazer_algo()
except:
    pass

# CORRETO
try:
    fazer_algo()
except SpecificException as exc:
    logger.warning("Erro específico: %s", exc)
    raise
except Exception as exc:
    logger.error("Erro inesperado: %s", exc)
    raise
```

---

## Fase 4: Performance

### Otimização de Queries (Obrigatório)

```python
# ERRADO - N+1 Query
posts = Post.objects.all()
for post in posts:
    print(post.author.name)  # Query para cada post!

# CORRETO - select_related (ForeignKey, OneToOne)
posts = Post.objects.select_related('author').all()

# CORRETO - prefetch_related (ManyToMany, reverse FK)
users = User.objects.prefetch_related('posts').all()
```

### Checklist de Performance

```
[ ] Queries com select_related para ForeignKey
[ ] Queries com prefetch_related para ManyToMany
[ ] Sem N+1 queries (verificar com django-debug-toolbar)
[ ] Transações atômicas para operações múltiplas
[ ] Paginação em listagens grandes
[ ] Índices nos campos filtrados frequentemente
```

### Transações Atômicas

```python
from django.db import transaction

# Para operações que devem ser atômicas
@transaction.atomic
def criar_usuario_com_perfil(data: dict) -> User:
    user = User.objects.create(**data['user'])
    Profile.objects.create(user=user, **data['profile'])
    return user
```

---

## Fase 5: Testes Locais

### Comandos obrigatórios

```bash
# 1. Lint (flake8)
python -m flake8 .

# 2. Formatação (black)
python -m black . --check

# 3. Testes
python manage.py test

# 4. Verificar bare excepts (CTO sempre pede)
grep -r "except:" --include="*.py" . | grep -v "except [A-Z]"

# 5. Verificar imports não usados
# (CodeQL vai pegar, mas melhor verificar antes)
```

### Comando único

```bash
python -m flake8 . && python -m black . --check && python manage.py test
```

### Padrão de Testes

```python
from django.test import TestCase
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock


class NomeServiceTest(TestCase):
    """Testes do NomeService."""

    def setUp(self):
        """Setup executado antes de cada teste."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_metodo_retorna_esperado(self):
        """Test que método retorna valor esperado."""
        service = NomeService(self.user)
        result = service.metodo_publico("param")
        self.assertEqual(result, expected_value)

    def test_metodo_com_erro_loga_exception(self):
        """Test que erros são logados corretamente."""
        with patch('app.services.logger') as mock_logger:
            with self.assertRaises(Exception):
                service.metodo_que_falha()
            mock_logger.error.assert_called_once()
```

---

## Fase 6: Integração

### Verificar integração com devel

```bash
# 1. Atualizar referências
git fetch origin

# 2. Ver quantos commits de diferença
git log origin/devel..HEAD --oneline

# 3. Verificar se há conflitos
git merge origin/devel --no-commit --no-ff

# Se houver conflitos:
git merge --abort
# Resolver conflitos ANTES de abrir PR

# 4. Ver todas as mudanças
git diff origin/devel...HEAD --stat
```

### Verificar migrations

```bash
# Verificar se há migrations conflitantes
python manage.py showmigrations

# Se criou migration, verificar se não conflita
python manage.py makemigrations --check
```

### Importante

- **Resolver conflitos localmente** antes de abrir o PR
- **Revisar o diff** para garantir que só está indo o que deveria
- **Migrations** não devem conflitar com outras branches

---

## Fase 7: PR

### Template obrigatório

```markdown
## Tipo de mudança
- [ ] `feat` / `fix` / `docs` / `refactor` / `perf` / `test` / `chore`

## Descrição
<!-- O QUE foi feito -->

## Motivação e contexto
<!-- POR QUÊ essa mudança é necessária -->

## Como foi testado?
- [ ] Testes unitários
- [ ] Testes manuais
- [ ] Testes de integração

## Checklist
- [ ] Meu código segue o padrão de estilo do projeto
- [ ] Realizei self-review do meu código
- [ ] Atualizei a documentação (se necessário)
- [ ] Minhas mudanças não geram novos warnings
- [ ] Testes novos e existentes passam localmente
- [ ] Queries otimizadas (select_related/prefetch_related)
- [ ] Sem bare excepts
- [ ] Type hints em funções públicas

## PRs Relacionadas
<!-- Se backend, linkar PR de frontend e vice-versa -->
- Frontend: https://github.com/PostNow-AI/PostNow-UI/pull/XX
```

### Boas práticas

- **PRs pequenas** (máximo ~500 linhas)
- **Uma responsabilidade** por PR
- **Linkar PRs relacionadas** entre frontend e backend
- **Mencionar migrations** se houver

---

## Fase 8: Pós-Push

### Verificações automáticas (aguardar passar)

| Check | O que verifica | Bloqueia? |
|-------|----------------|-----------|
| Vercel Preview | Deploy funciona | Não |
| CodeQL | Vulnerabilidades de segurança | **Sim** |
| GitGuardian | Secrets expostos | **Sim** |
| github-code-quality | Imports não usados, bare excepts | **Sim** |

### O que o github-code-quality verifica

- Imports não utilizados
- Bare except clauses
- Variáveis não utilizadas
- Regex com escaping incorreto

### Testar no Preview

1. Acessar URL de preview do Vercel
2. Testar endpoints alterados via Postman/curl
3. Verificar logs de erro

---

## Fase 9: Pós-Merge

### Quando criar release

| Situação | Ação |
|----------|------|
| Bug fix merged | Tag `vX.X.+1` (PATCH) |
| Nova feature merged | Tag `vX.+1.0` (MINOR) |
| Breaking change | Tag `v+1.0.0` (MAJOR) |

### Criar release

```bash
git checkout main
git pull
git tag -a v1.2.3 -m "Release v1.2.3 - Descrição"
git push origin v1.2.3
```

O workflow `release.yml` cria automaticamente:
- Release no GitHub
- Changelog baseado nos commits

### Checklist de Release

- [ ] Todos os PRs da release foram merged
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Tag criada
- [ ] Release notes geradas no GitHub
- [ ] Deploy em produção verificado
- [ ] Comunicar equipe

---

## Comandos Úteis

```bash
# === ANTES DO PR ===

# Atualizar e verificar integração
git fetch origin
git merge origin/devel --no-commit --no-ff
git diff origin/devel...HEAD --stat

# Todas as checagens de uma vez
python -m flake8 . && python -m black . --check && python manage.py test

# Verificar bare excepts
grep -r "except:" --include="*.py" . | grep -v "except [A-Z]"

# Verificar N+1 (instalar django-debug-toolbar)
# Ou usar logging de queries
python manage.py shell
>>> from django.db import connection
>>> connection.queries

# === PÓS-MERGE ===

# Release
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

---

## Padrões Django (Cursor Rules)

Temos regras configuradas em `.cursor/rules/` que definem padrões:

### Django-First Approach

- **PEP 8** compliance obrigatória
- **Arquitetura modular** com apps Django
- **Class-Based Views** preferidas
- **RESTful design** para APIs

### ORM Best Practices

```python
# Sempre usar ORM, evitar raw SQL
# Usar select_related e prefetch_related
# Query optimization é obrigatória

# Bom
Post.objects.select_related('author').filter(status='published')

# Evitar
Post.objects.raw('SELECT * FROM posts WHERE status = "published"')
```

### Business Logic

- Lógica de negócios em **models/managers** ou **services**
- Views devem ser **thin** (apenas orquestração)

### Authentication & Permissions

```python
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class MinhaView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
```

### Response Format

```python
# Formato unificado de response
{
    "success": True,
    "data": {...},
    "message": "Operação realizada com sucesso"
}

# Ou em caso de erro
{
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Campo obrigatório",
        "field": "email"
    }
}
```

---

## Feedbacks Recorrentes do CTO

### Alta Prioridade - Arquitetura SOLID/DRY

| Feedback | Solução |
|----------|---------|
| "Separar funções em arquivos próprios" | Criar arquivo em services/ ou utils/ |
| "Criar um service específico" | Extrair lógica para NomeService |
| "Mover para utils" | Funções auxiliares vão para utils/ |
| "Função muito grande" | Quebrar em funções < 50 linhas |
| "Criar serializer" | Para persistência de dados complexos |
| "Extrair para arquivo service específico" | Não misturar responsabilidades |

### Alta Prioridade - Documentação

| Feedback | Solução |
|----------|---------|
| "Não criar doc por PR/bugfix" | **NÃO** criar arquivos como `ENTREGA_PR40.md` |
| "Documentação polui e dificulta leitura" | Manter docs consolidadas por funcionalidade |
| "Atualizar doc antiga" | Editar doc existente com novo funcionamento |

**Regra:** Documentação deve ser **por funcionalidade**, não por PR. Em caso de bugfix, atualizar a documentação existente substituindo o texto para contemplar o novo funcionamento.

### Média Prioridade - Qualidade

| Feedback | Solução |
|----------|---------|
| "Bare except clause" | `except Exception as exc: logger.debug()` |
| "Import não utilizado" | Remover import |
| "Variável não utilizada" | Remover ou usar `_` prefix |
| "Timeout muito alto" | Reduzir para valores razoáveis |

### Performance

| Feedback | Solução |
|----------|---------|
| "Query N+1" | Usar select_related/prefetch_related |
| "Listagem lenta" | Adicionar paginação |
| "Muitas queries" | Consolidar em uma query otimizada |

---

## Métricas de Qualidade

| Métrica | Valor Atual | Meta |
|---------|-------------|------|
| Taxa de aprovação na 1ª review | ~30% | >70% |
| Reviews médias por PR | 2-3 | 1-2 |
| Testes por feature | 15-33 | Mínimo 10 |

**Para melhorar:** Seguir este checklist antes de abrir o PR.

---

## Segurança

### Checklist de Segurança (Pré-PR)

```
[ ] Sem secrets hardcoded no código
[ ] Variáveis sensíveis em .env (não commitado)
[ ] .env.example atualizado com novas variáveis
[ ] Permissions adequadas nas views (IsAuthenticated, etc)
[ ] Validação de input do usuário (serializers)
[ ] Sanitização de dados antes de salvar
[ ] Rate limiting em endpoints públicos
[ ] Endpoint de cron protegido com CRON_SECRET
```

### O que JÁ está implementado (usar!)

| Proteção | Como usar | Onde |
|----------|-----------|------|
| **Rate Limiting** | Cache-based, 5min cooldown | `ClientContext/views.py` |
| **Timing Attack Prevention** | `secrets.compare_digest()` | Validação de tokens |
| **XSS Prevention** | `html.escape()` | Templates de email |
| **Header Injection Prevention** | Sanitização de subject | Serviços de email |
| **CORS** | `CORS_ALLOWED_ORIGINS` | `settings.py` |
| **CSRF** | Middleware ativo | `settings.py` |
| **JWT Auth** | `simplejwt` | Todas as views |
| **AuditSystem** | Logging automático | App `AuditSystem` |
| **Input Validation** | 20+ validators | `serializers.py` |

### Padrões de Segurança Obrigatórios

#### 1. Validação de Token (Timing Safe)

```python
import secrets

# CORRETO - previne timing attacks
if secrets.compare_digest(provided_token, expected_token):
    # token válido

# ERRADO - vulnerável a timing attacks
if provided_token == expected_token:
    # token válido
```

#### 2. Sanitização de Output (XSS)

```python
import html

# CORRETO - previne XSS
safe_text = html.escape(user_input)

# ERRADO - vulnerável a XSS
unsafe_text = user_input
```

#### 3. Rate Limiting

```python
from django.core.cache import cache

RATE_LIMIT_SECONDS = 300  # 5 minutos

def check_rate_limit(user_id: int) -> bool:
    cache_key = f"rate_limit_{user_id}"
    if cache.get(cache_key):
        return False  # Bloqueado
    cache.set(cache_key, True, timeout=RATE_LIMIT_SECONDS)
    return True  # Permitido
```

#### 4. Proteção de Endpoints Cron

```python
import os

def verify_cron_secret(request) -> bool:
    expected = os.environ.get('CRON_SECRET')
    provided = request.headers.get('X-Cron-Secret')
    return secrets.compare_digest(provided or '', expected or '')
```

#### 5. Variáveis de Ambiente

```python
# CORRETO
import os
API_KEY = os.environ.get('API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')

# ERRADO - NUNCA fazer isso
API_KEY = 'sk-1234567890abcdef'
SECRET_KEY = 'hardcoded-secret'
```

### Verificações Automáticas

| Check | O que detecta | Bloqueia PR? |
|-------|---------------|--------------|
| **GitGuardian** | Secrets expostos | **Sim** |
| **CodeQL** | Vulnerabilidades de código | **Sim** (crítico) |
| **github-code-quality** | Bare excepts, imports não usados | **Sim** |

### OWASP Top 10 - Checklist

```
[ ] A01 - Broken Access Control → Permissions em todas as views
[ ] A02 - Cryptographic Failures → Secrets em .env, HTTPS only
[ ] A03 - Injection → Usar ORM, nunca raw SQL
[ ] A04 - Insecure Design → Validação em serializers
[ ] A05 - Security Misconfiguration → DEBUG=False em prod
[ ] A06 - Vulnerable Components → Manter deps atualizadas
[ ] A07 - Auth Failures → JWT + rate limiting
[ ] A08 - Data Integrity → Validação de input
[ ] A09 - Security Logging → AuditSystem ativo
[ ] A10 - SSRF → Validar URLs antes de fetch
```

---

## Referências

- [VERSIONING.md](./VERSIONING.md) - Guia de versionamento
- [PR Template](../.github/PULL_REQUEST_TEMPLATE.md) - Template de PR
- [Cursor Rules](../.cursor/rules/) - Padrões de código
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

*Documento criado em Março/2026 baseado na análise de PRs, feedbacks do CTO e Cursor Rules.*
