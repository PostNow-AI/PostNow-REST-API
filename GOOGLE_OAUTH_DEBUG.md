# Google OAuth Debug Guide

## Problema Atual

URL de erro: `http://localhost:5173/auth/google/callback?error=auth_failed&error_description=Google+authentication+failed`

## Configurações Atuais no Django

- **Provider**: google
- **Client ID**: 266814788714-9jhomtcfggughes050uk9l2678c6oir5.apps.googleusercontent.com
- **Site**: localhost:8000
- **Callback URL**: <http://localhost:8000/api/v1/auth/google/callback/>

## Verificações Necessárias no Google Cloud Console

### 1. URLs de Redirecionamento Autorizadas

Certifique-se de que estas URLs estão configuradas no Google Cloud Console:

```
http://localhost:8000/api/v1/auth/google/callback/
http://127.0.0.1:8000/api/v1/auth/google/callback/
```

### 2. Origens JavaScript Autorizadas

```
http://localhost:5173
http://127.0.0.1:5173
http://localhost:8000
http://127.0.0.1:8000
https://sonora-ui.vercel.app
```

### 3. Verificar se as APIs estão habilitadas

- Google+ API (descontinuada - use People API)
- Google People API
- Google Identity API

### 4. Comandos para Debug

```bash
# Verificar configurações no Django
python manage.py shell -c "
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
print('Sites:', Site.objects.all())
print('SocialApps:', SocialApp.objects.all())
"

# Testar endpoint de callback
curl -X GET "http://localhost:8000/api/v1/auth/google/callback/?error=test"
```

### 5. Logs para Verificar

Verificar os logs do servidor Django quando o erro ocorre para identificar a causa exata.
