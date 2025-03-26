from typing import Dict, Any, Callable


def get_handoff_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Get the definition for the handoff tool.

    Args:
        provider: The LLM provider (claude, openai, groq)

    Returns:
        The tool definition
    """
    if provider == "claude":
        return {
            "name": "handoff",
            "description": "Transfers the conversation to a specialized agent when the current task requires expertise beyond the current agent's capabilities. ALWAYS check for handoff triggers BEFORE responding to the user. Provide a clear explanation to the user why the handoff is necessary.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "target_agent": {
                        "type": "string",
                        "description": "The name of the specialized agent to hand off the conversation to.  Refer to the agent registry for available agents and their specific expertise.",
                    },
                    "task": {
                        "type": "string",
                        "description": "A precise description of the task the target agent should perform. This description MUST include the triggering keywords that prompted the handoff. Be specific and actionable.",
                    },
                    "context_summary": {
                        "type": "string",
                        "description": "A concise summary of the relevant conversation history and current state, providing essential background information for the target agent. Include key decisions, user intent, and unresolved issues.",
                    },
                },
                "required": ["target_agent", "task"],
            },
        }
    else:
        return {
            "type": "function",
            "function": {
                "name": "handoff",
                "description": "Transfers the conversation to a specialized agent when the current task requires expertise beyond the current agent's capabilities. ALWAYS check for handoff triggers BEFORE responding to the user. Provide a clear explanation to the user why the handoff is necessary.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_agent": {
                            "type": "string",
                            "description": "The name of the specialized agent to hand off the conversation to.  Refer to the agent registry for available agents and their specific expertise.",
                        },
                        "task": {
                            "type": "string",
                            "description": "A precise description of the task the target agent should perform. This description MUST include the triggering keywords that prompted the handoff. Be specific and actionable.",
                        },
                        "context_summary": {
                            "type": "string",
                            "description": "A concise summary of the relevant conversation history and current state, providing essential background information for the target agent. Include key decisions, user intent, and unresolved issues.",
                        },
                    },
                    "required": ["target_agent", "task"],
                },
            },
        }


def get_handoff_tool_handler(agent_manager) -> Callable:
    """
    Get the handler function for the handoff tool.

    Args:
        agent_manager: The agent manager instance

    Returns:
        The handler function
    """

    def handler(**params) -> str:
        """
        Handle a handoff request.

        Args:
            target_agent: The name of the agent to hand off to
            reason: The reason for the handoff
            context_summary: Optional summary of the conversation context

        Returns:
            A string describing the result of the handoff
        """
        target_agent = params.get("target_agent")
        task = params.get("task")
        context_summary = params.get("context_summary", "")

        if not target_agent:
            return "Error: No target agent specified"

        if not task:
            return "Error: No task specified for the handoff"

        result = agent_manager.perform_handoff(target_agent, task, context_summary)

        if result["success"]:
            return f"You are now {target_agent}. Continue to {task}. Here is the summary: {context_summary}"
        else:
            available_agents = ", ".join(result.get("available_agents", []))
            return f"Error: {result.get('error')}. Available agents: {available_agents}"

    return handler


def register(agent_manager, agent=None):
    """
    Register the handoff tool with all agents or a specific agent.

    Args:
        agent_manager: The agent manager instance
        agent: Specific agent to register with (optional)
    """

    # Create the tool definition and handler

    from swissknife.modules.tools.registration import register_tool

    register_tool(
        get_handoff_tool_definition, get_handoff_tool_handler, agent_manager, agent
    )
