# Sonora REST API - Documentação

API REST Django com autenticação por email e Google OAuth usando tokens JWT.

## 📚 **Documentação Organizada**

### 🚀 **Início Rápido**

- **[Configuração Inicial](docs/inicio-rapido/configuracao.md)** - Primeiros passos
- **[Deploy no Vercel](docs/inicio-rapido/deploy-vercel.md)** - Como fazer deploy

### 🔐 **Autenticação**

- **[Google OAuth](docs/autenticacao/google-oauth.md)** - Configuração e uso

### 🤖 **Sistema de IA**

- **[Modelos de IA](docs/ia/modelos-disponiveis.md)** - Gemini, OpenAI, Anthropic
- **[Sistema de Créditos](docs/ia/sistema-creditos.md)** - Compra e uso de créditos

### 💳 **Sistema de Créditos**

- **[Integração Stripe](docs/creditos/stripe.md)** - Pagamentos e webhooks

---

## 🚀 **Início Rápido**

1. **Instalar dependências:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar banco:**

   ```bash
   python manage.py migrate
   ```

3. **Executar servidor:**

   ```bash
   python manage.py runserver
   ```

## 📖 **Documentação Completa**

Visite as seções organizadas acima para guias detalhados e exemplos.

## 🔗 **Links Rápidos**

### **Endpoints Principais**

- **Autenticação:** `/api/v1/auth/`
- **Ideias:** `/api/v1/ideabank/`
- **Créditos:** `/api/v1/credits/`
- **Usuários:** `/api/v1/users/`

### **Scripts Úteis**

- **Setup Google OAuth:** `python scripts/setup_google_oauth.py`
- **Teste Google Auth:** `python scripts/test_google_auth.py`
- **Setup Stripe:** `python scripts/setup_stripe.py`

### **Deploy**

- **Vercel:** `vercel --prod`
- **Build Script:** `./vercel_build.sh`
- **Deploy Script:** `./deploy_to_vercel.sh`

## 📝 **Documentação em Desenvolvimento**

As seguintes seções estão sendo desenvolvidas e serão adicionadas em breve:

### **Início Rápido**

- Variáveis de Ambiente - Configurações necessárias

### **Autenticação**

- JWT Tokens - Sistema de autenticação
- Testes com Postman - Como testar endpoints

### **Sistema de IA**

- Geração de Ideias - Como funciona

### **Sistema de Créditos**

- Gestão de Créditos - Adição e dedução
- Transações - Histórico e auditoria

### **Banco de Dados**

- Modelos - Estrutura das tabelas
- Migrações - Como aplicar mudanças
- População - Dados iniciais

### **Desenvolvimento**

- Estrutura do Projeto - Organização dos arquivos
- Serviços - Lógica de negócio
- Testes - Como testar

## 📚 **Documentação Legada**

Os seguintes arquivos são da documentação anterior e podem ser úteis como referência:

- **[Google Console Setup](docs/google_console_setup.md)** - Configuração do Google OAuth
- **[Google OAuth Examples](docs/google_oauth_examples.md)** - Exemplos de integração
- **[Postman Testing Guide](docs/postman_testing_guide.md)** - Guia de testes
- **[AI Service Refactoring](docs/AI_SERVICE_REFACTORING.md)** - Refatoração dos serviços de IA
- **[Credit System Integration](docs/CREDIT_SYSTEM_INTEGRATION.md)** - Integração do sistema de créditos
- **[Frontend Error Handling](docs/FRONTEND_ERROR_HANDLING.md)** - Tratamento de erros no frontend
