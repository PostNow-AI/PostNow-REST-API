# 🏗️ Arquitetura do Sistema PostNow

## Visão Geral

O PostNow é uma plataforma completa de geração de conteúdo para redes sociais usando IA, composta por:

- **Backend**: API REST em Django com integração a múltiplos serviços de IA
- **Frontend**: SPA React com TypeScript e Vite

## 🎯 Fluxo Principal do Sistema

```
┌─────────────┐
│   Usuário   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│     Frontend (React + Vite)         │
│  - Login/Registro                   │
│  - Onboarding (3 etapas)            │
│  - Dashboard IdeaBank               │
│  - Geração de Conteúdo              │
└──────┬──────────────────────────────┘
       │ HTTP/REST API
       ▼
┌─────────────────────────────────────┐
│     Backend (Django REST)           │
│  - Autenticação JWT                 │
│  - Gestão de Perfil                 │
│  - Sistema de Créditos              │
│  - Orquestração de IA               │
└──────┬──────────────────────────────┘
       │
       ├──────────┬──────────┬─────────┐
       ▼          ▼          ▼         ▼
    Google     OpenAI   Anthropic   Stripe
    Gemini     GPT-4    Claude      Payments
```

## 📱 Frontend - Arquitetura React

### Estrutura de Componentes

```
src/
├── App.tsx                      # Componente raiz
├── main.tsx                     # Entry point
│
├── components/                  # Componentes reutilizáveis
│   ├── ui/                     # Design System (shadcn/ui)
│   │   ├── button.tsx          # Botões
│   │   ├── dialog.tsx          # Modais
│   │   ├── input.tsx           # Inputs
│   │   └── ...                 # Outros componentes UI
│   │
│   ├── ideabank/               # Features do IdeaBank
│   │   ├── PostCreationDialog.tsx
│   │   ├── PostList.tsx
│   │   └── PostViewDialog.tsx
│   │
│   ├── DashboardLayout.tsx     # Layout principal
│   ├── ProtectedRoute.tsx      # Guarda de autenticação
│   └── PublicRoute.tsx         # Rotas públicas
│
├── pages/                      # Páginas da aplicação
│   ├── LoginPage.tsx           # Login
│   ├── RegisterPage.tsx        # Registro
│   ├── IdeaBankPage.tsx        # Dashboard principal
│   ├── ProfilePage.tsx         # Perfil do usuário
│   ├── CreditsPage.tsx         # Gestão de créditos
│   └── SubscriptionPage.tsx    # Assinaturas
│
├── contexts/                   # Estado global
│   ├── AuthContext.tsx         # Autenticação
│   ├── OnboardingContext.tsx   # Onboarding
│   └── ThemeContext.tsx        # Tema (light/dark)
│
├── hooks/                      # Hooks customizados
│   ├── useAuth.ts              # Hook de autenticação
│   ├── useCredits.ts           # Hook de créditos
│   └── useSubscription.ts      # Hook de assinaturas
│
├── lib/                        # Utilitários
│   ├── api.ts                  # Cliente Axios
│   ├── auth.ts                 # Lógica de autenticação
│   └── utils.ts                # Funções auxiliares
│
└── types/                      # TypeScript types
    ├── user.ts
    ├── post.ts
    └── ...
```

### Fluxo de Autenticação

```
┌──────────────┐
│ LoginPage    │
└──────┬───────┘
       │ submit
       ▼
┌──────────────┐
│ AuthContext  │──────► localStorage (JWT)
└──────┬───────┘
       │ setUser
       ▼
┌──────────────┐
│ Protected    │
│ Route        │
└──────┬───────┘
       │ redirect
       ▼
┌──────────────┐
│ Dashboard    │
└──────────────┘
```

### Sistema de Roteamento

```typescript
<Routes>
  <Route path="/" element={<PublicRoute />}>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
  </Route>
  
  <Route path="/" element={<ProtectedRoute />}>
    <Route path="/ideabank" element={<IdeaBankPage />} />
    <Route path="/profile" element={<ProfilePage />} />
    <Route path="/credits" element={<CreditsPage />} />
    <Route path="/subscription" element={<SubscriptionPage />} />
  </Route>
</Routes>
```

## 🔧 Backend - Arquitetura Django

### Apps Django

