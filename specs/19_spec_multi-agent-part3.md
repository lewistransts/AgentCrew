# Update Agent System to Manage Tool Registration

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives
- Move tool registration from LLM services to individual agents
- Define specific tool sets for each specialized agent in main.py
- Ensure tools are properly registered/unregistered when switching agents
- Maintain compatibility with model switching functionality
- Fix the commented-out handoff tool registration in setup_agents function
- Enable the agent routing in InteractiveChat

## Contexts
- modules/llm/base.py: Contains the BaseLLMService class which defines the interface for LLM services
- modules/anthropic/service.py: Contains the AnthropicService implementation
- modules/openai/service.py: Contains the OpenAIService implementation
- modules/groq/service.py: Contains the GroqService implementation
- modules/agents/base.py: Contains the Agent base class
- modules/agents/manager.py: Contains the AgentManager class
- modules/agents/specialized/architect.py: Contains the ArchitectAgent class
- modules/agents/specialized/code_assistant.py: Contains the CodeAssistantAgent class
- modules/agents/specialized/documentation.py: Contains the DocumentationAgent class
- modules/agents/specialized/evaluation.py: Contains the EvaluationAgent class
- modules/chat/interactive.py: Contains the InteractiveChat class
- modules/tools/registry.py: Contains the ToolRegistry class
- main.py: Contains the setup_agents function and tool registration

## Low-level Tasks
1. UPDATE modules/llm/base.py:
   - Add a clear_tools(self) abstract method to BaseLLMService

2. UPDATE modules/anthropic/service.py:
   - Implement clear_tools(self) method to reset self.tools and self.tool_handlers

3. UPDATE modules/openai/service.py and modules/groq/service.py:
   - Make the same changes as in anthropic/service.py for consistency

4. UPDATE modules/agents/base.py:
   - Modify register_tool method to store tool definitions in the agent's tools list
   - Add a register_tools_with_llm(self) method to register all tools with the LLM service
   - Add a clear_tools_from_llm(self) method to clear tools from the LLM service

5. UPDATE modules/agents/manager.py:
   - Modify select_agent(self, agent_name: str) method to:
     - Clear tools from the previous agent's LLM service using clear_tools_from_llm
     - Register the new agent's tools with the LLM service using register_tools_with_llm

6. UPDATE main.py:
   - Remove the global tool registration for the LLM service (llm_service.register_all_tools())
   - Define specific tool sets for each specialized agent
   - Register appropriate tools with each agent type
   - Uncomment the register_handoff line in setup_agents function

7. UPDATE modules/chat/interactive.py:
   - Uncomment the line `messages = self.agent_manager.route_message(messages)` in _stream_assistant_response method
   - Update the model switching logic to preserve agent-specific tools when switching models

8. CREATE a tool registration helper function in main.py:
   - Create a register_agent_tools(agent, services) function that registers the appropriate tools for each agent type
   - Call this function for each agent in setup_agents
