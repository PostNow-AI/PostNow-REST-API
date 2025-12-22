#!/usr/bin/env python
"""
Script to help test Google OAuth authentication
This will help you get a Google access token for testing in Postman
"""

import os
import sys
import webbrowser

import django
from google_auth_oauthlib.flow import Flow

# Add parent directory to Python path so we can import Sonora_REST_API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
django.setup()


def get_google_access_token():
    """
    Get a Google access token for testing purposes
    """

    # You need to get these from your Google Cloud Console
    CLIENT_ID = input("Enter your Google Client ID: ")
    CLIENT_SECRET = input("Enter your Google Client Secret: ")

    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: CLIENT_ID and CLIENT_SECRET are required")
        return

    # OAuth 2.0 configuration
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8000/api/v1/auth/google/callback/"]
        }
    }

    # Scopes needed for user info
    scopes = ['openid', 'email', 'profile']

    # Create the flow
    flow = Flow.from_client_config(
        client_config,
        scopes=scopes,
        redirect_uri="http://localhost:8000/api/v1/auth/google/callback/"
    )

    # Get authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')

    print("\n" + "="*60)
    print("GOOGLE OAUTH TESTING STEPS:")
    print("="*60)
    print("1. Open this URL in your browser:")
    print(f"   {auth_url}")
    print("\n2. Complete the OAuth flow")
    print("3. You'll be redirected to a page that might show an error")
    print("4. Copy the ENTIRE URL from your browser's address bar")
    print("5. Paste it below")
    print("\nNote: The page might show an error, but we just need the URL with the code parameter")
    print("="*60)

    # Automatically open browser
    try:
        webbrowser.open(auth_url)
        print("✓ Browser opened automatically")
    except:
        print("! Could not open browser automatically")

    # Get the authorization response
    authorization_response = input(
        "\nPaste the full redirect URL here: ").strip()

    if not authorization_response:
        print("Error: No URL provided")
        return

    try:
        # Exchange authorization code for access token
        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials
        access_token = credentials.token

        print("\n" + "="*60)
        print("SUCCESS! Here's your access token for Postman:")
        print("="*60)
        print(f"Access Token: {access_token}")
        print("\nNow you can use this in Postman:")
        print("URL: http://localhost:8000/api/v1/auth/google/")
        print("Method: POST")
        print("Headers: Content-Type: application/json")
        print("Body (raw JSON):")
        print(f'{{"access_token": "{access_token}"}}')
        print("="*60)

        return access_token

    except Exception as e:
        print(f"Error exchanging code for token: {e}")
        print("\nMake sure:")
        print("1. You copied the complete URL")
        print("2. Your redirect URI is exactly: http://localhost:8000/api/v1/auth/google/callback/")
        print("3. Your Google OAuth app is properly configured")


if __name__ == "__main__":
    print("Google OAuth Access Token Generator for Testing")
    print("=" * 50)
    get_google_access_token()
