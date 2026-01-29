# Instagram Dashboard Integration - Sistema Completo

## 📋 Visão Geral

Sistema completo de integração com Instagram Graph API para buscar dados da conta do usuário e exibir em um dashboard analytics. Projetado para máxima simplicidade e experiência do usuário.

## ✨ Funcionalidades Implementadas

### Core Features
- ✅ **OAuth 2.0 Flow** - Conexão segura via Instagram
- ✅ **Token Management** - Refresh automático antes de expirar (60 dias)
- ✅ **Data Sync** - Sincronização manual com cooldown de 15min
- ✅ **Encryption** - Tokens criptografados com Fernet
- ✅ **Rate Limiting** - Proteção contra limites da API (200 calls/hora)

### Dashboard & Analytics
- ✅ **Métricas em Tempo Real** - Seguidores, impressões, alcance, engajamento
- ✅ **Timeline Analytics** - Histórico diário de métricas
- ✅ **Growth Tracking** - Acompanhamento de crescimento
- ✅ **Engagement Rate** - Cálculo automático de taxa de engajamento

### User Experience
- ✅ **Notificações Inteligentes** - Token expirando, erros, sucessos
- ✅ **Mensagens em Português** - Todas as mensagens de erro traduzidas
- ✅ **Documentação Completa** - Setup técnico + FAQ para usuários
- ✅ **Gamificação** - Achievement + 50 créditos na primeira conexão

### Admin & Monitoring
- ✅ **Admin Dashboard** - Gerenciamento completo via Django Admin
- ✅ **Health Check Endpoint** - Monitoramento de contas e tokens
- ✅ **Audit Logging** - Todas as ações registradas
- ✅ **Analytics Tracking** - Funil de conversão OAuth

## 🗂️ Estrutura do Projeto

```
SocialMediaIntegration/
├── models.py                    # 4 models (Account, Metrics, Notification, Attempt)
├── serializers.py               # Serializers com validação PT-BR
├── views.py                     # 8 API views (Connect, Callback, Status, Sync, etc.)
├── urls.py                      # Rotas /api/v1/social/instagram/*
├── admin.py                     # Admin com badges, filtros, ações em massa
├── services/
│   ├── instagram_oauth_service.py      # OAuth flow completo
│   ├── instagram_service.py            # Instagram Graph API wrapper
│   ├── notification_service.py         # Sistema de notificações
│   └── token_refresh_service.py        # Auto-refresh de tokens
├── utils/
│   └── encryption.py                   # Criptografia Fernet
├── management/commands/
│   └── refresh_instagram_tokens.py     # Cron job diário
└── migrations/
    └── 0001_initial.py                 # Migrations criadas
```

## 🔧 Setup Rápido

### 1. Instalar Dependência

```bash
pip install cryptography
```

### 2. Configurar Environment Variables

Adicione ao `.env`:

```bash
# Instagram Graph API
INSTAGRAM_APP_ID=seu_app_id
INSTAGRAM_APP_SECRET=seu_app_secret
INSTAGRAM_REDIRECT_URI=http://localhost:8000/api/v1/social/instagram/callback/

# Encryption Key (gere uma nova)
INSTAGRAM_TOKEN_ENCRYPTION_KEY=sua_chave_fernet_aqui
```

**Gerar Encryption Key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Migrations

```bash
python manage.py makemigrations SocialMediaIntegration
python manage.py migrate
```

### 4. Testar

```bash
python manage.py runserver

# Test endpoint
curl http://localhost:8000/api/v1/social/instagram/status/ \
  -H "Authorization: Bearer seu_jwt_token"
```

## 📡 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/v1/social/instagram/connect/` | Gera URL de autorização OAuth |
| `POST` | `/api/v1/social/instagram/callback/` | Processa callback OAuth |
| `GET` | `/api/v1/social/instagram/status/` | Status da conexão atual |
| `POST` | `/api/v1/social/instagram/sync/` | Sincronizar dados (manual) |
| `GET` | `/api/v1/social/instagram/metrics/` | Lista métricas (com filtros de data) |
| `DELETE` | `/api/v1/social/instagram/disconnect/` | Desconectar conta |
| `GET` | `/api/v1/social/instagram/notifications/` | Notificações do usuário |
| `GET` | `/api/v1/social/instagram/health/` | Health check (admin only) |

## 🔄 Fluxo de Conexão (OAuth)

