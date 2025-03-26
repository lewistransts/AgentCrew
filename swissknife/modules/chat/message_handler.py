from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import time
import traceback
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich.live import Live
from swissknife.modules.chat.history import ChatHistoryManager, ConversationTurn
from swissknife.modules.llm.base import BaseLLMService  # Assuming this exists
from swissknife.modules.agents.manager import AgentManager
from swissknife.modules.chat.file_handler import FileHandler
from swissknife.modules.llm.models import ModelRegistry
from swissknife.modules.llm.service_manager import ServiceManager
from swissknife.modules.llm.message import MessageTransformer

# Constants from the original code
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
RED = "\033[31m"
GRAY = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"
RICH_YELLOW = "yellow"
RICH_GRAY = "grey"


class Observable:
    """Base class for observables, implementing the observer pattern."""

    def __init__(self):
        self._observers: List["Observer"] = []

    def attach(self, observer: "Observer"):
        """Attaches an observer to the observable."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: "Observer"):
        """Detaches an observer from the observable."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify(self, event: str, data: Any = None):
        """Notifies all attached observers of a new event."""
        for observer in self._observers:
            observer.update(event, data)


class Observer(ABC):
    """Abstract base class for observers."""

    @abstractmethod
    def update(self, event: str, data: Any = None):
        """Updates the observer with new data from the observable."""
        pass


