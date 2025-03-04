import sys
import shutil
import pyperclip
import traceback
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.markdown import Markdown
from modules.llm.base import BaseLLMService
from .constants import (
    BLUE,
    GREEN,
    YELLOW,
    RESET,
    BOLD,
    GRAY,
)
from .file_completer import DirectoryListingCompleter


def get_terminal_width():
    """Get the current terminal width."""
    return shutil.get_terminal_size().columns


class InteractiveChat:
    def __init__(self, llm_service: BaseLLMService, memory_service=None):
        """
        Initialize the interactive chat with a LLM service.

        Args:
            llm_service: An implementation of BaseLLMService
            memory_service: Optional memory service for storing conversations
        """
        self.llm = llm_service
        self.console = Console()
        self.latest_assistant_response = ""
        self.memory_service = memory_service

    def _setup_key_bindings(self):
        """Set up key bindings for multiline input."""
        kb = KeyBindings()

        @kb.add(Keys.ControlS)
        def _(event):
            """Submit on Ctrl+S."""
            event.current_buffer.validate_and_handle()

        @kb.add(Keys.Enter)
        def _(event):
            """Insert newline on Enter."""
            event.current_buffer.insert_text("\n")

        @kb.add("escape", "c")  # Alt+C
        def _(event):
            """Copy latest assistant response to clipboard."""
            if self.latest_assistant_response:
                pyperclip.copy(self.latest_assistant_response)
                print(
                    f"\n{YELLOW}✓ Latest assistant response copied to clipboard!{RESET}"
                )
                print("> ", end="")
            else:
                print(f"\n{YELLOW}! No assistant response to copy.{RESET}")
                print("> ", end="")

        return kb

    def _clear_to_start(self, text):
        # Count how many lines were printed
        lines = text.count("\n") + 1

        # Move cursor to beginning of first line of output
        sys.stdout.write(f"\x1b[{lines}A\r")

        # Clear from cursor to end of screen
        sys.stdout.write("\x1b[J")

    def _stream_assistant_response(self, messages):
        """Stream the assistant's response and return the response and token usage."""
        assistant_response = ""
        input_tokens = 0
        output_tokens = 0
        tool_uses = []

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
                    ) = self.llm.process_stream_chunk(
                        chunk, assistant_response, tool_uses
                    )

                    # Update token counts
                    if chunk_input_tokens > 0:
                        input_tokens = chunk_input_tokens
                    if chunk_output_tokens > 0:
                        output_tokens = chunk_output_tokens

                    # Print chunk text if available
                    if chunk_text:
                        print(chunk_text, end="", flush=True)

            # Handle tool use if needed
            if tool_uses and len(tool_uses) > 0:
                messages.append(
                    self.llm.format_assistant_message(assistant_response, tool_uses)
                )
                for tool_use in tool_uses:
                    self._clear_to_start(assistant_response)
                    # Replace \n with two spaces followed by \n for proper Markdown line breaks
                    markdown_formatted_response = assistant_response.replace(
                        "\n", "  \n"
                    )
                    self.console.print(Markdown(markdown_formatted_response))

                    print(f"\n{YELLOW}🔧 Using tool: {tool_use['name']}{RESET}")
                    print(f"\n{GRAY}{tool_use}{RESET}")

                    try:
                        tool_result = self.llm.execute_tool(
                            tool_use["name"], tool_use["input"]
                        )
                        messages.append(
                            self.llm.format_tool_result(tool_use, tool_result)
                        )
                    except Exception as e:
                        messages.append(
                            self.llm.format_tool_result(tool_use, str(e), is_error=True)
                        )
                    # Get a new response with the tool result
                print(f"\n{GREEN}{BOLD}🤖 ASSISTANT (continued):{RESET}")
                return self._stream_assistant_response(messages)
            else:
                self._clear_to_start(assistant_response)
                # Replace \n with two spaces followed by \n for proper Markdown line breaks
                markdown_formatted_response = assistant_response.replace("\n", "  \n")
                self.console.print(Markdown(markdown_formatted_response))

                # Store the latest response
                self.latest_assistant_response = assistant_response

                return assistant_response, input_tokens, output_tokens

        except Exception as e:
            print(f"\n{YELLOW}❌ Error: {str(e)}{RESET}")
            return None, 0, 0

    def _print_welcome_message(self, divider):
        """Print the welcome message for the chat."""
        print(f"\n{YELLOW}{BOLD}🎮 Welcome to the interactive chat!{RESET}")
        print(f"{YELLOW}Type 'exit' or 'quit' to end the session.{RESET}")
        print(
            f"{YELLOW}Use '/file <file_path>' to include a file in your message.{RESET}"
        )
        print(f"{YELLOW}Use '/clear' to clear the conversation history.{RESET}")
        print(f"{YELLOW}Press Alt/Meta+C to copy the latest assistant response.{RESET}")
        print(divider)

    def _get_user_input(self, divider):
        """Get multiline input from the user."""
        print(f"\n{BLUE}{BOLD}👤 YOU:{RESET}")
        print(f"{YELLOW}(Press Enter for new line, Ctrl+S to submit){RESET}")

        kb = self._setup_key_bindings()
        session = PromptSession(key_bindings=kb, completer=DirectoryListingCompleter())

        try:
            user_input = session.prompt("> ")
            print(divider)
            return user_input
        except KeyboardInterrupt:
            print(f"{YELLOW}{BOLD}🎮 Chat interrupted. Goodbye!{RESET}")
            return "exit"

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

    def _process_user_input(self, user_input, messages, message_content, files):
        """Process user input and update messages accordingly."""
        # Handle exit command
        if self._handle_exit_command(user_input):
            return messages, True, False  # Return messages, exit flag, and clear flag

        # Handle clear command
        if user_input.lower() == "/clear":
            return self._handle_clear_command(), False, True  # Add a clear flag

        # Handle files that were loaded but not yet sent
        if files and not messages:
            combined_content = message_content.copy()
            combined_content.append({"type": "text", "text": user_input})
            messages.append({"role": "user", "content": combined_content})
        # Handle file command
        elif user_input.startswith("/file "):
            file_path = user_input[6:].strip()
            file_message = self.llm.handle_file_command(file_path)
            if file_message:
                messages.append({"role": "user", "content": file_message})
                return messages, False, True
        else:
            # Add regular text message
            messages.append({"role": "user", "content": user_input})

        return messages, False, False

    def start_chat(self, initial_content=None, files=None):
        """
        Start an interactive chat session using streaming mode.

        Args:
            initial_content (str, optional): Initial message to start the conversation
            files (list, optional): List of file paths to include in the initial message
        """
        messages = []
        message_content = []
        terminal_width = get_terminal_width()
        divider = "─" * terminal_width

        # Process files if provided
        if files:
            message_content = []
            for file_path in files:
                file_content = self.llm.process_file_for_message(file_path)
                if file_content:
                    message_content.append(file_content)

            # Add initial text if provided
            if initial_content:
                message_content.append({"type": "text", "text": initial_content})
                messages.append({"role": "user", "content": message_content})
                print(f"\n{BLUE}{BOLD}👤 YOU:{RESET} [Initial content with files]")
        elif initial_content:
            messages.append({"role": "user", "content": initial_content})
            print(f"\n{BLUE}{BOLD}👤 YOU:{RESET} [Initial content]")

        # Print welcome message
        self._print_welcome_message(divider)

        # Main chat loop
        while True:
            # Handle initial message or get user input
            if not (messages and len(messages) == 1 and initial_content):
                user_input = self._get_user_input(divider)

                # Process the user input
                messages, should_exit, was_cleared = self._process_user_input(
                    user_input, messages, message_content, files
                )

                # Exit if requested
                if should_exit:
                    break

                # Skip to next iteration if messages were cleared
                if was_cleared:
                    print(divider)
                    continue

                # Skip to next iteration if no messages to process
                if not messages:
                    print(divider)
                    continue

            # Get and display assistant response
            print(f"\n{GREEN}{BOLD}🤖 ASSISTANT:{RESET}")

            assistant_response, input_tokens, output_tokens = (
                self._stream_assistant_response(messages)
            )

            if assistant_response:
                # Add assistant's response to message history
                messages.append(self.llm.format_assistant_message(assistant_response))

                # Store conversation in memory if memory service is available
                if self.memory_service and user_input and assistant_response:
                    try:
                        self.memory_service.store_conversation(user_input, assistant_response)
                    except Exception as e:
                        print(f"\n{YELLOW}⚠️ Failed to store conversation in memory: {str(e)}{RESET}")

                # Display token usage and cost
                total_cost = self.llm.calculate_cost(input_tokens, output_tokens)
                print("\n")
                print(divider)
                print(
                    f"{YELLOW}📊 Token Usage: Input: {input_tokens:,} | Output: {output_tokens:,} | "
                    f"Total: {input_tokens + output_tokens:,} | Cost: ${total_cost:.4f}{RESET}"
                )
                print(divider)
            else:
                # Error occurred
                print(divider)
                break
