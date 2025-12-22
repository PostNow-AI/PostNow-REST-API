# 🚀 Guia Rápido - PostNow

## Começando o Trabalho

### 1. Abrir Terminal e Iniciar Backend
```bash
prpapi
```
✅ Backend estará em: http://127.0.0.1:8000

### 2. Abrir Novo Terminal e Iniciar Frontend
```bash
prpui
```
✅ Frontend estará em: http://localhost:5173

### 3. Acessar no Navegador
- Frontend: http://localhost:5173
- Backend API: http://127.0.0.1:8000
- Admin Django: http://127.0.0.1:8000/admin

## Fluxo de Desenvolvimento

### Backend (Python/Django)
```bash
# Acessar pasta
cd ~/Desktop/Postnow/PostNow-REST-API

# Ativar ambiente virtual
source venv/bin/activate

# Aplicar migrações do banco
python manage.py migrate

# Criar migrations após alterar models
python manage.py makemigrations

# Rodar servidor
python manage.py runserver

# Rodar testes
python manage.py test

# Criar superusuário (admin)
python manage.py createsuperuser

# Instalar nova dependência
pip install nome-pacote
pip freeze > requirements.txt
```

### Frontend (React/TypeScript)
```bash
# Acessar pasta
cd ~/Desktop/Postnow/PostNow-UI

# Instalar dependências
npm install

# Rodar servidor dev
npm run dev

# Build de produção
npm run build

# Preview build
npm run preview

# Lint do código
npm run lint

# Instalar nova dependência
npm install nome-pacote
```

## Git - Comandos Principais

### Status e Informações
```bash
git status              # Ver alterações
git branch              # Ver branches
git log --oneline       # Ver commits
```

### Fazer Commit
```bash
git add .                           # Adicionar arquivos
git commit -m "feat: descrição"     # Commit
git push                            # Enviar para GitHub
```

### Mudar de Branch
```bash
git checkout nome-da-branch         # Trocar branch
git checkout -b nova-branch         # Criar e trocar
```

### Atualizar do GitHub
```bash
git pull                            # Baixar mudanças
```

## Estrutura de Features

### Backend - Principais Apps Django
```
PostNow-REST-API/
├── Users/              # Sistema de autenticação
├── CreatorProfile/     # Perfil do criador (onboarding)
├── IdeaBank/           # Geração de conteúdo (IA)
├── CreditSystem/       # Créditos e assinaturas
└── services/           # Serviços de IA (Gemini, OpenAI, etc.)
```

### Frontend - Principais Módulos
```
PostNow-UI/src/
├── components/         # Componentes reutilizáveis
│   ├── ui/            # Design system (shadcn)
│   └── ideabank/      # Componentes específicos
├── pages/             # Páginas da aplicação
├── contexts/          # Estado global (Auth, Theme, etc.)
├── hooks/             # Hooks customizados
└── lib/               # Utilitários
```

## Endpoints Principais da API

### Autenticação
- `POST /api/v1/auth/login/` - Login
- `POST /api/v1/auth/register/` - Registro
- `POST /api/v1/auth/google/` - Google OAuth

### Perfil
- `GET /api/v1/creator-profile/` - Obter perfil
- `PATCH /api/v1/creator-profile/step-1/` - Completar etapa 1
- `PATCH /api/v1/creator-profile/step-2/` - Completar etapa 2
- `PATCH /api/v1/creator-profile/step-3/` - Completar etapa 3

### Geração de Conteúdo
- `POST /api/v1/ideabank/generate-content/` - Gerar texto
- `POST /api/v1/ideabank/generate-image/` - Gerar imagem

### Créditos
- `GET /api/v1/credits/balance/` - Ver saldo
- `POST /api/v1/credits/purchase/` - Comprar créditos

## Testar API com curl

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"seu@email.com","password":"senha"}'
```

### Obter Perfil (com token)
```bash
curl -X GET http://127.0.0.1:8000/api/v1/creator-profile/ \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

## Troubleshooting

### Backend não inicia
```bash
# Verificar se porta 8000 está em uso
lsof -ti:8000 | xargs kill -9

# Reativar ambiente virtual
cd ~/Desktop/Postnow/PostNow-REST-API
source venv/bin/activate

# Verificar migrações
python manage.py migrate
```

### Frontend não inicia
```bash
# Verificar se porta 5173 está em uso
lsof -ti:5173 | xargs kill -9

# Reinstalar dependências
cd ~/Desktop/Postnow/PostNow-UI
rm -rf node_modules package-lock.json
npm install
```

### Erro de CORS
- Verificar `ALLOWED_HOSTS` no Django settings
- Verificar `VITE_API_URL` no `.env` do frontend

### Erro de autenticação
- Verificar se token JWT está válido
- Verificar se `SECRET_KEY` do Django não mudou

## Variáveis de Ambiente

### Necessárias para Backend (.env)
```env
SECRET_KEY=...
DATABASE_URL=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GEMINI_API_KEY=...
STRIPE_SECRET_KEY=...
```

### Necessárias para Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=...
```

## Comandos de Deploy

### Backend (Vercel)
```bash
cd ~/Desktop/Postnow/PostNow-REST-API
vercel --prod
```

### Frontend (Vercel)
```bash
cd ~/Desktop/Postnow/PostNow-UI
npm run build
vercel --prod
```

## Atalhos Úteis

| Comando | Ação |
|---------|------|
| `prpapi` | Iniciar backend completo |
| `prpui` | Iniciar frontend completo |
| `Ctrl+C` | Parar servidor |
| `Cmd+K` | Limpar terminal |

## Links Importantes

- 📚 Documentação Django: https://docs.djangoproject.com/
- ⚛️ Documentação React: https://react.dev/
- 🎨 Shadcn UI: https://ui.shadcn.com/
- 🔥 Vite: https://vitejs.dev/
- 💳 Stripe: https://stripe.com/docs
- 🤖 Google Gemini: https://ai.google.dev/

---

💡 **Dica**: Mantenha sempre dois terminais abertos - um para backend e outro para frontend!
