# Sonora REST API - Plataforma de Geração de Conteúdo com IA

API REST Django completa para criação de conteúdo para redes sociais usando inteligência artificial. Sistema integrado com Google OAuth, sistema de créditos, assinaturas e geração automatizada de texto e imagens.

## 🏗️ **Arquitetura do Sistema**

### **📱 Core Features**

- **Geração de Conteúdo com IA**: Texto e imagens otimizadas para Feed, Reels e Stories
- **Weekly Context**: E-mail semanal de oportunidades de conteúdo com IA
- **Sistema de Créditos**: Controle de uso baseado em créditos com preços fixos
- **Perfil do Criador**: Onboarding em 3 etapas com personalização de marca
- **Assinaturas**: Planos mensais, trimestrais, semestrais e anuais via Stripe
- **Sistema de Fontes**: 26 fontes Google profissionais para overlay de texto
- **Autenticação Avançada**: Email + Google OAuth com JWT tokens

## 📧 **Weekly Context - E-mail Semanal de Oportunidades**

Pipeline automatizado que pesquisa fontes recentes, gera oportunidades rankeadas com IA e envia um e-mail semanal com sugestões de conteúdo personalizadas.

### **🎯 Propósito**

- **Reduzir tempo de pesquisa** do usuário (pauta semanal pronta)
- **Aumentar qualidade e confiabilidade** (guardrails de fonte + links válidos)
- **Acelerar criação** (CTA para "Criar Post" direto no app)

### **📚 Documentação do Weekly Context**

- **[Visão de Produto](PostNow-REST-API/docs/WEEKLY_CONTEXT_PRODUCT.md)** - Propósito, UX e critérios de qualidade
- **[Políticas e Override](PostNow-REST-API/docs/WEEKLY_CONTEXT_POLICIES.md)** - Admin, logs e operação
- **[Arquitetura](PostNow-REST-API/docs/WEEKLY_CONTEXT_ARCHITECTURE.md)** - Pipeline end-to-end, env vars e quota management

### **✅ Validação Rápida**

```bash
# Rodar testes do módulo
venv/bin/python manage.py test ClientContext.tests -v 2

# Rodar processo completo (gera e envia e-mail)
venv/bin/python scripts/trigger_team_validation.py
```

### **🆕 Recursos Principais**

- Policy automática por cliente com **override manual** via `CreatorProfile.weekly_context_policy_override`
- Telemetria e alertas em logs: `[POLICY]`, `[SOURCE_METRICS]`, `[LOW_SOURCE_COVERAGE]`, `[LOW_ALLOWLIST_RATIO]`
- Sistema de ranqueamento e validação de links
- Integração com Google Custom Search Engine

## 🎨 **Sistema de Perfil do Criador**

### **Onboarding em 3 Etapas**

```
📝 Etapa 1: Informações Pessoais
├── Nome Profissional
├── Profissão
├── Handle do Instagram
└── WhatsApp

🏢 Etapa 2: Informações do Negócio
├── Nome do Negócio
├── Especialização
├── Descrição do Negócio
├── Website e Instagram Empresarial
├── Público-Alvo (gênero, idade, localização, interesses)
└── Cidade de Atuação

🎨 Etapa 3: Identidade Visual
├── Tom de Voz (profissional, descontraído, amigável)
├── Paleta de 5 Cores (gerada automaticamente se não definida)
└── Logo (opcional, base64)
```

## 💳 **Sistema de Créditos e Assinaturas**

### **Modelo de Preços Fixos**

```python
FIXED_PRICES = {
    'image_generation': Decimal('0.23'),  # R$ 0,23 por imagem
    'text_generation': Decimal('0.02'),   # R$ 0,02 por texto
}
```

### **Tipos de Assinatura**

- **Monthly**: Renovação mensal
- **Semester**: A cada 6 meses
- **Yearly**: Anual

### **Sistema de Créditos**

```text
📊 Estrutura de Créditos:
├── monthly_credits: Créditos renovados automaticamente
├── balance: Saldo atual do usuário
├── monthly_credits_allocated: Créditos do ciclo atual
├── monthly_credits_used: Créditos utilizados no mês
└── last_credit_reset: Data do último reset mensal
```

