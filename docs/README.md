# Sonora REST API Documentation

Complete documentation for the Sonora REST API with Google OAuth authentication.

## 📋 Table of Contents

### Setup Guides

1. **[Google Console Setup](google_console_setup.md)**
   - How to configure Google OAuth in Google Cloud Console
   - Correct redirect URLs for Django backend
   - Step-by-step setup process

### Testing & Development

2. **[Postman Testing Guide](postman_testing_guide.md)**
   - 3 methods to get Google access tokens
   - Complete Postman configuration
   - Common errors and solutions
   - cURL examples

### Frontend Integration

3. **[Google OAuth Examples](google_oauth_examples.md)**
   - JavaScript integration examples
   - Google Identity Services setup
   - Response format documentation
   - Complete frontend workflows

## 🔗 Quick Links

### API Endpoints

- **Email Login:** `POST /api/v1/auth/login/`
- **Google OAuth:** `POST /api/v1/auth/google/`
- **Registration:** `POST /api/v1/auth/registration/`
- **User Details:** `GET /api/v1/auth/user/`
- **Logout:** `POST /api/v1/auth/logout/`

### Helper Scripts

- `manage_google_oauth.py` - Set up Google OAuth credentials
- `test_google_auth.py` - Generate access tokens for testing

## 🆘 Need Help?

1. **Setup Issues:** Start with [Google Console Setup](google_console_setup.md)
2. **Testing Problems:** Check [Postman Testing Guide](postman_testing_guide.md)
3. **Frontend Integration:** See [Google OAuth Examples](google_oauth_examples.md)

## 🔄 Authentication Flow

```
1. Frontend gets Google access token
2. Frontend sends token to Django API
3. Django validates with Google
4. Django returns JWT tokens
5. Frontend uses JWT for API calls
```

---

**Happy coding! 🚀**
