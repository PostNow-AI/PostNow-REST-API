"""
Chat History Service for managing AI conversation history.
"""

import logging
from typing import Dict, List, Optional

from django.contrib.auth.models import User

from .ai_service_factory import AIServiceFactory

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """Service for managing AI conversation history."""

    def __init__(self):
        self.ai_service_factory = AIServiceFactory()
        self.default_provider = 'google'
        self.default_model = 'gemini-2.5-flash'

    def save_chat_history(self, user: User, conversation_id: str,
                          messages: List[Dict], model_name: str = None) -> bool:
        """
        Save chat conversation history to storage.

        Args:
            user: The user whose conversation to save
            conversation_id: Unique identifier for the conversation
            messages: List of message dictionaries
            model_name: The AI model used in the conversation

        Returns:
            True if saved successfully, False otherwise
        """
        model_name = model_name or self.default_model

        # Use Google service for chat history operations
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            logger.error(
                "Google service not available for chat history operations")
            return False

        try:
            success = ai_service.save_chat_history(
                user, conversation_id, messages)
            if success:
                logger.info(
                    f"Chat history saved successfully for user {user.id}, conversation {conversation_id}")
            else:
                logger.warning(
                    f"Failed to save chat history for user {user.id}, conversation {conversation_id}")
            return success

        except Exception as e:
            logger.error(
                f"Error saving chat history for user {user.id}: {str(e)}")
            return False

    def load_chat_history(self, user: User, conversation_id: str,
                          model_name: str = None) -> Optional[List[Dict]]:
        """
        Load chat conversation history from storage.

        Args:
            user: The user whose conversation to load
            conversation_id: Unique identifier for the conversation
            model_name: The AI model used in the conversation

        Returns:
            List of message dictionaries or None if not found
        """
        model_name = model_name or self.default_model

        # Use Google service for chat history operations
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            logger.error(
                "Google service not available for chat history operations")
            return None

        try:
            messages = ai_service.load_chat_history(user, conversation_id)
            if messages:
                logger.info(
                    f"Chat history loaded successfully for user {user.id}, conversation {conversation_id}")
            else:
                logger.warning(
                    f"No chat history found for user {user.id}, conversation {conversation_id}")
            return messages

        except Exception as e:
            logger.error(
                f"Error loading chat history for user {user.id}: {str(e)}")
            return None

    def delete_chat_history(self, user: User, conversation_id: str,
                            model_name: str = None) -> bool:
        """
        Delete chat conversation history from storage.

        Args:
            user: The user whose conversation to delete
            conversation_id: Unique identifier for the conversation
            model_name: The AI model used in the conversation

        Returns:
            True if deleted successfully, False otherwise
        """
        model_name = model_name or self.default_model

        # Use Google service for chat history operations
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            logger.error(
                "Google service not available for chat history operations")
            return False

        try:
            success = ai_service.delete_chat_history(user, conversation_id)
            if success:
                logger.info(
                    f"Chat history deleted successfully for user {user.id}, conversation {conversation_id}")
            else:
                logger.warning(
                    f"Failed to delete chat history for user {user.id}, conversation {conversation_id}")
            return success

        except Exception as e:
            logger.error(
                f"Error deleting chat history for user {user.id}: {str(e)}")
            return False

    def list_conversations(self, user: User, model_name: str = None) -> List[str]:
        """
        List all conversation IDs for a user.

        Args:
            user: The user whose conversations to list
            model_name: The AI model used in the conversations

        Returns:
            List of conversation IDs
        """
        model_name = model_name or self.default_model

        # Use Google service for chat history operations
        ai_service = self.ai_service_factory.create_service(
            self.default_provider, model_name)
        if not ai_service:
            logger.error(
                "Google service not available for chat history operations")
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