```
PostNow-REST-API/
├── Sonora_REST_API/            # Configurações principais
│   ├── settings.py             # Configurações Django
│   ├── urls.py                 # Rotas principais
│   └── wsgi.py                 # WSGI entry point
│
├── Users/                      # Sistema de usuários
│   ├── models.py               # CustomUser
│   ├── serializers.py          # User serializers
│   ├── views.py                # Auth endpoints
│   └── managers.py             # UserManager
│
├── CreatorProfile/             # Perfil do criador
│   ├── models.py               # CreatorProfile, UserBehavior
│   ├── serializers.py          # Profile serializers
│   ├── views.py                # Profile endpoints
│   └── services/               # Lógica de negócio
│       └── onboarding_service.py
│
├── IdeaBank/                   # Geração de conteúdo
│   ├── models.py               # Post, PostIdea
│   ├── serializers.py          # Post serializers
│   ├── views.py                # Content endpoints
│   ├── gemini_service.py       # Google Gemini
│   └── services/               # Serviços de IA
│       ├── post_ai_service.py         # Orquestrador
│       ├── text_overlay_service.py    # Overlay de texto
│       ├── ai_service_factory.py      # Factory pattern
│       └── base_ai_service.py         # Classe base
│
├── CreditSystem/               # Sistema de créditos
│   ├── models.py               # UserCredits, Transaction, Plan
│   ├── serializers.py          # Credit serializers
│   ├── views.py                # Credit endpoints
│   ├── middleware.py           # Validação de créditos
│   └── services/               # Stripe integration
│       └── stripe_service.py
│
├── AuditSystem/                # Sistema de auditoria
│   ├── models.py               # AuditLog
│   └── middleware.py           # Logging automático
│
└── services/                   # Serviços compartilhados
    ├── google_oauth/           # OAuth Google
    ├── image_generation/       # Geração de imagens
    └── text_generation/        # Geração de texto
```

### Fluxo de Geração de Conteúdo

```
┌──────────────────────┐
│ IdeaBankView         │
│ (generate-content)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ CreditMiddleware     │──► Validar créditos
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ PostAIService        │──► Orquestrador
└──────┬───────────────┘
       │
       ├────────┬────────┬─────────┐
       ▼        ▼        ▼         ▼
   Gemini    OpenAI  Anthropic   Fallback
   
       │
       ▼
┌──────────────────────┐
│ UserCredits          │──► Deduzir créditos
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│ Response + Post      │
└──────────────────────┘
```

### Sistema de Créditos

```python
# Modelo UserCredits
class UserCredits(models.Model):
    user = models.OneToOneField(User)
    balance = models.DecimalField()              # Saldo atual
    monthly_credits = models.IntegerField()      # Créditos mensais do plano
    monthly_credits_allocated = models.IntegerField()  # Créditos do ciclo
    monthly_credits_used = models.IntegerField() # Usado no mês
    last_credit_reset = models.DateTimeField()   # Último reset

# Preços fixos
FIXED_PRICES = {
    'image_generation': Decimal('0.23'),  # R$ 0,23
    'text_generation': Decimal('0.02'),   # R$ 0,02
}

# Transação de crédito
class CreditTransaction(models.Model):
    user = models.ForeignKey(User)
    type = models.CharField(choices=[
        ('usage', 'Usage'),                # Uso
        ('monthly_allocation', 'Monthly')   # Renovação mensal
    ])
    amount = models.DecimalField()         # Valor
    operation_type = models.CharField()    # image/text
```

### Sistema de Assinaturas

```python
# Planos disponíveis
class SubscriptionPlan(models.Model):
    name = models.CharField()              # Nome do plano
    price = models.DecimalField()          # Preço
    monthly_credits = models.IntegerField() # Créditos mensais
    billing_period = models.CharField(choices=[
        ('monthly', 'Monthly'),
        ('semester', 'Semester'),
        ('yearly', 'Yearly')
    ])
    stripe_price_id = models.CharField()   # ID do Stripe

# Assinatura do usuário
class UserSubscription(models.Model):
    user = models.OneToOneField(User)
    plan = models.ForeignKey(SubscriptionPlan)
    status = models.CharField(choices=[
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired')
    ])
    stripe_subscription_id = models.CharField()
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
```

## 🤖 Sistema de IA - Factory Pattern

```python
# Factory de serviços
class AIServiceFactory:
    @staticmethod
    def create_service(provider: str) -> BaseAIService:
        if provider == 'gemini':
            return GeminiAIService()
        elif provider == 'openai':
            return OpenAIService()
        elif provider == 'anthropic':
            return AnthropicService()
        else:
            raise ValueError(f"Unknown provider: {provider}")

# Classe base
class BaseAIService(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def generate_image(self, prompt: str, **kwargs) -> bytes:
        pass
    
    @abstractmethod
    def get_cost(self, operation: str) -> Decimal:
        pass

# Orquestrador principal
class PostAIService:
    def __init__(self):
        self.factory = AIServiceFactory()
    
    def generate_content(self, post_type: str, context: dict) -> dict:
        # Seleciona melhor provedor baseado em custo
        provider = self._select_best_provider()
        service = self.factory.create_service(provider)
        
        # Gera prompt personalizado
        prompt = self._build_prompt(post_type, context)
        
        # Gera conteúdo
        text = service.generate_text(prompt)
        
        # Deduz créditos
        self._deduct_credits(user, 'text_generation')
        
        return {'text': text, 'cost': cost}
```

## 🎨 Sistema de Overlay de Texto

