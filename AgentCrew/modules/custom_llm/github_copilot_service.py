from uuid import uuid4
from AgentCrew.modules.custom_llm import CustomLLMService
import os
from dotenv import load_dotenv
from AgentCrew.modules import logger
from datetime import datetime


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

    def github_copilot_token_to_open_ai_key(self, copilot_api_key):
        """
        Convert GitHub Copilot token to OpenAI key format.

        Args:
            copilot_api_key: The GitHub Copilot token

        Returns:
            Updated OpenAI compatible token
        """
        openai_api_key = self.client.api_key

        if openai_api_key.startswith("ghu") or int(
            dict(x.split("=") for x in openai_api_key.split(";"))["exp"]
        ) < int(datetime.now().timestamp()):
            import requests

            headers = {
                "Authorization": f"Bearer {copilot_api_key}",
                "Content-Type": "application/json",
            }
            if self.extra_headers:
                headers.update(self.extra_headers)
            res = requests.get(
                "https://api.github.com/copilot_internal/v2/token", headers=headers
            )
            self.client.api_key = res.json()["token"]

    async def process_message(self, prompt: str, temperature: float = 0) -> str:
        # Check if using GitHub Copilot
        if self.base_url:
            from urllib.parse import urlparse

            parsed_url = urlparse(self.base_url)
            host = parsed_url.hostname
            if host and host.endswith(".githubcopilot.com"):
                self.base_url = self.base_url.rstrip("/")
                self.github_copilot_token_to_open_ai_key(self.api_key)
        return await super().process_message(prompt, temperature)

    async def stream_assistant_response(self, messages):
        """Stream the assistant's response with tool support."""
        # Check if using GitHub Copilot
        if self.base_url:
            from urllib.parse import urlparse

            parsed_url = urlparse(self.base_url)
            host = parsed_url.hostname
            if host and host.endswith(".githubcopilot.com"):
                self.base_url = self.base_url.rstrip("/")
                self.github_copilot_token_to_open_ai_key(self.api_key)
                # if len([m for m in messages if m.get("role") == "assistant"]) == 0:
                #     self._interaction_id = str(uuid4())
                if self.extra_headers:
                    self.extra_headers["X-Initiator"] = (
                        "user"
                        if messages[-1].get("role", "assistant") == "user"
                        else "agent"
                    )
                    self.extra_headers["X-Request-Id"] = str(uuid4())
                    # if self._interaction_id:
                    #     self.extra_headers["X-Interaction-Id"] = self._interaction_id

        return await super().stream_assistant_response(messages)
