from typing import Dict, Any, List, Optional
from .base import Agent


class AgentManager:
    """Manager for specialized agents."""

    def __init__(self):
        """Initialize the agent manager."""
        self.agents = {}
        self.current_agent = None
        self.handoff_history = []

    def register_agent(self, agent: Agent):
        """
        Register an agent with the manager.

        Args:
            agent: The agent to register
        """
        self.agents[agent.name] = agent
        # Set the first registered agent as the default
        if not self.current_agent:
            self.select_agent(agent.name)

    def select_agent(self, agent_name: str) -> bool:
        """
        Select an agent by name.

        Args:
            agent_name: The name of the agent to select

        Returns:
            True if the agent was selected, False otherwise
        """
        if agent_name in self.agents:
            # Get the new agent
            new_agent = self.agents[agent_name]

            # If there was a previous agent, clear its tools from the LLM
            if self.current_agent:
                self.current_agent.clear_tools_from_llm()

            # Set the new agent as current
            self.current_agent = new_agent

            # Update the LLM service with the new agent's system prompt
            if self.current_agent.llm:
                # Set the system prompt
                system_prompt = self.current_agent.get_system_prompt()
                self.current_agent.llm.set_system_prompt(system_prompt)

                # Register the new agent's tools with the LLM
                self.current_agent.register_tools_with_llm()

            return True
        return False

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """
        Get an agent by name.

        Args:
            agent_name: The name of the agent to get

        Returns:
            The agent, or None if not found
        """
        return self.agents.get(agent_name)

    def get_current_agent(self) -> Optional[Agent]:
        """
        Get the current agent.

        Returns:
            The current agent, or None if no agent is selected
        """
        return self.current_agent

    def perform_handoff(
        self, target_agent_name: str, reason: str, context_summary: str = None
    ) -> Dict[str, Any]:
        """
        Perform a handoff to another agent.

        Args:
            target_agent_name: The name of the agent to hand off to
            reason: The reason for the handoff
            context_summary: Optional summary of the conversation context

        Returns:
            A dictionary with the result of the handoff
        """
        if target_agent_name not in self.agents:
            return {
                "success": False,
                "error": f"Agent '{target_agent_name}' not found",
                "available_agents": list(self.agents.keys()),
            }

        source_agent = self.current_agent
        target_agent = self.agents[target_agent_name]

        # Record the handoff
        handoff_record = {
            "from": source_agent.name if source_agent else "None",
            "to": target_agent.name,
            "reason": reason,
            "context_summary": context_summary,
        }
        self.handoff_history.append(handoff_record)

        # Set the new current agent
        self.current_agent = target_agent

        return {"success": True, "handoff": handoff_record}

    def route_message(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Route messages to the current agent.

        Args:
            messages: The messages to route

        Returns:
            The processed messages with the agent's system prompt
        """
        if not self.current_agent:
            raise ValueError("No agent selected")

        return self.current_agent.process_messages(messages)