```python
class TextOverlayService:
    # 26 fontes Google disponíveis
    FONTS = [
        'Poppins-Bold.ttf',
        'Montserrat-Bold.ttf',
        'Inter-Bold.ttf',
        'Oswald-Bold.ttf',
        # ... mais 22 fontes
    ]
    
    # 9 posições disponíveis
    POSITIONS = [
        'top-left', 'top-center', 'top-right',
        'center-left', 'center-center', 'center-right',
        'bottom-left', 'bottom-center', 'bottom-right'
    ]
    
    def apply_overlay(self, image: Image, overlay_data: dict) -> Image:
        # Carregar fonte
        font = ImageFont.truetype(overlay_data['font-family'], size)
        
        # Calcular posição
        position = self._calculate_position(
            overlay_data['location'],
            image.size,
            text_size
        )
        
        # Aplicar efeitos
        if overlay_data.get('drop-shadow'):
            self._apply_shadow(draw, text, position, shadow_config)
        
        if overlay_data.get('stroke'):
            self._apply_stroke(draw, text, position, stroke_config)
        
        # Desenhar texto
        draw.text(position, text, fill=color, font=font)
        
        return image
```

## 🔒 Sistema de Autenticação

### JWT Tokens

```python
# Settings Django
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Endpoints
POST /api/v1/auth/login/        # Retorna access + refresh token
POST /api/v1/auth/refresh/      # Renova access token
POST /api/v1/auth/logout/       # Invalida tokens
```

### Google OAuth Flow

```
1. Frontend → Backend: solicita URL OAuth
2. Backend → Frontend: retorna URL do Google
3. Frontend → Google: redireciona usuário
4. Google → Frontend: callback com code
5. Frontend → Backend: envia code
6. Backend → Google: troca code por tokens
7. Google → Backend: retorna user info
8. Backend → Database: cria/atualiza user
9. Backend → Frontend: retorna JWT
10. Frontend → LocalStorage: armazena JWT
```

## 📊 Banco de Dados - Modelos Principais

```sql
-- Users
User (id, email, name, is_active, date_joined)

-- CreatorProfile
CreatorProfile (
    id, user_id, 
    professional_name, profession,
    business_name, specialization,
    target_audience, brand_colors,
    voice_tone, logo
)

-- IdeaBank
Post (
    id, user_id, creator_profile_id,
    type, name, objective,
    generated_text, image_url,
    overlay_data, created_at
)

-- CreditSystem
UserCredits (
    id, user_id, balance,
    monthly_credits, monthly_credits_used,
    last_credit_reset
)

CreditTransaction (
    id, user_id, type, amount,
    operation_type, created_at
)

SubscriptionPlan (
    id, name, price, monthly_credits,
    billing_period, stripe_price_id
)

UserSubscription (
    id, user_id, plan_id, status,
    stripe_subscription_id,
    current_period_start, current_period_end
)
```

## 🔄 API - Padrões de Response

### Sucesso
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Post Title",
    ...
  },
  "message": "Operation completed successfully"
}
```

### Erro
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_CREDITS",
    "message": "Créditos insuficientes",
    "details": {
      "required": "0.23",
      "available": "0.10"
    }
  }
}
```

### Validação
```json
{
  "success": false,
  "errors": {
    "email": ["Este campo é obrigatório"],
    "password": ["Senha muito curta"]
  }
}
```

## 🚀 Deploy - Arquitetura de Produção

```
┌────────────────────────────────────┐
│         Vercel Edge Network        │
│  - SSL/TLS automático              │
│  - CDN global                      │
│  - Cache inteligente               │
└──────┬─────────────────────────────┘
       │
       ├────────────┬─────────────────┐
       ▼            ▼                 ▼
┌─────────────┐ ┌──────────────┐ ┌──────────┐
│  Frontend   │ │   Backend    │ │ Database │
│   React     │ │    Django    │ │PostgreSQL│
│   (Vercel)  │ │   (Vercel)   │ │ (Ext)    │
└─────────────┘ └──────────────┘ └──────────┘
```

## 📈 Performance e Otimizações

### Frontend
- Code splitting por rota
- Lazy loading de componentes
- Image optimization (lazy + placeholder)
- TanStack Query para cache de API
- Bundle optimization (tree shaking)

### Backend
- Database indexing em campos frequentes
- Query optimization (select_related/prefetch_related)
- Cache de resultados com Redis (opcional)
- Compression middleware (GZip)
- Static files via CDN (WhiteNoise)

## 🔐 Segurança

### Frontend
- XSS prevention (React escaping)
- CSRF tokens em requests
- Secure cookies (HttpOnly + Secure + SameSite)
- Content Security Policy headers

### Backend
- JWT authentication
- Rate limiting
- SQL injection prevention (Django ORM)
- Password hashing (PBKDF2)
- CORS configuration
- Environment variables para secrets

---

💡 **Esta arquitetura foi desenhada para ser escalável, mantível e segura!**
