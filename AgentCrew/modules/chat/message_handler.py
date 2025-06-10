from abc import abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import traceback
import os
import time
import asyncio

from AgentCrew.modules import logger
from AgentCrew.modules.agents.base import MessageType
from AgentCrew.modules.agents.local_agent import LocalAgent
from AgentCrew.modules.chat.history import ChatHistoryManager, ConversationTurn
from AgentCrew.modules.agents import AgentManager
from AgentCrew.modules.chat.file_handler import FileHandler
from AgentCrew.modules.llm.model_registry import ModelRegistry
from AgentCrew.modules.llm.service_manager import ServiceManager
from AgentCrew.modules.llm.message import MessageTransformer
from AgentCrew.modules.memory import (
    BaseMemoryService,
    ContextPersistenceService,
    ChromaMemoryService,
)
from AgentCrew.modules.chat.consolidation import ConversationConsolidator


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
            observer.listen(event, data)


class Observer:
    """Abstract base class for observers."""

    @abstractmethod
    def listen(self, event: str, data: Any = None):
        """Updates the observer with new data from the observable."""
        pass


class MessageHandler(Observable):
    """
    Handles message processing, interaction with the LLM service, and manages
    conversation history. Uses the Observer pattern to notify UI components
    about relevant events.
    """

    def __init__(
        self,
        memory_service: BaseMemoryService,
        context_persistent_service: ContextPersistenceService,
    ):
        """
        Initializes the MessageHandler.

        Args:
            llm_service: The LLM service to use for generating responses.
            memory_service: Optional memory service for storing conversations.
        """
        super().__init__()
        self.agent_manager = AgentManager.get_instance()
        self.agent = self.agent_manager.get_current_agent()
        # self.llm = self.agent_manager.get_current_agent().llm
        self.memory_service = memory_service
        self.persistent_service = context_persistent_service
        self.history_manager = ChatHistoryManager()
        self.latest_assistant_response = ""
        self.conversation_turns = []
        self.current_user_input = None
        self.current_user_input_idx = -1
        self.last_assisstant_response_idx = -1
        self.file_handler = FileHandler()
        self.stop_streaming = False
        # self.messages = []  # Initialize empty messages list
        self.streamline_messages = []
        self.current_conversation_id = None  # ID for persistence

        # Tool confirmation tracking
        self._auto_approved_tools = set()  # Track tools approved for all future calls
        self._pending_confirmations = {}  # Store futures for confirmation requests
        self._next_confirmation_id = 0  # ID counter for confirmation requests

        self.start_new_conversation()  # Initialize first conversation

    def _messages_append(self, message):
        self.agent.history.append(message)

        std_msg = MessageTransformer.standardize_messages(
            [message], self.agent.get_provider(), self.agent.name
        )
        self.streamline_messages.extend(std_msg)

    async def process_user_input(
        self,
        user_input: str,
    ) -> Tuple[bool, bool]:
        """
        Processes user input, handles commands, and updates message history.

        Args:
            user_input: The input string from the user.
            message_content: Optional content to prepend.
            files: Optional files to include.

        Returns:
            Tuple of (exit_flag, clear_flag)
        """
        # Handle exit command
        if self._handle_exit_command(user_input):
            self._notify("exit_requested")
            return True, False

        # Handle clear command
        if user_input.lower() == "/clear":
            # Now handled by start_new_conversation
            self.start_new_conversation()
            return False, True  # exit_flag, clear_flag

        # Handle copy command
        if user_input.lower() == "/copy":
            self._notify("copy_requested", self.latest_assistant_response)
            return False, True  # Skip to next iteration

        # Handle debug command
        if user_input.lower() == "/debug":
            self._notify("debug_requested", self.agent.history)
            self._notify("debug_requested", self.streamline_messages)
            return False, True

        # Handle think command
        if user_input.lower().startswith("/think "):
            try:
                budget = user_input[7:].strip()
                self.agent.configure_think(budget)
                self._notify("think_budget_set", budget)
            except ValueError:
                self._notify("error", "Invalid budget value. Please provide a number.")
            return False, True

        # Handle consolidate command
        if user_input.lower().startswith("/consolidate"):
            try:
                # Extract the parameter (number of messages to preserve)
                parts = user_input.split()
                if len(parts) == 1:
                    # Default to preserving the last 10 messages if no count specified
                    preserve_count = 10
                else:
                    preserve_count = int(parts[1])

                if isinstance(self.agent, LocalAgent):
                    consolidator = ConversationConsolidator(self.agent.llm)

                    # Consolidate messages
                    result = await consolidator.consolidate(
                        self.streamline_messages, preserve_count
                    )

                    if result["success"]:
                        # Rebuild agent messages from consolidated messages
                        self.agent_manager.rebuild_agents_messages(
                            self.streamline_messages
                        )

                        # Notify UI about consolidation
                        self._notify("consolidation_completed", result)

                        # If we have a conversation ID, update the persistent storage
                        if self.current_conversation_id:
                            try:
                                self.persistent_service.append_conversation_messages(
                                    self.current_conversation_id,
                                    self.streamline_messages,
                                    True,  # Replace all messages with the consolidated version
                                )
                            except Exception as e:
                                self._notify(
                                    "error",
                                    f"Failed to save consolidated conversation: {str(e)}",
                                )

                        message = (
                            f"Consolidated {result['messages_consolidated']} messages, "
                            f"preserving {result['messages_preserved']} recent messages. "
                            f"Token savings: ~{result['original_token_count'] - result['consolidated_token_count']}"
                        )
                        self._notify("system_message", message)
                    else:
                        self._notify(
                            "system_message",
                            f"Consolidation skipped: {result['reason']}",
                        )

                    return False, True  # Not exiting, but handled command
                else:
                    self._notify(
                        "error",
                        "Consolidation is only supported with LocalAgent.",
                    )
            except ValueError as e:
                self._notify(
                    "error",
                    f"Invalid consolidation parameter: {str(e)}. Use /consolidate [number]",
                )
                return False, True
            except Exception as e:
                self._notify("error", f"Error during consolidation: {str(e)}")
                return False, True

        # Handle jump command
        if user_input.lower().startswith("/jump "):
            jumped = self._handle_jump_command(user_input)
            if jumped:
                return False, True
            return False, True

        # Handle agent command
        if user_input.lower().startswith("/agent"):
            success, message = self._handle_agent_command(user_input)
            self._notify(
                "agent_command_result", {"success": success, "message": message}
            )
            return False, True

        # Handle model command
        if user_input.lower().startswith("/model"):
            return self._handle_model_command(user_input)

        # Store non-command messages in history
        if not user_input.startswith("/"):
            self.history_manager.add_entry(user_input)

        # Handle files that were loaded but not yet sent
        # Handle file command
        if user_input.startswith("/file "):
            file_path = user_input[6:].strip()
            file_path = os.path.expanduser(file_path)

            # Process file with the file handling service
            file_content = self.file_handler.process_file(file_path)
            # Fallback to llm handle
            if not file_content:
                file_content = self.agent.format_message(
                    MessageType.FileContent, {"file_uri": file_path}
                )

            if file_content:
                self._messages_append({"role": "user", "content": [file_content]})
                if file_content.get("type", "") == "text":
                    # TODO: For testing retrieve with keywords when transfer
                    await self.memory_service.store_conversation(
                        file_content.get("text", ""), "", self.agent.name
                    )
                self._notify(
                    "file_processed",
                    {"file_path": file_path, "message": self.agent.history[-1]},
                )
                return False, True
            else:
                self._notify(
                    "error",
                    f"Failed to process file {file_path} Or Model is not supported",
                )
                return False, True
        else:
            # RAG base on user query
            if await self.memory_service.need_generate_user_context(user_input):
                self._notify("user_context_request", None)
                self._messages_append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Context from your memory:
                                {
                                    await self.memory_service.generate_user_context(
                                        user_input, self.agent.name
                                    )
                                }""",
                            }
                        ],
                    }
                )
            # Add regular text message
            self._messages_append(
                {"role": "user", "content": [{"type": "text", "text": user_input}]}
            )
            self.current_user_input = self.agent.history[-1]
            self.current_user_input_idx = len(self.streamline_messages) - 1
            self._notify(
                "user_message_created",
                {"message": self.agent.history[-1], "with_files": False},
            )

        return False, False

    def start_new_conversation(self):
        """Starts a new persistent conversation, clears history, and gets a new ID."""
        try:
            # Reset approved tools for the new conversation
            self._auto_approved_tools = set()

            # Ensure the service instance is available
            if (
                not hasattr(self, "persistent_service")
                or self.persistent_service is None
            ):
                raise RuntimeError(
                    "ContextPersistenceService not initialized in MessageHandler."
                )

            self.current_conversation_id = self.persistent_service.start_conversation()
            self.memory_service.session_id = self.current_conversation_id
            self.memory_service.loaded_conversation = False
            # self.messages = []  # Clear in-memory message list
            self.agent_manager.clean_agents_messages()
            self.streamline_messages = []
            self.conversation_turns = []  # Clear jump history
            self.memory_service.clear_conversation_context()
            self.last_assisstant_response_idx = 0
            self.current_user_input = None
            self.current_user_input_idx = -1
            # # Make sure memory service is processed with llm even if GROQ api is not available
            # if (
            #     isinstance(self.memory_service, ChromaMemoryService)
            #     and not self.memory_service.llm_service
            # ):
            #     self.memory_service.llm_service = self.agent.llm
            #
            # Notify UI about the new conversation
            self._notify(
                "system_message",
                f"Started new conversation: {self.current_conversation_id}",
            )
            # Re-use existing signal to clear UI display, ensures UI is reset
            self._notify("clear_requested")
            logger.info(
                f"INFO: Started new persistent conversation {self.current_conversation_id}"
            )
        except Exception as e:
            error_message = f"Failed to start new persistent conversation: {str(e)}"
            logger.error(f"ERROR: {error_message}")
            self._notify("error", {"message": error_message})

            self.current_conversation_id = (
                None  # Ensure saving fails safely if start fails
            )

    def _handle_exit_command(self, user_input: str) -> bool:
        """Check if the user wants to exit the chat."""
        return user_input.lower() in ["exit", "quit"]

    def _handle_jump_command(self, command: str) -> bool:
        """Handle the /jump command to rewind conversation to a previous turn."""
        try:
            # Extract the turn number from the command
            parts = command.split()
            if len(parts) != 2:
                self._notify("error", "Usage: /jump <turn_number>")
                return False

            turn_number = int(parts[1])

            # Validate the turn number
            if turn_number < 1 or turn_number > len(self.conversation_turns):
                self._notify(
                    "error",
                    f"Invalid turn number. Available turns: 1-{len(self.conversation_turns)}",
                )
                return False

            # Get the selected turn
            selected_turn = self.conversation_turns[turn_number - 1]

            # Provide feedback via notification

            # Truncate messages to the index from the selected turn
            self.streamline_messages = self.streamline_messages[
                : selected_turn.message_index
            ]
            if self.current_conversation_id:
                self.persistent_service.append_conversation_messages(
                    self.current_conversation_id,
                    self.streamline_messages,
                    True,
                )

            # Get the last assistant message from the streamline messages
            last_assistant_message = next(
                (
                    msg
                    for msg in reversed(self.streamline_messages)
                    if msg.get("role") == "assistant"
                ),
                None,
            )
            if last_assistant_message and last_assistant_message.get("agent", ""):
                self._handle_agent_command(f"/agent {last_assistant_message['agent']}")

            self.agent_manager.rebuild_agents_messages(self.streamline_messages)
            self.conversation_turns = self.conversation_turns[: turn_number - 1]
            self.last_assisstant_response_idx = len(self.agent.history)

            self._notify(
                "jump_performed",
                {"turn_number": turn_number, "preview": selected_turn.get_preview(100)},
            )

            # Return success
            return True

        except ValueError:
            self._notify("error", "Invalid turn number. Please provide a number.")
            return False

    def _handle_model_command(self, command: str) -> Tuple[bool, bool]:
        """
        Handle the /model command to switch models or list available models.

        Args:
            command: The model command string

        Returns:
            Tuple of (exit_flag, clear_flag)
        """
        model_id = command[7:].strip()
        registry = ModelRegistry.get_instance()
        manager = ServiceManager.get_instance()

        # If no model ID is provided, list available models
        if not model_id:
            models_by_provider = {}
            for provider in registry.get_providers():
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
                                "id": f"{model.provider}/{model.id}",
                                "name": model.name,
                                "description": model.description,
                                "capabilities": model.capabilities,
                                "current": current,
                            }
                        )

            self._notify("models_listed", models_by_provider)
            return False, True

        # Try to switch to the specified model
        if registry.set_current_model(model_id):
            model = registry.get_current_model()
            if model:
                # Update the LLM service
                manager.set_model(model.provider, model.id)

                # Get the new LLM service
                new_llm_service = manager.get_service(model.provider)

                # Update the agent manager with the new LLM service
                self.agent_manager.update_llm_service(new_llm_service)
                # if (
                #     isinstance(self.memory_service, ChromaMemoryService)
                #     and not self.memory_service.is_fixed_llm_service
                # ):
                #     # Update memory service with the new LLM service
                #     self.memory_service.llm_service = new_llm_service

                # Update our reference to the LLM
                # self..llm = self.agent_manager.get_current_agent().llm

                self._notify(
                    "model_changed",
                    {"id": model.id, "name": model.name, "provider": model.provider},
                )
            else:
                self._notify("error", "Failed to switch model.")
        else:
            self._notify("error", f"Unknown model: {model_id}")

        return False, True

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

            agents_info = {"current": self.agent.name, "available": {}}

            for agent_name, agent in self.agent_manager.agents.items():
                agents_info["available"][agent_name] = {
                    "description": agent.description,
                    "current": (self.agent and self.agent.name == agent_name),
                }

            self._notify("agents_listed", agents_info)
            return True, "Listed available agents"

        # If an agent name is provided, try to switch to that agent
        agent_name = parts[1]
        old_agent_name = self.agent_manager.get_current_agent().name
        if self.agent_manager.select_agent(agent_name):
            # Update the LLM reference to the new agent's LLM
            # self.llm = self.agent_manager.get_current_agent().llm
            self.agent = self.agent_manager.get_current_agent()
            old_agent = self.agent_manager.get_agent(old_agent_name)
            if old_agent:
                self.agent.history = list(old_agent.history)
                old_agent.history = []
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

    def _post_tool_transfer(self, tool_result):
        if self.current_conversation_id and self.last_assisstant_response_idx >= 0:
            self.persistent_service.append_conversation_messages(
                self.current_conversation_id,
                MessageTransformer.standardize_messages(
                    self.agent.history[self.last_assisstant_response_idx :],
                    self.agent.get_provider(),
                    self.agent.name,
                ),
            )

        # Update llm service when transfer agent
        self.agent = self.agent_manager.get_current_agent()

        self._messages_append(
            {
                "role": "user",
                "content": [{"type": "text", "text": tool_result}],
            }
        )
        if self.current_conversation_id:
            self.persistent_service.append_conversation_messages(
                self.current_conversation_id,
                [
                    {
                        "role": "user",
                        "agent": self.agent.name,
                        "content": [{"type": "text", "text": tool_result}],
                    }
                ],
            )
        self.last_assisstant_response_idx = len(self.agent.history)

        self._notify("agent_changed_by_transfer", self.agent.name)

    async def _wait_for_tool_confirmation(self, tool_use):
        """
        Create a future and wait for tool confirmation from the user.

        Args:
            tool_use: The tool use dictionary

        Returns:
            Dict with confirmation result containing action and any additional data
        """
        confirmation_id = self._next_confirmation_id
        self._next_confirmation_id += 1

        # Create a future that will be resolved when the user responds
        self._pending_confirmations[confirmation_id] = {"approval": "pending"}

        # Notify UI that confirmation is required
        tool_info = {**tool_use, "confirmation_id": confirmation_id}
        self._notify("tool_confirmation_required", tool_info)

        try:
            while self._pending_confirmations[confirmation_id]["approval"] == "pending":
                await asyncio.sleep(0.1)  # Wait for the user to respond
            # Wait for the user's response
            result = self._pending_confirmations[confirmation_id]
            logger.info(
                f"Successfully received tool confirmation {confirmation_id} with result: {result}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Error while waiting for tool confirmation {confirmation_id}: {str(e)}"
            )
            return {"action": "deny"}
        finally:
            # Clean up the future
            if confirmation_id in self._pending_confirmations:
                del self._pending_confirmations[confirmation_id]

    def resolve_tool_confirmation(self, confirmation_id, result):
        """
        Resolve a pending tool confirmation future with the user's decision.

        Args:
            confirmation_id: The ID of the confirmation request
            result: Dictionary with the user's decision (action: 'approve', 'approve_all', or 'deny')
        """
        if confirmation_id in self._pending_confirmations:
            self._pending_confirmations[confirmation_id] = {
                "approval": "done",
                **result,
            }

    async def get_assistant_response(
        self, input_tokens=0, output_tokens=0
    ) -> Tuple[Optional[str], int, int]:
        """
        Stream the assistant's response and return the response and token usage.

        Returns:
            Tuple of (assistant_response, input_tokens, output_tokens)
        """
        assistant_response = ""
        tool_uses = []
        thinking_content = ""  # Reset thinking content for new response
        thinking_signature = ""  # Store the signature
        start_thinking = False
        end_thinking = False

        # Create a reference to the streaming generator
        stream_generator = None

        try:
            # Store the generator in a variable so we can properly close it if needed
            stream_generator = self.agent.process_messages()

            async for (
                assistant_response,
                chunk_text,
                thinking_chunk,
            ) in stream_generator:
                # Check if stop was requested
                if self.stop_streaming:
                    self.stop_streaming = False  # Reset flag

                    # Properly close the generator instead of breaking
                    await stream_generator.aclose()
                    self._notify("streaming_stopped", assistant_response)

                # Accumulate thinking content if available
                if thinking_chunk:
                    think_text_chunk, signature = thinking_chunk

                    if not start_thinking:
                        # Notify about thinking process
                        self._notify("thinking_started", self.agent.name)
                        if not self.agent.is_streaming():
                            # Delays it a bit when using without stream
                            time.sleep(0.5)
                        start_thinking = True
                    if think_text_chunk:
                        thinking_content += think_text_chunk
                        self._notify("thinking_chunk", think_text_chunk)
                    if signature:
                        thinking_signature += signature
                if chunk_text:
                    # End thinking when chunk_text start
                    if not end_thinking and start_thinking:
                        self._notify("thinking_completed")
                        end_thinking = True
                    # Notify about response progress
                    if not self.agent.is_streaming():
                        # Delays it a bit when using without stream
                        time.sleep(0.5)
                    self._notify("response_chunk", (chunk_text, assistant_response))

            tool_uses, input_tokens_in_turn, output_tokens_in_turn = (
                self.agent.get_process_result()
            )
            input_tokens += input_tokens_in_turn
            output_tokens += output_tokens_in_turn
            # Handle tool use if needed
            if tool_uses and len(tool_uses) > 0:
                # Add thinking content as a separate message if available
                thinking_data = (
                    (thinking_content, thinking_signature) if thinking_content else None
                )
                thinking_message = self.agent.format_message(
                    MessageType.Thinking, {"thinking": thinking_data}
                )
                if thinking_message:
                    self._messages_append(thinking_message)
                    self._notify("thinking_message_added", thinking_message)

                # Format assistant message with the response and tool uses
                assistant_message = self.agent.format_message(
                    MessageType.Assistant,
                    {
                        "message": assistant_response,
                        "tool_uses": [t for t in tool_uses if t["name"] != "transfer"],
                    },
                )
                self._messages_append(assistant_message)
                self._notify("assistant_message_added", assistant_message)

                # Process each tool use
                for tool_use in tool_uses:
                    # Special handling for the transfer tool - always auto-approve
                    tool_name = tool_use["name"]
                    if tool_name == "transfer":
                        self._notify("tool_use", tool_use)
                        try:
                            tool_result = await self.agent.execute_tool_call(
                                tool_name, tool_use["input"]
                            )
                            self._post_tool_transfer(tool_result)
                        except Exception as e:
                            # if transfer failed we should add the tool_call message back for record
                            self._messages_append(
                                self.agent.format_message(
                                    MessageType.Assistant,
                                    {
                                        "message": assistant_response,
                                        "tool_uses": [tool_use],
                                    },
                                )
                            )
                            error_message = self.agent.format_message(
                                MessageType.ToolResult,
                                {
                                    "tool_use": tool_use,
                                    "tool_result": str(e),
                                    "is_error": True,
                                },
                            )
                            self._messages_append(error_message)
                            self._notify(
                                "tool_error",
                                {
                                    "tool_use": tool_use,
                                    "error": str(e),
                                    "message": error_message,
                                },
                            )
                        continue
                    # END transfer tool handling

                    # For all other tools, check if confirmation is needed
                    if tool_name not in self._auto_approved_tools:
                        # Request confirmation from the user
                        confirmation = await self._wait_for_tool_confirmation(tool_use)
                        action = confirmation.get("action", "deny")

                        if action == "deny":
                            # User denied the tool execution
                            error_message = self.agent.format_message(
                                MessageType.ToolResult,
                                {
                                    "tool_use": tool_use,
                                    "tool_result": "User denied permission to execute this tool.",
                                    "is_error": True,
                                },
                            )
                            self._messages_append(error_message)
                            self._notify(
                                "tool_denied",
                                {
                                    "tool_use": tool_use,
                                    "message": error_message,
                                },
                            )
                            continue  # Skip to the next tool

                        if action == "approve_all":
                            # Remember this tool for auto-approval
                            self._auto_approved_tools.add(tool_name)

                    # Tool is approved, execute it
                    self._notify("tool_use", tool_use)

                    try:
                        tool_result = await self.agent.execute_tool_call(
                            tool_name, tool_use["input"]
                        )

                        tool_result_message = self.agent.format_message(
                            MessageType.ToolResult,
                            {"tool_use": tool_use, "tool_result": tool_result},
                        )
                        self._messages_append(tool_result_message)
                        self._notify(
                            "tool_result",
                            {
                                "tool_use": tool_use,
                                "tool_result": tool_result,
                                "message": tool_result_message,
                            },
                        )

                    except Exception as e:
                        error_message = self.agent.format_message(
                            MessageType.ToolResult,
                            {
                                "tool_use": tool_use,
                                "tool_result": str(e),
                                "is_error": True,
                            },
                        )
                        self._messages_append(error_message)
                        self._notify(
                            "tool_error",
                            {
                                "tool_use": tool_use,
                                "error": str(e),
                                "message": error_message,
                            },
                        )

                self._notify(
                    "update_token_usage",
                    {"input_tokens": input_tokens, "output_tokens": output_tokens},
                )

                return await self.get_assistant_response()

            if thinking_content:
                # self._notify("thinking_completed")
                self._notify("agent_continue", self.agent.name)

            # Final assistant message
            self._notify("response_completed", assistant_response)

            # Store the latest response
            self.latest_assistant_response = assistant_response

            # Add assistant response to messages
            if assistant_response:
                self._messages_append(
                    self.agent.format_message(
                        MessageType.Assistant, {"message": assistant_response}
                    )
                )

            if self.current_user_input and self.current_user_input_idx >= 0:
                if self.memory_service:
                    user_input = ""
                    user_message = self.current_user_input  # Get the user message
                    if (
                        isinstance(user_message["content"], list)
                        and len(user_message["content"]) > 0
                    ):
                        for content_item in user_message["content"]:
                            if content_item.get("type") == "text":
                                user_input += content_item.get("text", "")
                    elif isinstance(user_message["content"], str):
                        user_input = user_message["content"]

                    try:
                        await self.memory_service.store_conversation(
                            user_input, assistant_response, self.agent.name
                        )
                    except Exception as e:
                        self._notify(
                            "error", f"Failed to store conversation in memory: {str(e)}"
                        )
                self.store_conversation_turn(
                    self.current_user_input, self.current_user_input_idx
                )
                # Store the conversation turn reference for /jump command
                self.current_user_input = None
                self.current_user_input_idx = -1

            # --- Start of Persistence Logic ---
            if self.current_conversation_id and self.last_assisstant_response_idx >= 0:
                try:
                    # Get all messages added since the user input for this turn
                    current_provider = self.agent.get_provider()
                    messages_for_this_turn = MessageTransformer.standardize_messages(
                        self.agent.history[self.last_assisstant_response_idx :],
                        current_provider,
                        self.agent.name,
                    )
                    if (
                        messages_for_this_turn
                    ):  # Only save if there are messages for the turn
                        self.persistent_service.append_conversation_messages(
                            self.current_conversation_id, messages_for_this_turn
                        )
                        self._notify(
                            "conversation_saved", {"id": self.current_conversation_id}
                        )
                except Exception as e:
                    error_message = f"Failed to save conversation turn to {self.current_conversation_id}: {str(e)}"
                    logger.error(f"ERROR: {error_message}")
                    self._notify("error", {"message": error_message})
            self.last_assisstant_response_idx = len(self.agent.history)
            # --- End of Persistence Logic ---

            return assistant_response, input_tokens, output_tokens

        except Exception as e:
            if self.current_user_input:
                self.store_conversation_turn(
                    self.current_user_input, self.current_user_input_idx
                )
                self.current_user_input = None
                self.current_user_input_idx = -1
            error_message = str(e)
            traceback_str = traceback.format_exc()
            self._notify(
                "error",
                {
                    "message": error_message,
                    "traceback": traceback_str,
                    "messages": self.agent.history,
                },
            )
            return None, 0, 0

    def store_conversation_turn(self, user_input, input_index):
        turn = ConversationTurn(
            user_input,  # User message for preview
            input_index,  # Index of the *start* of this turn's messages
        )
        self.conversation_turns.append(turn)

    # --- Add these new methods ---
    def list_conversations(self) -> List[Dict[str, Any]]:
        """Lists available conversations from the persistence service."""
        try:
            return self.persistent_service.list_conversations()
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            self._notify("error", f"Failed to list conversations: {e}")
            return []

    def load_conversation(self, conversation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Loads a specific conversation history and sets it as active."""
        try:
            # Reset approved tools for the loaded conversation
            self._auto_approved_tools = set()

            self.agent_manager.clean_agents_messages()
            history = self.persistent_service.get_conversation_history(conversation_id)
            if history:
                self.current_conversation_id = conversation_id
                self.memory_service.session_id = self.current_conversation_id
                self.memory_service.loaded_conversation = True
                last_agent_name = history[-1].get("agent", "")
                if last_agent_name and self.agent_manager.select_agent(last_agent_name):
                    self.agent = self.agent_manager.get_current_agent()
                    self._notify("agent_changed", last_agent_name)
                self.streamline_messages = history
                self.agent_manager.rebuild_agents_messages(self.streamline_messages)

                self.last_assisstant_response_idx = len(self.agent.history)

                for i, message in enumerate(self.streamline_messages):
                    role = message.get("role")
                    if role == "user":
                        content = message.get("content", "")
                        message_content = ""

                        # Handle different content structures (standardized format)
                        if isinstance(content, str):
                            message_content = content
                        elif isinstance(content, list) and content:
                            # Assuming the first item in the list contains the primary text
                            first_item = content[0]
                            if (
                                isinstance(first_item, dict)
                                and first_item.get("type") == "text"
                            ):
                                message_content = first_item.get("text", "")
                        if (
                            message_content
                            and not message_content.startswith(
                                "Context from your memory:"
                            )
                            and not message_content.startswith("Content of ")
                        ):
                            self.store_conversation_turn(message_content, i)

                logger.info(
                    f"Loaded conversation {conversation_id}"
                )  # Optional: Debugging
                self._notify(
                    "conversation_loaded", {"id": conversation_id, "history": history}
                )
                return history
            else:
                self._notify(
                    "error", f"Conversation {conversation_id} not found or empty."
                )
                return []
        except Exception as e:
            logger.error(f"Error loading conversation {conversation_id}: {e}")
            self._notify("error", f"Failed to load conversation {conversation_id}: {e}")

    def delete_conversation_by_id(self, conversation_id: str) -> bool:
        """
        Deletes a conversation by its ID, handling file deletion and UI updates.

        Args:
            conversation_id: The ID of the conversation to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        logger.info(f"INFO: Attempting to delete conversation: {conversation_id}")
        if self.persistent_service.delete_conversation(conversation_id):
            logger.info(
                f"INFO: Successfully deleted conversation file for ID: {conversation_id}"
            )
            self._notify("conversations_changed", None)
            self._notify(
                "system_message", f"Conversation {conversation_id[:8]}... deleted."
            )

            if self.current_conversation_id == conversation_id:
                logger.info(
                    f"INFO: Deleted conversation {conversation_id} was the current one. Starting new conversation."
                )
                self.start_new_conversation()  # This will notify "clear_requested"
            return True
        else:
            error_msg = f"Failed to delete conversation {conversation_id[:8]}..."
            logger.error(f"ERROR: {error_msg}")
            self._notify("error", {"message": error_msg})
            return False
