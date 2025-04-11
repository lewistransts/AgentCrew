from typing import Dict, Any, Callable


def get_transfer_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Get the definition for the transfer tool.

    Args:
        provider: The LLM provider (claude, openai, groq)

    Returns:
        The tool definition
    """
    if provider == "claude":
        return {
            "name": "transfer",
            "description": "transfer to a specialized agent when the current task requires expertise beyond the current agent's capabilities. Provide a clear explanation to the user why the transfer is necessary.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "target_agent": {
                        "type": "string",
                        "description": "The name of the specialized agent to transfer to. Refer to the ## Agents for list of available agents",
                    },
                    "task": {
                        "type": "string",
                        "description": "A precise description of the task the target agent should perform. This description MUST include the triggering keywords that prompted the transfer. Be specific and actionable.",
                    },
                    "report_back": {
                        "type": "boolean",
                        "default": "false",
                        "description": "Indicated task need to transfer back to original Agent for further processing",
                    },
                    "context_summary": {
                        "type": "string",
                        "description": "A concise summary of the relevant conversation history and current state, providing essential background information for the target agent. Include key decisions, user intent, and unresolved issues.",
                    },
                },
                "required": ["target_agent", "task", "report_back"],
            },
        }
    else:
        return {
            "type": "function",
            "function": {
                "name": "transfer",
                "description": "transfer to a specialized agent when the current task requires expertise beyond the current agent's capabilities. Provide a clear explanation to the user why the transfer is necessary.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_agent": {
                            "type": "string",
                            "description": "The name of the specialized agent to transfer to. Refer to the ## Agents for list of available agents",
                        },
                        "task": {
                            "type": "string",
                            "description": "A precise description of the task the target agent should perform. This description MUST include the triggering keywords that prompted the transfer. Be specific and actionable.",
                        },
                        "report_back": {
                            "type": "boolean",
                            "default": "false",
                            "description": "Indicated task need to transfer back to original Agent for any further processing",
                        },
                        "context_summary": {
                            "type": "string",
                            "description": "A concise summary of the relevant conversation history and current state, providing essential background information for the target agent. Include key decisions, user intent, and unresolved issues.",
                        },
                    },
                    "required": ["target_agent", "task", "report_back"],
                },
            },
        }


def get_transfer_tool_handler(agent_manager) -> Callable:
    """
    Get the handler function for the transfer tool.

    Args:
        agent_manager: The agent manager instance

    Returns:
        The handler function
    """

    def handler(**params) -> str:
        """
        Handle a transfer request.

        Args:
            target_agent: The name of the agent to transfer to
            reason: The reason for the transfer
            context_summary: Optional summary of the conversation context

        Returns:
            A string describing the result of the transfer
        """
        target_agent = params.get("target_agent")
        task = params.get("task")
        context_summary = params.get("context_summary", "")
        report_back = params.get("report_back", True)

        if not target_agent:
            return "Error: No target agent specified"

        if not task:
            return "Error: No task specified for the transfer"

        result = agent_manager.perform_transfer(target_agent, task, context_summary)
        if target_agent == "None":
            return "Error: Task is completed. This transfer is invalid"

        if result["success"]:
            if (
                report_back
                and "transfer" in result
                and result["transfer"]["from"] != "None"
            ):
                return f"You are now {target_agent}. Start {task}. transfer back to {result['transfer']['from']} for further processing. Here is the summary: {context_summary}"
            else:
                return f"You are now {target_agent}. Start {task}. Here is the summary: {context_summary}"
        else:
            available_agents = ", ".join(result.get("available_agents", []))
            return f"Error: {result.get('error')}. Available agents: {available_agents}"

    return handler


def register(agent_manager, agent=None):
    """
    Register the transfer tool with all agents or a specific agent.

    Args:
        agent_manager: The agent manager instance
        agent: Specific agent to register with (optional)
    """

    # Create the tool definition and handler

    from swissknife.modules.tools.registration import register_tool

    register_tool(
        get_transfer_tool_definition, get_transfer_tool_handler, agent_manager, agent
    )
