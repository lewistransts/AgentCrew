import os
import base64
import mimetypes
from groq import Groq
from dotenv import load_dotenv
from modules.llm.base import BaseLLMService
from .constants import (
    INPUT_TOKEN_COST_PER_MILLION,
    OUTPUT_TOKEN_COST_PER_MILLION,
    EXPLAIN_PROMPT,
    SUMMARIZE_PROMPT,
    CHAT_SYSTEM_PROMPT,
)


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
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
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

        return self.client.chat.completions.create(**stream_params, stream=True)
