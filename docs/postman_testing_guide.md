# Testing Google OAuth in Postman

## Method 1: Using the Test Script (Recommended)

1. **Run the test script**:

   ```bash
   source env/bin/activate
   python test_google_auth.py
   ```

2. **Follow the prompts**:

   - Enter your Google Client ID and Secret
   - Browser will open automatically
   - Complete Google OAuth flow
   - Copy the redirect URL and paste it back
   - Get your access token

3. **Use in Postman**:
   - **URL**: `http://localhost:8000/api/v1/auth/google/`
   - **Method**: `POST`
   - **Headers**: `Content-Type: application/json`
   - **Body** (raw/JSON):
     ```json
     {
       "access_token": "your_token_here"
     }
     ```

## Method 2: Manual Google OAuth (Browser Method)

1. **Create OAuth URL manually**:

   ```
   https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/api/v1/auth/google/callback/&scope=openid%20email%20profile&response_type=code&access_type=online
   ```

2. **Replace `YOUR_CLIENT_ID`** with your actual Google Client ID

3. **Open URL in browser**, complete OAuth flow

4. **Extract the code** from redirect URL:

   ```
   http://localhost:8000/api/v1/auth/google/callback/?code=SOME_LONG_CODE&scope=...
   ```

5. **Exchange code for token** using another API call in Postman:

   - **URL**: `https://oauth2.googleapis.com/token`
   - **Method**: `POST`
   - **Headers**: `Content-Type: application/x-www-form-urlencoded`
   - **Body** (x-www-form-urlencoded):
     ```
     client_id=YOUR_CLIENT_ID
     client_secret=YOUR_CLIENT_SECRET
     code=THE_CODE_FROM_STEP_4
     grant_type=authorization_code
     redirect_uri=http://localhost:8000/api/v1/auth/google/callback/
     ```

6. **Use the access_token** from response in your Django API

## Method 3: Google OAuth Playground (Easiest)

1. **Go to**: https://developers.google.com/oauthplayground/

2. **Step 1 - Select scopes**:

   - Add these scopes:
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
     - `openid`

3. **Step 1 - Configuration** (click gear icon):

   - Check "Use your own OAuth credentials"
   - Enter your Client ID and Secret

4. **Authorize APIs** → Complete OAuth flow

5. **Step 2 - Exchange authorization code** → Get tokens

6. **Copy the Access Token** and use in Postman

## Postman Configuration Details

### Headers:

```
Content-Type: application/json
```

### Body (raw, JSON):

```json
{
  "access_token": "ya29.a0AfH6SMBxxxxxxxxxxxxxxxxxxxxxx"
}
```

### Expected Response:

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

## Common Errors & Solutions

### Error 415 "Unsupported Media Type"

- **Cause**: Missing or incorrect `Content-Type` header
- **Solution**: Add `Content-Type: application/json` header

### Error 400 "access_token is required"

- **Cause**: Missing access_token in request body
- **Solution**: Include access_token in JSON body

### Error 400 "Invalid token"

- **Cause**: Expired or invalid Google access token
- **Solution**: Generate a new access token (they expire quickly, usually 1 hour)

### Error "Invalid client_id"

- **Cause**: Google OAuth app not configured correctly
- **Solution**: Check your Google Cloud Console settings

## Quick Test Commands

### Test regular email login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "msallesblanco@gmail.com", "password": "your_password"}'
```

### Test Google OAuth login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{"access_token": "your_google_access_token"}'
```

## Notes

- Google access tokens expire quickly (usually 1 hour)
- For testing, Method 3 (OAuth Playground) is often easiest
- The test script (Method 1) gives you the most control
- Make sure your Django server is running on `http://localhost:8000`
