import os
import sys
import base64
import mimetypes
import shutil
from anthropic import Anthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.markdown import Markdown

# Constants
# Token costs (USD per million tokens)
INPUT_TOKEN_COST_PER_MILLION = 3.0
OUTPUT_TOKEN_COST_PER_MILLION = 15.0

# Terminal formatting
COLORS_ENABLED = True  # Set to False to disable colors
BLUE = "\033[94m" if COLORS_ENABLED else ""
GREEN = "\033[92m" if COLORS_ENABLED else ""
YELLOW = "\033[93m" if COLORS_ENABLED else ""
RESET = "\033[0m" if COLORS_ENABLED else ""
BOLD = "\033[1m" if COLORS_ENABLED else ""

# Prompt templates
EXPLAIN_PROMPT = """
Please explain the following markdown content in a way that helps non-experts understand it better.
Break down complex concepts and provide clear explanations.
At the end, add a "Key Takeaways" section that highlights the most important points.

Content to explain:
{content}
"""

SUMMARIZE_PROMPT = """
Please provide a clear and concise summary of the following markdown content, starting directly with the content summary WITHOUT any introductory phrases or sentences.
Focus on the main points and key takeaways while maintaining the essential information, code snippets and examples.
Keep the summary well-structured and easy to understand.

Content to summarize:
{content}
"""

CHAT_SYSTEM_PROMPT = """
Your name is Terry. You are an AI assistant for software architects, providing expert support in searching, learning, analyzing, and brainstorming architectural solutions.

## Capabilities

**Information Retrieval**
- Provide accurate information on patterns, frameworks, technologies, and best practices
- Locate and summarize relevant technical resources and emerging trends

**Learning Support**
- Explain complex concepts clearly, adapting to different expertise levels
- Recommend quality learning resources and structured learning paths

**Analysis**
- Evaluate architectural decisions against quality attributes
- Compare approaches, support trade-off analysis, and identify potential risks
- Analyze technology compatibility and integration challenges

**Brainstorming**
- Generate diverse solution alternatives
- Challenge assumptions constructively
- Help structure and organize architectural thinking

## Interaction Approach
- Maintain professional yet conversational tone
- Ask clarifying questions when needed
- Provide balanced, well-structured responses
- Include visual aids or code examples when helpful
- Acknowledge knowledge limitations
- Use Markdown for response

Always support the architect's decision-making process rather than replacing it. Your goal is to enhance their capabilities through knowledge, perspective, and analytical support.
"""


# Utility functions
def get_terminal_width():
    """Get the current terminal width."""
    return shutil.get_terminal_size().columns