### **Transações de Créditos**

- **Usage**: Uso em operações de IA (texto/imagem)
- **Monthly Allocation**: Renovação mensal automática

## 🤖 **Sistema de Geração de Conteúdo**

### **Tipos de Conteúdo Suportados**

#### **📱 Feed Posts**

- **Estrutura**: Método AIDA (Atenção, Interesse, Desejo, Ação)
- **Formatação**: Parágrafos curtos, emojis estratégicos
- **Otimização**: Compliance com Meta e Google Ads
- **CTA**: Uma única chamada para ação natural

#### **🎬 Reels**

- **Formato**: Roteiro de até 15 segundos
- **Estrutura**: Blocos de tempo ([0s-3s], [3s-6s], etc.)
- **Gancho**: Forte impacto nos primeiros 3 segundos
- **Linguagem**: Frases curtas e dinâmicas

#### **📖 Stories**

- **Formato**: 1 tela interativa
- **Texto**: Frases curtas e impactantes
- **Interação**: Incentivo a engajamento
- **CTA**: Direta e clara

### **Geração de Imagens**

#### **📐 Formatos Automáticos**

- **Feed**: 1080x1080px (quadrado)
- **Reel Cover**: 1080x1920px (vertical)
- **Story**: 1080x1920px com área segura

#### **🎨 Sistema de Overlay de Texto**

- **26 Fontes Google**: Poppins, Montserrat, Inter, Oswald, etc.
- **Posicionamento**: 9 posições (top-left, center-center, etc.)
- **Efeitos**: Drop shadows, strokes, cores personalizadas
- **Responsivo**: Ajuste automático de tamanho

```json
{
  "titulo": {
    "title-content": "Seu Título Aqui",
    "font-family": "Poppins",
    "font-size": "48px",
    "font-weight": "bold",
    "color": "#FFFFFF",
    "drop-shadow": "2px 2px 4px rgba(0,0,0,0.8)",
    "location": "top-center"
  }
}
```

<!-- ### **Integração com Perfil do Criador**

- **Contexto Automático**: Dados do perfil incluídos nos prompts
- **Paleta de Cores**: Cores da marca aplicadas automaticamente
- **Tom de Voz**: Respeitado na geração de conteúdo
- **Público-Alvo**: Considerado na criação -->

---

## 🚀 **Início Rápido**

### **1. Instalação**

```bash
# Clonar repositório
git clone https://github.com/Sonora-Content-Producer/Sonora-REST-API.git
cd Sonora-REST-API

# Criar ambiente virtual
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# ou test_env\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### **2. Configuração**

```bash
# Configurar banco de dados
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Executar servidor
python manage.py runserver
```

### **3. Configurar APIs Externas**

```bash
# Setup Google OAuth
python scripts/setup_google_oauth.py

# Setup Stripe
python scripts/setup_stripe.py

# Teste APIs
python scripts/test_google_auth.py
```

## � **Endpoints da API**

### **📱 Principais Endpoints**

```text
🔐 Autenticação
├── POST /api/v1/auth/login/           # Login com email/senha
├── POST /api/v1/auth/google/          # Login com Google OAuth
├── POST /api/v1/auth/register/        # Registro de usuário
└── POST /api/v1/auth/refresh/         # Refresh token JWT

👤 Perfil do Criador
├── GET    /api/v1/creator-profile/           # Obter perfil
├── POST   /api/v1/creator-profile/           # Criar perfil
├── PUT    /api/v1/creator-profile/           # Atualizar perfil completo
├── PATCH  /api/v1/creator-profile/step-1/    # Completar etapa 1
├── PATCH  /api/v1/creator-profile/step-2/    # Completar etapa 2
└── PATCH  /api/v1/creator-profile/step-3/    # Completar etapa 3

🤖 Geração de Conteúdo
├── POST /api/v1/ideabank/generate-content/   # Gerar texto
├── POST /api/v1/ideabank/generate-image/     # Gerar imagem
├── POST /api/v1/ideabank/regenerate-content/ # Regenerar texto
└── POST /api/v1/ideabank/regenerate-image/   # Regenerar imagem

