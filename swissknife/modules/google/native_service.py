import os
import re
import json
import base64
import mimetypes
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from google import genai
from swissknife.modules.llm.models import ModelRegistry
from google.genai import types
from swissknife.modules.llm.base import BaseLLMService
from swissknife.modules.prompts.constants import (
    EXPLAIN_PROMPT,
    SUMMARIZE_PROMPT,
    CHAT_SYSTEM_PROMPT,
)


class GoogleStreamAdapter:
    """
    Adapter class that wraps Google GenAI streaming response to support context manager protocol.
    """

    def __init__(self, stream_generator):
        """
        Initialize the adapter with a Google GenAI stream generator.

        Args:
            stream_generator: The generator returned by generate_content_stream
        """
        self.stream_generator = stream_generator

    def __enter__(self):
        """Enter the context manager, returning self as the iterable."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager, handling cleanup if needed."""
        # No specific cleanup needed for Google GenAI stream
        pass

    def __iter__(self):
        """Return an iterator for the stream."""
        return self

    def __next__(self):
        """Get the next chunk from the stream generator."""
        try:
            return next(self.stream_generator)
        except StopIteration:
            raise
        except Exception as e:
            # Handle any Google GenAI specific exceptions
            print(f"Error in Google GenAI stream: {str(e)}")
            raise StopIteration


