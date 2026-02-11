# Sistema de Assinaturas - Documentação Técnica

## Visão Geral

O sistema de assinaturas integra o Stripe para processamento de pagamentos e gerenciamento de planos. Este documento descreve a arquitetura, endpoints e fluxos do sistema.

## Arquitetura

### Componentes Principais

```
CreditSystem/
├── models.py                    # SubscriptionPlan, UserSubscription
├── views.py                     # Views refatoradas (thin controllers)
├── serializers.py               # Serializers para API
└── services/
    ├── subscription_checkout_service.py  # Lógica de checkout
    └── subscription_service.py           # Processamento de webhooks
```

### Modelo de Dados

#### SubscriptionPlan
```python
{
    "id": int,
    "name": str,           # "Plano Mensal", "Plano Anual"
    "interval": str,       # "monthly", "yearly", "lifetime"
    "price": Decimal,      # Preço em BRL
    "monthly_credits": Decimal,
    "stripe_price_id": str,  # price_xxxxx do Stripe
    "is_active": bool
}
```

#### UserSubscription
```python
{
    "id": int,
    "user": User,
    "plan": SubscriptionPlan,
    "status": str,  # "active", "cancelled", "pending_payment"
    "start_date": datetime,
    "end_date": datetime | None,
    "stripe_subscription_id": str | None
}
```

## Endpoints da API

### Listar Planos (Público)
```http
GET /api/v1/credits/plans/
```

**Response 200:**
```json
[
    {
        "id": 1,
        "name": "Plano Mensal",
        "interval": "monthly",
        "price": "49.90",
        "monthly_credits": "100.00",
        "is_active": true
    }
]
```

### Criar Checkout Session (Autenticado)
```http
POST /api/v1/credits/checkout/
Authorization: Bearer <token>
Content-Type: application/json

{
    "plan_id": 1
}
```

**Response 200 (Sucesso):**
```json
{
    "success": true,
    "checkout_url": "https://checkout.stripe.com/c/pay/..."
}
```

**Response 200 (Já assinante do mesmo plano):**
```json
{
    "success": true,
    "message": "Você já está neste plano",
    "already_on_plan": true,
    "plan": "Plano Mensal"
}
```

**Response 409 (Upgrade necessário):**
```json
{
    "success": false,
    "message": "Você já possui uma assinatura ativa. Envie \"upgrade\": true para alterar o plano.",
    "upgrade_available": true,
    "current_plan": "Plano Mensal",
    "requested_plan": "Plano Anual"
}
```

### Upgrade de Plano
```http
POST /api/v1/credits/checkout/
Authorization: Bearer <token>
Content-Type: application/json

{
    "plan_id": 2,
    "upgrade": true
}
```

**Response 200 (Upgrade bem-sucedido):**
```json
{
    "success": true,
    "message": "Upgrade de assinatura realizado com sucesso.",
    "upgraded": true,
    "previous_plan": "Plano Mensal",
    "new_plan": "Plano Anual"
}
```

### Assinatura Atual (Autenticado)
```http
GET /api/v1/credits/subscription/current/
Authorization: Bearer <token>
```

**Response 200:**
```json
{
    "id": 1,
    "plan": {...},
    "status": "active",
    "start_date": "2026-02-10T00:00:00Z",
    "end_date": null
}
```

**Response 404 (Sem assinatura):**
```json
{
    "detail": "No active subscription found"
}
```

### Cancelar Assinatura
```http
POST /api/v1/credits/subscription/cancel/
Authorization: Bearer <token>
```

## Fluxos

### Fluxo de Nova Assinatura

```
1. Frontend solicita checkout
   POST /api/v1/credits/checkout/ {plan_id: 1}

2. Backend cria Stripe Checkout Session
   - Valida plano
   - Verifica assinatura existente
   - Cria session com trial_period_days

3. Frontend redireciona para Stripe
   window.location.href = checkout_url

4. Usuário completa pagamento no Stripe

5. Stripe envia webhook
   POST /api/v1/credits/webhooks/subscription/
   Event: customer.subscription.created

6. Backend processa webhook
   - Cria UserSubscription
   - Define créditos do usuário
   - Logs de auditoria

7. Stripe redireciona para success_url
```

### Fluxo de Upgrade

```
1. Usuário com assinatura ativa solicita novo plano
   POST /api/v1/credits/checkout/ {plan_id: 2}

2. Backend retorna upgrade_available: true (409)

3. Frontend confirma upgrade
   POST /api/v1/credits/checkout/ {plan_id: 2, upgrade: true}

4. Backend modifica assinatura no Stripe
   stripe.Subscription.modify()
   - proration_behavior: 'create_prorations'

5. Atualiza UserSubscription localmente
   - Novo plano
   - Reset de créditos
```