```
1. Frontend: GET /api/v1/social/instagram/connect/
   ← Response: { authorization_url, state }

2. User: Clica no authorization_url
   → Redirecionado para Instagram.com
   → Login e autoriza permissões
   → Instagram redireciona para callback com ?code=xxx&state=yyy

3. Frontend: POST /api/v1/social/instagram/callback/
   Body: { code, state }
   ← Backend: Troca code por token, valida account, salva
   ← Response: { success, account, is_first_connection }

4. ✅ Instagram conectado!
   → Notificação enviada
   → Achievement desbloqueado (+50 créditos)
```

## 📊 Models

### InstagramAccount
- Armazena conexão e tokens (encrypted)
- Campos: user, instagram_user_id, username, followers_count, access_token, expires_at
- Methods: `is_token_expiring_soon()`, `days_until_expiration()`

### InstagramMetrics
- Métricas diárias por conta
- Campos: account, date, impressions, reach, engagement, profile_views
- Method: `engagement_rate()`

### InstagramNotification
- Notificações para usuários
- Tipos: token_expiring, sync_error, first_connection, etc.
- Method: `mark_as_read()`

### InstagramConnectionAttempt
- Tracking de tentativas de conexão
- Para analytics de funil
- Campos: user, step, duration_seconds, error_message

## 🔐 Segurança

- **Tokens Criptografados**: Fernet symmetric encryption
- **State Token**: CSRF protection no OAuth flow
- **Cooldown**: 15min entre syncs para evitar rate limit
- **Retry Logic**: 3 tentativas com exponential backoff
- **Audit Logging**: Todas as ações registradas via AuditService

## 🔔 Sistema de Notificações

Notificações automáticas para:

- 🎉 **Primeira conexão** - "Instagram conectado com sucesso!"
- ⚠️ **Token expirando** - 7 dias antes de expirar
- ❌ **Erro de sync** - Rate limit, token inválido, etc.
- ✅ **Sync bem-sucedido** - Com crescimento de seguidores
- 🔌 **Conexão perdida** - Token expirado ou revogado
- 🏆 **Achievement** - Primeira conexão = +50 créditos

## 🛠️ Manutenção

### Cron Job (Token Refresh)

Adicione ao crontab:

```bash
# Refresh tokens diariamente às 3h
0 3 * * * cd /path/to/project && source venv/bin/activate && python manage.py refresh_instagram_tokens
```

Ou via Celery Beat:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'refresh-instagram-tokens': {
        'task': 'SocialMediaIntegration.tasks.refresh_tokens',
        'schedule': crontab(hour=3, minute=0),
    },
}
```

### Monitoramento

**Health Check:**
```bash
curl http://localhost:8000/api/v1/social/instagram/health/ \
  -H "Authorization: Bearer admin_token"
```

**Response:**
```json
{
  "status": "healthy",
  "active_accounts": 150,
  "tokens_expiring_soon": 5,
  "accounts_with_errors": 2,
  "instagram_api_status": "reachable"
}
```

## 📚 Documentação

- **Setup Técnico**: [docs/INSTAGRAM_INTEGRATION_SETUP.md](../docs/INSTAGRAM_INTEGRATION_SETUP.md)
  - Criar app no Meta Developer
  - Configurar OAuth e permissions
  - App Review (produção)
  - Troubleshooting completo

- **FAQ Usuários**: [docs/INSTAGRAM_USER_FAQ.md](../docs/INSTAGRAM_USER_FAQ.md)
  - Como conectar
  - Converter para Business
  - Solução de problemas
  - Desconectar

## 🚀 Próximos Passos (Futuro)

- [ ] **Dashboard Frontend** - Componentes React/Vue para visualizar métricas
- [ ] **Gamificação Avançada** - Mais achievements e badges
- [ ] **Support System** - Tickets in-app com contexto
- [ ] **Onboarding Integration** - Step 4 no CreatorProfile
- [ ] **Vídeo Tutorial** - Gravar e embedar no app
- [ ] **A/B Testing** - Testar diferentes mensagens de conversão

## 🐛 Troubleshooting Comum

### Erro: "No module named 'cryptography'"
```bash
pip install cryptography
```

### Erro: "INSTAGRAM_TOKEN_ENCRYPTION_KEY not found"
Gere e adicione ao `.env`:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Erro: "Invalid state token"
- Cache não está configurado (usa cache padrão do Django)
- State expira em 10min - usuário precisa completar OAuth rápido

### Erro: "Account must be Business"
Usuário precisa converter conta Personal → Business no Instagram App

## 📞 Suporte

- **Email**: suporte@postnow.com
- **Docs**: /docs/INSTAGRAM_*.md
- **Admin**: Django Admin → Social Media Integration

---

**Desenvolvido por**: Equipe PostNow  
**Data**: Janeiro 2026  
**Versão**: 1.0  
**Status**: ✅ Production Ready (após App Review)
