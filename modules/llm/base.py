from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, Generator


class BaseLLMService(ABC):
    """Base interface for LLM services."""
    
    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost of a request based on token usage."""
        pass
    
    @abstractmethod
    def summarize_content(self, content: str) -> str:
        """Summarize the provided content."""
        pass
    
    @abstractmethod
    def explain_content(self, content: str) -> str:
        """Explain the provided content."""
        pass
    
    @abstractmethod
    def process_file_for_message(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process a file and return the appropriate message content."""
        pass
    
    @abstractmethod
    def handle_file_command(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Handle the /file command and return message content."""
        pass
    
    @abstractmethod
    def stream_assistant_response(self, messages: List[Dict[str, Any]]) -> Any:
        """Stream the assistant's response."""
        pass
