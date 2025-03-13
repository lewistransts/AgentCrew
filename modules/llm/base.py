from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, Generator
from modules.tools.registry import ToolRegistry


class BaseLLMService(ABC):
    """Base interface for LLM services."""

    @property
    def provider_name(self) -> str:
        """Get the provider name for this service."""
        return getattr(self, "_provider_name", "unknown")

    @provider_name.setter
    def provider_name(self, value: str):
        """Set the provider name for this service."""
        self._provider_name = value

    def register_all_tools(self):
        """Register all available tools with this LLM service"""
        registry = ToolRegistry.get_instance()
        tool_definitions = registry.get_tool_definitions(self.provider_name)
        registered_tool = []
        for tool_def in tool_definitions:
            tool_name = self._extract_tool_name(tool_def)
            handler = registry.get_tool_handler(tool_name)
            if handler:
                self.register_tool(tool_def, handler)
                registered_tool.append(tool_name)
        if len(registered_tool) > 0:
            print(f"🔧 Available tools: {', '.join(registered_tool)}")

    def _extract_tool_name(self, tool_def):
        """Extract tool name from definition regardless of format"""
        if "name" in tool_def:
            return tool_def["name"]
        elif "function" in tool_def and "name" in tool_def["function"]:
            return tool_def["function"]["name"]
        else:
            raise ValueError("Could not extract tool name from definition")

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
    def set_think(self, budget_tokens: int) -> bool:
        """
        Enable or disable thinking mode with the specified token budget.

        Args:
            budget_tokens (int): Token budget for thinking. 0 to disable thinking mode.

        Returns:
            bool: True if thinking mode is supported and successfully set, False otherwise.
        """
        pass

    @abstractmethod
    def process_stream_chunk(
        self, chunk, assistant_response, tool_uses
    ) -> tuple[str, list[Dict] | None, int, int, str | None, tuple | None]:
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
                chunk_text (str or None) - text to print for this chunk,
                thinking_content (tuple or None) - thinking content from this chunk
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

    @abstractmethod
    def format_thinking_message(self, thinking_data) -> Dict[str, Any]:
        """
        Format thinking content into the appropriate message format for the LLM provider.

        Args:
            thinking_data: Tuple containing (thinking_content, thinking_signature)
                or None if no thinking data is available

        Returns:
            Dict[str, Any]: A properly formatted message containing thinking blocks
        """
        pass

    @abstractmethod
    def validate_spec(self, prompt: str) -> str:
        """
        Validate a specification prompt using the LLM.

        Args:
            prompt: The specification prompt to validate

        Returns:
            Validation result as a string (typically JSON)
        """
        pass
