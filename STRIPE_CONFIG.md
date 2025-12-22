# 🔧 Configuração do Stripe

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto Django com as seguintes variáveis:

```bash
# Stripe Configuration
# ⚠️ IMPORTANTE: Substitua pelos valores reais do seu dashboard Stripe

# Modo do Stripe (test ou live)
STRIPE_MODE=test

# Chaves de Teste (Sandbox)
STRIPE_PUBLISHABLE_KEY=pk_test
STRIPE_SECRET_KEY=sk_test
STRIPE_WEBHOOK_SECRET=whsec

# Chaves de Produção (quando estiver pronto)
# STRIPE_PUBLISHABLE_KEY=pk_live_...
# STRIPE_SECRET_KEY=sk_live_...
# STRIPE_WEBHOOK_SECRET=whsec_...

# Configurações do Sistema de Créditos
CREDIT_SYSTEM_ENABLED=True
DEFAULT_CREDIT_BALANCE=0.00

# URLs de Sucesso e Cancelamento
STRIPE_SUCCESS_URL=https://seu-dominio.com/credits/success
STRIPE_CANCEL_URL=https://seu-dominio.com/credits/cancel
```

## Passos para Configuração

### 1. Dashboard Stripe

- Acesse [dashboard.stripe.com](https://dashboard.stripe.com)
- Vá para **Developers > API keys**
- Copie as chaves de teste ou produção

### 2. Webhooks

- Vá para **Developers > Webhooks**
- Clique em **Add endpoint**
- URL: `https://seu-dominio.com/api/v1/credits/stripe/webhook/`
- Eventos: `checkout.session.completed`, `payment_intent.succeeded`, `payment_intent.payment_failed`

### 3. Produtos e Preços

- Vá para **Products**
- Crie os produtos para cada pacote de créditos
- Copie os **Price IDs** e atualize no Django

### 4. Atualizar IDs no Django

Execute o comando para popular os dados:

```bash
# Modo teste
python manage.py populate_credit_system --stripe-mode test

# Modo produção
python manage.py populate_credit_system --stripe-mode production
```

Depois atualize os `stripe_price_id` no admin do Django ou via shell.

## Testando a Configuração

### 1. Verificar Variáveis

```bash
python manage.py shell -c "from django.conf import settings; print(f'Stripe configurado: {bool(settings.STRIPE_SECRET_KEY)}')"
```

### 2. Testar Webhook

Use o Stripe CLI para testar webhooks localmente:

```bash
stripe listen --forward-to localhost:8000/api/v1/credits/stripe/webhook/
```

### 3. Testar Checkout

Acesse a página de créditos no frontend e tente comprar um pacote.

## Solução de Problemas

### Erro: "STRIPE_SECRET_KEY não configurada"

- Verifique se o arquivo `.env` está na raiz do projeto
- Confirme se as variáveis estão sendo carregadas

### Erro: "Assinatura inválida"

- Verifique se o `STRIPE_WEBHOOK_SECRET` está correto
- Confirme se o webhook está apontando para a URL correta

### Erro: "Pacote de créditos não encontrado"

- Verifique se os `stripe_price_id` estão corretos
- Confirme se os produtos existem no Stripe
