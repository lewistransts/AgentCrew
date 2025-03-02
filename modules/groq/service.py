import os
import base64
import contextlib
import json
import time
import threading
import itertools
import sys
from typing import Dict, Any
from groq import Groq
from dotenv import load_dotenv
from modules.llm.base import BaseLLMService
from ..prompts.constants import (
    EXPLAIN_PROMPT,
    SUMMARIZE_PROMPT,
    CHAT_SYSTEM_PROMPT,
)

INPUT_TOKEN_COST_PER_MILLION = 0.59
OUTPUT_TOKEN_COST_PER_MILLION = 0.79


def read_text_file(file_path):
    """Read and return the contents of a text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {str(e)}")
        return None


def read_binary_file(file_path):
    """Read a binary file and return base64 encoded content."""
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        return base64.b64encode(content).decode("utf-8")
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {str(e)}")
        return None


class GroqService(BaseLLMService):
    """Groq-specific implementation of the LLM service."""

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=api_key)
        # Set default model - can be updated based on Groq's available models
        self.model = "llama-3.2-90b-vision-preview"
        self.tools = []  # Initialize empty tools list
        self.tool_handlers = {}  # Map tool names to handler functions

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1_000_000) * INPUT_TOKEN_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000) * OUTPUT_TOKEN_COST_PER_MILLION
        return input_cost + output_cost

    def _process_content(self, prompt_template, content, max_tokens=2048):
        """Process content with a given prompt template."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt_template.format(content=content),
                    }
                ],
            )

            # Calculate and log token usage and cost
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_cost = self.calculate_cost(input_tokens, output_tokens)

            print("\nToken Usage Statistics:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens: {input_tokens + output_tokens:,}")
            print(f"Estimated cost: ${total_cost:.4f}")

            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Failed to process content: {str(e)}")

    def summarize_content(self, content: str) -> str:
        """Summarize the provided content using Groq."""
        return self._process_content(SUMMARIZE_PROMPT, content, max_tokens=2048)

    def explain_content(self, content: str) -> str:
        """Explain the provided content using Groq."""
        return self._process_content(EXPLAIN_PROMPT, content, max_tokens=1500)

    def process_file_for_message(self, file_path):
        """Process a file and return the appropriate message content."""
        content = read_text_file(file_path)
        if content:
            print(f"📄 Including text file: {file_path}")
            return {
                "type": "text",
                "text": f"Content of {file_path}:\n\n{content}",
            }

        return None

    def handle_file_command(self, file_path):
        """Handle the /file command and return message content."""
        content = read_text_file(file_path)
        if content:
            message_content = [
                {
                    "role": "user",
                    "content": f"I'm sharing this file with you:\n\nContent of {file_path}:\n\n{content}",
                }
            ]
            print(f"📄 Including text file: {file_path}")
            return message_content
        else:
            return None

    def _loading_animation(self, stop_event):
        """Display a loading animation in the terminal."""
        spinner = itertools.cycle(["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"])
        fun_words = [
            "Pondering",
            "Cogitating",
            "Ruminating",
            "Contemplating",
            "Brainstorming",
            "Calculating",
            "Processing",
            "Analyzing",
            "Deciphering",
            "Meditating",
            "Daydreaming",
            "Scheming",
            "Brewing",
            "Conjuring",
            "Inventing",
            "Imagining",
        ]
        import random

        fun_word = random.choice(fun_words)
        while not stop_event.is_set():
            sys.stdout.write("\r" + f"{fun_word} {next(spinner)} ")
            sys.stdout.flush()
            time.sleep(0.1)
        # Clear the spinner line when done
        sys.stdout.write("\r" + " " * 30 + "\r")
        sys.stdout.flush()

    def register_tool(self, tool_definition, handler_function):
        """
        Register a tool with its handler function.

        Args:
            tool_definition (dict): The tool definition following OpenAI's function schema
            handler_function (callable): Function to call when tool is used
        """
        self.tools.append(tool_definition)
        self.tool_handlers[tool_definition["function"]["name"]] = handler_function
        print(f"🔧 Registered tool: {tool_definition['function']['name']}")

    def execute_tool(self, tool_name, tool_params):
        """
        Execute a registered tool with the given parameters.

        Args:
            tool_name (str): Name of the tool to execute
            tool_params (dict): Parameters to pass to the tool

        Returns:
            dict: Result of the tool execution
        """
        if tool_name not in self.tool_handlers:
            return {"error": f"Tool '{tool_name}' not found"}

        handler = self.tool_handlers[tool_name]
        result = handler(**tool_params)
        return result

    def stream_assistant_response(self, messages):
        """Stream the assistant's response with tool support."""
        stream_params = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }

        # Add system message if provided
        if CHAT_SYSTEM_PROMPT:
            stream_params["messages"] = [
                {"role": "system", "content": CHAT_SYSTEM_PROMPT}
            ] + messages
        # Add tools if available
        if self.tools:
            stream_params["tools"] = self.tools

            # Start loading animation for tool-based requests
            stop_animation = threading.Event()
            animation_thread = threading.Thread(
                target=self._loading_animation, args=(stop_animation,)
            )
            animation_thread.daemon = True
            animation_thread.start()

            try:
                # Use non-streaming mode for tool support
                response = self.client.chat.completions.create(**stream_params)
            finally:
                # Stop the animation when response is received
                stop_animation.set()
                animation_thread.join()

            @contextlib.contextmanager
            def simulate_stream(data):
                yield data.choices

            # Return a list containing the single response to simulate a stream
            return simulate_stream(response)
        else:
            # Use actual streaming when no tools are needed
            return self.client.chat.completions.create(**stream_params, stream=True)

    def process_stream_chunk(
        self, chunk, assistant_response, tool_use
    ) -> tuple[str, dict | None, int, int, str | None]:
        """
        Process a single chunk from the streaming response.

        Args:
            chunk: The chunk from the stream
            assistant_response: Current accumulated assistant response
            tool_use: Current tool use information

        Returns:
            tuple: (
                updated_assistant_response (str),
                updated_tool_use (dict or None),
                input_tokens (int),
                output_tokens (int),
                chunk_text (str or None) - text to print for this chunk
            )
        """
        # Check if this is a non-streaming response (for tool use)
        if hasattr(chunk, "message"):
            # This is a complete response, not a streaming chunk
            message = chunk.message
            content = message.content or ""
            # Check for tool calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_call = message.tool_calls[0]
                function = tool_call.function

                updated_tool_use = {
                    "id": tool_call.id,
                    "name": function.name,
                    "input": json.loads(function.arguments),
                    "type": tool_call.type,
                    "response": "",
                }

                # Return with tool use information and the full content
                return (
                    content,
                    updated_tool_use,
                    chunk.usage.prompt_tokens if hasattr(chunk, "usage") else 0,
                    chunk.usage.completion_tokens if hasattr(chunk, "usage") else 0,
                    content,  # Return the full content to be printed
                )

            # Regular response without tool calls
            return (
                content,
                None,
                chunk.usage.prompt_tokens if hasattr(chunk, "usage") else 0,
                chunk.usage.completion_tokens if hasattr(chunk, "usage") else 0,
                content,  # Return the full content to be printed
            )

        # Handle regular streaming chunk
        chunk_text = chunk.choices[0].delta.content or ""
        updated_assistant_response = assistant_response + chunk_text

        # Get token counts if available in the chunk
        input_tokens = getattr(chunk, "usage", {}).get("prompt_tokens", 0)
        output_tokens = getattr(chunk, "usage", {}).get("completion_tokens", 0)

        return (
            updated_assistant_response,
            tool_use,
            input_tokens,
            output_tokens,
            chunk_text,
        )

    def format_tool_result(
        self, tool_use: Dict, tool_result: Any, is_error: bool = False
    ) -> Dict[str, Any]:
        """
        Format a tool result for Groq API.

        Args:
            tool_use_id: The ID of the tool use
            tool_result: The result from the tool execution
            is_error: Whether the result is an error

        Returns:
            A formatted message that can be appended to the messages list
        """
        # Groq follows OpenAI format for tool responses
        message = {
            "role": "tool",
            "tool_call_id": tool_use["id"],
            "name": tool_use["name"],
            "content": str(tool_result),  # Groq expects string content
        }

        # Note: OpenAI/Groq format doesn't have a standard way to indicate errors
        # We could potentially prefix the content with "ERROR: " if needed
        if is_error:
            message["content"] = f"ERROR: {message['content']}"

        return message

    def format_assistant_message(
        self, assistant_response: str, tool_use: Dict | None = None
    ) -> Dict[str, Any]:
        """Format the assistant's response for Groq API."""
        # Groq uses a simpler format with just a string content
        if tool_use:
            return {
                "role": "assistant",
                "content": assistant_response,
                "tool_calls": [
                    {
                        "id": tool_use["id"],
                        "function": {
                            "name": tool_use["name"],
                            "arguments": json.dumps(tool_use["input"]),
                        },
                        "type": tool_use["type"],
                    }
                ],
            }
        else:
            return {
                "role": "assistant",
                "content": assistant_response,
            }
