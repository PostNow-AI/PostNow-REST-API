# Google Console Redirect URL Setup

## ✅ CORRECT - Backend URLs (Django server)

In Google Cloud Console → Credentials → OAuth 2.0 Client IDs → Authorized redirect URIs:

```
http://localhost:8000/api/v1/auth/google/callback/
http://127.0.0.1:8000/api/v1/auth/google/callback/
https://yourdomain.com/api/v1/auth/google/callback/  (for production)
```

## ❌ WRONG - Frontend URLs

Don't use frontend URLs like:

```
http://localhost:3000/auth/callback  ❌
http://localhost:3000/login          ❌
```

## Why Backend URLs?

1. **Django-allauth expects it**: The library needs a callback endpoint to complete OAuth flow
2. **Security**: Backend validates the authorization code securely
3. **Token exchange**: Backend exchanges code for access token internally

## Complete Setup Process:

### 1. Google Cloud Console

- **Authorized redirect URIs**: `http://localhost:8000/api/v1/auth/google/callback/`
- **Authorized JavaScript origins**: `http://localhost:8000` (and your frontend domain)

### 2. Configure Django

```bash
source env/bin/activate
python manage_google_oauth.py YOUR_CLIENT_ID YOUR_CLIENT_SECRET
```

### 3. Frontend Usage

Your frontend gets Google token, then sends to Django:

```javascript
// Frontend gets token from Google
const token = "ya29.a0AfH6SMB...";

// Send to Django backend
fetch("http://localhost:8000/api/v1/auth/google/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ access_token: token }),
});
```

## Authentication Flow:

```
1. Frontend → Google OAuth → Gets access_token
2. Frontend → Django API (/api/v1/auth/google/) → Sends access_token
3. Django → Validates with Google → Returns JWT token
4. Frontend → Uses JWT for API calls
```

The callback URL is just a technical requirement - your actual authentication happens via the API endpoint!
