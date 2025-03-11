from typing import Dict, Any, Callable
import os
from modules import code_analysis
from .spec_validation import SpecPromptValidationService
from modules.tools.registry import ToolRegistry


def get_spec_validation_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Get the tool definition for the spec validation tool.

    Args:
        provider: The LLM provider (claude, openai, groq)

    Returns:
        Tool definition compatible with the specified provider
    """
    if provider == "claude":
        return {
            "name": "validate_spec",
            "description": "Validates a specification prompt for clarity, completeness, and feasibility",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The specification prompt to validate",
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "The repo directory path to validate spec prompt against",
                    },
                },
                "required": ["prompt", "code_analysis"],
            },
        }
    elif provider in ["openai", "groq"]:
        return {
            "type": "function",
            "function": {
                "name": "validate_spec",
                "description": "Validates a specification prompt for clarity, completeness, and feasibility",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The specification prompt to validate",
                        },
                        "repo_path": {
                            "type": "string",
                            "description": "The repo directory path to validate spec prompt against",
                        },
                    },
                    "required": ["prompt", "code_analysis"],
                },
            },
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def get_spec_validation_tool_handler(
    spec_validation_service: SpecPromptValidationService,
) -> Callable:
    """
    Get the handler function for the spec validation tool.

    Args:
        spec_validation_service: The spec validation service instance

    Returns:
        Function that handles spec validation requests
    """

    def handle_spec_validation(**params) -> str:
        prompt = params.get("prompt", "")
        repo_path = params.get("repo_path", "")

        real_path = os.path.expanduser(repo_path)
        # Validate the spec
        validation_result = spec_validation_service.validate(prompt, real_path)

        # Check if validation meets criteria

        # Format the result as a readable string
        return validation_result

    return handle_spec_validation


def register(service_instance=None):
    """Register the spec validation tool with the tool registry."""
    if service_instance is None:
        service_instance = SpecPromptValidationService()

    registry = ToolRegistry.get_instance()

    registry.register_tool(
        get_spec_validation_tool_definition,
        get_spec_validation_tool_handler,
        service_instance,
    )
