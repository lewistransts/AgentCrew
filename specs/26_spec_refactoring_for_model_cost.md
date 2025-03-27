# Migrate Token Price Constants to Model Class and ModelRegistry

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives
- Add `input_token_price_1m` and `output_token_price_1m` fields to the `Model` class in `swissknife/modules/llm/models.py`.
- Update the `ModelRegistry` class in `swissknife/modules/llm/models.py` to handle the new fields when registering and retrieving models, specifically in the `_initialize_default_models` and `register_model` methods.
- Remove the `INPUT_TOKEN_COST_PER_MILLION` and `OUTPUT_TOKEN_COST_PER_MILLION` constants from the LLM service classes (`swissknife/modules/openai/service.py` and `swissknife/modules/anthropic/service.py`).
- Modify the `calculate_cost` methods in the LLM service classes (`swissknife/modules/openai/service.py` and `swissknife/modules/anthropic/service.py`) to retrieve token prices from the `ModelRegistry` instead of using the local constants.

## Contexts
- swissknife/modules/llm/models.py: Contains the `Model` class and `ModelRegistry` class.
- swissknife/modules/openai/service.py: Contains the `OpenAIService` class and its `calculate_cost` method.
- swissknife/modules/anthropic/service.py: Contains the `AnthropicService` class and its `calculate_cost` method.

## Low-level Tasks
1. UPDATE swissknife/modules/llm/models.py:
   - Modify the `Model` class to include `input_token_price_1m` and `output_token_price_1m` fields (float, default to 0.0).
   - Modify the `_initialize_default_models` method in the `ModelRegistry` class to include values for the new fields when creating default `Model` instances. Use the values I provided earlier.
   - Ensure the `register_model` method in the `ModelRegistry` class correctly handles the new fields.

2. UPDATE swissknife/modules/openai/service.py:
   - Remove the `INPUT_TOKEN_COST_PER_MILLION` and `OUTPUT_TOKEN_COST_PER_MILLION` constants.
   - Modify the `calculate_cost` method to retrieve the token prices from the `ModelRegistry` using `ModelRegistry.get_instance().get_current_model()` and access the `input_token_price_1m` and `output_token_price_1m` attributes.

3. UPDATE swissknife/modules/anthropic/service.py:
   - Remove the `INPUT_TOKEN_COST_PER_MILLION` and `OUTPUT_TOKEN_COST_PER_MILLION` constants.
   - Modify the `calculate_cost` method to retrieve the token prices from the `ModelRegistry` using `ModelRegistry.get_instance().get_current_model()` and access the `input_token_price_1m` and `output_token_price_1m` attributes.
