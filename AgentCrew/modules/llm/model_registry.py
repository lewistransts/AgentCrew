from typing import Dict, List, Optional
from .types import Model
from .constants import AVAILABLE_MODELS


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

    @classmethod
    def get_model_capabilities(cls, mode_id):
        registry = ModelRegistry.get_instance()
        model = registry.get_model(mode_id)
        if not model:
            return []
        return model.capabilities

    def _initialize_default_models(self):
        """Initialize the registry with default models."""
        default_models = AVAILABLE_MODELS

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
