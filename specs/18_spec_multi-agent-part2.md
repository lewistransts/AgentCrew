# Update LLM Services to Use Agent System Prompts

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives
- Modify LLM services to use the current agent's system prompt instead of the hardcoded one
- Ensure that when agents are switched, both the system prompt and tool set are properly updated
- Update the agent manager to handle tool registration and system prompt updates when switching agents
- Fix the commented-out handoff tool registration in setup_agents function
- Enable the agent routing in InteractiveChat

## Contexts
- modules/llm/base.py: Contains the BaseLLMService class which defines the interface for LLM services
- modules/anthropic/service.py: Contains the AnthropicService implementation
- modules/openai/service.py: Contains the OpenAIService implementation
- modules/groq/service.py: Contains the GroqService implementation
- modules/agents/manager.py: Contains the AgentManager class
- modules/chat/interactive.py: Contains the InteractiveChat class
- main.py: Contains the setup_agents function

## Low-level Tasks
1. UPDATE modules/llm/base.py:
   - Add a set_system_prompt(self, system_prompt: str) abstract method to BaseLLMService
   - Add a clear_tools(self) abstract method to BaseLLMService

2. UPDATE modules/anthropic/service.py:
   - Add a system_prompt instance variable in __init__ method, initialized with CHAT_SYSTEM_PROMPT
   - Implement set_system_prompt(self, system_prompt: str) method to update the system_prompt variable
   - Implement clear_tools(self) method to reset self.tools and self.tool_handlers
   - Modify stream_assistant_response to use self.system_prompt instead of CHAT_SYSTEM_PROMPT

3. UPDATE modules/openai/service.py:
   - Add a system_prompt instance variable in __init__ method, initialized with CHAT_SYSTEM_PROMPT
   - Implement set_system_prompt(self, system_prompt: str) method to update the system_prompt variable
   - Implement clear_tools(self) method to reset self.tools and self.tool_handlers
   - Modify stream_assistant_response to use self.system_prompt instead of hardcoded prompt

4. UPDATE modules/groq/service.py:
   - Add a system_prompt instance variable in __init__ method, initialized with CHAT_SYSTEM_PROMPT
   - Implement set_system_prompt(self, system_prompt: str) method to update the system_prompt variable
   - Implement clear_tools(self) method to reset self.tools and self.tool_handlers
   - Modify stream_assistant_response to use self.system_prompt instead of hardcoded prompt

5. UPDATE modules/agents/manager.py:
   - Modify select_agent(self, agent_name: str) method to:
     - Clear tools from the previous agent's LLM service if there was a previous agent
     - Update the LLM service with the new agent's system prompt via set_system_prompt
     - Re-register the agent's tools with the LLM service

