# Google OAuth Authentication Setup

## 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API (or Google Identity API)
4. Go to **Credentials** > **Create Credentials** > **OAuth 2.0 Client IDs**
5. Configure the OAuth consent screen
6. Add authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/google/callback/`
   - `http://127.0.0.1:8000/api/v1/auth/google/callback/`
   - Add your production domain when deploying

## 2. Configure Django App

Run the setup script with your Google OAuth credentials:

```bash
source env/bin/activate
python manage_google_oauth.py YOUR_CLIENT_ID YOUR_CLIENT_SECRET
```

## 3. API Endpoints

### Regular Email/Password Authentication (existing)

```
POST /api/v1/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "userpassword"
}
```

### Google OAuth Authentication (new)

```
POST /api/v1/auth/google/
Content-Type: application/json

{
    "access_token": "google_access_token_from_frontend"
}
```

## 4. Frontend Integration Example (JavaScript)

### Option 1: Using Google Identity Services (Recommended)

```html
<!-- Include Google Identity Services -->
<script src="https://accounts.google.com/gsi/client" async defer></script>

<div
  id="g_id_onload"
  data-client_id="YOUR_GOOGLE_CLIENT_ID"
  data-callback="handleCredentialResponse"
></div>
<div class="g_id_signin" data-type="standard"></div>

<script>
  function handleCredentialResponse(response) {
    // Decode the JWT token to get user info
    const responsePayload = decodeJwtResponse(response.credential);

    // Send to your Django backend
    fetch("/api/v1/auth/google/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        access_token: response.credential,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.access_token) {
          // Store JWT token
          localStorage.setItem("access_token", data.access_token);
          console.log("Login successful!");
        }
      });
  }

  function decodeJwtResponse(token) {
    var base64Url = token.split(".")[1];
    var base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    var jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map(function (c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    );
    return JSON.parse(jsonPayload);
  }
</script>
```

### Option 2: Using Google APIs Client Library

```javascript
// Initialize Google API
gapi.load("auth2", function () {
  gapi.auth2.init({
    client_id: "YOUR_GOOGLE_CLIENT_ID",
  });
});

// Sign in function
function signInWithGoogle() {
  const authInstance = gapi.auth2.getAuthInstance();
  authInstance.signIn().then(function (googleUser) {
    const access_token = googleUser.getAuthResponse().access_token;

    // Send to Django backend
    fetch("/api/v1/auth/google/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        access_token: access_token,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);
          console.log("Login successful!");
        }
      });
  });
}
```

## 5. Response Format

Both email/password and Google OAuth return the same JWT token format:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "pk": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

## 6. Using JWT Tokens

Include the access token in subsequent API requests:

```javascript
fetch("/api/v1/some-protected-endpoint/", {
  method: "GET",
  headers: {
    Authorization: "Bearer " + localStorage.getItem("access_token"),
    "Content-Type": "application/json",
  },
});
```

## 7. Registration

Users are automatically registered when they sign in with Google for the first time. The system will:

- Create a new user account
- Set the email from Google profile
- Set first_name and last_name from Google profile
- Generate a random password (not used since they login via Google)

## 8. Troubleshooting

### Common Errors:

1. **"access_token is required"** - Make sure you're sending the Google access token in the request body
2. **"Invalid token"** - Check that your Google OAuth app is properly configured
3. **"Redirect URI mismatch"** - Verify your redirect URIs in Google Console match your Django settings

### Debug Mode:

Check Django logs for detailed error messages when authentication fails.
