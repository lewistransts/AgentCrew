# swissknife/modules/chat/interactive.py

import sys
import traceback
import os
import time
import pyperclip
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich.live import Live
from swissknife.modules.llm.service_manager import ServiceManager
from swissknife.modules.llm.models import ModelRegistry
from swissknife.modules.llm.message import MessageTransformer
from .constants import BLUE, GREEN, YELLOW, RESET, BOLD, GRAY, RICH_YELLOW, RICH_GRAY
from .completers import ChatCompleter
from .history import ChatHistoryManager, ConversationTurn
from swissknife.modules.agents.manager import AgentManager
from swissknife.modules.chat.file_handler import FileHandler

# Color constants for error messages
RED = "\033[91m"  # Red color for errors
RESET = "\033[0m"  # Reset color

class InteractiveChat:
    def __init__(self, memory_service=None):
        """
        Initialize the interactive chat.

        Args:
            memory_service: Optional memory service for storing conversations
        """
        self.agent_manager = AgentManager.get_instance()
        self.llm = self.agent_manager.get_current_agent().llm
        self.agent_name = self.agent_manager.get_current_agent().name
        self.console = Console()
        self.latest_assistant_response = ""
        self.memory_service = memory_service
        self._last_ctrl_c_time = 0  # Initialize the last Ctrl+C time
        self.history_manager = ChatHistoryManager()  # Initialize history manager
        self.conversation_turns = []  # Track conversation turns
        self.current_user_message = None  # Track the current user message
        self.messages = []  # Store messages as an instance variable
        self.file_handler = FileHandler()

    def _copy_to_clipboard(self):
        """Copy the latest assistant response to clipboard and show confirmation."""
        if self.latest_assistant_response:
            pyperclip.copy(self.latest_assistant_response)
            print(f"\n{YELLOW}✓ Latest assistant response copied to clipboard!{RESET}")
            return True
        else:
            print(f"\n{YELLOW}! No assistant response to copy.{RESET}")
            return False

    def _setup_key_bindings(self):
        """Set up key bindings for multiline input."""
        kb = KeyBindings()

        @kb.add(Keys.ControlS)
        def _(event):
            """Submit on Ctrl+S."""
            if event.current_buffer.text.strip():
                event.current_buffer.validate_and_handle()

        @kb.add(Keys.Enter)
        def _(event):
            """Insert newline on Enter."""
            event.current_buffer.insert_text("\n")

        @kb.add("escape", "c")  # Alt+C
        def _(event):
            """Copy latest assistant response to clipboard."""
            self._copy_to_clipboard()
            print("> ", end="")

        @kb.add(Keys.ControlC)
        def _(event):
            """Handle Ctrl+C with confirmation for exit."""
            current_time = time.time()
            if (
                hasattr(self, "_last_ctrl_c_time")
                and current_time - self._last_ctrl_c_time < 1
            ):
                print(f"\n{YELLOW}{BOLD}🎮 Confirmed exit. Goodbye!{RESET}")
                sys.exit(0)
            else:
                self._last_ctrl_c_time = current_time
                print(f"\n{YELLOW}Press Ctrl+C again within 1 seconds to exit.{RESET}")
                print("> ", end="")

        @kb.add(Keys.Up)
        def _(event):
            """Navigate to previous history entry."""
            buffer = event.current_buffer
            document = buffer.document

            # Check if cursor is at the first line's start
            cursor_position = document.cursor_position
            if document.cursor_position_row == 0 and cursor_position <= len(
                document.current_line
            ):
                # Get previous history entry
                prev_entry = self.history_manager.get_previous()
                if prev_entry is not None:
                    # Replace current text with history entry
                    buffer.text = prev_entry
                    # Move cursor to end of text
                    buffer.cursor_position = len(prev_entry)
            else:
                # Regular up arrow behavior - move cursor up
                buffer.cursor_up()

        @kb.add(Keys.Down)
        def _(event):
            """Navigate to next history entry if cursor is at last line."""
            buffer = event.current_buffer
            document = buffer.document

            # Check if cursor is at the last line
            if document.cursor_position_row == document.line_count - 1:
                # Get next history entry
                next_entry = self.history_manager.get_next()
                if next_entry is not None:
                    # Replace current text with history entry
                    buffer.text = next_entry
                    # Move cursor to end of text
                    buffer.cursor_position = len(next_entry)
            else:
                # Regular down arrow behavior - move cursor down
                buffer.cursor_down()

        return kb

    def _stream_assistant_response(self, messages, input_tokens=0, output_tokens=0):
        """Stream the assistant's response and return the response and token usage."""
        assistant_response = ""
        tool_uses = []
        thinking_content = ""  # Reset thinking content for new response
        thinking_signature = ""  # Store the signature
        start_thinking = True

        try:
            with Live("", console=self.console, vertical_overflow="crop") as live:
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

                            # Print thinking content with a special format
                            if start_thinking:
                                self.console.print(
                                    Text(
                                        f"\n💭 {self.agent_name.upper()}'s thinking process:",
                                        style=RICH_YELLOW,
                                    )
                                )
                                start_thinking = False
                            self.console.print(
                                Text(f"{thinking_chunk}", style=RICH_GRAY),
                                end="",
                                soft_wrap=True,
                            )

                        # Update live rich markdown
                        live.update(
                            Markdown(
                                "\n".join(
                                    assistant_response.split("\n")[
                                        self.console.size.height * -1 + 10 :
                                    ]
                                )
                            )
                        )
                live.update("")

            # Handle tool use if needed
            if tool_uses and len(tool_uses) > 0:
                # Add thinking content as a separate message if available
                thinking_data = (
                    (thinking_content, thinking_signature) if thinking_content else None
                )
                thinking_message = self.llm.format_thinking_message(thinking_data)
                if thinking_message:
                    messages.append(thinking_message)

                # Format assistant message with the response and tool uses
                assistant_message = self.llm.format_assistant_message(
                    assistant_response, tool_uses
                )
                messages.append(assistant_message)

                # Replace \n with two spaces followed by \n for proper Markdown line breaks
                markdown_formatted_response = assistant_response.replace("\n", "  \n")
                self.console.print(Markdown(markdown_formatted_response))
                for tool_use in tool_uses:
                    print(f"\n{YELLOW}🔧 Using tool: {tool_use['name']}{RESET}")
                    print(f"\n{GRAY}{tool_use}{RESET}")

                    try:
                        tool_result = self.llm.execute_tool(
                            tool_use["name"], tool_use["input"]
                        )
                        messages.append(
                            self.llm.format_tool_result(tool_use, tool_result)
                        )
                        # Update llm service when handoff agent
                        if tool_use["name"] == "handoff":
                            self.llm = self.agent_manager.get_current_agent().llm
                            self.agent_name = (
                                self.agent_manager.get_current_agent().name
                            )

                    except Exception as e:
                        messages.append(
                            self.llm.format_tool_result(tool_use, str(e), is_error=True)
                        )
                    # Get a new response with the tool result
                print(
                    f"\n{GREEN}{BOLD}🤖 {self.agent_name.upper()} (continued):{RESET}"
                )
                return self._stream_assistant_response(
                    messages, input_tokens, output_tokens
                )
            # Replace \n with two spaces followed by \n for proper Markdown line breaks
            markdown_formatted_response = assistant_response.replace("\n", "  \n")
            self.console.print(Markdown(markdown_formatted_response))

            # Store the latest response
            self.latest_assistant_response = assistant_response

            return assistant_response, input_tokens, output_tokens

        except Exception as e:
            print(f"\n{YELLOW}❌ Error: {str(e)}{RESET}")
            print(traceback.format_exc())
            print(messages)
            return None, 0, 0

    def _print_welcome_message(self, divider):
        """Print the welcome message for the chat."""
        welcome_messages = [
            f"\n{YELLOW}{BOLD}🎮 Welcome to the interactive chat!{RESET}",
            f"{YELLOW}Press Ctrl+C twice to exit.{RESET}",
            f"{YELLOW}Type 'exit' or 'quit' to end the session.{RESET}",
            f"{YELLOW}Use '/file <file_path>' to include a file in your message.{RESET}",
            f"{YELLOW}Use '/clear' to clear the conversation history.{RESET}",
            f"{YELLOW}Use '/think <budget>' to enable Claude's thinking mode (min 1024 tokens).{RESET}",
            f"{YELLOW}Use '/think 0' to disable thinking mode.{RESET}",
            f"{YELLOW}Use '/model [model_id]' to switch models or list available models.{RESET}",
            f"{YELLOW}Use '/jump <turn_number>' to rewind the conversation to a previous turn.{RESET}",
            f"{YELLOW}Use '/copy' to copy the latest assistant response to clipboard.{RESET}",
            f"{YELLOW}Press Alt/Meta+C to copy the latest assistant response.{RESET}",
            f"{YELLOW}Use Up/Down arrow keys to navigate through command history.{RESET}",
            f"{YELLOW}Use '/agent [agent_name]' to switch agents or list available agents.{RESET}",
        ]

        for message in welcome_messages:
            print(message)
        print(divider)

    def _get_user_input(self, divider):
        """Get multiline input from the user."""
        print(f"\n{BLUE}{BOLD}👤 YOU:{RESET}")
        print(
            f"{YELLOW}(Press Enter for new line, Ctrl+S to submit, Up/Down for history){RESET}"
        )

        kb = self._setup_key_bindings()
        session = PromptSession(
            key_bindings=kb, completer=ChatCompleter(self.conversation_turns)
        )

        try:
            user_input = session.prompt("> ")
            # Reset history position after submission
            self.history_manager.reset_position()
            print(divider)
            return user_input
        except KeyboardInterrupt:
            # This should not be reached with our custom handler, but keep as fallback
            print(
                f"\n{YELLOW}{BOLD}🎮 Chat interrupted. Press Ctrl+C again to exit.{RESET}"
            )
            return ""  # Return empty string instead of "exit" to continue the chat

    def _handle_clear_command(self):
        """Handle the /clear command to reset conversation history."""
        messages = []
        print(f"{YELLOW}{BOLD}🎮 Chat history cleared.{RESET}")
        return messages

    def _handle_exit_command(self, user_input):
        """Check if the user wants to exit the chat."""
        if user_input.lower() in ["exit", "quit"]:
            print(f"{YELLOW}{BOLD}🎮 Ending chat session. Goodbye!{RESET}")
            return True
        return False

    def _handle_jump_command(self, command):
        """Handle the /jump command to rewind conversation to a previous turn."""
        try:
            # Extract the turn number from the command
            parts = command.split()
            if len(parts) != 2:
                print(f"{YELLOW}Usage: /jump <turn_number>{RESET}")
                return None, False

            turn_number = int(parts[1])

            # Validate the turn number
            if turn_number < 1 or turn_number > len(self.conversation_turns):
                print(
                    f"{YELLOW}Invalid turn number. Available turns: 1-{len(self.conversation_turns)}{RESET}"
                )
                return None, False

            # Get the selected turn
            selected_turn = self.conversation_turns[turn_number - 1]

            # Provide feedback
            print(f"{YELLOW}{BOLD}🕰️ Jumping to turn {turn_number}...{RESET}")
            print(
                f"{YELLOW}Conversation rewound to: {selected_turn.get_preview(100)}{RESET}"
            )

            # Truncate messages to the index from the selected turn
            truncated_messages = self.messages[: selected_turn.message_index]
            self.conversation_turns = self.conversation_turns[: turn_number - 1]

            # Return the truncated messages
            return truncated_messages, True

        except ValueError:
            print(f"{YELLOW}Invalid turn number. Please provide a number.{RESET}")
            return None, False

    def _handle_model_command(self, command, messages):
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
            print(f"{YELLOW}Available models:{RESET}")
            for provider in ["claude", "openai", "groq", "google"]:
                print(f"\n{YELLOW}{provider.capitalize()} models:{RESET}")
                for model in registry.get_models_by_provider(provider):
                    current = (
                        " (current)"
                        if registry.current_model
                        and registry.current_model.id == model.id
                        else ""
                    )
                    print(f"  - {model.id}: {model.name}{current}")
                    print(f"    {model.description}")
                    print(f"    Capabilities: {', '.join(model.capabilities)}")
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

                print(f"{YELLOW}Switched to {model.name} ({model.id}){RESET}")
            else:
                print(f"{YELLOW}Failed to switch model.{RESET}")
        else:
            print(f"{YELLOW}Unknown model: {model_id}{RESET}")

        return messages, False, True

    def _handle_agent_command(self, command):
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

            print(f"{YELLOW}Current agent: {current_agent_name}{RESET}")
            print(f"{YELLOW}Available agents:{RESET}")

            for agent_name, agent in self.agent_manager.agents.items():
                current = (
                    " (current)"
                    if current_agent and current_agent.name == agent_name
                    else ""
                )
                print(f"  - {agent_name}{current}: {agent.description}")

            return True, "Listed available agents"

        # If an agent name is provided, try to switch to that agent
        agent_name = parts[1]
        if self.agent_manager.select_agent(agent_name):
            # Update the LLM reference to the new agent's LLM
            self.llm = self.agent_manager.get_current_agent().llm
            self.agent_name = agent_name
            return True, f"Switched to {agent_name} agent"
        else:
            available_agents = ", ".join(self.agent_manager.agents.keys())
            return (
                False,
                f"Unknown agent: {agent_name}. Available agents: {available_agents}",
            )

    def _process_user_input(self, user_input, messages, message_content, files):
        """Process user input and update messages accordingly."""
        # Handle exit command
        if self._handle_exit_command(user_input):
            return messages, True, False  # Return messages, exit flag, and clear flag

        # Handle clear command
        if user_input.lower() == "/clear":
            self.conversation_turns = []  # Clear conversation turns as well
            return self._handle_clear_command(), False, True  # Add a clear flag

        # Handle copy command
        if user_input.lower() == "/copy":
            self._copy_to_clipboard()
            return messages, False, True  # Skip to next iteration

        # Handle debug command
        if user_input.lower() == "/debug":
            import json

            print(f"{YELLOW}Current messages:{RESET}")
            try:
                self.console.print(json.dumps(self.messages, indent=2))
            except Exception:
                print(self.messages)
            return messages, False, True  # Skip to next iteration

        # Handle think command
        if user_input.lower().startswith("/think "):
            try:
                budget = int(user_input[7:].strip())
                self.llm.set_think(budget)
            except ValueError:
                print(f"{YELLOW}Invalid budget value. Please provide a number.{RESET}")
            return messages, False, True  # Skip to next iteration

        # Handle jump command
        if user_input.lower().startswith("/jump "):
            new_messages, jumped = self._handle_jump_command(user_input)
            if jumped and new_messages:
                return new_messages, False, True
            return messages, False, True  # Skip to next iteration

        # Handle agent command
        if user_input.lower().startswith("/agent"):
            success, message = self._handle_agent_command(user_input)
            if success:
                print(f"{YELLOW}{message}{RESET}")
            else:
                print(f"{YELLOW}Error: {message}{RESET}")
            return messages, False, True  # Skip to next iteration

        # Handle model command
        if user_input.lower().startswith("/model"):
            return self._handle_model_command(user_input, messages)

        # Store non-command messages in history
        if not user_input.startswith("/"):
            self.history_manager.add_entry(user_input)

        # Handle files that were loaded but not yet sent
        if files and not messages:
            combined_content = message_content.copy()
            combined_content.append({"type": "text", "text": user_input})
            messages.append({"role": "user", "content": combined_content})
        # Handle file command
        elif user_input.startswith("/file "):
            file_path = user_input[6:].strip()
            file_path = os.path.expanduser(file_path)

            # Process file with the file handling service
            file_content = self.file_handler.process_file(file_path)

            if file_content:
                messages.append({"role": "user", "content": [file_content]})
                return messages, False, True
            else:
                print(f"{RED}Error: Failed to process file {file_path}{RESET}")
                return messages, False, True
        else:
            # Add regular text message
            messages.append(
                {"role": "user", "content": [{"type": "text", "text": user_input}]}
            )

        return messages, False, False

    def divider(self):
        divider = "─"
        return divider * self.console.size.width

    def start_chat(self, initial_content=None, files=None):
        """
        Start an interactive chat session using streaming mode.

        Args:
            initial_content (str, optional): Initial message to start the conversation
            files (list, optional): List of file paths to include in the initial message
        """
        self.messages = []  # Reset messages at the start of a new chat
        message_content = []
        session_cost = 0.0
        user_input = None
        # Process files if provided
        if files:
            message_content = []
            for file_path in files:
                # Use the file handling service instead of direct LLM processing
                file_content = self.file_handler.process_file(file_path)
                if file_content:
                    message_content.append(file_content)

            # Add initial text if provided
            if initial_content:
                message_content.append({"type": "text", "text": initial_content})
                self.messages.append({"role": "user", "content": message_content})
                print(f"\n{BLUE}{BOLD}👤 YOU:{RESET} [Initial content with files]")
        elif initial_content:
            self.messages.append({"role": "user", "content": initial_content})
            print(f"\n{BLUE}{BOLD}👤 YOU:{RESET} [Initial content]")

        # Print welcome message
        self._print_welcome_message(self.divider())

        # Main chat loop
        while True:
            # Handle initial message or get user input
            if not (self.messages and len(self.messages) == 1 and initial_content):
                user_input = self._get_user_input(self.divider())

                # Process the user input
                self.messages, should_exit, was_cleared = self._process_user_input(
                    user_input, self.messages, message_content, files
                )

                # Exit if requested
                if should_exit:
                    break

                # Skip to next iteration if messages were cleared
                if was_cleared:
                    print(self.divider())
                    continue

                # Skip to next iteration if no messages to process
                if not self.messages:
                    print(self.divider())
                    continue

            # Get and display assistant response
            print(f"\n{GREEN}{BOLD}🤖 {self.agent_name.upper()}:{RESET}")

            assistant_response, input_tokens, output_tokens = (
                self._stream_assistant_response(self.messages)
            )

            if assistant_response:
                # Add assistant's response to message history
                self.messages.append(
                    self.llm.format_assistant_message(assistant_response)
                )

                # Store the conversation turn if user initiated
                if user_input:
                    # Only store turns initiated by user input (not initial content)
                    # Store the conversation turn with message index
                    for i, message in reversed(list(enumerate(self.messages))):
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

                # Store conversation in memory if memory service is available
                if self.memory_service and user_input and assistant_response:
                    try:
                        self.memory_service.store_conversation(
                            user_input, assistant_response
                        )
                    except Exception as e:
                        print(
                            f"\n{YELLOW}⚠️ Failed to store conversation in memory: {str(e)}{RESET}"
                        )

                # Display token usage and cost
                total_cost = self.llm.calculate_cost(input_tokens, output_tokens)
                session_cost += total_cost
                print("\n")
                print(self.divider())
                print(
                    f"{YELLOW}📊 Token Usage: Input: {input_tokens:,} | Output: {output_tokens:,} | "
                    f"Total: {input_tokens + output_tokens:,} | Cost: ${total_cost:.4f} | Total: {session_cost:.4f}{RESET}"
                )
                print(self.divider())
            else:
                # Error occurred
                print(self.divider())
                continue
