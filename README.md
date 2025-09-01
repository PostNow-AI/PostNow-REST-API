# Sonora REST API - Documentação

API REST Django com autenticação por email e Google OAuth usando tokens JWT.

## 📚 **Documentação Organizada**

### 🚀 **Início Rápido**

- **[Configuração Inicial](inicio-rapido/configuracao.md)** - Primeiros passos
- **[Variáveis de Ambiente](inicio-rapido/variaveis-ambiente.md)** - Configurações necessárias
- **[Deploy no Vercel](inicio-rapido/deploy-vercel.md)** - Como fazer deploy

### 🔐 **Autenticação**

- **[Google OAuth](autenticacao/google-oauth.md)** - Configuração e uso
- **[JWT Tokens](autenticacao/jwt-tokens.md)** - Sistema de autenticação
- **[Testes com Postman](autenticacao/testes-postman.md)** - Como testar endpoints

### 🤖 **Sistema de IA**

- **[Modelos de IA](ia/modelos-disponiveis.md)** - Gemini, OpenAI, Anthropic
- **[Geração de Ideias](ia/geracao-ideias.md)** - Como funciona

- **[Sistema de Créditos](ia/sistema-creditos.md)** - Compra e uso de créditos

### 💳 **Sistema de Créditos**

- **[Integração Stripe](creditos/stripe.md)** - Pagamentos e webhooks

- **[Gestão de Créditos](creditos/gestao.md)** - Adição e dedução
- **[Transações](creditos/transacoes.md)** - Histórico e auditoria

### 🗄️ **Banco de Dados**

- **[Modelos](banco-dados/modelos.md)** - Estrutura das tabelas
- **[Migrações](banco-dados/migracoes.md)** - Como aplicar mudanças
- **[População](banco-dados/populacao.md)** - Dados iniciais

### 🔧 **Desenvolvimento**

- **[Estrutura do Projeto](desenvolvimento/estrutura.md)** - Organização dos arquivos
- **[Serviços](desenvolvimento/servicos.md)** - Lógica de negócio
- **[Testes](desenvolvimento/testes.md)** - Como testar

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
