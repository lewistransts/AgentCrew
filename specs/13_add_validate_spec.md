# Implement Multi-LLM Spec Prompt Validation

> Ingest the information from these files, implement the Low-level Tasks, and
> generate the code that will satisfy Objectives

## Objectives

- Extend the existing LLM service framework to include spec validation
  capabilities for different LLM providers.
- Ensure each LLM service (e.g., OpenAI, Anthropic) can process spec validation
  requests.
- Enable the `SpecPromptValidationService` to select the appropriate LLM
  provider and obtain validation feedback.

## Contexts

- `modules/coder/validation_config.py`: Contains the validation prompt template
  and criteria settings.
- `modules/coder/spec_validation.py`: Manages the spec validation logic,
  integrating with LLM services.
- `modules/coder/tool.py`: Registers and handles the spec prompt validation
  tool.
- `modules/llm/base.py`: Base class for LLM services.
- `modules/openai/service.py`: Implementation details for OpenAI interaction.
- `modules/groq/service.py`: Implementation details for Groq interaction.
- `modules/anthropic/service.py`: Implementation details for Anthropic
  interaction.
- `main.py`: main program cli file

## Low-level Tasks

- CREATE `modules/coder/validation_config.py`:

  - Define a prompt template named `validation_prompt_template` for LLM spec
    validation.

- CREATE `modules/coder/spec_validation.py`:

  - Add functionality to the `SpecPromptValidationService` class to call the LLM
    service with the validation prompt.
  - Implement a `validate` method that constructs and sends the prompt to the
    LLM and parses the response for issues and suggestions.

- CREATE `modules/coder/tool.py`:

  - Add the `get_spec_validation_tool_definition` and the
    `get_spec_validation_tool_handler` to utilize the updated
    `SpecPromptValidationService` for validation.

- UPDATE `modules/llm/base.py`:

  - Add an abstract method `validate_spec(self, prompt)` to serve as a blueprint
    for derived services.

- UPDATE `modules/openai/service.py`:

  - Implement `validate_spec` within `OpenAIService` to conduct spec validation
    using the OpenAI API.

- UPDATE `modules/groq/service.py`:

  - Implement `validate_spec` within `GroqService` to conduct spec validation
    using the OpenAI API.

- UPDATE `modules/anthropic/service.py`:
  - Implement `validate_spec` within `AnthropicService` to handle spec
    validation via the Anthropic API.
- UPDATE `main.py`
  - Register spec_tools module
