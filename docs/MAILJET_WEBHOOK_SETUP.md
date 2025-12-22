# Configuração do Webhook Mailjet

Este documento descreve como configurar o webhook do Mailjet para rastrear eventos de email (aberturas, cliques,
bounces, etc.) no sistema PostNow.

## Visão Geral

O webhook do Mailjet permite que o sistema PostNow receba notificações em tempo real sobre eventos de email, como:

- **Open**: Email aberto pelo destinatário
- **Click**: Link no email clicado
- **Bounce**: Email rejeitado
- **Spam**: Email marcado como spam
- **Blocked**: Email bloqueado
- **Unsub**: Destinatário cancelou inscrição

## Endpoint do Webhook

O endpoint para receber eventos do Mailjet é:

```
POST /api/v1/audit/webhooks/mailjet/
```

**URL Completa (produção):**

```
https://seu-dominio.com/api/v1/audit/webhooks/mailjet/
```

**URL de desenvolvimento:**

```
http://localhost:8000/api/v1/audit/webhooks/mailjet/
```

## Configuração no Painel Mailjet

### Passo 1: Acessar o Painel Mailjet

1. Faça login em [Mailjet](https://app.mailjet.com/)
2. Vá para **Account Settings** (Configurações da Conta)
3. Clique em **Event Tracking (Webhooks)** no menu lateral

### Passo 2: Adicionar Novo Webhook

1. Clique em **Add New Webhook**
2. Preencha as informações:
    - **URL**: `https://seu-dominio.com/api/v1/audit/webhooks/mailjet/`
    - **Event Type**: Selecione os eventos que deseja rastrear:
        - ✅ **Open** (Recomendado)
        - ✅ **Click** (Recomendado)
        - ✅ **Bounce** (Recomendado)
        - ⬜ **Spam** (Opcional)
        - ⬜ **Blocked** (Opcional)
        - ⬜ **Unsub** (Opcional)
        - ⬜ **Sent** (Opcional)

3. **Método**: Certifique-se de que está configurado como **POST**
4. Clique em **Save**

### Passo 3: Testar o Webhook

O Mailjet oferece uma funcionalidade de teste:

1. Após adicionar o webhook, clique em **Test**
2. Selecione um tipo de evento (ex: "Open")
3. Clique em **Send Test**
4. Verifique se o evento foi registrado no AuditLog

## Formato do Payload

O Mailjet envia eventos no seguinte formato JSON:

```json
[
  {
    "event": "open",
    "time": 1433333949,
    "MessageID": 19421777835146490,
    "email": "usuario@example.com",
    "mj_campaign_id": 7257,
    "mj_contact_id": 4,
    "customcampaign": "",
    "CustomID": "helloworld",
    "Payload": "",
    "ip": "127.0.0.1",
    "geo": "US",
    "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  }
]
```

## Como os Eventos São Processados

O endpoint do webhook processa cada evento da seguinte forma:

1. **Mapeia o tipo de evento** para uma ação do AuditLog:
    - `open` → `email_opened`
    - `click` → `email_clicked`
    - `bounce` → `email_bounced`
    - `spam`, `blocked`, `unsub` → `email_failed`

2. **Tenta identificar o usuário** pelo email fornecido no evento

3. **Registra no AuditLog** com os seguintes detalhes:
    - `operation_category`: `email`
    - `action`: Ação mapeada (ex: `email_opened`)
    - `status`: `success`
    - `user`: Usuário identificado (se encontrado)
    - `details`: JSON com informações completas do evento

4. **Retorna uma resposta** confirmando o processamento

## Verificando os Logs

Após configurar o webhook, você pode verificar os eventos registrados de várias formas:

### Via Django Admin

1. Acesse o Django Admin
2. Vá para **AuditSystem > Audit Logs**
3. Filtre por:
    - **Operation Category**: `email`
    - **Action**: `email_opened`, `email_clicked`, etc.

### Via API (exemplo futuro)

Você pode criar endpoints adicionais para consultar estatísticas de email:

```python
# Exemplo: quantos emails foram abertos hoje
from datetime import date
from AuditSystem.models import AuditLog

today_opens = AuditLog.objects.filter(
    action='email_opened',
    timestamp__date=date.today()
).count()
```

### Via SQL

```sql
SELECT
    action, COUNT (*) as total, COUNT (DISTINCT user_id) as unique_users
FROM AuditSystem_auditlog
WHERE operation_category = 'email'
  AND DATE (timestamp) = CURRENT_DATE
GROUP BY action;
```

## Segurança

### Autenticação

Atualmente, o endpoint aceita requisições sem autenticação (necessário para webhooks externos).

**Recomendações futuras de segurança:**

1. **Token de verificação**: Adicionar um token secreto compartilhado
   ```python
   # Exemplo de implementação
   MAILJET_WEBHOOK_SECRET = os.getenv('MAILJET_WEBHOOK_SECRET')
   
   if request.headers.get('X-Mailjet-Signature') != MAILJET_WEBHOOK_SECRET:
       return Response({'error': 'Unauthorized'}, status=403)
   ```

2. **Whitelist de IPs**: Aceitar apenas IPs do Mailjet
    - IPs do Mailjet: Consulte [documentação oficial](https://dev.mailjet.com/email/guides/webhooks/)

3. **Rate Limiting**: Implementar limite de requisições

### Validação de Payload

O endpoint já valida:

- ✅ Formato do payload (array ou objeto)
- ✅ Campos obrigatórios
- ✅ Tratamento de exceções

## Troubleshooting

### Webhook não está recebendo eventos

1. **Verifique a URL**: Certifique-se de que a URL está acessível publicamente
2. **Teste com ngrok** (desenvolvimento):
   ```bash
   ngrok http 8000
   # Use a URL do ngrok no Mailjet: https://xxxxx.ngrok.io/api/v1/audit/webhooks/mailjet/
   ```
3. **Verifique os logs do servidor**:
   ```bash
   tail -f /var/log/your-app/error.log
   ```

### Eventos não aparecem no AuditLog

1. **Verifique o Django Admin** para erros no AuditLog
2. **Consulte os logs de sistema**:
   ```python
   from AuditSystem.models import AuditLog
   
   errors = AuditLog.objects.filter(
       action='system_error',
       error_message__icontains='mailjet'
   ).order_by('-timestamp')[:10]
   
   for error in errors:
       print(error.error_message)
       print(error.details)
   ```

### Email do usuário não está sendo identificado

O sistema tenta encontrar o usuário pelo email. Se não encontrar:

- O evento ainda é registrado
- `user` será `null` no AuditLog
- O email fica armazenado em `details['email']`

## Exemplos de Uso

### Estatísticas de Email

```python
from datetime import timedelta
from django.utils import timezone
from AuditSystem.models import AuditLog

# Taxa de abertura dos últimos 7 dias
last_week = timezone.now() - timedelta(days=7)

emails_sent = AuditLog.objects.filter(
    action='email_sent',
    timestamp__gte=last_week
).count()

emails_opened = AuditLog.objects.filter(
    action='email_opened',
    timestamp__gte=last_week
).count()

open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
print(f"Taxa de abertura: {open_rate:.2f}%")
```

### Engajamento por Usuário

```python
from django.db.models import Count
from AuditSystem.models import AuditLog

# Usuários mais engajados (que mais abrem emails)
top_users = AuditLog.objects.filter(
    action='email_opened'
).values('user__username', 'user__email').annotate(
    open_count=Count('id')
).order_by('-open_count')[:10]

for user in top_users:
    print(f"{user['user__username']}: {user['open_count']} aberturas")
```

## Referências

- [Mailjet Webhooks Documentation](https://dev.mailjet.com/email/guides/webhooks/)
- [Mailjet Event Types](https://dev.mailjet.com/email/reference/webhook/)
- [PostNow Audit System Documentation](./AUDIT_SYSTEM.md)

## Changelog

- **2025-12-19**: Implementação inicial do webhook Mailjet
    - Suporte para eventos: open, click, bounce, spam, blocked, unsub
    - Integração com AuditLog
    - Documentação criada