class MessageHandler(Observable):
    """
    Handles message processing, interaction with the LLM service, and manages
    conversation history. Uses the Observer pattern to notify UI components
    about relevant events.
    """

    def __init__(self, memory_service=None):
        """
        Initializes the MessageHandler.

        Args:
            llm_service: The LLM service to use for generating responses.
            memory_service: Optional memory service for storing conversations.
        """
        super().__init__()
        self.agent_manager = AgentManager.get_instance()
        self.llm = self.agent_manager.get_current_agent().llm
        self.agent_name = self.agent_manager.get_current_agent().name
        self.memory_service = memory_service
        self.history_manager = ChatHistoryManager()
        self.latest_assistant_response = ""
        self.conversation_turns = []
        self.file_handler = FileHandler()

    def process_user_input(
        self,
        user_input: str,
        messages: List[Dict[str, Any]],
        message_content: Optional[List[Dict]] = None,
        files: Optional[List[str]] = None,
    ) -> Tuple[List[Dict[str, Any]], bool, bool]:
        """
        Processes user input, handles commands, and updates message history.

        Args:
            user_input: The input string from the user.
            messages: Current message history.
            message_content: Optional content to prepend.
            files: Optional files to include.

        Returns:
            Tuple of (messages, exit_flag, clear_flag)
        """
        # Handle exit command
        if self._handle_exit_command(user_input):
            self._notify("exit_requested")
            return messages, True, False

        # Handle clear command
        if user_input.lower() == "/clear":
            self.conversation_turns = []  # Clear conversation turns
            self._notify("clear_requested")
            return [], False, True  # messages, exit_flag, clear_flag

        # Handle copy command
        if user_input.lower() == "/copy":
            self._notify("copy_requested", self.latest_assistant_response)
            return messages, False, True  # Skip to next iteration

        # Handle debug command
        if user_input.lower() == "/debug":
            self._notify("debug_requested", messages)
            return messages, False, True

        # Handle think command
        if user_input.lower().startswith("/think "):
            try:
                budget = int(user_input[7:].strip())
                self.llm.set_think(budget)
                self._notify("think_budget_set", budget)
            except ValueError:
                self._notify("error", "Invalid budget value. Please provide a number.")
            return messages, False, True

        # Handle jump command
        if user_input.lower().startswith("/jump "):
            new_messages, jumped = self._handle_jump_command(user_input, messages)
            if jumped and new_messages:
                return new_messages, False, True
            return messages, False, True

        # Handle agent command
        if user_input.lower().startswith("/agent"):
            success, message = self._handle_agent_command(user_input)
            self._notify(
                "agent_command_result", {"success": success, "message": message}
            )
            return messages, False, True

        # Handle model command
        if user_input.lower().startswith("/model"):
            return self._handle_model_command(user_input, messages)

        # Store non-command messages in history
        if not user_input.startswith("/"):
            self.history_manager.add_entry(user_input)

        # Handle files that were loaded but not yet sent
        if files and not messages:
            combined_content = message_content.copy() if message_content else []
            combined_content.append({"type": "text", "text": user_input})
            messages.append({"role": "user", "content": combined_content})
            self._notify(
                "user_message_created", {"message": messages[-1], "with_files": True}
            )
        # Handle file command
        elif user_input.startswith("/file "):
            file_path = user_input[6:].strip()
            file_path = os.path.expanduser(file_path)

            # Process file with the file handling service
            file_content = self.file_handler.process_file(file_path)

            if file_content:
                messages.append({"role": "user", "content": [file_content]})
                self._notify(
                    "file_processed", {"file_path": file_path, "message": messages[-1]}
                )
                return messages, False, True
            else:
                self._notify("error", f"Failed to process file {file_path}")
                return messages, False, True
        else:
            # Add regular text message
            messages.append(
                {"role": "user", "content": [{"type": "text", "text": user_input}]}
            )
            self._notify(
                "user_message_created", {"message": messages[-1], "with_files": False}
            )

        return messages, False, False

    def _handle_exit_command(self, user_input: str) -> bool:
        """Check if the user wants to exit the chat."""
        return user_input.lower() in ["exit", "quit"]

    def _handle_jump_command(
        self, command: str, messages: List[Dict[str, Any]]
    ) -> Tuple[Optional[List[Dict[str, Any]]], bool]:
        """Handle the /jump command to rewind conversation to a previous turn."""
        try:
            # Extract the turn number from the command
            parts = command.split()
            if len(parts) != 2:
                self._notify("error", "Usage: /jump <turn_number>")
                return None, False

            turn_number = int(parts[1])

            # Validate the turn number
            if turn_number < 1 or turn_number > len(self.conversation_turns):
                self._notify(
                    "error",
                    f"Invalid turn number. Available turns: 1-{len(self.conversation_turns)}",
                )
                return None, False

            # Get the selected turn
            selected_turn = self.conversation_turns[turn_number - 1]

            # Provide feedback via notification
            self._notify(
                "jump_performed",
                {"turn_number": turn_number, "preview": selected_turn.get_preview(100)},
            )

            # Truncate messages to the index from the selected turn
            truncated_messages = messages[: selected_turn.message_index]
            self.conversation_turns = self.conversation_turns[: turn_number - 1]

            # Return the truncated messages
            return truncated_messages, True

        except ValueError:
            self._notify("error", "Invalid turn number. Please provide a number.")
            return None, False

    def _handle_model_command(
        self, command: str, messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], bool, bool]:
        """
        Handle the /model command to switch models or list available models.

        Args:
            command: The model command string
            messages: The current message history

        Returns:
            Tuple of (messages, exit_flag, clear_flag)
        """
        model_id = command[7:].strip()
        registry = ModelRegistry.get_instance()
        manager = ServiceManager.get_instance()

        # If no model ID is provided, list available models
        if not model_id:
            models_by_provider = {}
            for provider in ["claude", "openai", "groq", "google"]:
                models = registry.get_models_by_provider(provider)
                if models:
                    models_by_provider[provider] = []
                    for model in models:
                        current = (
                            registry.current_model
                            and registry.current_model.id == model.id
                        )
                        models_by_provider[provider].append(
                            {
                                "id": model.id,
                                "name": model.name,
                                "description": model.description,
                                "capabilities": model.capabilities,
                                "current": current,
                            }
                        )

            self._notify("models_listed", models_by_provider)
            return messages, False, True

        # Try to switch to the specified model
        if registry.set_current_model(model_id):
            model = registry.get_current_model()
            if model:
                # Get the current provider
                current_provider = self.llm.provider_name

                # If we're switching providers, convert messages
                if current_provider != model.provider:
                    # Standardize messages from current provider
                    std_messages = MessageTransformer.standardize_messages(
                        messages, current_provider
                    )
                    # Convert to new provider format
                    messages = MessageTransformer.convert_messages(
                        std_messages, model.provider
                    )

                # Update the LLM service
                manager.set_model(model.provider, model.id)

                # Get the new LLM service
                new_llm_service = manager.get_service(model.provider)

                # Update the agent manager with the new LLM service
                self.agent_manager.update_llm_service(new_llm_service)

                # Update our reference to the LLM
                self.llm = self.agent_manager.get_current_agent().llm

                self._notify(
                    "model_changed",
                    {"id": model.id, "name": model.name, "provider": model.provider},
                )
            else:
                self._notify("error", "Failed to switch model.")
        else:
            self._notify("error", f"Unknown model: {model_id}")

        return messages, False, True

    def _handle_agent_command(self, command: str) -> Tuple[bool, str]:
        """
        Handle the /agent command to switch agents or list available agents.

        Args:
            command: The agent command string

        Returns:
            Tuple of (success, message)
        """
        parts = command.split()

        # If no agent name is provided, list available agents
        if len(parts) == 1:
            available_agents = list(self.agent_manager.agents.keys())
            current_agent = self.agent_manager.get_current_agent()
            current_agent_name = current_agent.name if current_agent else "None"

            agents_info = {"current": current_agent_name, "available": {}}

            for agent_name, agent in self.agent_manager.agents.items():
                agents_info["available"][agent_name] = {
                    "description": agent.description,
                    "current": (current_agent and current_agent.name == agent_name),
                }

            self._notify("agents_listed", agents_info)
            return True, "Listed available agents"

        # If an agent name is provided, try to switch to that agent
        agent_name = parts[1]
        if self.agent_manager.select_agent(agent_name):
            # Update the LLM reference to the new agent's LLM
            self.llm = self.agent_manager.get_current_agent().llm
            self.agent_name = agent_name
            self._notify("agent_changed", agent_name)
            return True, f"Switched to {agent_name} agent"
        else:
            available_agents = ", ".join(self.agent_manager.agents.keys())
            self._notify(
                "error",
                f"Unknown agent: {agent_name}. Available agents: {available_agents}",
            )
            return (
                False,
                f"Unknown agent: {agent_name}. Available agents: {available_agents}",
            )

    def get_assistant_response(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[Optional[str], int, int]:
        """
        Stream the assistant's response and return the response and token usage.

        Args:
            messages: A list of messages representing the conversation history.

        Returns:
            Tuple of (assistant_response, input_tokens, output_tokens)
        """
        assistant_response = ""
        tool_uses = []
        thinking_content = ""  # Reset thinking content for new response
        thinking_signature = ""  # Store the signature
        start_thinking = True
        input_tokens = 0
        output_tokens = 0

        try:
            with self.llm.stream_assistant_response(messages) as stream:
                for chunk in stream:
                    # Process the chunk using the LLM service
                    (
                        assistant_response,
                        tool_uses,
                        chunk_input_tokens,
                        chunk_output_tokens,
                        chunk_text,
                        thinking_chunk,
                    ) = self.llm.process_stream_chunk(
                        chunk, assistant_response, tool_uses
                    )

                    # Update token counts
                    if chunk_input_tokens > 0:
                        input_tokens = chunk_input_tokens
                    if chunk_output_tokens > 0:
                        output_tokens = chunk_output_tokens

                    # Accumulate thinking content if available
                    if thinking_chunk:
                        thinking_chunk, signature = thinking_chunk
                        if thinking_chunk:
                            thinking_content += thinking_chunk
                        if signature:
                            thinking_signature += signature

                        # Notify about thinking process
                        if start_thinking:
                            self._notify("thinking_started", self.agent_name)
                            start_thinking = False
                        self._notify("thinking_chunk", thinking_chunk)

                    # Notify about response progress
                    self._notify("response_chunk", assistant_response)

            # Handle tool use if needed
            if tool_uses and len(tool_uses) > 0:
                # Add thinking content as a separate message if available
                thinking_data = (
                    (thinking_content, thinking_signature) if thinking_content else None
                )
                thinking_message = self.llm.format_thinking_message(thinking_data)
                if thinking_message:
                    messages.append(thinking_message)
                    self._notify("thinking_message_added", thinking_message)

                # Format assistant message with the response and tool uses
                assistant_message = self.llm.format_assistant_message(
                    assistant_response, tool_uses
                )
                messages.append(assistant_message)
                self._notify("assistant_message_added", assistant_message)

                # Process each tool use
                for tool_use in tool_uses:
                    self._notify("tool_use", tool_use)

                    try:
                        tool_result = self.llm.execute_tool(
                            tool_use["name"], tool_use["input"]
                        )
                        tool_result_message = self.llm.format_tool_result(
                            tool_use, tool_result
                        )
                        messages.append(tool_result_message)
                        self._notify(
                            "tool_result",
                            {
                                "tool_use": tool_use,
                                "tool_result": tool_result,
                                "message": tool_result_message,
                            },
                        )

                        # Update llm service when handoff agent
                        if tool_use["name"] == "handoff":
                            self.llm = self.agent_manager.get_current_agent().llm
                            self.agent_name = (
                                self.agent_manager.get_current_agent().name
                            )
                            self._notify("agent_changed_by_handoff", self.agent_name)

                    except Exception as e:
                        error_message = self.llm.format_tool_result(
                            tool_use, str(e), is_error=True
                        )
                        messages.append(error_message)
                        self._notify(
                            "tool_error",
                            {
                                "tool_use": tool_use,
                                "error": str(e),
                                "message": error_message,
                            },
                        )

                # Continuation after tool use
                self._notify("agent_continue", self.agent_name)
                return self.get_assistant_response(messages)

            if thinking_content:
                self._notify("thinking_completed")
                self._notify("agent_continue", self.agent_name)

            # Final assistant message
            self._notify("response_completed", assistant_response)

            # Store the latest response
            self.latest_assistant_response = assistant_response

            # Store conversation in memory if memory service is available
            if (
                self.memory_service
                and messages[-1]["role"] == "user"
                and assistant_response
            ):
                user_input = ""
                if (
                    isinstance(messages[-1]["content"], list)
                    and len(messages[-1]["content"]) > 0
                ):
                    for content_item in messages[-1]["content"]:
                        if content_item.get("type") == "text":
                            user_input += content_item.get("text", "")
                elif isinstance(messages[-1]["content"], str):
                    user_input = messages[-1]["content"]

                try:
                    self.memory_service.store_conversation(
                        user_input, assistant_response
                    )
                except Exception as e:
                    self._notify(
                        "error", f"Failed to store conversation in memory: {str(e)}"
                    )

            # Store the conversation turn
            for i, message in reversed(list(enumerate(messages))):
                if (
                    isinstance(message, dict)
                    and "role" in message
                    and message["role"] == "user"
                ):
                    if (
                        "content" in message
                        and isinstance(message["content"], list)
                        and len(message["content"]) > 0
                        and "type" in message["content"][0]
                        and message["content"][0]["type"] == "tool_result"
                    ):
                        continue
                    turn = ConversationTurn(
                        message,  # User message for preview
                        i,  # Index of the last message
                    )
                    self.conversation_turns.append(turn)
                    break

            return assistant_response, input_tokens, output_tokens

        except Exception as e:
            error_message = str(e)
            traceback_str = traceback.format_exc()
            self._notify(
                "error",
                {
                    "message": error_message,
                    "traceback": traceback_str,
                    "messages": messages,
                },
            )
            return None, 0, 0
