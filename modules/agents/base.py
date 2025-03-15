from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable


class Agent(ABC):
    """Base class for all specialized agents."""

    def __init__(self, name: str, description: str, llm_service):
        """
        Initialize a new agent.

        Args:
            name: The name of the agent
            description: A description of the agent's capabilities
            llm_service: The LLM service to use for this agent
        """
        self.name = name
        self.description = description
        self.llm = llm_service
        self.system_prompt = None
        self.tools = []

    def register_tool(self, tool_definition, handler_function):
        """
        Register a tool with this agent.

        Args:
            tool_definition: The tool definition
            handler_function: The function that handles the tool
        """
        # Store the tool definition and handler in the agent's tools list
        self.tools.append((tool_definition, handler_function))

    def set_system_prompt(self, prompt: str):
        """
        Set the system prompt for this agent.

        Args:
            prompt: The system prompt
        """
        self.system_prompt = prompt

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.

        Returns:
            The system prompt
        """
        return self.system_prompt

    def register_tools_with_llm(self):
        """
        Register all of this agent's tools with the LLM service.
        """
        if not self.llm:
            return
            
        for tool_definition, handler_function in self.tools:
            self.llm.register_tool(tool_definition, handler_function)
    
    def clear_tools_from_llm(self):
        """
        Clear all tools from the LLM service.
        """
        if self.llm:
            self.llm.clear_tools()
    
    def process_messages(self, messages: List[Dict[str, Any]]):
        """
        Process messages using this agent.

        Args:
            messages: The messages to process

        Returns:
            The processed messages with the agent's response
        """
        # Ensure the first message is a system message with the agent's prompt
        if not messages or messages[0].get("role") != "system":
            system_message = {"role": "system", "content": self.get_system_prompt()}
            messages = [system_message] + messages
        elif messages[0].get("role") == "system":
            # Update the system message with this agent's prompt
            messages[0]["content"] = self.get_system_prompt()

        return messages
