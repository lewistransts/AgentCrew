from AgentCrew.modules.custom_llm import CustomLLMService
import os
from dotenv import load_dotenv
from AgentCrew.modules import logger


class GithubCopilotService(CustomLLMService):
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GITHUB_COPILOT_API_KEY")
        if not api_key:
            raise ValueError(
                "GITHUB_COPILOT_API_KEY not found in environment variables"
            )
        super().__init__(
            api_key=api_key,
            base_url="https://api.githubcopilot.com",
            provider_name="github_copilot",
            extra_headers={
                "Copilot-Integration-Id": "vscode-chat",
                "Editor-Plugin-Version": "CopilotChat.nvim/*",
                "Editor-Version": "Neovim/0.9.0",
            },
        )
        self.model = "gpt-4.1"
        self.current_input_tokens = 0
        self.current_output_tokens = 0
        self.temperature = 0.6
        self._is_thinking = False
        # self._interaction_id = None
        logger.info("Initialized Github Copilot Service")
