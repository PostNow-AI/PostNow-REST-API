# 🚀 Guia de Deploy - Celery + Redis

## ✅ Ambiente Local (Desenvolvimento)

### 1. Instalar Dependências

```bash
cd PostNow-REST-API
pip install -r requirements.txt
```

### 2. Iniciar Redis com Docker

```bash
docker-compose up redis -d
```

Ou instalar Redis localmente:

```bash
# macOS
brew install redis
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis
```

### 3. Aplicar Migrations

```bash
python manage.py migrate
```

### 4. Iniciar Celery Worker (Terminal 1)

```bash
celery -A Sonora_REST_API worker --loglevel=info
```

### 5. Iniciar Django Dev Server (Terminal 2)

```bash
python manage.py runserver
```

### 6. Iniciar Frontend (Terminal 3)

```bash
cd PostNow-UI
npm run dev
```

---

## 🌐 Deploy em Produção

### Arquitetura Recomendada

```
┌─────────────┐
│   Frontend  │  → Vercel (React/Vite)
│   (Vercel)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Backend   │  → Railway (Django)
│  (Railway)  │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│    Redis    │   │   Celery    │
│  (Railway)  │   │  Worker     │
│             │◄──┤  (Railway)  │
└─────────────┘   └─────────────┘
```

---

## 📦 1. Deploy do Redis (Railway)

### Passo 1: Criar Projeto no Railway

1. Acesse [railway.app](https://railway.app)
2. Clique em "New Project"
3. Selecione "Deploy Redis"
4. Copie o **REDIS_URL** gerado (ex: `redis://red-xxxxx:6379`)

### Passo 2: Configurar Variáveis de Ambiente

No Railway, adicione:

```env
REDIS_URL=redis://red-xxxxx:6379
CELERY_BROKER_URL=redis://red-xxxxx:6379/0
CELERY_RESULT_BACKEND=redis://red-xxxxx:6379/0
```

---

## 🐍 2. Deploy do Django Backend (Railway)

### Passo 1: Criar Serviço no Railway

1. No mesmo projeto, clique em "New Service"
2. Selecione "Deploy from GitHub"
3. Conecte o repositório `PostNow-REST-API`
4. Railway detectará automaticamente o `Procfile` ou `railway.json`

### Passo 2: Criar `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate"
  },
  "deploy": {
    "startCommand": "gunicorn Sonora_REST_API.wsgi:application --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

### Passo 3: Criar `Procfile`

```
web: gunicorn Sonora_REST_API.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A Sonora_REST_API worker --loglevel=info
```

### Passo 4: Adicionar `gunicorn` ao `requirements.txt`

```
gunicorn==23.0.0
```

### Passo 5: Configurar Variáveis de Ambiente

```env
DJANGO_SETTINGS_MODULE=Sonora_REST_API.settings
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-railway-domain.up.railway.app
DATABASE_URL=mysql://...
REDIS_URL=redis://red-xxxxx:6379
CELERY_BROKER_URL=redis://red-xxxxx:6379/0
CELERY_RESULT_BACKEND=redis://red-xxxxx:6379/0
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
GEMINI_API_KEY=...
```

---

## 🔄 3. Deploy do Celery Worker (Railway)

### Opção A: Mesmo Projeto, Novo Serviço

1. No Railway, clique em "New Service"
2. Selecione o mesmo repositório
3. Em "Start Command", coloque:

```bash
celery -A Sonora_REST_API worker --loglevel=info
```

### Opção B: Usar `Procfile` com Railway Worker

Railway detecta automaticamente o `Procfile` e cria 2 serviços:
- **web** → Django
- **worker** → Celery

**Vantagem:** Escala independentemente!

---

## ⚛️ 4. Deploy do Frontend (Vercel)

### Passo 1: Conectar ao Vercel

1. Acesse [vercel.com](https://vercel.com)
2. Clique em "New Project"
3. Conecte o repositório `PostNow-UI`
4. Vercel detecta automaticamente o Vite

### Passo 2: Configurar Build

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install"
}
```

### Passo 3: Configurar Variáveis de Ambiente

```env
VITE_API_URL=https://your-railway-backend.up.railway.app
```

### Passo 4: Deploy

```bash
vercel --prod
```

---

## 🧪 Teste de Integração

### 1. Verificar Redis

```bash
redis-cli -u redis://red-xxxxx:6379
> PING
PONG
```

### 2. Verificar Celery Worker

```bash
# Logs do Railway
railway logs --service worker
```

Deve aparecer:

```
[2025-01-03 10:00:00,000: INFO/MainProcess] Connected to redis://red-xxxxx:6379/0
[2025-01-03 10:00:00,000: INFO/MainProcess] celery@worker ready.
```

### 3. Testar Geração de Campanha

1. Acesse o frontend: `https://your-vercel-app.vercel.app`
2. Crie uma nova campanha
3. Clique em "Gerar Posts"
4. Deve aparecer o progress bar com polling a cada 2s

---

## 📊 Monitoramento

### Railway

```bash
# Logs do Django
railway logs --service web

# Logs do Celery
railway logs --service worker

# Logs do Redis
railway logs --service redis
```

### Celery Flower (Opcional)

Para monitorar tasks em produção:

```bash
# Adicionar ao requirements.txt
flower==2.0.1

# Iniciar (local ou Railway)
celery -A Sonora_REST_API flower --port=5555
```

Acesse: `http://localhost:5555`

---

## 💰 Custos Estimados

| Serviço        | Plano Recomendado | Custo/Mês |
|----------------|-------------------|-----------|
| Vercel         | Hobby (Free)      | $0        |
| Railway Redis  | Shared (512MB)    | $5        |
| Railway Django | Starter (1GB)     | $5        |
| Railway Worker | Starter (1GB)     | $5        |
| **TOTAL**      |                   | **$15/mês** |

---

## 🔧 Troubleshooting

### Erro: "No module named 'celery'"

```bash
pip install celery redis
```

### Erro: "Connection refused" (Redis)

- Verificar se Redis está rodando
- Verificar `CELERY_BROKER_URL` no `.env`

### Tarefas não executam

1. Verificar se worker está rodando: `railway logs --service worker`
2. Verificar conexão do worker com Redis
3. Reiniciar worker: `railway restart --service worker`

### Progress não atualiza no Frontend

1. Verificar endpoint `/progress/` retorna dados
2. Verificar polling no `useCampaignProgress` (2s)
3. Verificar console do navegador para erros

---

## 🎯 Próximos Passos (Opcional)

1. **Celery Beat**: Tarefas agendadas (cleanup de progress)
2. **Celery Flower**: Monitoramento avançado
3. **Redis Sentinel**: Alta disponibilidade
4. **Horizontal Scaling**: Múltiplos workers
5. **Task Priority Queue**: Priorizar campanhas premium

---

## 📚 Referências

- [Celery Docs](https://docs.celeryq.dev/)
- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)
- [Redis Docs](https://redis.io/docs/)

