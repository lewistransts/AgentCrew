import sys
import os
import shutil
import pyperclip
import traceback
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.markdown import Markdown
from modules.llm.base import BaseLLMService
from modules.llm.service_manager import ServiceManager
from modules.llm.models import ModelRegistry
from modules.llm.message import MessageTransformer
from .constants import (
    BLUE,
    GREEN,
    YELLOW,
    RESET,
    BOLD,
    GRAY,
)
from .completers import ChatCompleter


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

    def _stream_assistant_response(self, messages, input_tokens=0, output_tokens=0):
        """Stream the assistant's response and return the response and token usage."""
        assistant_response = ""
        tool_uses = []
        thinking_content = ""  # Reset thinking content for new response
        thinking_signature = ""  # Store the signature
        start_thinking = True

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
                        # if signature:
                        #     thinking_signature = signature
                        # Print thinking content with a special format
                        if start_thinking:
                            print(f"\n{YELLOW}💭 Claude's thinking process:{RESET}")
                            start_thinking = False
                        print(f"{GRAY}{thinking_chunk}{RESET}", end="", flush=True)

                    # Print chunk text if available
                    if chunk_text:
                        print(chunk_text, end="", flush=True)

            # Handle tool use if needed
            if tool_uses and len(tool_uses) > 0:
                # Add thinking content as a separate message if available
                if thinking_content:
                    self._clear_to_start(thinking_content)
                    print(f"{GRAY}{thinking_content}{RESET}", end="", flush=True)
                    print("\n---\n")

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

                self._clear_to_start(assistant_response)
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
                    except Exception as e:
                        messages.append(
                            self.llm.format_tool_result(tool_use, str(e), is_error=True)
                        )
                    # Get a new response with the tool result
                print(f"\n{GREEN}{BOLD}🤖 ASSISTANT (continued):{RESET}")
                return self._stream_assistant_response(
                    messages, input_tokens, output_tokens
                )
            else:
                self._clear_to_start(assistant_response)

                # Replace \n with two spaces followed by \n for proper Markdown line breaks
                markdown_formatted_response = assistant_response.replace("\n", "  \n")
                self.console.print(Markdown(markdown_formatted_response))

                # Store the latest response
                self.latest_assistant_response = assistant_response

                # Add the assistant's response
                messages.append(self.llm.format_assistant_message(assistant_response))

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
        print(
            f"{YELLOW}Use '/think <budget>' to enable Claude's thinking mode (min 1024 tokens).{RESET}"
        )
        print(f"{YELLOW}Use '/think 0' to disable thinking mode.{RESET}")
        print(
            f"{YELLOW}Use '/model [model_id]' to switch models or list available models.{RESET}"
        )
        print(f"{YELLOW}Press Alt/Meta+C to copy the latest assistant response.{RESET}")
        print(divider)

    def _get_user_input(self, divider):
        """Get multiline input from the user."""
        print(f"\n{BLUE}{BOLD}👤 YOU:{RESET}")
        print(f"{YELLOW}(Press Enter for new line, Ctrl+S to submit){RESET}")

        kb = self._setup_key_bindings()
        session = PromptSession(key_bindings=kb, completer=ChatCompleter())

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

        # Handle think command
        if user_input.lower().startswith("/think "):
            try:
                budget = int(user_input[7:].strip())
                self.llm.set_think(budget)
            except ValueError:
                print(f"{YELLOW}Invalid budget value. Please provide a number.{RESET}")
            return messages, False, True  # Skip to next iteration

        # Handle model command
        if user_input.lower().startswith("/model"):
            model_id = user_input[7:].strip()
            registry = ModelRegistry.get_instance()
            manager = ServiceManager.get_instance()

            # If no model ID is provided, list available models
            if not model_id:
                print(f"{YELLOW}Available models:{RESET}")
                for provider in ["claude", "openai", "groq"]:
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
                    self.llm = manager.get_service(model.provider)
                    manager.set_model(model.provider, model.id)

                    print(f"{YELLOW}Switched to {model.name} ({model.id}){RESET}")
                else:
                    print(f"{YELLOW}Failed to switch model.{RESET}")
            else:
                print(f"{YELLOW}Unknown model: {model_id}{RESET}")

            return messages, False, True

        # Handle files that were loaded but not yet sent
        if files and not messages:
            combined_content = message_content.copy()
            combined_content.append({"type": "text", "text": user_input})
            messages.append({"role": "user", "content": combined_content})
        # Handle file command
        elif user_input.startswith("/file "):
            file_path = user_input[6:].strip()
            file_path = os.path.expanduser(file_path)
            file_message = self.llm.handle_file_command(file_path)
            if file_message:
                messages.append({"role": "user", "content": file_message})
                return messages, False, True
        else:
            # Add regular text message
            messages.append(
                {"role": "user", "content": [{"type": "text", "text": user_input}]}
            )

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
        session_cost = 0.0
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
                print(divider)
                print(
                    f"{YELLOW}📊 Token Usage: Input: {input_tokens:,} | Output: {output_tokens:,} | "
                    f"Total: {input_tokens + output_tokens:,} | Cost: ${total_cost:.4f} | Total: {session_cost:.4f}{RESET}"
                )
                print(divider)
            else:
                # Error occurred
                print(divider)
                continue
