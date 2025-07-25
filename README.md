# Sonora REST API

A Django REST API with email and Google OAuth authentication using JWT tokens.

## 📚 Documentation

All documentation has been moved to the [docs/](docs/) folder:

- **[Getting Started](docs/google_console_setup.md)** - Google OAuth setup guide
- **[Testing with Postman](docs/postman_testing_guide.md)** - How to test API endpoints
- **[Frontend Integration](docs/google_oauth_examples.md)** - JavaScript examples for frontend

## 🚀 Quick Start

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database:**

   ```bash
   python manage.py migrate
   ```

3. **Configure Google OAuth:**

   ```bash
   python manage_google_oauth.py YOUR_CLIENT_ID YOUR_CLIENT_SECRET
   ```

4. **Run server:**

   ```bash
   python manage.py runserver
   ```

## 🔐 Authentication Endpoints

- **Email/Password Login:** `POST /api/v1/auth/login/`
- **Google OAuth Login:** `POST /api/v1/auth/google/`
- **User Registration:** `POST /api/v1/auth/registration/`

## 📖 Full Documentation

Visit the [docs/](docs/) folder for complete guides and examples.

---

**Note:** Make sure to check the documentation for detailed setup instructions and troubleshooting guides.