## Service Layer

### SubscriptionCheckoutService

Classe responsável por encapsular a lógica de checkout:

```python
from CreditSystem.services.subscription_checkout_service import (
    SubscriptionCheckoutService,
    CheckoutResult
)

# Uso
service = SubscriptionCheckoutService(user, plan_id)

# 1. Validar plano
result = service.validate_plan()
if not result.success:
    return Response(result.message, status=result.status_code)

# 2. Verificar assinatura existente
existing = service.check_existing_subscription()
if existing:
    return Response(existing.data)

# 3. Processar upgrade ou criar checkout
if service.existing_subscription:
    result = service.handle_upgrade(upgrade_requested=True)
else:
    result = service.create_checkout_session()
```

### CheckoutResult

Dataclass para padronizar respostas:

```python
@dataclass
class CheckoutResult:
    success: bool
    message: str
    data: Optional[dict] = None
    status_code: int = 200
```

## Configuração

### Variáveis de Ambiente

```env
# Stripe Keys
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Frontend URL (para redirects)
FRONTEND_URL=http://localhost:3000

# Trial period
SUBSCRIPTION_TRIAL_DAYS=10
```

### Settings Django

```python
# settings.py
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
SUBSCRIPTION_TRIAL_DAYS = 10
```

## Testes

### Executar Testes

```bash
# Ativar venv
source venv/bin/activate

# Rodar testes do checkout
python manage.py test CreditSystem.tests.test_stripe_checkout --keepdb -v 2
```

### Cobertura de Testes

| Teste | Descrição |
|-------|-----------|
| `test_checkout_requires_authentication` | Checkout requer login |
| `test_checkout_requires_plan_id` | plan_id é obrigatório |
| `test_checkout_invalid_plan_returns_404` | Plano inexistente |
| `test_checkout_plan_without_stripe_id_returns_503` | Plano sem Stripe ID |
| `test_checkout_success` | Checkout criado com sucesso |
| `test_checkout_includes_trial_period` | Trial configurado corretamente |
| `test_same_plan_returns_already_subscribed` | Mesmo plano detectado |
| `test_different_plan_requires_upgrade_flag` | Upgrade requer flag |
| `test_active_subscription_returns_data` | Retorna assinatura ativa |
| `test_no_subscription_returns_404` | 404 sem assinatura |

## Webhooks

### Endpoint
```
POST /api/v1/credits/webhooks/subscription/
```

### Eventos Processados

| Evento | Ação |
|--------|------|
| `customer.subscription.created` | Cria UserSubscription |
| `customer.subscription.updated` | Atualiza status |
| `customer.subscription.deleted` | Marca como cancelada |
| `invoice.payment_succeeded` | Reset de créditos |
| `invoice.payment_failed` | Marca pagamento pendente |
| `checkout.session.completed` | Processa compras lifetime |

### Idempotência

O webhook verifica se a assinatura já existe antes de criar:

```python
existing_sub = UserSubscription.objects.filter(
    stripe_subscription_id=stripe_subscription_id
).first()
if existing_sub:
    return {'status': 'success', 'message': 'Assinatura já registrada'}
```

## Frontend Integration

### Config Centralizada

```typescript
// src/config/subscription.ts
export const SUBSCRIPTION_CONFIG = {
  TRIAL_DAYS: 10,
  PLAN_INTERVAL_MAP: {
    monthly: "monthly",
    annual: "yearly",
  },
} as const;
```

### Hook de Checkout

```typescript
import { useCreateCheckoutSession } from '@/features/Subscription/hooks/useSubscription';

const { mutateAsync, isPending } = useCreateCheckoutSession();

const handleCheckout = async (planId: number) => {
  await mutateAsync({
    plan_id: planId,
    success_url: `${origin}/?checkout=success`,
    cancel_url: `${origin}/onboarding?checkout=cancelled`,
  });
  // Redireciona automaticamente para Stripe
};
```

## Troubleshooting

### Stripe Price ID não encontrado

```
Error: No such price: 'price_xxx'
```

**Solução:** Verificar se está usando Price IDs do ambiente correto (test vs live):
- Test keys: usar Price IDs criados em test mode
- Live keys: usar Price IDs criados em live mode

### Webhook não processa

1. Verificar `STRIPE_WEBHOOK_SECRET` está configurado
2. Verificar assinatura do webhook: `stripe listen --forward-to localhost:8000/api/v1/credits/webhooks/subscription/`
3. Verificar logs: `tail -f /tmp/stripe_subscription_webhook_debug.log`

### Trial não aparece

Verificar `SUBSCRIPTION_TRIAL_DAYS` em settings.py e que o plano não é `lifetime`.
