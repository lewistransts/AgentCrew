import sys
import time
import pyperclip
from typing import Dict, Any
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

from swissknife.modules.chat.message_handler import Observer
from swissknife.modules.chat.completers import ChatCompleter
from swissknife.modules.chat.constants import (
    YELLOW,
    GREEN,
    BLUE,
    RED,
    GRAY,
    RESET,
    BOLD,
    RICH_YELLOW,
    RICH_GRAY,
)


class ConsoleUI(Observer):
    """
    A console-based UI for the interactive chat that implements the Observer interface
    to receive updates from the MessageHandler.
    """

    def __init__(self, message_handler):
        """
        Initialize the ConsoleUI.

        Args:
            message_handler: The MessageHandler instance that this UI will observe.
        """
        self.message_handler = message_handler
        self.message_handler.attach(self)

        self.console = Console()
        self.live = None  # Will be initialized during response streaming
        self._last_ctrl_c_time = 0
        self.latest_assistant_response = ""

        # Set up key bindings
        self.kb = self._setup_key_bindings()

    def listen(self, event: str, data: Any = None):
        """
        Update method required by the Observer interface. Handles events from the MessageHandler.

        Args:
            event: The type of event that occurred.
            data: The data associated with the event.
        """
        if event == "thinking_started":
            self.display_thinking_started(data)  # data is agent_name
        elif event == "thinking_chunk":
            self.display_thinking_chunk(data)  # data is the thinking chunk
        elif event == "response_chunk":
            chunk, assistant_response = data
            self.update_live_display(assistant_response)  # data is the response chunk
        elif event == "tool_use":
            self.display_tool_use(data)  # data is the tool use object
        elif event == "tool_result":
            pass
            # self.display_tool_result(data)  # data is dict with tool_use and tool_result
        elif event == "tool_error":
            self.display_tool_error(data)  # data is dict with tool_use and error
        elif event == "response_completed":
            self.finish_response(data)  # data is the complete response
        elif event == "error":
            self.display_error(data)  # data is the error message or dict
        elif event == "clear_requested":
            self.display_message(f"{YELLOW}{BOLD}🎮 Chat history cleared.{RESET}")
        elif event == "exit_requested":
            self.display_message(
                f"{YELLOW}{BOLD}🎮 Ending chat session. Goodbye!{RESET}"
            )
            sys.exit(0)
        elif event == "copy_requested":
            self.copy_to_clipboard(data)  # data is the text to copy
        elif event == "debug_requested":
            self.display_debug_info(data)  # data is the debug information
        elif event == "think_budget_set":
            self.display_message(
                f"{YELLOW}Thinking budget set to {data} tokens.{RESET}"
            )
        elif event == "models_listed":
            self.display_models(data)  # data is dict of models by provider
        elif event == "model_changed":
            self.display_message(
                f"{YELLOW}Switched to {data['name']} ({data['id']}){RESET}"
            )
        elif event == "agents_listed":
            self.display_agents(data)  # data is dict of agent info
        elif event == "agent_changed":
            self.display_message(f"{YELLOW}Switched to {data} agent{RESET}")
        elif event == "agent_changed_by_handoff":
            self.display_message(f"{YELLOW}Handed off to {data} agent{RESET}")
        elif event == "agent_continue":
            self.display_message(f"\n{GREEN}{BOLD}🤖 {data.upper()}:{RESET}")
        elif event == "jump_performed":
            self.display_message(
                f"{YELLOW}{BOLD}🕰️ Jumping to turn {data['turn_number']}...{RESET}\n"
                f"{YELLOW}Conversation rewound to: {data['preview']}{RESET}"
            )
        elif event == "thinking_completed":
            self.console.print("\n")
            self.display_divider()
        elif event == "file_processed":
            self.display_message(f"{YELLOW}Processed file: {data['file_path']}{RESET}")

    def display_thinking_started(self, agent_name: str):
        """Display the start of the thinking process."""
        self.console.print(
            Text(f"\n💭 {agent_name.upper()}'s thinking process:", style=RICH_YELLOW)
        )

    def display_thinking_chunk(self, chunk: str):
        """Display a chunk of the thinking process."""
        self.console.print(Text(chunk, style=RICH_GRAY), end="", soft_wrap=True)

    def update_live_display(self, chunk: str):
        """Update the live display with a new chunk of the response."""
        if not self.live:
            self.start_streaming_response(self.message_handler.agent_name)

        updated_text = chunk

        # Only show the last part that fits in the console
        lines = updated_text.split("\n")
        height_limit = (
            self.console.size.height - 10
        )  # leave some space for other elements
        if len(lines) > height_limit:
            lines = lines[-height_limit:]

        self.live.update(Markdown("\n".join(lines)))

    def display_tool_use(self, tool_use: Dict):
        """Display information about a tool being used."""
        print(f"\n{YELLOW}🔧 Using tool: {tool_use['name']}{RESET}")
        print(f"\n{GRAY}{tool_use}{RESET}")

    def display_tool_result(self, data: Dict):
        """Display the result of a tool execution."""
        tool_use = data["tool_use"]
        tool_result = data["tool_result"]
        print(f"{GREEN}✓ Tool result for {tool_use['name']}:{RESET}")
        print(f"{GRAY}{tool_result}{RESET}")

    def display_tool_error(self, data: Dict):
        """Display an error that occurred during tool execution."""
        tool_use = data["tool_use"]
        error = data["error"]
        print(f"{RED}❌ Error in tool {tool_use['name']}: {error}{RESET}")

    def finish_response(self, response: str):
        """Finalize and display the complete response."""
        if self.live:
            self.live.update("")
            self.live.stop()
            self.live = None

        # Replace \n with two spaces followed by \n for proper Markdown line breaks
        markdown_formatted_response = response.replace("\n", "  \n")
        self.console.print(Markdown(markdown_formatted_response))

        # Store the latest response
        self.latest_assistant_response = response

    def display_error(self, error):
        """Display an error message."""
        if isinstance(error, dict):
            print(f"\n{RED}❌ Error: {error['message']}{RESET}")
            if "traceback" in error:
                print(f"{GRAY}{error['traceback']}{RESET}")
        else:
            print(f"\n{RED}❌ Error: {error}{RESET}")

    def display_message(self, message: str):
        """Display a generic message."""
        print(message)

    def display_divider(self):
        """Display a divider line."""
        divider = "─" * self.console.size.width
        print(divider)

    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard and show confirmation."""
        if text:
            pyperclip.copy(text)
            print(f"\n{YELLOW}✓ Text copied to clipboard!{RESET}")
        else:
            print(f"\n{YELLOW}! No text to copy.{RESET}")

    def display_debug_info(self, debug_info):
        """Display debug information."""
        import json

        print(f"{YELLOW}Current messages:{RESET}")
        try:
            self.console.print(json.dumps(debug_info, indent=2))
        except Exception:
            print(debug_info)

    def display_models(self, models_by_provider: Dict):
        """Display available models grouped by provider."""
        print(f"{YELLOW}Available models:{RESET}")
        for provider, models in models_by_provider.items():
            print(f"\n{YELLOW}{provider.capitalize()} models:{RESET}")
            for model in models:
                current = " (current)" if model["current"] else ""
                print(f"  - {model['id']}: {model['name']}{current}")
                print(f"    {model['description']}")
                print(f"    Capabilities: {', '.join(model['capabilities'])}")

    def display_agents(self, agents_info: Dict):
        """Display available agents."""
        print(f"{YELLOW}Current agent: {agents_info['current']}{RESET}")
        print(f"{YELLOW}Available agents:{RESET}")

        for agent_name, agent_data in agents_info["available"].items():
            current = " (current)" if agent_data["current"] else ""
            print(f"  - {agent_name}{current}: {agent_data['description']}")

    def get_user_input(self, conversation_turns=None):
        """
        Get multiline input from the user with support for command history.

        Args:
            conversation_turns: Optional list of conversation turns for completions.

        Returns:
            The user input as a string.
        """
        print(f"\n{BLUE}{BOLD}👤 YOU:{RESET}")
        print(
            f"{YELLOW}🤖 "
            f"{self.message_handler.agent_name} 🧠 {self.message_handler.llm.model}\n"
            f"(Press Enter for new line, Ctrl+S to submit, Up/Down for history)"
            f"{RESET}"
        )

        session = PromptSession(
            key_bindings=self.kb,
            completer=ChatCompleter(
                conversation_turns or self.message_handler.conversation_turns
            ),
        )

        try:
            user_input = session.prompt("> ")
            # Reset history position after submission
            self.message_handler.history_manager.reset_position()
            self.display_divider()
            return user_input
        except KeyboardInterrupt:
            # This should not be reached with our custom handler, but keep as fallback
            print(
                f"\n{YELLOW}{BOLD}🎮 Chat interrupted. Press Ctrl+C again to exit.{RESET}"
            )
            return ""  # Return empty string to continue the chat

    def start_streaming_response(self, agent_name: str):
        """
        Start streaming the assistant's response.

        Args:
            agent_name: The name of the agent providing the response.
        """
        print(f"\n{GREEN}{BOLD}🤖 {agent_name.upper()}:{RESET}")
        self.live = Live("", console=self.console, vertical_overflow="crop")
        self.live.start()

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
            self.copy_to_clipboard(self.latest_assistant_response)
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
                prev_entry = self.message_handler.history_manager.get_previous()
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
                next_entry = self.message_handler.history_manager.get_next()
                if next_entry is not None:
                    # Replace current text with history entry
                    buffer.text = next_entry
                    # Move cursor to end of text
                    buffer.cursor_position = len(next_entry)
            else:
                # Regular down arrow behavior - move cursor down
                buffer.cursor_down()

        return kb

    def print_welcome_message(self):
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
        self.display_divider()

    def display_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        session_cost: float,
    ):
        """Display token usage and cost information."""
        print("\n")
        self.display_divider()
        print(
            f"{YELLOW}📊 Token Usage: Input: {input_tokens:,} | Output: {output_tokens:,} | "
            f"Total: {input_tokens + output_tokens:,} | Cost: ${total_cost:.4f} | Total: {session_cost:.4f}{RESET}"
        )
        self.display_divider()

    def start(self):
        self.print_welcome_message()

        session_cost = 0.0

        while True:
            # Get user input
            user_input = self.get_user_input()

            # Process user input and commands
            # self.start_streaming_response(self.message_handler.agent_name)
            should_exit, was_cleared = self.message_handler.process_user_input(
                user_input
            )

            # Exit if requested
            if should_exit:
                break

            # Skip to next iteration if messages were cleared
            if was_cleared:
                continue

            # Skip to next iteration if no messages to process
            if not self.message_handler.messages:
                continue

            # Start streaming response
            # self.start_streaming_response(self.message_handler.agent_name)

            # Get assistant response
            assistant_response, input_tokens, output_tokens = (
                self.message_handler.get_assistant_response()
            )

            if assistant_response:
                # Calculate and display token usage
                total_cost = self.message_handler.llm.calculate_cost(
                    input_tokens, output_tokens
                )
                session_cost += total_cost
                self.display_token_usage(
                    input_tokens, output_tokens, total_cost, session_cost
                )
