# 📧 Webhook Mailjet - Implementação Completa

## 🎯 Resumo

Sistema completo para rastrear eventos de email (aberturas, cliques, bounces) enviados pelo Mailjet através de webhooks,
registrando tudo no AuditLog do PostNow.

## ✅ Status

**IMPLEMENTADO E TESTADO** - Pronto para produção!

## 📁 Estrutura de Arquivos

```
PostNow-REST-API/
│
├── AuditSystem/
│   ├── models.py              # ✏️ Modificado - Adicionadas ações email_opened, email_clicked
│   ├── views.py               # ✏️ Modificado - Endpoint mailjet_webhook() criado
│   ├── urls.py                # ✏️ Modificado - Rota webhooks/mailjet/ adicionada
│   └── migrations/
│       └── 0007_alter_auditlog_action.py  # ✨ Criado e aplicado
│
├── docs/
│   ├── MAILJET_WEBHOOK_QUICK_START.md     # 🚀 Guia rápido
│   ├── MAILJET_WEBHOOK_SETUP.md           # 📖 Documentação completa
│   ├── MAILJET_WEBHOOK_IMPLEMENTATION.md  # 📋 Resumo da implementação
│   └── README_MAILJET_WEBHOOK.md          # 📄 Este arquivo
│
└── scripts/
    └── test_mailjet_webhook.py   # 🧪 Script de testes
```

## 🚀 Início Rápido

### 1. O Endpoint Já Está Funcionando!

```
POST /api/v1/audit/webhooks/mailjet/
```

### 2. Configurar no Painel Mailjet

1. Acesse: [Mailjet Account Settings](https://app.mailjet.com/account/settings)
2. Vá em: **Event Tracking (Webhooks)**
3. Adicione a URL: `https://seu-dominio.com/api/v1/audit/webhooks/mailjet/`
4. Selecione eventos: **Open**, **Click**, **Bounce**
5. Salve e teste!

### 3. Testar Localmente

```bash
# Opção 1: Com curl
curl -X POST http://localhost:8000/api/v1/audit/webhooks/mailjet/ \
  -H "Content-Type: application/json" \
  -d '[{"event":"open","time":1733000000,"MessageID":123,"email":"test@example.com"}]'

# Opção 2: Com o script de teste
python scripts/test_mailjet_webhook.py

# Opção 3: Com ngrok (para testar com Mailjet real)
ngrok http 8000
# Use a URL do ngrok no painel Mailjet
```

## 📊 Como Funciona

```
┌─────────────┐
│   Mailjet   │  Usuário abre email
│   Servers   │  ──────────────────────┐
└──────┬──────┘                        │
       │                               │
       │ POST webhook event            │
       │ (open, click, bounce)         ▼
       │                          ┌──────────┐
       │                          │  Email   │
       ▼                          │  Client  │
┌─────────────────────────────┐  └──────────┘
│  PostNow API                │
│  /api/v1/audit/webhooks/    │
│         mailjet/            │
└──────────┬──────────────────┘
           │
           │ 1. Recebe evento
           │ 2. Identifica usuário (por email)
           │ 3. Mapeia evento → ação
           │ 4. Salva no AuditLog
           ▼
    ┌─────────────┐
    │  AuditLog   │
    │  Database   │
    └─────────────┘
           │
           │ Análise de dados
           ▼
    ┌─────────────┐
    │  Métricas   │
    │  Dashboard  │
    └─────────────┘
```

## 🎯 Eventos Suportados

| Evento  | Ação no AuditLog | Status         |
|---------|------------------|----------------|
| open    | email_opened     | ✅ Testado      |
| click   | email_clicked    | ✅ Testado      |
| bounce  | email_bounced    | ✅ Testado      |
| spam    | email_failed     | ✅ Implementado |
| blocked | email_failed     | ✅ Implementado |
| unsub   | email_failed     | ✅ Implementado |

## 💾 Dados Salvos

Cada evento é salvo no `AuditLog` com:

```python
{
    "operation_category": "email",
    "action": "email_opened",  # ou email_clicked, email_bounced
    "status": "success",
    "user": User,  # Identificado automaticamente pelo email
    "resource_type": "Email",
    "resource_id": "MessageID",
    "details": {
        "event_type": "open",
        "email": "usuario@example.com",
        "message_id": "123456789",
        "ip": "127.0.0.1",
        "user_agent": "Mozilla/5.0...",
        "geo": "BR",
        "timestamp": 1733000000,
        # ... outros dados do Mailjet
    }
}
```

## 📈 Exemplos de Análise

### Taxa de Abertura

```python
from AuditSystem.models import AuditLog
from datetime import timedelta
from django.utils import timezone

last_week = timezone.now() - timedelta(days=7)
sent = AuditLog.objects.filter(action='email_sent', timestamp__gte=last_week).count()
opened = AuditLog.objects.filter(action='email_opened', timestamp__gte=last_week).count()
rate = (opened / sent * 100) if sent > 0 else 0
print(f"Taxa de Abertura: {rate:.2f}%")
```

### Usuários Mais Engajados

```python
from django.db.models import Count

top_users = AuditLog.objects.filter(
    action='email_opened'
).values('user__username').annotate(
    count=Count('id')
).order_by('-count')[:10]
```

## 📚 Documentação

### Para Usuários

- **[🚀 Guia Rápido](./MAILJET_WEBHOOK_QUICK_START.md)** - Para começar agora!
- **[📖 Configuração Completa](./MAILJET_WEBHOOK_SETUP.md)** - Todas as opções e detalhes

### Para Desenvolvedores

- **[📋 Resumo da Implementação](./MAILJET_WEBHOOK_IMPLEMENTATION.md)** - O que foi feito
- **[🧪 Script de Testes](../scripts/test_mailjet_webhook.py)** - Testar o endpoint

### Referências Externas

- [Mailjet Webhooks Documentation](https://dev.mailjet.com/email/guides/webhooks/)
- [Mailjet Event Types](https://dev.mailjet.com/email/reference/webhook/)

## 🔒 Segurança

### Atual

- ✅ CSRF exempt (necessário para webhooks)
- ✅ AllowAny permission (Mailjet precisa acessar)
- ✅ Validação de payload
- ✅ Tratamento de exceções

### Melhorias Futuras (Opcionais)

- [ ] Token de verificação compartilhado
- [ ] Whitelist de IPs do Mailjet
- [ ] Rate limiting
- [ ] Logging de tentativas suspeitas

## 🧪 Testes Realizados

```
✅ Email Opened Event  - PASSOU
✅ Email Clicked Event - PASSOU  
✅ Email Bounced Event - PASSOU
✅ Multiple Events     - PASSOU

Resultado:
- 1 evento de email_opened registrado
- 2 eventos de email_clicked registrados
- 2 eventos de email_bounced registrados

Todos os dados foram salvos corretamente no banco de dados!
```

## 🎉 Pronto para Usar!

A implementação está **completa e testada**. Próximos passos:

1. ✅ **Código implementado** - FEITO
2. ✅ **Testes locais** - FEITO
3. ⬜ **Configurar no Mailjet** - Aguardando deploy/URL de produção
4. ⬜ **Monitorar eventos** - Após configuração
5. ⬜ **Analisar métricas** - Após coleta de dados

## 💡 Suporte

Se precisar de ajuda:

1. Consulte os arquivos de documentação acima
2. Execute o script de teste para verificar o endpoint
3. Verifique os logs do Django para erros
4. Consulte a documentação oficial do Mailjet

---

**Data de Implementação:** 19 de Dezembro de 2025  
**Versão:** 1.0  
**Status:** ✅ PRODUCTION READY