💳 Sistema de Créditos
├── GET  /api/v1/credits/balance/             # Saldo de créditos
├── GET  /api/v1/credits/transactions/        # Histórico
├── POST /api/v1/credits/purchase/            # Comprar créditos
└── GET  /api/v1/credits/packages/            # Pacotes disponíveis

📊 Assinaturas
├── GET  /api/v1/subscriptions/plans/         # Planos disponíveis
├── POST /api/v1/subscriptions/subscribe/     # Assinar plano
├── GET  /api/v1/subscriptions/status/        # Status da assinatura
└── POST /api/v1/subscriptions/cancel/        # Cancelar assinatura
```

## 📚 **Estrutura do Projeto**

```text
Sonora-REST-API/
├── 📁 CreatorProfile/          # Sistema de perfil do criador
│   ├── models.py              # CreatorProfile, UserBehavior
│   ├── serializers.py         # Serialização para API
│   ├── views.py               # Endpoints do perfil
│   └── services/              # Lógica de negócio
├── 📁 CreditSystem/           # Sistema de créditos e assinaturas
│   ├── models.py              # UserCredits, CreditTransaction, SubscriptionPlan
│   ├── middleware.py          # Validação de créditos
│   └── services/              # Integração Stripe
├── 📁 IdeaBank/               # Sistema de geração de conteúdo
│   ├── models.py              # Post, PostIdea
│   ├── gemini_service.py      # Integração Google Gemini
│   └── services/              # AI Services (OpenAI, Anthropic, etc.)
│       ├── post_ai_service.py          # Orquestração principal
│       ├── text_overlay_service.py     # Sistema de fontes
│       ├── ai_service_factory.py       # Factory pattern
│       └── base_ai_service.py          # Classe base
├── 📁 static/fonts/           # 26 Google Fonts (8.1MB)
├── 📁 scripts/                # Scripts de configuração e teste
└── 📁 docs/                   # Documentação completa
```

## 🛠️ **Tecnologias e Dependências**

### **Backend**

- **Django 4.2+**: Framework web principal
- **Django REST Framework**: API REST
- **PostgreSQL**: Banco de dados principal
- **JWT**: Autenticação stateless
- **Celery**: Processamento assíncrono

### **APIs de IA**

- **Google Gemini**: Geração de texto e imagem (principal)
- **OpenAI GPT**: Modelos alternativos
- **Anthropic Claude**: Opção premium

### **Pagamentos e Assinaturas**

- **Stripe**: Processamento de pagamentos
- **Webhooks**: Automação de assinaturas

### **Processamento de Imagem**

- **Pillow (PIL)**: Manipulação de imagens
- **26 Google Fonts**: Sistema completo de tipografia

## 🚢 **Deploy e Produção**

### **Vercel (Recomendado)**

```bash
# Deploy automático
vercel --prod

# Ou usar script personalizado
./deploy_to_vercel.sh
```

### **Variáveis de Ambiente Necessárias**

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Google APIs
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GEMINI_API_KEY=your-gemini-api-key

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# OpenAI (opcional)
OPENAI_API_KEY=sk-...

# Anthropic (opcional)
ANTHROPIC_API_KEY=sk-ant-...
```

## � **Documentação Detalhada**

### **🚀 Início Rápido**

- **[Configuração Inicial](docs/inicio-rapido/configuracao.md)** - Setup completo
- **[Deploy no Vercel](docs/inicio-rapido/deploy-vercel.md)** - Produção

### **🔐 Autenticação**

- **[Google OAuth](docs/autenticacao/google-oauth.md)** - Integração completa
- **[JWT Tokens](docs/autenticacao/jwt.md)** - Sistema de tokens

### **🤖 Sistema de IA**

- **[Modelos Disponíveis](docs/ia/modelos-disponiveis.md)** - Gemini, OpenAI, Anthropic
- **[Geração de Texto](docs/ia/geracao-texto.md)** - Prompts e personalização
- **[Geração de Imagem](docs/ia/geracao-imagem.md)** - Overlays e fontes

