# PostNow REST API

REST API para geração de conteúdo com IA para redes sociais.

![CI](https://github.com/PostNow-AI/PostNow-REST-API/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/django-4.2+-green.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)

## Sobre

PostNow é uma plataforma de geração de conteúdo com IA que cria posts otimizados para Instagram, incluindo:

- **Feed Posts** - Copies persuasivas com método AIDA
- **Reels** - Roteiros de 20-40 segundos
- **Stories** - 5 ideias diárias de engajamento
- **Imagens** - Prompts otimizados para geração visual

## Tech Stack

- **Framework:** Django 4.2+ / Django REST Framework
- **Python:** 3.11+
- **Database:** SQLite (dev) / MySQL (prod)
- **AI:** Google Gemini, OpenAI
- **Storage:** AWS S3
- **CI/CD:** GitHub Actions

## Quick Start

```bash
# Clone o repositório
git clone https://github.com/PostNow-AI/PostNow-REST-API.git
cd PostNow-REST-API

# Crie o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Configure o ambiente
export DJANGO_SETTINGS_MODULE=Sonora_REST_API.settings
export USE_SQLITE=True

# Execute as migrations
python -m django migrate

# Inicie o servidor
python -m django runserver
```

## Estrutura do Projeto

```
PostNow-REST-API/
├── Sonora_REST_API/     # Configurações Django
├── IdeaBank/            # Geração de ideias com IA
│   ├── models.py        # PostIdea model
│   ├── services/        # PromptService (core da geração)
│   └── tests/           # Testes unitários
├── CreatorProfile/      # Perfis de criadores
│   ├── models.py        # CreatorProfile, VisualStylePreference
│   └── fixtures/        # 18 estilos visuais pré-configurados
├── CreditSystem/        # Sistema de créditos
├── ClientContext/       # Contexto semanal do cliente
├── Analytics/           # Métricas e analytics
├── Campaigns/           # Gestão de campanhas
├── scripts/             # Scripts utilitários
└── docs/                # Documentação adicional
```

## Estilos Visuais

O sistema inclui 18 estilos visuais pré-configurados:

| Estilo | Descrição |
|--------|-----------|
| Minimalista Moderno | Design clean com espaço negativo |
| Bold Vibrante | Cores saturadas e tipografia impactante |
| Elegante Editorial | Estética de revista de luxo |
| Tech Futurista | Dark mode com neon e glass morphism |
| Zen Japonês | Minimalismo com conceito "ma" |
| E mais 13... | Ver fixtures para lista completa |

## Desenvolvimento

### Executar Testes

```bash
# Todos os testes
python -m django test --settings=Sonora_REST_API.settings

# Com coverage
coverage run -m django test --settings=Sonora_REST_API.settings
coverage report
```

### Linting

```bash
# Verificar código
ruff check .

# Formatar código
ruff format .
```

### Pre-commit Hooks

```bash
# Instalar hooks
pip install pre-commit
pre-commit install

# Executar manualmente
pre-commit run --all-files
```

## Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para guidelines de contribuição.

## Segurança

Para reportar vulnerabilidades, veja [SECURITY.md](SECURITY.md).

## Licença

Este software é proprietário e confidencial. Veja [LICENSE](LICENSE) para detalhes.

---

Desenvolvido por [PostNow AI](https://postnow.com.br)
