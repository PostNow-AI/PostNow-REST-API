"""
Encryption utilities for sensitive data (OAuth tokens, etc.)
Uses Fernet symmetric encryption from cryptography library.
"""

import os

from cryptography.fernet import Fernet


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    Uses Fernet (symmetric encryption) with key stored in environment variables.
    """

    def __init__(self):
        # Get encryption key from environment
        key = os.getenv('INSTAGRAM_TOKEN_ENCRYPTION_KEY')

        if not key:
            # Generate a new key if not set (for development)
            # In production, this should be set in environment variables
            key = Fernet.generate_key().decode()
            print("⚠️  WARNING: No INSTAGRAM_TOKEN_ENCRYPTION_KEY found!")
            print(f"⚠️  Generated temporary key: {key}")
            print(
                f"⚠️  Add this to your .env file: INSTAGRAM_TOKEN_ENCRYPTION_KEY={key}")

        # Ensure key is bytes
        if isinstance(key, str):
            key = key.encode()

        self.cipher = Fernet(key)

    def encrypt_token(self, plain_text: str) -> str:
        """
        Encrypt a token/string.

        Args:
            plain_text: The plain text to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        if not plain_text:
            return plain_text

        # Convert to bytes if string
        if isinstance(plain_text, str):
            plain_text = plain_text.encode()

        # Encrypt and return as string
        encrypted = self.cipher.encrypt(plain_text)
        return encrypted.decode()

    def decrypt_token(self, encrypted_text: str) -> str:
        """
        Decrypt a token/string.

        Args:
            encrypted_text: The encrypted text to decrypt

        Returns:
            Decrypted plain text string
        """
        if not encrypted_text:
            return encrypted_text

        # Convert to bytes if string
        if isinstance(encrypted_text, str):
            encrypted_text = encrypted_text.encode()

        # Decrypt and return as string
        decrypted = self.cipher.decrypt(encrypted_text)
        return decrypted.decode()


# Singleton instance
_encryption_service = None


def get_encryption_service():
    """Get or create encryption service singleton"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_token(plain_text: str) -> str:
    """Helper function to encrypt a token"""
    service = get_encryption_service()
    return service.encrypt_token(plain_text)


def decrypt_token(encrypted_text: str) -> str:
    """Helper function to decrypt a token"""
    service = get_encryption_service()
    return service.decrypt_token(encrypted_text)
