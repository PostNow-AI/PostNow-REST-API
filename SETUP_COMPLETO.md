# ✅ Setup Completo - PostNow

## 📁 Estrutura do Projeto

```
/Users/rogerioresende/Desktop/Postnow/
├── PostNow-REST-API/          # Backend Django
│   ├── venv/                  # Ambiente virtual Python
│   ├── manage.py              # Django management
│   └── requirements.txt       # Dependências Python
│
└── PostNow-UI/                # Frontend React + Vite
    ├── node_modules/          # Dependências Node.js
    ├── package.json           # Configuração npm
    ├── .env                   # Variáveis de ambiente
    └── src/                   # Código-fonte React
```

## 🚀 Comandos Rápidos (Aliases)

### Backend - `prpapi`
```bash
prpapi  # Vai para PostNow-REST-API, ativa venv, instala deps e roda servidor Django
```

**O que faz:**
1. `cd` para `/Users/rogerioresende/Desktop/Postnow/PostNow-REST-API`
2. Verifica status do git
3. Ativa ambiente virtual Python (`source venv/bin/activate`)
4. Instala dependências (`pip install -r requirements.txt`)
5. Inicia servidor Django em `http://127.0.0.1:8000/`

### Frontend - `prpui`
```bash
prpui  # Vai para PostNow-UI, instala deps e roda servidor Vite
```

**O que faz:**
1. `cd` para `/Users/rogerioresende/Desktop/Postnow/PostNow-UI`
2. Verifica status do git
3. Instala dependências npm (`npm install`)
4. Inicia servidor Vite em `http://localhost:5173/`

## 🔧 Configurações do Sistema

### Backend (.env)
- Localização: `/Users/rogerioresende/Desktop/Postnow/PostNow-REST-API/.env`
- Variáveis principais:
  - `SECRET_KEY`: Chave secreta Django
  - `DATABASE_URL`: Conexão com banco de dados
  - `GOOGLE_CLIENT_ID/SECRET`: OAuth Google
  - `GEMINI_API_KEY`: Google Gemini para IA
  - `STRIPE_SECRET_KEY`: Pagamentos

### Frontend (.env)
- Localização: `/Users/rogerioresende/Desktop/Postnow/PostNow-UI/.env`
- Configurações atuais:
```env
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_51QQQ
VITE_STRIPE_SUCCESS_URL=http://localhost:5173/credits/success
VITE_STRIPE_CANCEL_URL=http://localhost:5173/credits/cancel
```

## 📦 Dependências Instaladas

### Backend (Python)
- ✅ Django 5.2.4
- ✅ Django REST Framework 3.16.0
- ✅ Google Gemini SDK
- ✅ Stripe SDK
- ✅ JWT Authentication
- ✅ PostgreSQL adapter

### Frontend (Node.js)
- ✅ React 19.1.0
- ✅ Vite 7.1.11
- ✅ TypeScript 5.8.3
- ✅ Tailwind CSS 4.1.11
- ✅ Shadcn UI components
- ✅ React Router 7.7.1
- ✅ Axios 1.11.0
- ✅ TanStack Query 5.83.0

## 🌐 URLs de Desenvolvimento

| Serviço | URL | Status |
|---------|-----|--------|
| Backend API | http://127.0.0.1:8000 | ✅ Rodando (terminal 2) |
| Frontend | http://localhost:5173 | ✅ Rodando (terminal 36013) |
| Admin Django | http://127.0.0.1:8000/admin | ✅ Disponível |

## 🔑 Repositórios GitHub

- **Backend**: https://github.com/PostNow-AI/PostNow-REST-API.git
- **Frontend**: https://github.com/PostNow-AI/PostNow-UI.git

Branch atual: `feat/Rogerio-weekly-context`

## 🛠️ Comandos Úteis

### Geral
```bash
cd ~/Desktop/Postnow              # Ir para pasta do projeto
```

### Backend
```bash
prpapi                            # Iniciar backend completo
cd ~/Desktop/Postnow/PostNow-REST-API
source venv/bin/activate          # Ativar ambiente virtual
python manage.py runserver        # Rodar servidor
python manage.py migrate          # Aplicar migrações
python manage.py createsuperuser  # Criar admin
```

### Frontend
```bash
prpui                             # Iniciar frontend completo
cd ~/Desktop/Postnow/PostNow-UI
npm install                       # Instalar dependências
npm run dev                       # Rodar servidor dev
npm run build                     # Build produção
npm run preview                   # Preview build
```

## 📝 Notas Importantes

1. **Versão do Node.js**: Você está usando v20.18.2. O Vite recomenda v20.19+ ou v22.12+, mas funciona com aviso.

2. **Vulnerabilidades npm**: Existem 2 vulnerabilidades moderadas. Execute `npm audit fix` quando possível:
   ```bash
   cd ~/Desktop/Postnow/PostNow-UI
   npm audit fix
   ```

3. **Ambiente Virtual Python**: Sempre ative o venv antes de trabalhar no backend:
   ```bash
   source ~/Desktop/Postnow/PostNow-REST-API/venv/bin/activate
   ```

4. **Git**: Ambos os projetos estão na branch `feat/Rogerio-weekly-context` e sincronizados com o remoto.

## 🐛 Problemas Resolvidos

✅ **Problema**: Comando `prpui` não funcionava (diretório PostNow-UI não existia)
- **Solução**: Clonado repositório do GitHub

✅ **Problema**: Erro no `nvm use --lts` no alias `prpui`
- **Solução**: Comentada linha do NVM (usando Node.js padrão do sistema)

✅ **Problema**: Faltava arquivo `.env` no frontend
- **Solução**: Criado arquivo `.env` com configurações corretas

## 🎯 Próximos Passos Sugeridos

1. **Atualizar Node.js** (opcional, mas recomendado):
   ```bash
   # Usando nvm (se estiver instalado)
   nvm install --lts
   nvm use --lts
   ```

2. **Configurar variáveis de ambiente sensíveis**:
   - Adicionar chaves reais do Stripe no `.env` do frontend
   - Configurar chaves do Google OAuth no backend

3. **Corrigir vulnerabilidades npm**:
   ```bash
   cd ~/Desktop/Postnow/PostNow-UI
   npm audit fix
   ```

4. **Testar integração Frontend-Backend**:
   - Abrir http://localhost:5173
   - Fazer login/registro
   - Testar geração de conteúdo

## 🎉 Status Final

✅ **Backend**: Configurado e rodando em http://127.0.0.1:8000  
✅ **Frontend**: Configurado e rodando em http://localhost:5173  
✅ **Repositórios**: Clonados e sincronizados  
✅ **Aliases**: `prpapi` e `prpui` funcionando  
✅ **Dependências**: Todas instaladas  

**O sistema está pronto para desenvolvimento!** 🚀

---

_Última atualização: 18 de dezembro de 2024_
