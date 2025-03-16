# Updating Remaining Tool Modules

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives
- Update all remaining tool modules to support agent-specific registration
- Ensure consistent agent parameter handling across all tool modules
- Maintain backward compatibility with the global ToolRegistry
- Standardize error handling for tool registration across modules

## Contexts
- modules/code_analysis/tool.py: Code analysis tools
- modules/coder/tool.py: Specification validation and implementation tools
- modules/web_search/tool.py: Web search and extraction tools
- modules/scraping/tool.py: Web content scraping tools
- modules/mcpclient/tool.py: MCP client connection tools
- modules/agents/tools/handoff.py: Agent handoff tools
- modules/memory/tool.py: Memory retrieval and management tools

## Low-level Tasks
1. UPDATE modules/code_analysis/tool.py:
   - Modify register function to accept agent parameter
   - Update tool registration to support agent-specific registration
   - Maintain backward compatibility with global registry

2. UPDATE modules/coder/tool.py:
   - Add agent parameter to register function
   - Adapt spec validation and implementation tools for agent-specific registration
   - Ensure proper service instance handling

3. UPDATE modules/web_search/tool.py:
   - Update register function with agent parameter support
   - Modify web search and extract tool registration for agents
   - Maintain backward compatibility

4. UPDATE modules/scraping/tool.py:
   - Add agent-specific registration to scraping tools
   - Update register function signature and implementation
   - Ensure proper error handling

5. UPDATE modules/mcpclient/tool.py:
   - Modify MCP client tools for agent-specific registration
   - Update connect, list, and call tool registration
   - Ensure backward compatibility

6. UPDATE modules/agents/tools/handoff.py:
   - Adapt handoff tool to support agent-specific registration
   - Update register function to accept agent parameter
   - Ensure proper agent_manager handling

7. UPDATE modules/memory/tool.py:
   - Modify memory tools to support agent registration
   - Update retrieve and forget tool registration
   - Ensure backward compatibility
