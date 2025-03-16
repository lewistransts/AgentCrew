
# Agent Manager and Service Management

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives
- Update AgentManager to support lazy-loading of agent tools
- Implement model switching capability with proper tool re-registration
- Add agent switching logic that activates only the current agent
- Create service management facilities for handling LLM service lifecycle

## Contexts
- modules/agents/manager.py: Contains the AgentManager class
- modules/llm/service_manager.py: Contains the ServiceManager class
- main.py: Contains setup_agents and other initialization functions
- modules/chat/interactive.py: Contains the InteractiveChat class handling commands

## Low-level Tasks
1. UPDATE modules/agents/manager.py:
   - Update register_agent to avoid immediate activation
   - Enhance select_agent to properly activate/deactivate agents
   - Implement update_llm_service for model switching
   - Add proper handling of agent tool registration state

2. UPDATE modules/llm/service_manager.py:
   - Implement get_service method to retrieve current LLM service
   - Create set_model method to handle model switching
   - Add cleanup method for proper resource management

3. UPDATE modules/chat/interactive.py:
   - Add _handle_model_command to support model switching
   - Update _process_user_input to handle model switching command

