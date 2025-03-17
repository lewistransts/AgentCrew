from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Model:
    """Model metadata class."""

    id: str
    provider: str
    name: str
    description: str
    capabilities: List[str]
    default: bool = False


class ModelRegistry:
    """Registry for available LLM models."""

    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of ModelRegistry."""
        if cls._instance is None:
            cls._instance = ModelRegistry()
        return cls._instance

    def __init__(self):
        """Initialize the model registry with default models."""
        if ModelRegistry._instance is not None:
            raise RuntimeError(
                "ModelRegistry is a singleton. Use get_instance() instead."
            )

        self.models: Dict[str, Model] = {}
        self.current_model: Optional[Model] = None
        self._initialize_default_models()

    def _initialize_default_models(self):
        """Initialize the registry with default models."""
        default_models = [
            Model(
                id="claude-3-7-sonnet-latest",
                provider="claude",
                name="Claude 3.7 Sonnet",
                description="Anthropic's most powerful model with advanced reasoning",
                capabilities=["thinking", "tool_use", "vision"],
                default=True,
            ),
            Model(
                id="claude-3-5-sonnet-latest",
                provider="claude",
                name="Claude 3.5 Sonnet",
                description="Anthropic's Claude 3.5 Sonnet model - balanced performance and capabilities",
                capabilities=["tool_use", "vision"],
            ),
            Model(
                id="claude-3-5-haiku-latest",
                provider="claude",
                name="Claude 3.5 Haiku",
                description="Anthropic's fastest model",
                capabilities=["tool_use", "vision"],
            ),
            Model(
                id="gpt-4o",
                provider="openai",
                name="GPT-4o",
                description="Fast, intelligent, flexible GPT model",
                capabilities=["tool_use", "vision"],
            ),
            Model(
                id="gpt-4o-mini",
                provider="openai",
                name="GPT-4o Mini",
                description="Fast, affordable small model for focused tasks",
                capabilities=["tool_use", "vision"],
            ),
            Model(
                id="o3-mini",
                provider="openai",
                name="GPT o3 mini",
                description="Fast, flexible, intelligent reasoning model",
                capabilities=["thinking"],
            ),
            Model(
                id="deepseek-r1-distill-llama-70b",
                provider="groq",
                name="DeepSeek R1 Distill",
                description="DeepSeek's powerful model optimized for Groq",
                capabilities=["tool_use"],
            ),
            Model(
                id="llama3-70b-8192",
                provider="groq",
                name="Llama 3 70B",
                description="Meta's Llama 3 70B model optimized for Groq",
                capabilities=["tool_use"],
            ),
            Model(
                id="qwen-qwq-32b",
                provider="groq",
                name="QwQ 32B",
                description="SLM from Alibaba",
                capabilities=["thinking", "tool_use"],
                default=True,
            ),
        ]

        for model in default_models:
            self.register_model(model)

        # Set the default model
        for model in default_models:
            if model.default:
                self.current_model = model
                break

    def register_model(self, model: Model):
        """
        Register a model in the registry.

        Args:
            model: The model to register
        """
        self.models[model.id] = model

    def get_model(self, model_id: str) -> Optional[Model]:
        """
        Get a model by ID.

        Args:
            model_id: The model ID

        Returns:
            The model if found, None otherwise
        """
        return self.models.get(model_id)

    def get_models_by_provider(self, provider: str) -> List[Model]:
        """
        Get all models for a specific provider.

        Args:
            provider: The provider name

        Returns:
            List of models for the provider
        """
        return [model for model in self.models.values() if model.provider == provider]

    def set_current_model(self, model_id: str) -> bool:
        """
        Set the current model by ID.

        Args:
            model_id: The model ID

        Returns:
            True if successful, False otherwise
        """
        model = self.get_model(model_id)
        if model:
            self.current_model = model
            return True
        return False

    def get_current_model(self) -> Optional[Model]:
        """
        Get the current model.

        Returns:
            The current model if set, None otherwise
        """
        return self.current_model