def read_text_file(file_path):
    """Read and return the contents of a text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"{YELLOW}❌ Error reading file {file_path}: {str(e)}{RESET}")
        return None


def read_binary_file(file_path):
    """Read a binary file and return base64 encoded content."""
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        return base64.b64encode(content).decode("utf-8")
    except Exception as e:
        print(f"{YELLOW}❌ Error reading file {file_path}: {str(e)}{RESET}")
        return None


class AnthropicClient:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=api_key)

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1_000_000) * INPUT_TOKEN_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000) * OUTPUT_TOKEN_COST_PER_MILLION
        return input_cost + output_cost

    def _process_content(self, prompt_template, content, max_tokens=2048):
        """Process content with a given prompt template."""
        try:
            message = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt_template.format(content=content),
                    }
                ],
            )

            content_block = message.content[0]
            if not isinstance(content_block, TextBlock):
                raise ValueError(
                    "Unexpected response type: message content is not a TextBlock"
                )

            # Calculate and log token usage and cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_cost = self.calculate_cost(input_tokens, output_tokens)

            print(f"\nToken Usage Statistics:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens: {input_tokens + output_tokens:,}")
            print(f"Estimated cost: ${total_cost:.4f}")

            return content_block.text
        except Exception as e:
            raise Exception(f"Failed to process content: {str(e)}")

    def summarize_content(self, content: str) -> str:
        """Summarize the provided content using Claude."""
        return self._process_content(SUMMARIZE_PROMPT, content, max_tokens=2048)

    def explain_content(self, content: str) -> str:
        """Explain the provided content using Claude."""
        return self._process_content(EXPLAIN_PROMPT, content, max_tokens=1500)

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

        return kb

    def _process_file_for_message(self, file_path):
        """Process a file and return the appropriate message content."""
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type == "application/pdf":
            pdf_data = read_binary_file(file_path)
            if pdf_data:
                print(f"{BLUE}📄 Including PDF document: {file_path}{RESET}")
                return {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    },
                }
        else:
            content = read_text_file(file_path)
            if content:
                print(f"{BLUE}📄 Including text file: {file_path}{RESET}")
                return {
                    "type": "text",
                    "text": f"Content of {file_path}:\n\n{content}",
                }

        return None

    def _handle_file_command(self, file_path):
        """Handle the /file command and return message content."""
        mime_type, _ = mimetypes.guess_type(file_path)
        message_content = []

        if mime_type == "application/pdf":
            pdf_data = read_binary_file(file_path)
            if pdf_data:
                message_content.append(
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    }
                )
                message_content.append(
                    {
                        "type": "text",
                        "text": "I'm sharing this PDF file with you. Please analyze it.",
                    }
                )
                print(f"{BLUE}📄 Including PDF document: {file_path}{RESET}")
            else:
                return None
        else:
            content = read_text_file(file_path)
            if content:
                message_content = [
                    {
                        "type": "text",
                        "text": f"I'm sharing this file with you:\n\nContent of {file_path}:\n\n{content}",
                    }
                ]
                print(f"{BLUE}📄 Including text file: {file_path}{RESET}")
            else:
                return None

        return message_content

    # def _clear_to_start(self, text):
    #     lines = text.split("\n")  # separate lines
    #     lines = lines[::-1]  # reverse list
    #     nlines = len(lines)  # number of lines
    #
    #     for i, line in enumerate(lines):  # iterate through lines from last to first
    #         sys.stdout.write("\r")  # move to beginning of line
    #         sys.stdout.write(
    #             " " * len(line)
    #         )  # replace text with spaces (thus overwriting it)
    #
    #         if i < nlines - 1:  # not first line of text
    #             sys.stdout.write("\x1b[1A")  # move up one line
    #
    #     sys.stdout.write("\r")  # move to beginning of line again
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
        console = Console()

        try:
            with self.client.messages.stream(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4096,
                system=CHAT_SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for chunk in stream:
                    if chunk.type == "content_block_delta" and hasattr(
                        chunk.delta, "text"
                    ):
                        print(chunk.delta.text, end="", flush=True)
                        assistant_response += chunk.delta.text
                    elif (
                        chunk.type == "message_start"
                        and hasattr(chunk, "message")
                        and hasattr(chunk.message, "usage")
                    ):
                        if hasattr(chunk.message.usage, "input_tokens"):
                            input_tokens = chunk.message.usage.input_tokens
                    elif (
                        chunk.type == "message_delta"
                        and hasattr(chunk, "usage")
                        and chunk.usage
                    ):
                        if hasattr(chunk.usage, "output_tokens"):
                            output_tokens = chunk.usage.output_tokens

            self._clear_to_start(assistant_response)
            # print("\n")
            # print("\n")
            # Replace \n with two spaces followed by \n for proper Markdown line breaks
            markdown_formatted_response = assistant_response.replace("\n", "  \n")
            console.print(Markdown(markdown_formatted_response))

            return assistant_response, input_tokens, output_tokens

        except Exception as e:
            print(f"\n{YELLOW}❌ Error: {str(e)}{RESET}")
            return None, 0, 0

    def _print_welcome_message(self, divider):
        """Print the welcome message for the chat."""
        print(f"\n{YELLOW}{BOLD}🎮 Welcome to the interactive chat with Claude!{RESET}")
        print(f"{YELLOW}Type 'exit' or 'quit' to end the session.{RESET}")
        print(
            f"{YELLOW}Use '/file <file_path>' to include a file in your message.{RESET}"
        )
        print(f"{YELLOW}Use '/clear' to clear the conversation history.{RESET}")
        print(divider)

    def _get_user_input(self, divider):
        """Get multiline input from the user."""
        print(f"\n{BLUE}{BOLD}👤 YOU:{RESET}")
        print(f"{YELLOW}(Press Enter for new line, Ctrl+S to submit){RESET}")

        kb = self._setup_key_bindings()
        session = PromptSession(key_bindings=kb)

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
            file_message = self._handle_file_command(file_path)
            if file_message:
                messages.append({"role": "user", "content": file_message})
        else:
            # Add regular text message
            messages.append({"role": "user", "content": user_input})

        return messages, False, False

    def interactive_chat(self, initial_content=None, files=None):
        """
        Start an interactive chat session with Claude using streaming mode.

        Args:
            initial_content (str, optional): Initial message to start the conversation
            files (list, optional): List of file paths to include in the initial message
        """
        messages = []
        message_content = []
        console = Console()
        terminal_width = get_terminal_width()
        divider = "─" * terminal_width

        # Process files if provided
        if files:
            message_content = []
            for file_path in files:
                file_content = self._process_file_for_message(file_path)
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
            print(f"\n{GREEN}{BOLD}🤖 CLAUDE:{RESET}")

            assistant_response, input_tokens, output_tokens = (
                self._stream_assistant_response(messages)
            )

            if assistant_response:
                # Add assistant's response to message history
                messages.append({"role": "assistant", "content": assistant_response})

                # Display token usage and cost
                total_cost = self.calculate_cost(input_tokens, output_tokens)
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
