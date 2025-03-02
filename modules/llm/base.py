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

    @abstractmethod
    def register_tool(self, tool_definition, handler_function):
        """
        Register a tool with its handler function.

        Args:
            tool_definition (dict): The tool definition following Anthropic's schema
            handler_function (callable): Function to call when tool is used
        """
        pass

    @abstractmethod
    def execute_tool(self, tool_name, tool_params) -> Any:
        """
        Execute a registered tool with the given parameters.

        Args:
            tool_name (str): Name of the tool to execute
            tool_params (dict): Parameters to pass to the tool

        Returns:
            dict: Result of the tool execution
        """
        pass

    @abstractmethod
    def process_stream_chunk(
        self, chunk, assistant_response, tool_uses
    ) -> tuple[str, list[Dict] | None, int, int, str | None]:
        """
        Process a single chunk from the streaming response.

        Args:
            chunk: The chunk from the stream
            assistant_response: Current accumulated assistant response
            tool_uses: Current tool use information

        Returns:
            tuple: (
                updated_assistant_response (str),
                updated_tool_uses (List of dict or empty),
                input_tokens (int),
                output_tokens (int),
                chunk_text (str or None) - text to print for this chunk
            )
        """
        pass

    @abstractmethod
    def format_tool_result(
        self, tool_use: Dict, tool_result: Any, is_error: bool = False
    ) -> Dict[str, Any]:
        """
        Format a tool result into the appropriate message format for the LLM provider.

        Args:
            tool_use_id: The ID of the tool use
            tool_result: The result from the tool execution
            is_error: Whether the result is an error

        Returns:
            A formatted message that can be appended to the messages list
        """
        pass

    @abstractmethod
    def format_assistant_message(
        self, assistant_response: str, tool_uses: list[Dict] | None = None
    ) -> Dict[str, Any]:
        """
        Format the assistant's response into the appropriate message format for the LLM provider.

        Args:
            assistant_response (str): The text response from the assistant
            tool_use (Dict, optional): Tool use information if a tool was used

        Returns:
            Dict[str, Any]: A properly formatted message to append to the messages list
        """
        pass
