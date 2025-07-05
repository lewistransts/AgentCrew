from AgentCrew.modules.custom_llm import CustomLLMService
import os
from dotenv import load_dotenv
from AgentCrew.modules import logger
from typing import Dict, Any


class DeepInfraService(CustomLLMService):
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("DEEPINFRA_API_KEY")
        if not api_key:
            raise ValueError("DEEPINFRA_API_KEY not found in environment variables")
        super().__init__(
            api_key=api_key,
            base_url="https://api.deepinfra.com/v1/openai",
            provider_name="deepinfra",
        )
        self.model = "Qwen/Qwen3-235B-A22B"
        self.current_input_tokens = 0
        self.current_output_tokens = 0
        self.temperature = 0.6
        self._is_thinking = False
        logger.info("Initialized DeepInfra Service")

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
        if isinstance(tool_result, list):
            parsed_tool_result = []
            for res in tool_result:
                # Skipping vision/image tool results for Groq
                # if res.get("type", "text") == "image_url":
                #     if "vision" in ModelRegistry.get_model_capabilities(self.model):
                #         parsed_tool_result.append(res)
                # else:
                if res.get("type", "text") == "text":
                    parsed_tool_result.append(res.get("text", ""))
            tool_result = "\n".join(parsed_tool_result) if parsed_tool_result else ""
        message = {
            "role": "tool",
            "tool_call_id": tool_use["id"],
            "name": tool_use["name"],
            "content": tool_result,  # Groq and deepinfra expects string content
        }

        # Add error indication if needed
        if is_error:
            message["content"] = f"ERROR: {message['content']}"

        return message
