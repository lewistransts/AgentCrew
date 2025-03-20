import os
import base64
import json
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from swissknife.modules.llm.base import BaseLLMService
from ..prompts.constants import (
    EXPLAIN_PROMPT,
    SUMMARIZE_PROMPT,
    CHAT_SYSTEM_PROMPT,
)

INPUT_TOKEN_COST_PER_MILLION = 2.5  # Adjust based on current OpenAI pricing
OUTPUT_TOKEN_COST_PER_MILLION = 10  # Adjust based on current OpenAI pricing


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


class OpenAIService(BaseLLMService):
    """OpenAI-specific implementation of the LLM service."""

    def __init__(self, api_key=None, base_url=None):
        load_dotenv()
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        # Set default model
        self.model = "gpt-4o"
        self.tools = []  # Initialize empty tools list
        self.tool_handlers = {}  # Map tool names to handler functions
        self._provider_name = "openai"
        self.system_prompt = CHAT_SYSTEM_PROMPT

    def set_think(self, budget_tokens: int) -> bool:
        """
        Enable or disable thinking mode with the specified token budget.

        Args:
            budget_tokens (int): Token budget for thinking. 0 to disable thinking mode.

        Returns:
            bool: True if thinking mode is supported and successfully set, False otherwise.
        """
        print("Thinking mode is not supported for OpenAI models.")
        return False

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost based on token usage."""
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
        """Summarize the provided content using OpenAI."""
        return self._process_content(SUMMARIZE_PROMPT, content, max_tokens=2048)

    def explain_content(self, content: str) -> str:
        """Explain the provided content using OpenAI."""
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
                    "type": "text",
                    "text": f"I'm sharing this file with you:\n\nContent of {file_path}:\n\n{content}",
                }
            ]
            print(f"📄 Including text file: {file_path}")
            return message_content
        else:
            return None

    def register_tool(self, tool_definition, handler_function):
        """
        Register a tool with its handler function.

        Args:
            tool_definition (dict): The tool definition following OpenAI's function schema
            handler_function (callable): Function to call when tool is used
        """
        self.tools.append(tool_definition)

        # Extract the name based on tool structure
        if "function" in tool_definition:
            tool_name = tool_definition["function"]["name"]
        elif "name" in tool_definition:
            tool_name = tool_definition["name"]
        else:
            raise ValueError("Tool definition must contain a name")

        self.tool_handlers[tool_name] = handler_function
        print(f"🔧 Registered tool: {tool_name}")

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
            "messages": messages,
            "stream_options": {"include_usage": True},
            "max_tokens": 4096,
        }
        if self.model.startswith("o3"):
            stream_params["reasoning_effort"] = "high"
            stream_params["parallel_tool_calls"] = False
        else:
            stream_params["top_p"] = 0.2
            stream_params["temperature"] = 0.3

        # Add system message if provided
        if self.system_prompt:
            stream_params["messages"] = [
                {"role": "system", "content": self.system_prompt}
            ] + messages

        # Add tools if available
        if self.tools:
            stream_params["tools"] = self.tools

        return self.client.chat.completions.create(**stream_params, stream=True)

    def process_stream_chunk(
        self, chunk, assistant_response: str, tool_uses: List[Dict]
    ) -> Tuple[str, List[Dict], int, int, Optional[str], Optional[tuple]]:
        """
        Process a single chunk from the streaming response.

        Args:
            chunk: The chunk from the stream
            assistant_response: Current accumulated assistant response
            tool_uses: Current tool use information

        Returns:
            tuple: (
                updated_assistant_response,
                updated_tool_uses,
                input_tokens,
                output_tokens,
                chunk_text,
                thinking_data
            )
        """
        chunk_text = None
        input_tokens = 0
        output_tokens = 0
        # thinking_content = None  # OpenAI doesn't support thinking mode

        # Handle tool call chunks
        if len(chunk.choices) > 0 and hasattr(chunk.choices[0].delta, "tool_calls"):
            delta_tool_calls = chunk.choices[0].delta.tool_calls
            if delta_tool_calls:
                # Process each tool call in the delta
                for tool_call_delta in delta_tool_calls:
                    tool_call_index = tool_call_delta.index

                    # Check if this is a new tool call
                    if tool_call_index >= len(tool_uses):
                        # Create a new tool call entry
                        tool_uses.append(
                            {
                                "id": tool_call_delta.id
                                if hasattr(tool_call_delta, "id")
                                else None,
                                "name": getattr(tool_call_delta.function, "name", "")
                                if hasattr(tool_call_delta, "function")
                                else "",
                                "input": {},
                                "type": "function",
                                "response": "",
                            }
                        )

                    # Update existing tool call with new data
                    if hasattr(tool_call_delta, "id") and tool_call_delta.id:
                        tool_uses[tool_call_index]["id"] = tool_call_delta.id

                    if hasattr(tool_call_delta, "function"):
                        if (
                            hasattr(tool_call_delta.function, "name")
                            and tool_call_delta.function.name
                        ):
                            tool_uses[tool_call_index]["name"] = (
                                tool_call_delta.function.name
                            )

                        if (
                            hasattr(tool_call_delta.function, "arguments")
                            and tool_call_delta.function.arguments
                        ):
                            # Accumulate arguments as they come in chunks
                            current_args = tool_uses[tool_call_index].get(
                                "args_json", ""
                            )
                            tool_uses[tool_call_index]["args_json"] = (
                                current_args + tool_call_delta.function.arguments
                            )

                            # Try to parse JSON if it seems complete
                            try:
                                args_json = tool_uses[tool_call_index]["args_json"]
                                tool_uses[tool_call_index]["input"] = json.loads(
                                    args_json
                                )
                                # Keep args_json for accumulation but use input for execution
                            except json.JSONDecodeError:
                                # Arguments JSON is still incomplete, keep accumulating
                                pass

                # For tool calls, we don't append to assistant_response as it's handled separately
                return (
                    assistant_response,
                    tool_uses,
                    input_tokens,
                    output_tokens,
                    "",
                    None,
                )

        # Handle regular content chunks
        if (
            len(chunk.choices) > 0
            and hasattr(chunk.choices[0].delta, "content")
            and chunk.choices[0].delta.content is not None
        ):
            chunk_text = chunk.choices[0].delta.content
            assistant_response += chunk_text

        # Handle final chunk with usage information
        if hasattr(chunk, "usage"):
            if hasattr(chunk.usage, "prompt_tokens"):
                input_tokens = chunk.usage.prompt_tokens
            if hasattr(chunk.usage, "completion_tokens"):
                output_tokens = chunk.usage.completion_tokens

        return (
            assistant_response,
            tool_uses,
            input_tokens,
            output_tokens,
            chunk_text,
            None,
        )

    def format_tool_result(
        self, tool_use: Dict, tool_result: Any, is_error: bool = False
    ) -> Dict[str, Any]:
        """
        Format a tool result for OpenAI API.

        Args:
            tool_use: The tool use details
            tool_result: The result from the tool execution
            is_error: Whether the result is an error

        Returns:
            A formatted message for tool response
        """
        # OpenAI format for tool responses
        message = {
            "role": "tool",
            "tool_call_id": tool_use["id"],
            "content": str(tool_result),
        }

        # Add error indication if needed
        if is_error:
            message["content"] = f"ERROR: {message['content']}"

        return message

    def format_assistant_message(
        self, assistant_response: str, tool_uses: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Format the assistant's response for OpenAI API.

        Args:
            assistant_response: The response text
            tool_uses: List of tool use details

        Returns:
            Formatted assistant message
        """
        if tool_uses and any(tu.get("id") for tu in tool_uses):
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
                    for tool_use in tool_uses
                    if tool_use.get("id")  # Only include tool calls with valid IDs
                ],
            }
        else:
            return {
                "role": "assistant",
                "content": assistant_response,
            }

    def format_thinking_message(self, thinking_data) -> Optional[Dict[str, Any]]:
        """
        Format thinking content into the appropriate message format for OpenAI.

        Args:
            thinking_data: Tuple containing (thinking_content, thinking_signature)
                or None if no thinking data is available

        Returns:
            Dict[str, Any]: A properly formatted message containing thinking blocks
        """
        # OpenAI doesn't support thinking blocks, so we return None
        return None

    def validate_spec(self, prompt: str) -> str:
        """
        Validate a specification prompt using OpenAI.

        Args:
            prompt: The specification prompt to validate

        Returns:
            Validation result as a JSON string
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                response_format={"type": "json_object"},
            )

            # Calculate and log token usage and cost
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_cost = self.calculate_cost(input_tokens, output_tokens)

            print("\nSpec Validation Token Usage:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens: {input_tokens + output_tokens:,}")
            print(f"Estimated cost: ${total_cost:.4f}")

            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"Failed to validate specification: {str(e)}")

    def set_system_prompt(self, system_prompt: str):
        """
        Set the system prompt for the LLM service.

        Args:
            system_prompt: The system prompt to use
        """
        self.system_prompt = system_prompt

    def clear_tools(self):
        """
        Clear all registered tools from the LLM service.
        """
        self.tools = []
        self.tool_handlers = {}
