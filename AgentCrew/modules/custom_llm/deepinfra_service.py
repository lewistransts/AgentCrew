from AgentCrew.modules.custom_llm import CustomLLMService
import os
from dotenv import load_dotenv
from AgentCrew.modules import logger


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
