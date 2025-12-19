# Mailjet Webhook - Guia Rápido 🚀

## ✅ Status da Implementação

**TUDO PRONTO E TESTADO!** ✨

Os testes confirmaram que o sistema está funcionando perfeitamente:

- ✅ Endpoint criado e funcional
- ✅ Eventos de "open" registrados como `email_opened`
- ✅ Eventos de "click" registrados como `email_clicked`
- ✅ Eventos de "bounce" registrados como `email_bounced`
- ✅ Múltiplos eventos processados corretamente
- ✅ Dados salvos no AuditLog com sucesso

## 📍 URL do Webhook

```
POST /api/v1/audit/webhooks/mailjet/
```

**Produção:** `https://seu-dominio.com/api/v1/audit/webhooks/mailjet/`

**Desenvolvimento (com ngrok):**

```bash
ngrok http 8000
# Usar: https://xxxxx.ngrok.io/api/v1/audit/webhooks/mailjet/
```

## 🎯 Configuração Rápida no Mailjet

### 1. Acesse o Painel Mailjet

[https://app.mailjet.com/account/settings](https://app.mailjet.com/account/settings)

### 2. Configure o Webhook

```
📍 Localização: Account Settings > Event Tracking (Webhooks)
🔘 Botão: "Add New Webhook"

📝 Configurações:
   URL: https://seu-dominio.com/api/v1/audit/webhooks/mailjet/
   Method: POST
   
✅ Eventos a Selecionar:
   [x] Open    (Email aberto)
   [x] Click   (Link clicado)
   [x] Bounce  (Email rejeitado)
   [ ] Spam    (Opcional)
   [ ] Blocked (Opcional)
   [ ] Unsub   (Opcional)
```

### 3. Salvar e Testar

Clique em **"Test"** no painel Mailjet para enviar um evento de teste.

## 🧪 Teste Local Rápido

```bash
# Teste simples com curl
curl -X POST http://localhost:8000/api/v1/audit/webhooks/mailjet/ \
  -H "Content-Type: application/json" \
  -d '[{
    "event": "open",
    "time": 1733000000,
    "MessageID": 123456789,
    "email": "test@example.com",
    "ip": "127.0.0.1",
    "geo": "BR",
    "agent": "Mozilla/5.0"
  }]'

# Resposta esperada:
# {"success":true,"message":"Processados 1 eventos com sucesso",...}
```

Ou use o script de teste:

```bash
python scripts/test_mailjet_webhook.py
```

## 📊 Verificar Eventos Registrados

### No Django Admin

```
/admin/AuditSystem/auditlog/

Filtros:
- Operation category: email
- Action: email_opened / email_clicked / email_bounced
```

### No Python Shell

```python
from AuditSystem.models import AuditLog

# Ver últimos eventos
events = AuditLog.objects.filter(
    action='email_opened'
).order_by('-timestamp')[:5]

for e in events:
    print(f"{e.details['email']} - {e.timestamp}")

# Contar aberturas hoje
from datetime import date

today_opens = AuditLog.objects.filter(
    action='email_opened',
    timestamp__date=date.today()
).count()
print(f"Aberturas hoje: {today_opens}")
```

## 📈 Análise Rápida de Métricas

### Taxa de Abertura (últimos 7 dias)

```python
from datetime import timedelta
from django.utils import timezone
from AuditSystem.models import AuditLog

last_week = timezone.now() - timedelta(days=7)

sent = AuditLog.objects.filter(
    action='email_sent',
    timestamp__gte=last_week
).count()

opened = AuditLog.objects.filter(
    action='email_opened',
    timestamp__gte=last_week
).count()

if sent > 0:
    rate = (opened / sent) * 100
    print(f"📊 Taxa de Abertura: {rate:.2f}%")
    print(f"📧 Emails Enviados: {sent}")
    print(f"👀 Emails Abertos: {opened}")
```

### Top 5 Usuários Mais Engajados

```python
from django.db.models import Count

top_users = AuditLog.objects.filter(
    action__in=['email_opened', 'email_clicked']
).values('user__username', 'user__email').annotate(
    count=Count('id')
).order_by('-count')[:5]

for user in top_users:
    print(f"🏆 {user['user__username']}: {user['count']} interações")
```

## 🔍 Estrutura dos Dados Salvos

Cada evento do Mailjet é salvo como:

```python
AuditLog
{
    id: 13294,
    user: User | None,  # Identificado automaticamente pelo email
    operation_category: 'email',
    action: 'email_opened',  # ou email_clicked, email_bounced
    status: 'success',
    resource_type: 'Email',
    resource_id: '123456789',  # MessageID do Mailjet
    timestamp: '2025-12-19 12:47:36',
    details: {
        'event_type': 'open',
        'email': 'test@example.com',
        'message_id': '123456789',
        'ip': '127.0.0.1',
        'user_agent': 'Mozilla/5.0',
        'geo': 'BR',
        'timestamp': 1733000000
    }
}
```

## 🎨 Eventos Suportados

| Evento Mailjet | Ação no AuditLog | Descrição                  |
|----------------|------------------|----------------------------|
| `open`         | `email_opened`   | Email foi aberto           |
| `click`        | `email_clicked`  | Link no email foi clicado  |
| `bounce`       | `email_bounced`  | Email foi rejeitado        |
| `spam`         | `email_failed`   | Marcado como spam          |
| `blocked`      | `email_failed`   | Email bloqueado            |
| `unsub`        | `email_failed`   | Usuário cancelou inscrição |

## 🚨 Troubleshooting

### Webhook não recebe eventos

```bash
# 1. Verificar se o servidor está acessível
curl -I https://seu-dominio.com/api/v1/audit/webhooks/mailjet/

# 2. Testar localmente com ngrok (desenvolvimento)
ngrok http 8000

# 3. Verificar logs de erro
tail -f logs/error.log
```

### Eventos não aparecem no AuditLog

```python
# Verificar erros do sistema
from AuditSystem.models import AuditLog

errors = AuditLog.objects.filter(
    action='system_error',
    error_message__icontains='mailjet'
).order_by('-timestamp')[:5]

for e in errors:
    print(f"❌ {e.timestamp}: {e.error_message}")
```

## 📚 Documentação Completa

Para mais detalhes, consulte:

- **Configuração Detalhada:** `docs/MAILJET_WEBHOOK_SETUP.md`
- **Resumo da Implementação:** `docs/MAILJET_WEBHOOK_IMPLEMENTATION.md`
- **Script de Teste:** `scripts/test_mailjet_webhook.py`

## ✨ Próximos Passos

1. ✅ **Implementação completa** - FEITO!
2. ✅ **Testes locais** - FEITO!
3. ⬜ **Configurar no Mailjet** - Aguardando URL de produção
4. ⬜ **Monitorar primeiros eventos** - Após configuração
5. ⬜ **Criar dashboard de métricas** (Opcional)
6. ⬜ **Adicionar alertas** (Opcional)

## 🎉 Resultado dos Testes

```
============================================================
ESTATÍSTICAS POR TIPO DE EVENTO (Testes Realizados)
============================================================
email_opened: 1 evento   ✅
email_clicked: 2 eventos ✅
email_bounced: 2 eventos ✅

Todos os eventos foram registrados corretamente no banco de dados!
```

---

**Implementado em:** 19 de Dezembro de 2025  
**Status:** ✅ PRONTO PARA PRODUÇÃO  
**Testado:** ✅ SIM

