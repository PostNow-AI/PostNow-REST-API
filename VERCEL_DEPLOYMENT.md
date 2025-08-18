# 🚀 Vercel Deployment Guide

## **Variáveis de Ambiente Necessárias**

### **1. Configuração do Banco de Dados (OBRIGATÓRIAS)**

```bash
DB_NAME=sonora_db
DB_USER=sonora_user
DB_USER_PASSWORD=your_secure_password
DB_HOST=your_mysql_host
DB_PORT=3306
```

### **2. Configurações do Django (OBRIGATÓRIAS)**

```bash
SECRET_KEY=your_django_secret_key_here
DEBUG=False
```

### **3. Google OAuth (OPCIONAL)**

```bash
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret
```

### **4. CORS Adicional (OPCIONAL)**

```bash
ADDITIONAL_CORS_ORIGINS=https://yourdomain.com,https://anotherdomain.com
```

## **Como Configurar no Vercel**

### **1. Via Dashboard Web:**

1. Acesse [vercel.com](https://vercel.com)
2. Vá para seu projeto `sonora-rest-api`
3. Clique em **Settings** → **Environment Variables**
4. Adicione cada variável acima

### **2. Via Vercel CLI:**

```bash
# Configurar variáveis de ambiente
vercel env add DB_NAME
vercel env add DB_USER
vercel env add DB_USER_PASSWORD
vercel env add DB_HOST
vercel env add DB_PORT
vercel env add SECRET_KEY

# Fazer redeploy após adicionar as variáveis
vercel --prod
```

## **Configuração Recomendada para Produção**

### **Banco de Dados:**

- **Aiven Cloud**: `mvp-db-sonora-content-producer.g.aivencloud.com:20430`
- **PlanetScale**: Alternativa serverless
- **Supabase**: Alternativa PostgreSQL
- **Neon**: Alternativa PostgreSQL serverless

### **Segurança:**

- ✅ Use senhas fortes
- ✅ Habilite SSL para conexões de banco
- ✅ Configure CORS adequadamente
- ✅ Use HTTPS em produção

## **Troubleshooting**

### **Erro: "NoneType object has no attribute 'startswith'"**

- **Causa**: Variáveis de banco não configuradas
- **Solução**: Configure todas as variáveis DB_* no Vercel

### **Erro: "Can't connect to MySQL server"**

- **Causa**: Host/porta incorretos ou firewall
- **Solução**: Verifique conectividade e configurações de rede

### **Erro: "Access denied for user"**

- **Causa**: Credenciais incorretas
- **Solução**: Verifique usuário e senha do banco

## **Teste de Conectividade**

Após configurar as variáveis:

```bash
# Testar endpoint público
curl https://your-vercel-url.vercel.app/api/v1/ideabank/public/options/

# Verificar logs
vercel logs https://your-vercel-url.vercel.app
```

## **Monitoramento**

- **Vercel Analytics**: Performance e erros
- **Logs**: `vercel logs [URL]`
- **Status**: `vercel ls`
- **Redeploy**: `vercel --prod`
