# Sistema de Email - PostNow

Documentação consolidada do sistema de envio e rastreamento de emails do PostNow.

---

## Visao Geral

O PostNow utiliza o **Mailjet** como provedor de email para:

- Envio de emails transacionais (oportunidades, contexto semanal, etc.)
- Rastreamento de eventos (aberturas, cliques, bounces)
- Auditoria completa no AuditLog

### Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PostNow   │────►│   Mailjet   │────►│  Usuario    │
│    API      │     │   Servers   │     │   Email     │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                          │                    │
                          │  Webhook           │ Abre/Clica
                          │  (eventos)         │
                          ▼                    │
                   ┌─────────────┐             │
                   │  AuditLog   │◄────────────┘
                   │  Database   │
                   └─────────────┘
```

---

## Configuracao do Mailjet

### Credenciais

As credenciais do Mailjet sao configuradas via variaveis de ambiente:

```bash
MAILJET_API_KEY=<sua_api_key>
MAILJET_SECRET_KEY=<sua_secret_key>
```

### Endpoint do Webhook

```
POST /api/v1/audit/webhooks/mailjet/
```

**URL Producao:** `https://postnow.com.br/api/v1/audit/webhooks/mailjet/`

### Configuracao no Painel Mailjet

1. Acesse [Mailjet Account Settings](https://app.mailjet.com/account/settings)
2. Va para **Event Tracking (Webhooks)**
3. Clique em **Add New Webhook**
4. Configure:
   - **URL**: `https://postnow.com.br/api/v1/audit/webhooks/mailjet/`
   - **Method**: POST
   - **Eventos**: Open, Click, Bounce (recomendados)
5. Salve e teste

### Eventos Rastreados

| Evento Mailjet | Acao no AuditLog | Descricao                  |
|----------------|------------------|----------------------------|
| `open`         | `email_opened`   | Email foi aberto           |
| `click`        | `email_clicked`  | Link no email foi clicado  |
| `bounce`       | `email_bounced`  | Email foi rejeitado        |
| `spam`         | `email_failed`   | Marcado como spam          |
| `blocked`      | `email_failed`   | Email bloqueado            |
| `unsub`        | `email_failed`   | Usuario cancelou inscricao |

### Dados Salvos no AuditLog

```python
{
    "operation_category": "email",
    "action": "email_opened",
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
        "timestamp": 1733000000
    }
}
```

---

## Configuracao SPF/DNS

### Problema Conhecido

O dominio `postnow.com.br` pode ter **dois registros SPF separados**, o que e invalido (RFC 7208).

**Incorreto:**
```
TXT: "v=spf1 include:spf.umbler.com ~all"
TXT: "v=spf1 include:spf.mailjet.com ?all"
```

**Correto (unificado):**
```
v=spf1 include:spf.umbler.com include:spf.mailjet.com ~all
```

### Como Corrigir

1. Acesse o painel DNS (Registro.br ou Umbler)
2. Localize registros TXT com `v=spf1`
3. Remova os dois registros antigos
4. Adicione um novo registro:
   - **Tipo**: TXT
   - **Nome**: @ (ou vazio)
   - **Valor**: `v=spf1 include:spf.umbler.com include:spf.mailjet.com ~all`
   - **TTL**: 3600

### Verificacao

```bash
# Verificar SPF atual
dig postnow.com.br TXT +short

# Resultado esperado (apenas UMA linha com v=spf1):
"v=spf1 include:spf.umbler.com include:spf.mailjet.com ~all"
```

### Servicos Afetados

| Servico    | Funcao                                   |
|------------|------------------------------------------|
| **Umbler** | Hospedagem de caixas @postnow.com.br     |
| **Mailjet**| Envio de emails transacionais do sistema |

---

## Arquivos Relacionados

### Codigo

```
AuditSystem/
├── models.py           # Eventos: email_opened, email_clicked, email_bounced
├── views.py            # Endpoint mailjet_webhook()
├── urls.py             # Rota webhooks/mailjet/
└── migrations/
    └── 0007_alter_auditlog_action.py

ClientContext/
├── services/opportunities_generation_service.py  # Envio de emails
└── views.py                                       # Endpoints que disparam emails
```

### Scripts

```
scripts/
├── test_mailjet_webhook.py      # Testes do webhook
└── mailjet_webhook_queries.py   # Exemplos de analise
```

---

## Analise de Metricas

### Taxa de Abertura

```python
from AuditSystem.models import AuditLog
from datetime import timedelta
from django.utils import timezone

last_week = timezone.now() - timedelta(days=7)

sent = AuditLog.objects.filter(
    action='email_sent',
    timestamp__gte=last_week
).count()

opened = AuditLog.objects.filter(
    action='email_opened',
    timestamp__gte=last_week
).count()

rate = (opened / sent * 100) if sent > 0 else 0
print(f"Taxa de Abertura: {rate:.2f}%")
```

### Usuarios Mais Engajados

```python
from django.db.models import Count

top_users = AuditLog.objects.filter(
    action__in=['email_opened', 'email_clicked']
).values('user__username', 'user__email').annotate(
    count=Count('id')
).order_by('-count')[:10]

for user in top_users:
    print(f"{user['user__username']}: {user['count']} interacoes")
```

### Verificar no Django Admin

1. Acesse `/admin/AuditSystem/auditlog/`
2. Filtre por:
   - **Operation Category**: email
   - **Action**: email_opened / email_clicked / email_bounced

---

## Troubleshooting

### Webhook nao recebe eventos

1. **Verificar URL acessivel:**
   ```bash
   curl -I https://postnow.com.br/api/v1/audit/webhooks/mailjet/
   ```

2. **Desenvolvimento local (usar ngrok):**
   ```bash
   ngrok http 8000
   # Usar URL gerada no Mailjet
   ```

3. **Verificar logs:**
   ```bash
   tail -f logs/error.log
   ```

### Eventos nao aparecem no AuditLog

```python
from AuditSystem.models import AuditLog

errors = AuditLog.objects.filter(
    action='system_error',
    error_message__icontains='mailjet'
).order_by('-timestamp')[:5]

for e in errors:
    print(f"{e.timestamp}: {e.error_message}")
```

### Usuario nao identificado

Se o email nao corresponde a um usuario:
- O evento ainda e registrado
- `user` sera `null` no AuditLog
- O email fica em `details['email']`

### SPF nao validado no Mailjet

```bash
# Via API
curl -X POST "https://api.mailjet.com/v3/REST/dns/<ID>/check" \
  -u "$MJ_APIKEY_PUBLIC:$MJ_APIKEY_PRIVATE"
```

Ou: Dashboard Mailjet > Sender domains > postnow.com.br > Check DNS

---

## Seguranca

### Implementado

- CSRF exempt (necessario para webhooks externos)
- Validacao de payload
- Tratamento de excecoes
- Logging de erros

### Melhorias Futuras

- [ ] Token de verificacao compartilhado com Mailjet
- [ ] Whitelist de IPs do Mailjet
- [ ] Rate limiting

---

## Referencias

### Documentacao Oficial

- [Mailjet Webhooks](https://dev.mailjet.com/email/guides/webhooks/)
- [Mailjet Event Types](https://dev.mailjet.com/email/reference/webhook/)
- [Mailjet Dashboard](https://app.mailjet.com/)
- [RFC 7208 - SPF](https://tools.ietf.org/html/rfc7208)

### Contatos

- **Mailjet Support:** https://www.mailjet.com/support/
- **Umbler SPF:** https://help.umbler.com/hc/pt-br/articles/210313303

---

**Ultima atualizacao:** 04 de Marco de 2026
**Status:** Ativo

