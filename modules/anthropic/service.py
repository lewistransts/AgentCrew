import os
import base64
import mimetypes
from typing import Dict, Any
from anthropic import Anthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv
from modules.llm.base import BaseLLMService
from ..prompts.constants import (
    EXPLAIN_PROMPT,
    SUMMARIZE_PROMPT,
    CHAT_SYSTEM_PROMPT,
)


INPUT_TOKEN_COST_PER_MILLION = 3.0
OUTPUT_TOKEN_COST_PER_MILLION = 15.0

# INPUT_TOKEN_COST_PER_MILLION = 0.8
# OUTPUT_TOKEN_COST_PER_MILLION = 4.0


def read_text_file(file_path):
    """Read and return the contents of a text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        # try again with cp1252 encoding
        try:
            with open(file_path, "r", encoding="cp1252") as f:
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


class AnthropicService(BaseLLMService):
    """Anthropic-specific implementation of the LLM service."""

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-latest"
        # self.model = "claude-3-5-haiku-latest"
        self.tools = []  # Initialize empty tools list
        self.tool_handlers = {}  # Map tool names to handler functions
        self.thinking_enabled = False
        self.thinking_budget = 0
        self.caching_blocks = 0
        self._provider_name = "claude"

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1_000_000) * INPUT_TOKEN_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000) * OUTPUT_TOKEN_COST_PER_MILLION
        return input_cost + output_cost

    def _process_content(self, prompt_template, content, max_tokens=2048):
        """Process content with a given prompt template."""
        try:
            message = self.client.messages.create(
                model=self.model,
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

            print("\nToken Usage Statistics:")
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

    def _process_file(self, file_path, for_command=False):
        """
        Process a file and return the appropriate message content.

        Args:
            file_path: Path to the file to process
            for_command: If True, format for /file command with different text prefix

        Returns:
            Content object for the file or None if processing failed
        """
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type == "application/pdf":
            pdf_data = read_binary_file(file_path)
            if pdf_data:
                print(f"📄 Including PDF document: {file_path}")
                return {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    },
                }
        elif mime_type and mime_type.startswith("image/"):
            image_data = read_binary_file(file_path)
            if image_data:
                print(f"🖼️ Including image: {file_path}")
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data,
                    },
                }
        else:
            content = read_text_file(file_path)
            if content:
                print(f"📄 Including text file: {file_path}")
                text_prefix = (
                    "I'm sharing this file with you:\n\n" if for_command else ""
                )
                return {
                    "type": "text",
                    "text": f"{text_prefix}Content of {file_path}:\n\n{content}",
                }

        return None

    def process_file_for_message(self, file_path):
        """Process a file and return the appropriate message content."""
        return self._process_file(file_path, for_command=False)

    def handle_file_command(self, file_path):
        """Handle the /file command and return message content."""
        content = self._process_file(file_path, for_command=True)
        if content:
            return [content]
        return None

    def register_tool(self, tool_definition, handler_function):
        """
        Register a tool with its handler function.

        Args:
            tool_definition (dict): The tool definition following Anthropic's schema
            handler_function (callable): Function to call when tool is used
        """
        self.tools.append(tool_definition)
        self.tool_handlers[tool_definition["name"]] = handler_function
        # print(f"🔧 Registered tool: {tool_definition['name']}")

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

    def process_stream_chunk(self, chunk, assistant_response, tool_uses):
        """
        Process a single chunk from the Anthropic streaming response.

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
                chunk_text (str or None) - text to print for this chunk,
                thinking_data (tuple or None) - thinking content from this chunk
            )
        """
        chunk_text = None
        thinking_content = None
        thinking_signature = None
        input_tokens = 0
        output_tokens = 0

        if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
            chunk_text = chunk.delta.text
            assistant_response += chunk_text
        elif chunk.type == "content_block_delta" and hasattr(chunk.delta, "thinking"):
            # Process thinking content
            thinking_content = chunk.delta.thinking
        elif chunk.type == "content_block_delta" and hasattr(chunk.delta, "signature"):
            # Capture thinking signature
            thinking_signature = chunk.delta.signature
        elif (
            chunk.type == "message_start"
            and hasattr(chunk, "message")
            and hasattr(chunk.message, "usage")
        ):
            if hasattr(chunk.message.usage, "input_tokens"):
                input_tokens = chunk.message.usage.input_tokens
        elif chunk.type == "message_delta" and hasattr(chunk, "usage") and chunk.usage:
            if hasattr(chunk.usage, "output_tokens"):
                output_tokens = chunk.usage.output_tokens
        elif chunk.type == "message_stop" and hasattr(chunk, "message"):
            if (
                hasattr(chunk.message, "stop_reason")
                and chunk.message.stop_reason == "tool_use"
                and hasattr(chunk.message, "content")
            ):
                # Extract tool use information
                for content_block in chunk.message.content:
                    if (
                        hasattr(content_block, "type")
                        and content_block.type == "tool_use"
                    ):
                        tool_uses = [
                            {
                                "name": content_block.name,
                                "input": content_block.input,
                                "id": content_block.id,
                                "response": content_block,
                            }
                        ]
                        break
                    # elif (
                    #     hasattr(content_block, "type")
                    #     and content_block.type == "thinking"
                    # ):
                    #     # Store thinking content and signature from final message
                    #     thinking_content = content_block.thinking
                    #     if hasattr(content_block, "signature"):
                    #         thinking_signature = content_block.signature

        # Return thinking_signature as part of the thinking_content
        # We'll use a tuple to return both thinking content and signature
        thinking_data = None
        if thinking_content is not None or thinking_signature is not None:
            thinking_data = (thinking_content, thinking_signature)

        return (
            assistant_response,
            tool_uses,
            input_tokens,
            output_tokens,
            chunk_text,
            thinking_data,
        )

    def format_tool_result(
        self, tool_use: Dict, tool_result: Any, is_error: bool = False
    ) -> Dict[str, Any]:
        """
        Format a tool result for Claude API.

        Args:
            tool_use_id: The ID of the tool use
            tool_result: The result from the tool execution
            is_error: Whether the result is an error

        Returns:
            A formatted message that can be appended to the messages list
        """
        message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use["id"],
                    "content": tool_result,
                }
            ],
        }

        # Add is_error flag if this is an error
        if is_error:
            message["content"][0]["is_error"] = True

        if len(str(tool_result)) > 1024 and self.caching_blocks < 4:
            message["content"][0]["cache_control"] = {"type": "ephemeral"}
            self.caching_blocks += 1
        return message

    def format_assistant_message(
        self, assistant_response: str, tool_uses: list[Dict] | None = None
    ) -> Dict[str, Any]:
        """Format the assistant's response for Anthropic API."""
        # Fix the issue with assistant message return empty
        if assistant_response == "":
            assistant_response = " "
        assistant_message = {
            "role": "assistant",
            "content": [{"type": "text", "text": assistant_response}],
        }

        # If there's a tool use response, add it to the content array
        if (
            tool_uses
            and tool_uses[0]
            and "response" in tool_uses[0]
            and tool_uses[0]["response"] != ""
        ):
            assistant_message["content"].append(tool_uses[0]["response"])

        return assistant_message

    def format_thinking_message(self, thinking_data) -> Dict[str, Any]:
        """
        Format thinking content into the appropriate message format for Claude.

        Args:
            thinking_data: Tuple containing (thinking_content, thinking_signature)
                or None if no thinking data is available

        Returns:
            Dict[str, Any]: A properly formatted message containing thinking blocks
        """
        if not thinking_data:
            return None

        thinking_content, thinking_signature = thinking_data

        if not thinking_content:
            return None

        # For Claude, thinking blocks need to be preserved in the assistant's message
        thinking_block = {"type": "thinking", "thinking": thinking_content}

        # Add signature if available
        if thinking_signature:
            thinking_block["signature"] = thinking_signature

        return {"role": "assistant", "content": [thinking_block]}

    def validate_spec(self, prompt: str) -> str:
        """
        Validate a specification prompt using Anthropic Claude.

        Args:
            prompt: The specification prompt to validate

        Returns:
            Validation result as a JSON string
        """

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
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

            print("\nSpec Validation Token Usage:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens: {input_tokens + output_tokens:,}")
            print(f"Estimated cost: ${total_cost:.4f}")

            return content_block.text
        except Exception as e:
            raise Exception(f"Failed to validate specification: {str(e)}")

    def set_think(self, budget_tokens: int) -> bool:
        """
        Enable or disable thinking mode with the specified token budget.

        Args:
            budget_tokens (int): Token budget for thinking. 0 to disable thinking mode.

        Returns:
            bool: True if thinking mode is supported and successfully set, False otherwise.
        """
        if budget_tokens == 0:
            self.thinking_enabled = False
            self.thinking_budget = 0
            print("Thinking mode disabled.")
            return True
        if not self.model.startswith("claude-3-7-sonnet"):
            print("Thinking mode is disabled for this model.")
            return False

        # Ensure minimum budget is 1024 tokens
        if budget_tokens < 1024:
            print("Warning: Minimum thinking budget is 1024 tokens. Setting to 1024.")
            budget_tokens = 1024

        self.thinking_enabled = True
        self.thinking_budget = budget_tokens
        print(f"Thinking mode enabled with budget of {budget_tokens} tokens.")
        return True

    def stream_assistant_response(self, messages):
        """Stream the assistant's response with tool support."""
        # first cache for system prompt and tool
        if self.caching_blocks == 0:
            messages[-1]["content"][-1]["cache_control"] = {"type": "ephemeral"}
            self.caching_blocks += 1
        stream_params = {
            "model": self.model,
            "max_tokens": 8192,
            "system": CHAT_SYSTEM_PROMPT,
            "messages": messages,
        }

        # Add thinking configuration if enabled
        if self.thinking_enabled:
            stream_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget,
            }
        else:
            stream_params["temperature"] = 0.2
            stream_params["top_p"] = 0.1

        # Add tools if available
        if self.tools:
            stream_params["tools"] = self.tools
        return self.client.messages.stream(**stream_params)
