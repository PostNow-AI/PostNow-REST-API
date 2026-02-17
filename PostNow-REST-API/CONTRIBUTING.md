# Guia de Contribuição - PostNow REST API

## Começando

1. Clone o repositório
2. Crie um virtual environment: `python -m venv venv`
3. Ative: `source venv/bin/activate`
4. Instale dependências: `pip install -r requirements.txt` (ou instale manualmente Django e dependências)
5. Configure pre-commit: `pre-commit install`

## Workflow de Desenvolvimento

### Branches

- `main` - Produção (protegida)
- `develop` - Desenvolvimento
- `feature/*` - Novas features
- `fix/*` - Correções de bugs
- `hotfix/*` - Correções urgentes em produção

### Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(module): add new feature
fix(module): fix specific bug
docs: update documentation
refactor(module): code refactoring
test(module): add or update tests
chore: maintenance tasks
```

### Pull Requests

1. Crie uma branch a partir de `develop`
2. Faça suas mudanças
3. Rode os testes: `python -m django test --settings=Sonora_REST_API.settings`
4. Rode o linter: `ruff check .`
5. Abra um PR para `develop`
6. Aguarde review e CI passar

## Padrões de Código

- Python 3.11+
- Django 4.2+
- Linha máxima: 100 caracteres
- Docstrings em português
- Type hints quando possível
- Testes para nova funcionalidade

## Testes

```bash
# Rodar todos os testes
python -m django test --settings=Sonora_REST_API.settings

# Com coverage
coverage run -m django test --settings=Sonora_REST_API.settings
coverage report
```

## Estrutura do Projeto

```
PostNow-REST-API/
├── Sonora_REST_API/     # Configurações Django
├── IdeaBank/            # Geração de ideias com IA
├── CreatorProfile/      # Perfis de criadores
├── CreditSystem/        # Sistema de créditos
├── ClientContext/       # Contexto do cliente
├── Analytics/           # Métricas e analytics
├── AuditSystem/         # Sistema de auditoria
├── Campaigns/           # Gestão de campanhas
├── Carousel/            # Carrosséis de conteúdo
├── Users/               # Gestão de usuários
├── GlobalOptions/       # Configurações globais
├── scripts/             # Scripts utilitários
└── docs/                # Documentação
```

## Dúvidas?

Abra uma issue ou entre em contato: dev@postnow.com.br
