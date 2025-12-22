# ⚡ Referência Rápida - PostNow

## 🚀 Início Rápido

```bash
# Terminal 1 - Backend
prpapi

# Terminal 2 - Frontend  
prpui

# Abrir navegador
open http://localhost:5173
```

## 📁 Caminhos

```bash
# Projeto
cd ~/Desktop/Postnow

# Backend
cd ~/Desktop/Postnow/PostNow-REST-API

# Frontend
cd ~/Desktop/Postnow/PostNow-UI
```

## 🔑 Aliases

| Alias | O que faz |
|-------|-----------|
| `prpapi` | Inicia backend Django (porta 8000) |
| `prpui` | Inicia frontend Vite (porta 5173) |
| `cdpapi` | cd para PostNow-REST-API |
| `cdpui` | cd para PostNow-UI |

## 🌐 URLs

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://127.0.0.1:8000 |
| Django Admin | http://127.0.0.1:8000/admin |
| API Docs | http://127.0.0.1:8000/api/docs |

## 🛠️ Comandos Backend

```bash
cd ~/Desktop/Postnow/PostNow-REST-API

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
python manage.py runserver

# Aplicar migrações
python manage.py migrate

# Criar migrations
python manage.py makemigrations

# Criar superusuário
python manage.py createsuperuser

# Shell Django
python manage.py shell

# Rodar testes
python manage.py test
```

## ⚛️ Comandos Frontend

```bash
cd ~/Desktop/Postnow/PostNow-UI

# Instalar dependências
npm install

# Rodar servidor dev
npm run dev

# Build produção
npm run build

# Preview build
npm run preview

# Lint
npm run lint

# Fix vulnerabilities
npm audit fix
```

## 📡 Endpoints Principais

### Autenticação
```bash
POST /api/v1/auth/login/
POST /api/v1/auth/register/
POST /api/v1/auth/google/
POST /api/v1/auth/refresh/
```

### Perfil
```bash
GET    /api/v1/creator-profile/
PATCH  /api/v1/creator-profile/step-1/
PATCH  /api/v1/creator-profile/step-2/
PATCH  /api/v1/creator-profile/step-3/
```

### Conteúdo
```bash
POST /api/v1/ideabank/generate-content/
POST /api/v1/ideabank/generate-image/
```

### Créditos
```bash
GET  /api/v1/credits/balance/
POST /api/v1/credits/purchase/
```

## 🐛 Troubleshooting

### Matar processos
```bash
# Backend (porta 8000)
lsof -ti:8000 | xargs kill -9

# Frontend (porta 5173)
lsof -ti:5173 | xargs kill -9
```

### Ver processos rodando
```bash
ps aux | grep -E "(vite|runserver)" | grep -v grep
```

### Reinstalar dependências

**Backend:**
```bash
cd ~/Desktop/Postnow/PostNow-REST-API
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd ~/Desktop/Postnow/PostNow-UI
rm -rf node_modules package-lock.json
npm install
```

## 📊 Git

```bash
# Status
git status
git branch
git log --oneline

# Commit
git add .
git commit -m "feat: descrição"
git push

# Branches
git checkout nome-branch
git checkout -b nova-branch

# Atualizar
git pull
```

## 🔐 Variáveis de Ambiente

### Backend (.env)
```env
SECRET_KEY=...
DATABASE_URL=...
GEMINI_API_KEY=...
STRIPE_SECRET_KEY=...
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=...
```

## 📚 Documentação

| Arquivo | Conteúdo |
|---------|----------|
| `SETUP_CONCLUIDO.md` | Resumo do setup |
| `SETUP_COMPLETO.md` | Setup detalhado |
| `GUIA_RAPIDO.md` | Comandos diários |
| `ARQUITETURA.md` | Estrutura do sistema |
| `REFERENCIA_RAPIDA.md` | Este arquivo |

## 🎯 Checklist Diário

- [ ] `prpapi` (terminal 1)
- [ ] `prpui` (terminal 2)
- [ ] Abrir http://localhost:5173
- [ ] Verificar status: `git status`
- [ ] Fazer commit: `git add . && git commit -m "..."`
- [ ] Push: `git push`

## 📞 Links

- Backend GitHub: https://github.com/PostNow-AI/PostNow-REST-API
- Frontend GitHub: https://github.com/PostNow-AI/PostNow-UI
- Branch atual: `feat/Rogerio-weekly-context`

---

**Imprima este arquivo para referência rápida!** 📋
