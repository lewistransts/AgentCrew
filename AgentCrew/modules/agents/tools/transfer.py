from typing import Dict, Any, Callable

from AgentCrew.modules.agents import AgentManager


def get_transfer_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Get the definition for the transfer tool.

    Args:
        provider: The LLM provider (claude, openai, groq)

    Returns:
        The tool definition
    """
    tool_description = "Transfers the current task to a specialized agent when the user's request requires expertise or capabilities beyond your current abilities. This ensures the user receives the most accurate and efficient assistance. YOU MUST provide essential context from the current conversation, as the target agent does NOT have access to the prior history. Always explain the reason for the transfer to the user before invoking this tool"
    tool_arguments = {
        "target_agent": {
            "type": "string",
            "description": "The unique identifier or name of the specialized agent to transfer the task to. Refer to the official <Available_Agents_List> tags for available specialist agents and their capabilities.",
        },
        "task_description": {
            "type": "string",
            "description": "A precise, actionable description of the task for the target agent. This MUST clearly state what the target agent needs to achieve and SHOULD include any triggering keywords or phrases from the user that initiated the need for transfer. Think of this as the 'mission objective' for the other agent.",
        },
        "included_context": {
            "type": "array",
            "items": {"type": "string"},
            "description": "An array of verbatim quoted strings from the conversation history (user messages, your responses, previous tool outputs). This is VITAL as the target agent has NO prior conversation history. Select only essential snippets that are absolutely necessary for the target agent to understand the task, the history of the request, and complete the task accurately. Prioritize: 1. Important information you (the current agent) have already provided or discovered. 2. Any relevant previous tool outputs. 3. The user's original request/question. 4. Key clarifications or constraints provided by the user. Avoid including irrelevant chitchat. Be concise but comprehensive.",
        },
        "post_action": {
            "type": "string",
            "description": "Defines the expected next action for the target agent after it has completed its assigned task. For example: 'report back to \"requestor agent\" about the task', 'ask user for the next phase', 'transfer it to other agent to continue the task', etc...",
        },
    }

    tool_required = ["target_agent", "task_description", "included_context"]
    if provider == "claude":
        return {
            "name": "transfer",
            "description": tool_description,
            "input_schema": {
                "type": "object",
                "properties": tool_arguments,
                "required": tool_required,
            },
        }
    else:
        return {
            "type": "function",
            "function": {
                "name": "transfer",
                "description": tool_description,
                "parameters": {
                    "type": "object",
                    "properties": tool_arguments,
                    "required": tool_required,
                },
            },
        }


def get_transfer_tool_handler(agent_manager: AgentManager) -> Callable:
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
        task = params.get("task_description")
        included_context = params.get("included_context", [])
        post_action = params.get("post_action", "")

        if not target_agent:
            raise ValueError("Error: No target agent specified")

        if not task:
            raise ValueError("Error: No task specified for the transfer")

        if target_agent == agent_manager.current_agent.name:
            raise ValueError("Error: Cannot transfer to same agent")

        result = agent_manager.perform_transfer(target_agent, task)
        if target_agent == "None":
            raise ValueError("Error: Task is completed. This transfer is invalid")

        response = ""

        if result["success"] and result["transfer"]["from"] != "None":
            response = f"## Task from {result['transfer']['from']} via `transfer` tool: {task}  \n"

            response += (
                f"> Disclaimer: I only delegate task from {result['transfer']['from']}."
                "If you need more context or asking question, use `transfer` tool  \n"
            )

            if included_context:
                response += f"\n## Shared Context:  \n{'\n\n'.join(included_context)}"

            if post_action:
                response += f"\n## When task is completed: {post_action}"

            return response

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

    from AgentCrew.modules.tools.registration import register_tool

    register_tool(
        get_transfer_tool_definition, get_transfer_tool_handler, agent_manager, agent
    )