class GoogleAINativeService(BaseLLMService):
    """
    Google GenAI service implementation using the native Python SDK.
    This service connects to Google's Gemini models using the official Google GenAI SDK.
    """

    def __init__(self):
        """Initialize the Google GenAI service."""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Initialize the Google GenAI client
        self.client = genai.Client(api_key=api_key)

        # Default model
        self.model = "gemini-2.5-pro-preview-03-25"

        # Initialize tools and handlers
        self.tools = []
        self.tool_handlers = {}
        self.tool_definitions = []  # Keep original definitions for reference

        # Provider name and system prompt
        self._provider_name = "google"
        self.system_prompt = CHAT_SYSTEM_PROMPT

    def set_think(self, budget_tokens: int) -> bool:
        """
        Enable or disable thinking mode with the specified token budget.
        Currently not supported in Google GenAI.

        Args:
            budget_tokens (int): Token budget for thinking. 0 to disable thinking mode.

        Returns:
            bool: True if thinking mode is supported and successfully set, False otherwise.
        """
        print("Thinking mode is not supported for Google GenAI models.")
        return False

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost based on token usage.

        Args:
            input_tokens (int): Number of input tokens
            output_tokens (int): Number of output tokens

        Returns:
            float: Estimated cost in USD
        """
        # Current Gemini pricing as of March 2025
        current_model = ModelRegistry.get_instance().get_model(self.model)
        if current_model:
            input_cost = (input_tokens / 1_000_000) * current_model.input_token_price_1m
            output_cost = (
                output_tokens / 1_000_000
            ) * current_model.output_token_price_1m
            return input_cost + output_cost
        return 0.0

    def _process_content(self, prompt_template, content, max_tokens=2048):
        """
        Process content with a given prompt template.

        Args:
            prompt_template (str): The template with {content} placeholder
            content (str): The content to process
            max_tokens (int): Maximum tokens for the response

        Returns:
            str: The processed content
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_template.format(content=content),
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens, temperature=0.2
                ),
            )

            # Get token usage if available
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                if hasattr(response.usage_metadata, "prompt_token_count"):
                    input_tokens = response.usage_metadata.prompt_token_count or 0
                if hasattr(response.usage_metadata, "candidates_token_count"):
                    output_tokens = response.usage_metadata.candidates_token_count or 0

            # Calculate and log cost
            total_cost = self.calculate_cost(input_tokens, output_tokens)
            print("\nToken Usage Statistics:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens: {input_tokens + output_tokens:,}")
            print(f"Estimated cost: ${total_cost:.4f}")

            return response.text or ""
        except Exception as e:
            raise Exception(f"Failed to process content: {str(e)}")

    def summarize_content(self, content: str) -> str:
        """
        Summarize the provided content using Google GenAI.

        Args:
            content (str): The content to summarize

        Returns:
            str: The summarized content
        """
        return self._process_content(SUMMARIZE_PROMPT, content, max_tokens=2048)

    def explain_content(self, content: str) -> str:
        """
        Explain the provided content using Google GenAI.

        Args:
            content (str): The content to explain

        Returns:
            str: The explained content
        """
        return self._process_content(EXPLAIN_PROMPT, content, max_tokens=1500)

    def process_file_for_message(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Process a file and return the appropriate message content.

        Args:
            file_path (str): Path to the file

        Returns:
            Optional[Dict[str, Any]]: The message content or None if processing failed
        """
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"

            # For text files, read directly
            if mime_type.startswith("text/"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                print(f"📄 Including text file: {file_path}")
                return {
                    "type": "text",
                    "text": f"Content of {file_path}:\n\n{content}",
                }

            # For binary files, encode as base64
            with open(file_path, "rb") as f:
                content = f.read()
            encoded = base64.b64encode(content).decode("utf-8")

            print(f"📄 Including file: {file_path} (MIME type: {mime_type})")
            return {
                "mime_type": mime_type,
                "data": encoded,
                "file_name": os.path.basename(file_path),
            }
        except Exception as e:
            print(f"❌ Error processing file {file_path}: {str(e)}")
            return None

    def handle_file_command(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Handle the /file command and return message content.

        Args:
            file_path (str): Path to the file

        Returns:
            Optional[List[Dict[str, Any]]]: Message content or None if processing failed
        """
        result = self.process_file_for_message(file_path)
        if result:
            if "type" in result and result["type"] == "text":
                return [
                    {
                        "type": "text",
                        "text": f"I'm sharing this file with you:\n\n{result['text']}",
                    }
                ]
            else:
                # For now, we'll just use text for file content
                return [
                    {
                        "type": "text",
                        "text": f"I'm sharing this file with you: {os.path.basename(file_path)}",
                    }
                ]
        return None

    def register_tool(self, tool_definition, handler_function):
        """
        Register a tool with its handler function.

        Args:
            tool_definition (dict): The tool definition following OpenAI's function schema
            handler_function (callable): Function to call when tool is used
        """
        # Store original tool definition for reference
        self.tool_definitions.append(tool_definition)

        # Extract tool name from definition
        tool_name = self._extract_tool_name(tool_definition)

        # Extract parameters schema
        parameters = {}
        required = []

        if "function" in tool_definition:
            parameters = (
                tool_definition["function"].get("parameters", {}).get("properties", {})
            )
            required = (
                tool_definition["function"].get("parameters", {}).get("required", [])
            )
            description = tool_definition["function"].get("description", "")
        else:
            parameters = tool_definition.get("parameters", {}).get("properties", {})
            required = tool_definition.get("parameters", {}).get("required", [])
            description = tool_definition.get("description", "")

        # Create a function declaration for Google GenAI
        function_declaration = types.FunctionDeclaration(
            name=tool_name,
            description=description,
        )

        # Convert parameters to Google GenAI format
        for param_name, param_def in parameters.items():
            if not function_declaration.parameters:
                function_declaration.parameters = types.Schema(
                    type=types.Type.OBJECT, properties={}
                )
            param_type = param_def.get("type", "STRING").upper()
            if param_type == "INTEGER":
                param_type = "NUMBER"

            if (
                function_declaration.parameters is not None
                and function_declaration.parameters.properties is not None
            ):
                function_declaration.parameters.properties[param_name] = types.Schema(
                    type=types.Type(param_type),
                    description=param_def.get("description", None),
                )
                if param_type == "OBJECT":
                    function_declaration.parameters.properties[
                        param_name
                    ].properties = {}
        # Add required parameters
        if required and function_declaration.parameters:
            function_declaration.parameters.required = required

        # Create a Tool object with the function declaration
        self.tools.append(types.Tool(function_declarations=[function_declaration]))

        # Store the handler function
        self.tool_handlers[tool_name] = handler_function

        print(f"🔧 Registered tool: {tool_name}")

    def execute_tool(self, tool_name, tool_params) -> Any:
        """
        Execute a registered tool with the given parameters.

        Args:
            tool_name (str): Name of the tool to execute
            tool_params (dict): Parameters to pass to the tool

        Returns:
            Any: Result of the tool execution
        """
        if tool_name not in self.tool_handlers:
            return f"Error: Tool '{tool_name}' not found"

        try:
            handler = self.tool_handlers[tool_name]
            result = handler(**tool_params)
            return result
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"

    def stream_assistant_response(self, messages: List[Dict[str, Any]]) -> Any:
        """
        Stream the assistant's response with tool support.
        Returns a context manager compatible adapter around the Google GenAI stream.

        Args:
            messages (List[Dict[str, Any]]): The conversation messages

        Returns:
            GoogleStreamAdapter: A context manager compatible adapter
        """
        try:
            # Convert messages to Google GenAI format
            google_messages = self._convert_messages_to_google_format(messages)

            # Create configuration with tools
            config = types.GenerateContentConfig(
                temperature=0.6,
                top_p=0.95,
                # max_output_tokens=8192,
            )

            # Add system instruction if available
            if self.system_prompt:
                config.system_instruction = self.system_prompt

            # Add tools if available
            if self.tools:
                config.tools = self.tools
            # Get the stream generator
            stream_generator = self.client.models.generate_content_stream(
                model=self.model, contents=google_messages, config=config
            )

            # Wrap in adapter that supports context manager protocol
            return GoogleStreamAdapter(stream_generator)
        except Exception as e:
            print(f"Error creating stream: {str(e)}")

            # Create a dummy adapter that returns an empty response
            class EmptyStreamAdapter:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass

                def __iter__(self):
                    return self

                def __next__(self):
                    raise StopIteration

            return EmptyStreamAdapter()

    def _convert_messages_to_google_format(self, messages: List[Dict[str, Any]]):
        """
        Convert standard messages to Google GenAI format.

        Args:
            messages (List[Dict[str, Any]]): Standard message format

        Returns:
            List: Messages in Google GenAI format as Content or Part objects
        """
        from google.genai.types import Content, Part

        # Create a conversation in Google format
        google_messages = []

        # print(messages)
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                google_content = Content(role="user", parts=[])
                if isinstance(content, list):
                    for c in content:
                        if google_content.parts is not None:
                            if isinstance(c, dict):
                                google_content.parts.append(
                                    Part.from_text(text=c.get("text", ""))
                                )
                            else:
                                google_content.parts.append(Part.from_text(text=c))
                else:
                    if google_content.parts is not None:
                        google_content.parts.append(Part.from_text(text=content))
                # Create a user message
                google_messages.append(google_content)

            elif role == "assistant":
                # Create an assistant message
                parts = [Part.from_text(text=content)]

                # Add tool calls if present
                if "tool_calls" in msg:
                    for tool_call in msg["tool_calls"]:
                        # We can't directly add function calls in this format
                        # so we'll add a text representation
                        tool_text = f"\nUsing tool: {tool_call.get('name', '')}\n"
                        tool_text += f"Arguments: {json.dumps(tool_call.get('arguments', {}), indent=2)}"
                        parts.append(Part.from_text(text=tool_text))

                google_messages.append(Content(role="model", parts=parts))

            elif role == "tool":
                # Tool responses need to be sent as user messages
                tool_content = f"Tool result: {content}"
                google_messages.append(
                    Content(role="user", parts=[Part.from_text(text=tool_content)])
                )

        return google_messages

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
        chunk_text = ""
        input_tokens = 0
        output_tokens = 0
        thinking_content = ""

        if hasattr(chunk, "candidates") and chunk.candidates:
            for candidate in chunk.candidates:
                if (
                    hasattr(candidate, "content")
                    and candidate.content
                    and candidate.content.parts is not None
                ):
                    # get chunk text
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text is not None:
                            chunk_text += part.text

                        # get the thinking data
                        if hasattr(part, "thought") and part.thought is not None:
                            thinking_content += part.thought
                        # Check if this part has a function call
                        if hasattr(part, "function_call") and part.function_call:
                            function_call = part.function_call

                            # Create a unique ID for this tool call
                            tool_id = f"{function_call.name}_{len(tool_uses)}"

                            # Check if this function is already in tool_uses
                            existing_tool = next(
                                (
                                    t
                                    for t in tool_uses
                                    if t.get("name") == function_call.name
                                ),
                                None,
                            )

                            if existing_tool:
                                # Update the existing tool
                                if (
                                    hasattr(function_call, "args")
                                    and function_call.args
                                ):
                                    existing_tool["input"] = function_call.args
                            else:
                                # Create a new tool use entry
                                tool_uses.append(
                                    {
                                        "id": tool_id,
                                        "name": function_call.name,
                                        "input": function_call.args
                                        if hasattr(function_call, "args")
                                        else {},
                                        "type": "function",
                                        "response": "",
                                    }
                                )

        assistant_response += chunk_text
        # Process tool usage information from text if present
        tool_pattern = r"Using tool: (\w+)\s*(?:\n)?Arguments: (\{[\s\S]*\})"
        tool_matches = re.findall(tool_pattern, assistant_response, re.M)

        for tool_name, tool_args_str in tool_matches:
            if assistant_response.count("{") > assistant_response.count("}"):
                ## ignore if curly brackets not close
                break
            try:
                # Parse the JSON arguments
                tool_args = json.loads(tool_args_str)

                # Create a unique ID for this tool call
                tool_id = f"{tool_name}_{len(tool_uses)}"

                # Check if this tool is already in tool_uses
                existing_tool = next(
                    (t for t in tool_uses if t.get("name") == tool_name),
                    None,
                )

                if existing_tool:
                    # Update the existing tool
                    existing_tool["input"] = tool_args
                else:
                    # Create a new tool use entry
                    tool_uses.append(
                        {
                            "id": tool_id,
                            "name": tool_name,
                            "input": tool_args,
                            "type": "function",
                            "response": "",
                        }
                    )
            except json.JSONDecodeError:
                print(f"Failed to parse tool arguments: {tool_args_str}")

        assistant_response = re.sub(tool_pattern, "", assistant_response)
        # Process usage information if available
        if hasattr(chunk, "usage_metadata"):
            if hasattr(chunk.usage_metadata, "prompt_token_count"):
                input_tokens = chunk.usage_metadata.prompt_token_count or 0
            if hasattr(chunk.usage_metadata, "candidates_token_count"):
                output_tokens = chunk.usage_metadata.candidates_token_count or 0

        return (
            assistant_response or " ",
            tool_uses,
            input_tokens,
            output_tokens,
            chunk_text,
            (thinking_content, None) if thinking_content.strip() else None,
        )

    def format_tool_result(
        self, tool_use: Dict, tool_result: Any, is_error: bool = False
    ) -> Dict[str, Any]:
        """
        Format a tool result for the Google GenAI API.

        Args:
            tool_use: The tool use details
            tool_result: The result from the tool execution
            is_error: Whether the result is an error

        Returns:
            A formatted message for tool response
        """
        content = str(tool_result)
        if is_error:
            content = f"ERROR: {content}"

        # Return in a format expected by the interactive chat
        return {"role": "tool", "tool_call_id": tool_use["id"], "content": content}

    def format_assistant_message(
        self, assistant_response: str, tool_uses: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Format the assistant's response for the Google GenAI API.

        Args:
            assistant_response: The response text
            tool_uses: List of tool use details

        Returns:
            Formatted assistant message
        """
        if tool_uses and any(tu.get("id") for tu in tool_uses):
            # Assistant message with tool calls
            return {
                "role": "assistant",
                "content": assistant_response,
                "tool_calls": [
                    {
                        "id": tool_use["id"],
                        "name": tool_use["name"],
                        "arguments": tool_use["input"],
                        "type": tool_use["type"],
                    }
                    for tool_use in tool_uses
                    if tool_use.get("id")  # Only include tool calls with valid IDs
                ],
            }
        else:
            # Simple assistant message
            return {"role": "assistant", "content": assistant_response}

    def format_thinking_message(self, thinking_data) -> Optional[Dict[str, Any]]:
        """
        Format thinking content into the appropriate message format.
        Not supported by Google GenAI.

        Args:
            thinking_data: Tuple containing (thinking_content, thinking_signature)
                or None if no thinking data is available

        Returns:
            Dict[str, Any]: A properly formatted message containing thinking blocks
        """
        # Google doesn't support thinking blocks
        return None

    def validate_spec(self, prompt: str) -> str:
        """
        Validate a specification prompt using Google GenAI.

        Args:
            prompt: The specification prompt to validate

        Returns:
            Validation result as a JSON string
        """
        try:
            # Request JSON response
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            # Calculate and log token usage
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                if hasattr(response.usage_metadata, "prompt_token_count"):
                    input_tokens = response.usage_metadata.prompt_token_count or 0
                if hasattr(response.usage_metadata, "candidates_token_count"):
                    output_tokens = response.usage_metadata.candidates_token_count or 0

            # Calculate cost
            total_cost = self.calculate_cost(input_tokens, output_tokens)

            print("\nSpec Validation Token Usage:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens: {input_tokens + output_tokens:,}")
            print(f"Estimated cost: ${total_cost:.4f}")

            # Return the response text (should be JSON)
            return response.text or ""
        except Exception as e:
            raise Exception(f"Failed to validate specification: {str(e)}")

    def set_system_prompt(self, system_prompt: str):
        """
        Set the system prompt for the Google GenAI service.

        Args:
            system_prompt: The system prompt to use
        """
        self.system_prompt = system_prompt

    def clear_tools(self):
        """
        Clear all registered tools from the Google GenAI service.
        """
        self.tools = []
        self.tool_handlers = {}
        self.tool_definitions = []
