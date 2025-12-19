# Configuração Visual - Painel Mailjet

Este guia visual mostra exatamente como configurar o webhook no painel Mailjet.

## 🌐 URL de Acesso

https://app.mailjet.com/account/settings

## 📍 Navegação no Painel

```
Mailjet Dashboard
    └── Account Settings (ícone de engrenagem, canto superior direito)
        └── REST API
            └── Event tracking (Webhooks)
```

## 🎯 Tela de Configuração

```
┌─────────────────────────────────────────────────────────────────┐
│                     Event Tracking (Webhooks)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [+ Add New Webhook]                                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Webhook Configuration                                    │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │                                                           │ │
│  │  URL *                                                    │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ https://seu-dominio.com/api/v1/audit/webhooks/      │ │ │
│  │  │ mailjet/                                             │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │  Event type *                                            │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ [✓] open     - Triggers when email is opened        │ │ │
│  │  │ [✓] click    - Triggers when link is clicked        │ │ │
│  │  │ [✓] bounce   - Triggers on hard/soft bounce         │ │ │
│  │  │ [ ] spam     - Triggers when marked as spam         │ │ │
│  │  │ [ ] blocked  - Triggers when sending is blocked     │ │ │
│  │  │ [ ] unsub    - Triggers on unsubscribe              │ │ │
│  │  │ [ ] sent     - Triggers when email is sent          │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │  Status                                                  │ │
│  │  ● Active    ○ Inactive                                 │ │
│  │                                                           │ │
│  │  [Cancel]                              [Save]  [Test]    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📝 Passo a Passo Detalhado

### Passo 1: Acessar Event Tracking

1. Faça login no Mailjet
2. Clique no ícone de **engrenagem** (Settings) no canto superior direito
3. No menu lateral esquerdo, procure por **REST API**
4. Clique em **Event tracking (Webhooks)**

### Passo 2: Adicionar Novo Webhook

1. Clique no botão **"+ Add New Webhook"** (azul, no topo)
2. Uma modal ou nova página será aberta

### Passo 3: Configurar a URL

```
Campo: URL *
Valor: https://seu-dominio.com/api/v1/audit/webhooks/mailjet/

⚠️  IMPORTANTE: 
- Para desenvolvimento local, use ngrok
- A URL deve ser HTTPS em produção
- Não esqueça a barra final (/)
```

### Passo 4: Selecionar Eventos

**Recomendado para começar:**

```
✅ open    - Rastreia quando emails são abertos
✅ click   - Rastreia quando links são clicados
✅ bounce  - Rastreia emails rejeitados
```

**Opcional (pode adicionar depois):**

```
⬜ spam    - Emails marcados como spam
⬜ blocked - Emails bloqueados
⬜ unsub   - Cancelamentos de inscrição
⬜ sent    - Confirmação de envio (pode gerar muito volume)
```

### Passo 5: Salvar e Testar

1. Verifique se o Status está como **"Active"**
2. Clique em **"Save"**
3. Clique em **"Test"** para enviar um evento de teste
4. Verifique se o evento aparece no seu AuditLog

## 🧪 Testar o Webhook

### Teste Integrado do Mailjet

```
┌─────────────────────────────────────────────────────────┐
│  Test Webhook                                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Select event type to test:                            │
│  ┌───────────────────────────────────────────────────┐ │
│  │ [▼] open                                          │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│                           [Cancel]  [Send Test Event]  │
└─────────────────────────────────────────────────────────┘
```

1. Selecione o tipo de evento (ex: "open")
2. Clique em **"Send Test Event"**
3. O Mailjet enviará um POST para sua URL
4. Você verá uma confirmação na tela

### Verificar se Funcionou

**No Django:**

```python
from AuditSystem.models import AuditLog

# Verificar último evento
last = AuditLog.objects.filter(
    action='email_opened'
).order_by('-timestamp').first()

if last:
    print(f"✅ Webhook funcionando!")
    print(f"Email: {last.details['email']}")
    print(f"Timestamp: {last.timestamp}")
```

## 🔧 Configuração para Desenvolvimento Local

### Usando ngrok

```bash
# 1. Instalar ngrok (se não tiver)
# https://ngrok.com/download

# 2. Iniciar o servidor Django
python manage.py runserver

# 3. Em outro terminal, iniciar ngrok
ngrok http 8000

# 4. Copiar a URL HTTPS gerada (ex: https://abc123.ngrok.io)

# 5. Usar no Mailjet:
# https://abc123.ngrok.io/api/v1/audit/webhooks/mailjet/
```

### Visualizar Requisições no ngrok

Acesse no navegador:

```
http://localhost:4040
```

Aqui você verá todas as requisições que o Mailjet está enviando!

## 📊 Exemplo de Payload do Mailjet

Quando você configurar corretamente, o Mailjet enviará JSONs assim:

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
    "ip": "192.168.1.1",
    "geo": "BR",
    "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
  }
]
```

## ✅ Checklist de Configuração

- [ ] Webhook criado no painel Mailjet
- [ ] URL correta configurada (HTTPS em produção)
- [ ] Eventos selecionados (open, click, bounce)
- [ ] Status = Active
- [ ] Teste enviado pelo painel
- [ ] Evento apareceu no AuditLog
- [ ] ngrok configurado (se desenvolvimento)
- [ ] Monitoramento ativo

## 🚨 Problemas Comuns

### ❌ Webhook não recebe eventos

**Soluções:**

```
1. Verificar se a URL está acessível publicamente
   curl -I https://seu-dominio.com/api/v1/audit/webhooks/mailjet/
   
2. Verificar firewall/proxy
   
3. Em desenvolvimento, usar ngrok
   
4. Verificar logs do servidor
```

### ❌ Eventos chegam mas não são salvos

**Soluções:**

```python
# Verificar erros no AuditLog
from AuditSystem.models import AuditLog

errors = AuditLog.objects.filter(
    action='system_error',
    error_message__icontains='mailjet'
).order_by('-timestamp')[:5]

for e in errors:
    print(e.error_message)
    print(e.details)
```

### ❌ Teste do Mailjet retorna erro

**Possíveis causas:**

```
- URL incorreta
- Servidor não está rodando
- CORS/CSRF bloqueando (não deveria, pois está @csrf_exempt)
- Firewall bloqueando IPs do Mailjet
```

## 📱 Contatos de Suporte

- **Mailjet Support:** https://www.mailjet.com/support/
- **Mailjet Documentation:** https://dev.mailjet.com/email/guides/webhooks/
- **PostNow Documentation:** Veja os arquivos em /docs/

## 🎯 URLs de Referência

- **Painel Mailjet:** https://app.mailjet.com/
- **Webhooks Settings:** https://app.mailjet.com/account/settings
- **API Documentation:** https://dev.mailjet.com/
- **Webhook Events:** https://dev.mailjet.com/email/reference/webhook/

---

**Última atualização:** 19 de Dezembro de 2025  
**Versão:** 1.0

