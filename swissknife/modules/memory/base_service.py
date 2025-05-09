from typing import List, Dict, Any
from abc import ABC, abstractmethod


class BaseMemoryService(ABC):
    """Service for storing and retrieving conversation memory."""

    @property
    def session_id(self) -> str:
        """Get the provider name for this service."""
        return getattr(self, "_provider_name", "unknown")

    @session_id.setter
    def session_id(self, value: str):
        """Set the provider name for this service."""
        self._session_id = value

    @abstractmethod
    async def store_conversation(
        self, user_message: str, assistant_response: str
    ) -> List[str]:
        """
        Store a conversation exchange in memory.

        Args:
            user_message: The user's message
            assistant_response: The assistant's response

        Returns:
            List of memory IDs created
        """
        pass

    @abstractmethod
    async def need_generate_user_context(self, user_input) -> bool:
        pass

    @abstractmethod
    def clear_conversation_context(self):
        pass

    @abstractmethod
    async def generate_user_context(self, user_input: str) -> str:
        """
        Generate context based on user input by retrieving relevant memories.

        Args:
            user_input: The current user message to generate context for

        Returns:
            Formatted string containing relevant context from past conversations
        """
        pass

    @abstractmethod
    async def retrieve_memory(self, keywords: str, limit: int = 5) -> str:
        """
        Retrieve relevant memories based on keywords.

        Args:
            keywords: Keywords to search for
            limit: Maximum number of results to return

        Returns:
            Formatted string of relevant memories
        """
        pass

    @abstractmethod
    def cleanup_old_memories(self, months: int = 1) -> int:
        """
        Remove memories older than the specified number of months.

        Args:
            months: Number of months to keep

        Returns:
            Number of memories removed
        """
        pass

    @abstractmethod
    def forget_topic(self, topic: str) -> Dict[str, Any]:
        """
        Remove memories related to a specific topic based on keyword search.

        Args:
            topic: Keywords describing the topic to forget

        Returns:
            Dict with success status and information about the operation
        """
        pass
