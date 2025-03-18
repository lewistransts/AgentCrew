from typing import Optional

from .validation_config import validation_prompt_template
from swissknife.modules.llm.service_manager import ServiceManager
from swissknife.modules.code_analysis import CodeAnalysisService


class SpecPromptValidationService:
    """Service for validating specification prompts using LLM."""

    def __init__(self, preferred_provider: Optional[str] = None):
        """
        Initialize the spec validation service.

        Args:
            preferred_provider: Optional preferred LLM provider (claude, openai, groq)
        """
        self.preferred_provider = (
            preferred_provider or "claude"
        )  # Default to Claude if not specified

    def validate(self, prompt: str, repo_path: str) -> str:
        """
        Validate a specification prompt using the preferred LLM provider.

        Args:
            prompt: The specification prompt to validate

        Returns:
            Dict containing validation results with issues, suggestions, and assessment
        """
        try:
            # Get the LLM service for the preferred provider
            service_manager = ServiceManager.get_instance()
            llm_service = service_manager.get_service(self.preferred_provider)

            code_analyze = CodeAnalysisService()

            code_analysis = code_analyze.analyze_code_structure(repo_path)

            if isinstance(code_analysis, dict) and "error" in code_analysis:
                raise Exception(f"Failed to analyze code: {code_analysis['error']}")

            validation_prompt = validation_prompt_template.format(
                prompt=prompt, code_analysis=code_analysis
            )

            # Call the validate_spec method on the LLM service
            validation_result = llm_service.validate_spec(validation_prompt)
            print(validation_result)

            # Parse and structure the validation result
            return validation_result
        except Exception as e:
            # If all providers fail, return an error
            print(str(e))
            raise