### **💳 Sistema de Créditos**

- **[Integração Stripe](docs/creditos/stripe.md)** - Pagamentos e webhooks
- **[Gestão de Créditos](docs/creditos/gestao.md)** - Transações e saldos
- **[Planos de Assinatura](docs/creditos/assinaturas.md)** - Configuração de planos

### **🎨 Sistema de Fontes**

- **[Coleção de Fontes](docs/FONT_COLLECTION.md)** - 26 fontes Google disponíveis
- **[Overlay de Texto](docs/fontes/overlay.md)** - Sistema de sobreposição

### **👤 Perfil do Criador**

- **[Onboarding](docs/perfil/onboarding.md)** - Processo em 3 etapas
- **[Personalização](docs/perfil/personalizacao.md)** - Cores e identidade visual

## 🧪 **Scripts de Teste e Configuração**

```bash
# Testes do sistema
python scripts/test_google_auth.py          # Teste Google OAuth
python scripts/test_all_fonts.py            # Teste todas as 26 fontes
python scripts/create_font_showcase.py      # Showcase visual das fontes
python scripts/test_credit_deduction_e2e.py # Teste sistema de créditos

# Configuração
python scripts/setup_google_oauth.py        # Setup Google OAuth
python scripts/setup_stripe.py              # Setup Stripe
python scripts/manage_google_oauth.py       # Gerenciar OAuth

# Debug e desenvolvimento
python scripts/test_api_debug.py            # Debug da API
python scripts/test_working_models.py       # Teste modelos de IA
python scripts/test_ai_selection.py         # Teste seleção de IA
```

## 🔧 **Utilitários de Desenvolvimento**

### **Gerenciamento de Fontes**

- **Font Test Suite**: Validação completa de todas as fontes
- **Font Showcase Generator**: Demonstração visual
- **Font Collection**: 26 fontes organizadas por categoria

### **Sistema de IA**

- **Model Selection**: Escolha automática baseada em custo-benefício
- **Credit Validation**: Validação antes de operações
- **Fallback System**: Modelos alternativos em caso de falha

### **Monitoramento**

- **Credit Transactions**: Histórico completo de transações
- **User Behavior**: Tracking de preferências
- **Subscription Status**: Monitoramento de assinaturas

## 🌟 **Features Destacadas**

### **🎯 Personalização Inteligente**

- Contexto automático do perfil do criador nos prompts
- Paleta de cores da marca aplicada automaticamente
- Tom de voz respeitado na geração de conteúdo

### **💰 Sistema Econômico**

- Preços fixos: R$ 0,02 (texto) e R$ 0,23 (imagem)
- Seleção automática do modelo mais econômico
- Renovação mensal automática de créditos

### **🎨 Design Profissional**

- 26 fontes Google profissionais
- Sistema de overlay com efeitos avançados
- Formatos otimizados para cada tipo de conteúdo

### **⚡ Performance e Escalabilidade**

- Factory pattern para serviços de IA
- Middleware de validação de créditos
- Processamento assíncrono com Celery
- Deploy serverless no Vercel

---

## 📞 **Suporte e Contribuição**

### **Documentação de Referência**

- **[AI Service Refactoring](docs/AI_SERVICE_REFACTORING.md)** - Arquitetura dos serviços
- **[Credit System Integration](docs/CREDIT_SYSTEM_INTEGRATION.md)** - Sistema de créditos
- **[Frontend Error Handling](docs/FRONTEND_ERROR_HANDLING.md)** - Tratamento de erros
- **[Google Console Setup](docs/google_console_setup.md)** - Configuração OAuth
- **[Postman Testing Guide](docs/postman_testing_guide.md)** - Testes de API

### **Contato**

- **Repositório**: [Sonora-Content-Producer/Sonora-REST-API](https://github.com/Sonora-Content-Producer/Sonora-REST-API)
- **Issues**: Para bugs e solicitações de features
- **Discussions**: Para dúvidas e discussões técnicas

---

_🚀 Sonora REST API - Plataforma completa de geração de conteúdo com IA para criadores de conteúdo e profissionais de marketing digital._