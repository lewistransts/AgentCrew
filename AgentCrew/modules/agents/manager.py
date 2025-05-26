import toml
import json
from typing import Dict, Any, Optional, List

from AgentCrew.modules.agents import BaseAgent, LocalAgent
from AgentCrew.modules.llm.message import MessageTransformer


class AgentManager:
    """Manager for specialized agents."""

    _instance = None

    def __new__(cls):
        """Ensure only one instance is created (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @staticmethod
    def load_agents_from_config(config_path: str) -> list:
        """
        Load agent definitions from a TOML or JSON configuration file.

        Args:
            config_path: Path to the configuration file.

        Returns:
            List of agent dictionaries.
        """
        try:
            if config_path.endswith(".toml"):
                with open(config_path, "r") as file:
                    config = toml.load(file)
            elif config_path.endswith(".json"):
                with open(config_path, "r") as file:
                    config = json.load(file)
            else:
                raise ValueError(
                    "Unsupported configuration file format. Use TOML or JSON."
                )
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except (toml.TomlDecodeError, json.JSONDecodeError):
            raise ValueError("Invalid configuration file format.")

        return config.get("agents", []) + config.get("remote_agents", [])

    def __init__(self):
        """Initialize the agent manager."""
        if not self._initialized:
            self.agents: Dict[str, BaseAgent] = {}
            self.current_agent: Optional[BaseAgent] = None
            self.transfer_history = []
            self._initialized = True

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of AgentManager."""
        if cls._instance is None:
            cls._instance = AgentManager()
        return cls._instance

    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the manager.

        Args:
            agent: The agent to register
        """
        self.agents[agent.name] = agent

    def deregister_agent(self, agent_name: str):
        """
        Register an agent with the manager.

        Args:
            agent: The agent to register
        """
        del self.agents[agent_name]

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

            # If there was a previous agent, deactivate it
            if self.current_agent:
                self.current_agent.deactivate()

            # Set the new agent as current
            self.current_agent = new_agent

            if self.current_agent and isinstance(self.current_agent, LocalAgent):
                if not self.current_agent.custom_system_prompt:
                    self.current_agent.set_custom_system_prompt(
                        self.get_transfer_system_prompt()
                    )
            # Activate the new agent
            if self.current_agent:
                self.current_agent.activate()

            return True
        return False

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.

        Args:
            agent_name: The name of the agent to get

        Returns:
            The agent, or None if not found
        """
        return self.agents.get(agent_name)

    def get_local_agent(self, agent_name) -> Optional[LocalAgent]:
        agent = self.agents.get(agent_name)
        if isinstance(agent, LocalAgent):
            return agent
        else:
            return None

    def clean_agents_messages(self):
        for _, agent in self.agents.items():
            agent.history = []
            agent.shared_context_pool = {}

    def rebuild_agents_messages(self, streamline_messages):
        self.clean_agents_messages()
        for _, agent in self.agents.items():
            agent.history = MessageTransformer.convert_messages(
                [
                    msg
                    for msg in streamline_messages
                    if msg.get("agent", "") == agent.name
                ],
                agent.get_provider(),
            )

    def get_current_agent(self) -> BaseAgent:
        """
        Get the current agent.

        Returns:
            The current agent, or None if no agent is selected
        """
        if not self.current_agent:
            raise ValueError("Current agent is not set")
        return self.current_agent

    def perform_transfer(
        self, target_agent_name: str, task: str, relevant_messages: List[int]
    ) -> Dict[str, Any]:
        """
        Perform a transfer to another agent.

        Args:
            target_agent_name: The name of the agent to transfer to
            reason: The reason for the transfer
            context_summary: Optional summary of the conversation context

        Returns:
            A dictionary with the result of the transfer
        """
        if target_agent_name not in self.agents:
            raise ValueError(
                f"Agent '{target_agent_name}' not found. Available_agents: {list(self.agents.keys())}"
            )

        source_agent = self.current_agent

        relevant_data = []
        direct_injected_messages = []
        if source_agent:
            if target_agent_name not in source_agent.shared_context_pool:
                source_agent.shared_context_pool[target_agent_name] = []
            for i, msg in enumerate(source_agent.std_history):
                if (
                    i in relevant_messages
                    and i not in source_agent.shared_context_pool[target_agent_name]
                ):
                    if "content" in msg:
                        content = ""
                        processing_content = msg["content"]
                        if msg.get("role", "") == "tool":
                            processing_content = msg.get("tool_result", {}).get(
                                "content", ""
                            )
                        if isinstance(processing_content, str):
                            content = msg.get("content", "")
                        elif (
                            isinstance(processing_content, List)
                            and len(processing_content) > 0
                        ):
                            if "text" == processing_content[0].get("type", ""):
                                content = processing_content[0]["text"]
                            elif processing_content[0].get("type", "") == "image_url":
                                direct_injected_messages.append(msg)
                        if content.strip():
                            actor = (
                                msg.get("agent", "Assistant")
                                if msg["role"] == "assistant"
                                else msg.get("role", "")
                            )
                            relevant_data.append(
                                f"----Message from {actor}----\n{content}\n----End message from {actor}----"
                            )
                    # Set the new current agent
                    source_agent.shared_context_pool[target_agent_name].append(i)

        # Record the transfer
        transfer_record = {
            "from": source_agent.name if source_agent else "None",
            "to": target_agent_name,
            "reason": task,
            "relevant_data": relevant_data,
        }
        # Set the new current agent
        self.select_agent(target_agent_name)
        if direct_injected_messages and self.current_agent:
            self.current_agent.history.extend(
                MessageTransformer.convert_messages(
                    direct_injected_messages, self.current_agent.get_provider()
                )
            )

        self.transfer_history.append(transfer_record)

        return {"success": True, "transfer": transfer_record}

    def update_llm_service(self, llm_service):
        """
        Update the LLM service for all agents.

        Args:
            llm_service: The new LLM service to use
        """
        if self.current_agent:
            # Deactivate the current agent
            self.current_agent.deactivate()

            if isinstance(self.current_agent, LocalAgent):
                # Update the LLM service for the current agent
                self.current_agent.update_llm_service(llm_service)

            # Reactivate the agent with the new LLM service
            self.current_agent.activate()

            # Update all other agents' LLM service but keep them deactivated
            for _, agent in self.agents.items():
                if agent != self.current_agent:
                    if isinstance(agent, LocalAgent):
                        agent.update_llm_service(llm_service)

    def get_transfer_system_prompt(self):
        """
        Generate a transfer section for the system prompt based on available agents.

        Returns:
            str: A formatted string containing transfer instructions and available agents
        """
        if not self.agents:
            return ""

        # Build agent descriptions
        agent_descriptions = []
        for name, agent in self.agents.items():
            if self.current_agent and name == self.current_agent.name:
                continue
            agent_desc = ""
            if hasattr(agent, "description") and agent.description:
                agent_desc = f"    <agent>\n      <name>{name}</name>\n      <description>{agent.description}</description>"
            else:
                agent_desc = f"    <agent>\n      <name>{name}</name>"
            if isinstance(agent, LocalAgent) and agent.tools and len(agent.tools) > 0:
                agent_desc += f"\n      <tools>\n        <tool>{'</tool>\n        <tool>'.join(agent.tools)}</tool>\n      </tools>\n    </agent>"
            else:
                agent_desc += "\n    </agent>"
            agent_descriptions.append(agent_desc)

        transfer_prompt = f"""<Agents>
  <transfer_rules>
    - When you encounter a task that falls outside your specialized expertise, you must transfer the conversation to a more appropriate agent from the available list. This ensures the user receives the most accurate and helpful assistance possible.
    - You're ONLY able to transfer to one agent at a time.
    - Define `post_action` in `transfer` tool's arguments whenever possible.
    - Each Agent has his own conversation history with user. use `relevant_messages` to share any messages matter to the task.
    - Use `relevant_messages` to provide message indices DIRECT related to the task from your conversation history.
    - To perform a transfer, use `transfer` tool with target_agent, task, relevant_messages arguments, include post_action whenever possible.
  </transfer_rules>
  <agent_lists>
{"\n".join(agent_descriptions)}
  </agent_lists>
</Agents>"""

        return transfer_prompt
