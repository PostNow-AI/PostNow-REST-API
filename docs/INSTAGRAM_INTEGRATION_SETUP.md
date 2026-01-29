# Instagram Integration - Setup Guide

Este guia completo explica como configurar a integração com Instagram Graph API no PostNow, desde a criação do app no Meta for Developers até a configuração em produção.

## 📋 Pré-requisitos

Antes de começar, você precisará:

1. ✅ Conta no [Meta for Developers](https://developers.facebook.com/)
2. ✅ Instagram Business ou Creator Account
3. ✅ Facebook Page conectada à conta do Instagram
4. ✅ Acesso ao código-fonte do PostNow (backend)

---

## 1. Criar App no Meta for Developers

### Passo 1.1: Acessar Meta Developer Console

1. Acesse https://developers.facebook.com/
2. Faça login com sua conta Facebook/Meta
3. Clique em **"My Apps"** no topo
4. Clique em **"Create App"**

### Passo 1.2: Configurar Tipo de App

1. Selecione **"Business"** como tipo de app
   - Isso permite acesso ao Instagram Graph API
2. Preencha as informações:
   - **App Display Name**: `PostNow Instagram Integration` (ou nome da sua preferência)
   - **App Contact Email**: Seu email de contato
   - **Business Account**: Selecione sua conta (ou crie uma)
3. Clique em **"Create App"**

### Passo 1.3: Adicionar Instagram Graph API

1. No dashboard do seu app, procure por **"Add Product"** na sidebar
2. Encontre **"Instagram Graph API"**
3. Clique em **"Set Up"**

![Screenshot exemplo: Instagram Graph API Product](https://via.placeholder.com/800x400?text=Instagram+Graph+API+Setup)

---

## 2. Configurar Permissões (Permissions)

### Passo 2.1: Adicionar Permissions Necessárias

No painel do Instagram Graph API:

1. Vá em **"Instagram Graph API" → "Permissions"**
2. Adicione as seguintes permissions:
   - ✅ `instagram_basic` - Acesso básico ao perfil
   - ✅ `instagram_manage_insights` - Acesso a métricas e insights
   - ✅ `pages_read_engagement` - Leitura de engajamento da Page

**⚠️ Nota**: Em modo Development, essas permissions funcionam apenas para usuários de teste (até 5 usuários).

### Passo 2.2: Configurar OAuth Redirect URIs

1. Vá em **"Instagram Graph API" → "Settings"** ou **"Basic Settings"**
2. Role até encontrar **"Valid OAuth Redirect URIs"**
3. Adicione as seguintes URLs:

**Development:**
```
http://localhost:8000/api/v1/social/instagram/callback/
http://127.0.0.1:8000/api/v1/social/instagram/callback/
```

**Production:**
```
https://seudominio.com/api/v1/social/instagram/callback/
https://api.seudominio.com/api/v1/social/instagram/callback/
```

4. Clique em **"Save Changes"**

![Screenshot: OAuth Redirect URIs](https://via.placeholder.com/800x300?text=OAuth+Redirect+URIs+Configuration)

---

## 3. Obter Credenciais

### Passo 3.1: App ID e App Secret

1. Vá em **"Settings" → "Basic"**
2. Você verá:
   - **App ID**: `123456789012345` (exemplo)
   - **App Secret**: Clique em **"Show"** para revelar

### Passo 3.2: Copiar Credenciais

Copie ambos os valores. Você precisará deles para configurar o backend.

**🔒 Segurança**: 
- **NUNCA** compartilhe o App Secret
- **NUNCA** commit o App Secret no Git
- Use variáveis de ambiente para armazenar

---

## 4. Configurar Backend (Django)

### Passo 4.1: Adicionar Variáveis de Ambiente

Edite o arquivo `.env` do projeto:

```bash
# Instagram Graph API Credentials
INSTAGRAM_APP_ID=123456789012345
INSTAGRAM_APP_SECRET=seu_app_secret_aqui
INSTAGRAM_REDIRECT_URI=http://localhost:8000/api/v1/social/instagram/callback/

# Instagram Token Encryption Key (gere uma nova)
INSTAGRAM_TOKEN_ENCRYPTION_KEY=gerar_chave_fernet_aqui
```

### Passo 4.2: Gerar Encryption Key

Para gerar uma chave de criptografia Fernet:

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

Ou via terminal:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copie o resultado para `INSTAGRAM_TOKEN_ENCRYPTION_KEY`.

### Passo 4.3: Instalar Dependências

Adicione ao `requirements.txt` se ainda não estiver:

```txt
cryptography>=41.0.0
requests>=2.31.0
```

Instale:
```bash
pip install cryptography requests
```

### Passo 4.4: Criar Migrations

```bash
python manage.py makemigrations SocialMediaIntegration
python manage.py migrate
```

### Passo 4.5: Verificar Configuração

Execute o servidor:
```bash
python manage.py runserver
```

Teste o endpoint de status:
```bash
curl http://localhost:8000/api/v1/social/instagram/status/ \
  -H "Authorization: Bearer seu_jwt_token"
```

Resposta esperada:
```json
{
  "is_connected": false,
  "connection_status": "disconnected",
  "account_info": null
}
```

---

## 5. Converter Conta Instagram para Business

**⚠️ IMPORTANTE**: Apenas contas Business ou Creator podem usar a API.

### Passo 5.1: No Instagram App (Mobile)

1. Abra o Instagram app
2. Vá em **Perfil → Menu (☰) → Settings**
3. Toque em **Account**
4. Toque em **Switch to Professional Account**
5. Escolha **Business** (ou Creator se preferir)

### Passo 5.2: Conectar Facebook Page

1. Durante o processo de conversão, será solicitado conectar uma Facebook Page
2. Se não tiver uma Page:
   - Crie uma em https://facebook.com/pages/create
   - Preencha nome, categoria, descrição
   - Volte e conecte ao Instagram

3. Se já tiver uma Page:
   - Selecione a Page existente
   - Autorize a conexão

### Passo 5.3: Verificar Conexão

1. No Instagram: **Settings → Account → Linked Accounts → Facebook**
2. Deve aparecer a Page conectada

**📹 Tutorial em Vídeo**: [Link para vídeo tutorial de conversão]

---

## 6. Testar Integração (Development Mode)

### Passo 6.1: Adicionar Usuários de Teste

Em Development Mode, apenas usuários específicos podem conectar:

1. No Meta Developer Console: **Roles → Test Users**
2. Clique em **"Add Test Users"**
3. Ou adicione usuários reais em **Roles → Developers/Testers**

### Passo 6.2: Conectar Instagram

No frontend do PostNow:

1. Login com um usuário de teste
2. Vá em **Settings → Instagram Integration**
3. Clique em **"Conectar Instagram"**
4. Autorize as permissões
5. Verifique se aparece como conectado

### Passo 6.3: Testar Sync Manual

1. Clique em **"Atualizar Dados"**
2. Aguarde alguns segundos
3. Verifique se métricas aparecem:
   - Seguidores
   - Impressões
   - Alcance
   - Engajamento

---

## 7. Preparar para Produção (App Review)

Para usar com usuários reais, é necessário App Review do Facebook.

### Passo 7.1: Pré-requisitos App Review

1. ✅ App deve estar em Development Mode
2. ✅ Ter testado com usuários de teste
3. ✅ Ter Privacy Policy URL válida
4. ✅ Ter Terms of Service URL
5. ✅ Gravar vídeo demo do fluxo OAuth

### Passo 7.2: Criar Privacy Policy

Exemplo de conteúdo mínimo:

```markdown
# Privacy Policy - PostNow Instagram Integration

## Data We Collect
- Instagram username
- Follower count
- Post impressions and reach
- Engagement metrics (likes, comments, saves)

## How We Use Data
- Display analytics dashboard
- Generate content recommendations
- Track growth over time

## Data Security
- Tokens are encrypted
- No passwords stored
- Data not shared with third parties

## User Rights
- Disconnect Instagram anytime
- Request data deletion
```

Hospede em: `https://seudominio.com/privacy-policy`

### Passo 7.3: Submeter para App Review

1. No Meta Developer Console: **App Review → Permissions and Features**
2. Clique em **"Request"** para cada permission:
   - `instagram_basic`
   - `instagram_manage_insights`
   - `pages_read_engagement`

3. Preencha para cada uma:
   - **How will your app use this permission?**
     - Descreva o uso (ex: "Display Instagram analytics dashboard to users")
   - **Step-by-step instructions**:
     ```
     1. User logs in to PostNow
     2. Goes to Settings → Instagram
     3. Clicks "Connect Instagram"
     4. Authorizes permissions
     5. Views dashboard with metrics
     ```
   - **Screencast video**: Upload vídeo de 1-3min mostrando o fluxo completo

4. Clique em **"Submit for Review"**

### Passo 7.4: Template de Justificativa

**Para `instagram_basic`:**
```
We use instagram_basic to identify the user's Instagram account and display 
their profile information (username, profile picture) in our dashboard. 
This allows users to see which account is connected.
```

**Para `instagram_manage_insights`:**
```
We use instagram_manage_insights to fetch analytics data (impressions, reach, 
engagement) and display it in a dashboard. This helps users understand their 
Instagram performance and make data-driven decisions about their content strategy.
```

**Para `pages_read_engagement`:**
```
We use pages_read_engagement to access Instagram Business account data linked 
to Facebook Pages, which is required by Instagram Graph API architecture for 
Business accounts.
```

### Passo 7.5: Aguardar Aprovação

- ⏳ Tempo médio: 7-14 dias
- 📧 Você receberá email com resultado
- ✅ Se aprovado: App entra em Live Mode automaticamente
- ❌ Se rejeitado: Veja feedback, corrija, e resubmeta

---

## 8. Deploy em Produção

### Passo 8.1: Atualizar Variáveis de Ambiente

No servidor de produção (`.env` ou variáveis do hosting):

```bash
# Production Instagram Credentials
INSTAGRAM_APP_ID=seu_app_id_production
INSTAGRAM_APP_SECRET=seu_app_secret_production
INSTAGRAM_REDIRECT_URI=https://api.seudominio.com/api/v1/social/instagram/callback/
INSTAGRAM_TOKEN_ENCRYPTION_KEY=sua_chave_fernet_production
```

### Passo 8.2: Configurar Cron Job (Token Refresh)

Adicione ao crontab para refresh automático de tokens:

```bash
# Refresh Instagram tokens daily at 3 AM
0 3 * * * cd /path/to/project && source venv/bin/activate && python manage.py refresh_instagram_tokens
```

Ou via Celery Beat (se estiver usando):

```python
# celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'refresh-instagram-tokens': {
        'task': 'SocialMediaIntegration.tasks.refresh_tokens',
        'schedule': crontab(hour=3, minute=0),
    },
}
```

### Passo 8.3: Monitorar Health Check

Configure monitoring para o endpoint:
```
GET /api/v1/social/instagram/health/
```

Verifique diariamente:
- Tokens expirando
- Contas com erro
- Status da API do Instagram

---

## 9. Troubleshooting

### Erro: "Invalid State Token"

**Causa**: State token expirou ou foi alterado.

**Solução**:
1. Verifique se cache está funcionando (Redis/Memcached)
2. State expira em 10 minutos - usuário precisa completar OAuth rapidamente
3. Teste novamente gerando novo link de conexão

### Erro: "Account must be Business or Creator"

**Causa**: Conta Instagram é Personal.

**Solução**:
1. Siga [Seção 5](#5-converter-conta-instagram-para-business)
2. Converta para Business/Creator
3. Tente conectar novamente

### Erro: "Invalid Client Secret"

**Causa**: App Secret incorreto ou não está sendo lido.

**Solução**:
1. Verifique `.env` tem `INSTAGRAM_APP_SECRET` correto
2. Reinicie servidor Django
3. Confirme App Secret no Meta Developer Console

### Erro: "Rate Limit Exceeded"

**Causa**: Muitas requisições em pouco tempo (200 calls/hora por usuário).

**Solução**:
1. Sistema já tem cooldown de 15min entre syncs manuais
2. Aguarde 1 hora para rate limit resetar
3. Não faça syncs automáticos muito frequentes

### Erro: "Token Expired"

**Causa**: Token não foi renovado em 60 dias.

**Solução**:
1. Verifique se cron job de refresh está rodando
2. Usuário precisa reconectar Instagram
3. Tokens são auto-renovados se <7 dias para expirar

### Permissions Negadas no App Review

**Causa**: Vídeo demo incompleto ou justificativa insuficiente.

**Solução**:
1. Grave vídeo mostrando TODO o fluxo
2. Inclua narração explicando cada step
3. Mostre valor claro para o usuário
4. Resubmeta com mais detalhes

---

## 10. Recursos Adicionais

### Documentação Oficial

- [Instagram Graph API Docs](https://developers.facebook.com/docs/instagram-api/)
- [Instagram Basic Display API](https://developers.facebook.com/docs/instagram-basic-display-api/)
- [App Review Guide](https://developers.facebook.com/docs/app-review)

### FAQs

**P: Posso usar Instagram Basic Display API ao invés de Graph API?**  
R: Basic Display API é apenas para contas pessoais e não oferece insights. Use Graph API para Business accounts.

**P: Preciso renovar tokens manualmente?**  
R: Não, o sistema renova automaticamente tokens que expiram em <7 dias via cron job.

**P: Quantos usuários posso ter em Development Mode?**  
R: Até 5 usuários de teste. Para uso público, precisa App Review.

**P: Instagram não está aparecendo no OAuth?**  
R: Verifique se adicionou Instagram Graph API como produto no Meta Developer Console.

---

## 📞 Suporte

- **Documentação Usuário**: [docs/INSTAGRAM_USER_FAQ.md](INSTAGRAM_USER_FAQ.md)
- **Issues GitHub**: [Link para issues]
- **Email Suporte**: suporte@postnow.com

---

**Última Atualização**: Janeiro 2026  
**Versão**: 1.0  
**Autor**: Equipe PostNow
