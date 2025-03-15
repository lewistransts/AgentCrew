# Implement Multi-Agent Architecture with Agent Manager

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives
- Create a base Agent class that defines shared behavior across all specialized agents
- Implement an AgentManager class to handle agent selection and task routing
- Integrate the handoff tool for transferring tasks between specialized agents
- Update InteractiveChat to work with the agent system instead of directly with LLM services
- Modify main.py to initialize the multi-agent system

## Contexts
- ./modules/llm/base.py: Contains the BaseLLMService class which defines the interface for LLM services
- ./modules/chat/interactive.py: Contains the InteractiveChat class that manages the chat interface
- ./main.py: Contains the main application entry point and service initialization
- ./modules/tools/registry.py: Contains the ToolRegistry class for registering and managing tools

## Low-level Tasks
1. CREATE modules/agents/__init__.py:
   - Create an empty init file to mark the directory as a Python package

2. CREATE modules/agents/base.py:
   - Implement the base Agent class with the following methods:
     - __init__(self, name, description, llm_service)
     - register_tool(self, tool_definition, handler_function)
     - set_system_prompt(self, prompt)
     - get_system_prompt(self)
     - process_messages(self, messages)

3. CREATE modules/agents/manager.py:
   - Implement the AgentManager class with the following methods:
     - __init__(self)
     - register_agent(self, agent)
     - select_agent(self, agent_name)
     - get_agent(self, agent_name)
     - get_current_agent(self)
     - perform_handoff(self, target_agent_name, reason, context_summary=None)
     - route_message(self, messages)

4. CREATE modules/agents/tools/__init__.py:
   - Create an empty init file to mark the directory as a Python package

5. CREATE modules/agents/tools/handoff.py:
   - Implement the handoff tool with the following functions:
     - get_handoff_tool_definition()
     - get_handoff_tool_handler(agent_manager)
     - handle_handoff(params) (inside get_handoff_tool_handler)
     - register(agent_manager)

6. CREATE modules/agents/specialized/__init__.py:
   - Create an empty init file to mark the directory as a Python package

7. CREATE modules/agents/specialized/architect.py:
   - Implement the ArchitectAgent class with the following methods:
     - __init__(self, llm_service)
     - get_system_prompt(self) -> overriding the base method

8. CREATE modules/agents/specialized/code_assistant.py:
   - Implement the CodeAssistantAgent class with the following methods:
     - __init__(self, llm_service)
     - get_system_prompt(self) -> overriding the base method

9. CREATE modules/agents/specialized/documentation.py:
   - Implement the DocumentationAgent class with the following methods:
     - __init__(self, llm_service)
     - get_system_prompt(self) -> overriding the base method

10. CREATE modules/agents/specialized/evaluation.py:
    - Implement the EvaluationAgent class with the following methods:
      - __init__(self, llm_service)
      - get_system_prompt(self) -> overriding the base method

11. UPDATE modules/chat/interactive.py:
    - Modify InteractiveChat class:
      - Update __init__(self, agent_manager, memory_service=None)
      - Update _stream_assistant_response(self, messages, input_tokens=0, output_tokens=0)
      - Add _handle_agent_command(self, command)
      - Update _process_user_input to handle agent commands
      - Update _print_welcome_message to include agent command information

12. UPDATE main.py:
    - Add setup_agents(services) function to initialize the multi-agent system
    - Modify the chat function to use the agent manager instead of directly using LLM services
    - Update services_load to include agent manager initialization
    - Ensure all necessary services are passed to the appropriate agents
