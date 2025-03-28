from typing import Dict
from swissknife.modules.deepinfra import DeepInfraService
from swissknife.modules.google import GoogleAINativeService
from swissknife.modules.llm.base import BaseLLMService
from swissknife.modules.anthropic import AnthropicService
from swissknife.modules.groq import GroqService
from swissknife.modules.openai import OpenAIService


class ServiceManager:
    """Singleton manager for LLM service instances."""

    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of ServiceManager."""
        if cls._instance is None:
            cls._instance = ServiceManager()
        return cls._instance

    def __init__(self):
        """Initialize the service manager with empty service instances."""
        if ServiceManager._instance is not None:
            raise RuntimeError(
                "ServiceManager is a singleton. Use get_instance() instead."
            )

        self.services: Dict[str, BaseLLMService] = {}
        self.service_classes = {
            "claude": AnthropicService,
            "groq": GroqService,
            "openai": OpenAIService,
            "google": GoogleAINativeService,
            "deepinfra": DeepInfraService,
        }

    def get_service(self, provider: str) -> BaseLLMService:
        """
        Get or create a service instance for the specified provider.

        Args:
            provider: The provider name (claude, groq, openai)

        Returns:
            An instance of the appropriate LLM service
        """
        if provider not in self.service_classes:
            raise ValueError(
                f"Unknown provider: {provider}. Available providers: {', '.join(self.service_classes.keys())}"
            )

        # Create the service if it doesn't exist
        if provider not in self.services:
            try:
                self.services[provider] = self.service_classes[provider]()
                # Register tools with the new service
                self.services[provider].register_all_tools()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize {provider} service: {str(e)}")

        return self.services[provider]

    def set_model(self, provider: str, model_id: str) -> bool:
        """
        Set the model for a specific provider.

        Args:
            provider: The provider name
            model_id: The model ID to use

        Returns:
            True if successful, False otherwise
        """
        service = self.get_service(provider)
        if hasattr(service, "model"):
            service.model = model_id
            return True
        return False
