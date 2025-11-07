"""
Gemini Chat Service for managing AI conversation history.
"""

import logging
from typing import Dict, List, Optional

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory

logger = logging.getLogger(__name__)


class GeminiChatService:
    """Service for managing chat conversations with Gemini AI."""

    def __init__(self):
        self.ai_service_factory = AIServiceFactory()
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'

    def save_chat_history(self, user: User, conversation_id: str, messages: List[Dict]) -> bool:
        """
        Save chat conversation history.

        Args:
            user: The user whose conversation to save
            conversation_id: Unique conversation identifier
            messages: List of message dictionaries

        Returns:
            True if saved successfully, False otherwise
        """
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, self.default_model)
        if not ai_service:
            logger.error(
                "Gemini service not available for chat history operations")
            return False

        try:
            success = ai_service.save_chat_history(
                user, conversation_id, messages)
            if success:
                logger.info(
                    f"Chat history saved for user {user.id}, conversation {conversation_id}")
            else:
                logger.warning(
                    f"Failed to save chat history for user {user.id}, conversation {conversation_id}")
            return success

        except Exception as e:
            logger.error(
                f"Error saving chat history for user {user.id}: {str(e)}")
            return False

    def load_chat_history(self, user: User, conversation_id: str) -> Optional[List[Dict]]:
        """
        Load chat conversation history.

        Args:
            user: The user whose conversation to load
            conversation_id: Unique conversation identifier

        Returns:
            List of message dictionaries or None if not found
        """
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, self.default_model)
        if not ai_service:
            logger.error(
                "Gemini service not available for chat history operations")
            return None

        try:
            messages = ai_service.load_chat_history(user, conversation_id)
            if messages:
                logger.info(
                    f"Chat history loaded for user {user.id}, conversation {conversation_id}")
            else:
                logger.warning(
                    f"No chat history found for user {user.id}, conversation {conversation_id}")
            return messages

        except Exception as e:
            logger.error(
                f"Error loading chat history for user {user.id}: {str(e)}")
            return None

    def delete_chat_history(self, user: User, conversation_id: str) -> bool:
        """
        Delete chat conversation history.

        Args:
            user: The user whose conversation to delete
            conversation_id: Unique conversation identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, self.default_model)
        if not ai_service:
            logger.error(
                "Gemini service not available for chat history operations")
            return False

        try:
            success = ai_service.delete_chat_history(user, conversation_id)
            if success:
                logger.info(
                    f"Chat history deleted for user {user.id}, conversation {conversation_id}")
            else:
                logger.warning(
                    f"Failed to delete chat history for user {user.id}, conversation {conversation_id}")
            return success

        except Exception as e:
            logger.error(
                f"Error deleting chat history for user {user.id}: {str(e)}")
            return False

    def list_conversations(self, user: User) -> List[str]:
        """
        List all conversation IDs for a user.

        Args:
            user: The user whose conversations to list

        Returns:
            List of conversation IDs
        """
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, self.default_model)
        if not ai_service:
            logger.error(
                "Gemini service not available for chat history operations")
            return []

        try:
            conversations = ai_service.list_conversations(user)
            logger.info(
                f"Retrieved {len(conversations)} conversations for user {user.id}")
            return conversations

        except Exception as e:
            logger.error(
                f"Error listing conversations for user {user.id}: {str(e)}")
            return []

    def convert_history_to_serializable(self, history) -> List[Dict]:
        """
        Convert chat history to a serializable format.

        Args:
            history: Raw chat history from Gemini

        Returns:
            List of serializable message dictionaries
        """
        try:
            # This would contain the logic to convert Gemini history format
            # For now, delegate to the actual Gemini service
            ai_service = self.ai_service_factory.create_service(
                self.default_provider, self.default_model)
            if ai_service and hasattr(ai_service, '_convert_history_to_serializable'):
                return ai_service._convert_history_to_serializable(history)

            logger.error("History conversion not available")
            return []

        except Exception as e:
            logger.error(f"Error converting chat history: {str(e)}")
            return []
