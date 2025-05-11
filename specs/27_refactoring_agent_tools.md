
# Refactor Tool Registration Logic

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives
- Move the tool registration logic from `AgentCrew.main.py` to the `BaseAgent` class in `AgentCrew.modules/agents/base.py`.
- Allow each agent to define its own list of tools.
- Improve separation of concerns and reduce complexity in the tool registration process.
- Ensure that all existing functionality remains intact after the refactoring.

## Contexts
- AgentCrew.main.py: Contains the `register_agent_tools` function and the `setup_agents` function.
- AgentCrew.modules/agents/base.py: Contains the `Agent` class.
- AgentCrew.modules/agents/specialized/architect.py: Contains the `ArchitectAgent` class.
- AgentCrew.modules/agents/specialized/code_assistant.py: Contains the `CodeAssistantAgent` class.
- AgentCrew.modules/agents/specialized/documentation.py: Contains the `DocumentationAgent` class.

## Low-level Tasks
1. UPDATE AgentCrew.modules/agents/base.py:
   - Modify the `Agent` class to accept a `services` dictionary in its `__init__` method.
   - Add a `tools` attribute (List[str]) to the `Agent` class to define the list of tool names that the agent needs.
   - Move the logic from the `register_agent_tools` function in `main.py` to a new `register_tools` method in the `Agent` class. This method should iterate through the `tools` list and register the corresponding tools using the `services` dictionary.
   - Call the `register_tools` method at the end of the `__init__` method in the `Agent` class.

2. UPDATE AgentCrew.modules/agents/specialized/architect.py:
   - Add a `tools` attribute to the `ArchitectAgent` class and initialize it with the appropriate list of tool names: `["handoff", "clipboard", "memory", "web_search", "code_analysis"]`.
   - Ensure the `__init__` method of the `ArchitectAgent` calls the superclass `__init__` method with the `services` dictionary.

3. UPDATE AgentCrew.modules/agents/specialized/code_assistant.py:
   - Add a `tools` attribute to the `CodeAssistantAgent` class and initialize it with the appropriate list of tool names: `["handoff", "clipboard", "memory", "code_analysis", "spec_validator"]`.
   - Ensure the `__init__` method of the `CodeAssistantAgent` calls the superclass `__init__` method with the `services` dictionary.

4. UPDATE AgentCrew.modules/agents/specialized/documentation.py:
   - Add a `tools` attribute to the `DocumentationAgent` class and initialize it with the appropriate list of tool names: `["handoff", "clipboard", "memory", "web_search"]`.
   - Ensure the `__init__` method of the `DocumentationAgent` calls the superclass `__init__` method with the `services` dictionary.

5. UPDATE AgentCrew.main.py:
   - Remove the `register_agent_tools` function.
   - Modify the `setup_agents` function to pass the `services` dictionary to each agent during initialization.
