from typing import Dict, Any, Generator, List, Optional, Tuple
from uuid import uuid4
import time

from pydantic import ValidationError
from swissknife.modules.a2a.adapters import (
    convert_swissknife_message_to_a2a,
    convert_a2a_send_task_response_to_swissknife_message,
)
from swissknife.modules.llm.message import MessageTransformer
from swissknife.modules.agents.base import BaseAgent, MessageType
from common.client import A2ACardResolver, A2AClient
from common.types import TaskSendParams, SendTaskResponse, TaskState
import asyncio


class RemoteAgent(BaseAgent):
    def __init__(self, name: str, agent_url: str):
        self.card_resolver = A2ACardResolver(agent_url)
        self.agent_card = self.card_resolver.get_agent_card()
        self.client = A2AClient(self.agent_card, timeout=600)
        self.name = name
        self.description = self.agent_card.description
        self.history = []
        self.shared_context_pool: Dict[str, List[int]] = {}

    def activate(self) -> bool:
        """
        Activate this agent by registering all tools with the LLM service.

        Returns:
            True if activation was successful, False otherwise
        """
        return True

    def deactivate(self) -> bool:
        """
        Deactivate this agent by clearing all tools from the LLM service.

        Returns:
            True if deactivation was successful, False otherwise
        """
        return True

    @property
    def std_history(self):
        return MessageTransformer.standardize_messages(
            self.history, "a2a_remote", self.name
        )

    def get_provider(self) -> str:
        return (
            self.agent_card.provider.organization
            if self.agent_card.provider
            else "a2a_remote"
        )

    def get_model(self) -> str:
        return self.get_provider() + "-" + self.agent_card.version

    def is_streaming(self) -> bool:
        return False

    def format_message(
        self, message_type: MessageType, message_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if message_type == MessageType.Assistant:
            return {
                "role": "assistant",
                "content": [{"type": "text", "text": message_data.get("message", "")}],
            }
        elif message_type == MessageType.Thinking:
            return None
        elif message_type == MessageType.ToolResult:
            return {
                "role": "tool",
                "tool_call_id": message_data.get("tool_use", {"id": ""})["id"],
                "content": message_data.get("tool_result", ""),
            }
        elif message_type == MessageType.FileContent:
            return None

    def execute_tool_call(self, tool_name: str, tool_input: Dict) -> Any:
        return None

    def configure_think(self, think_setting):
        pass

    def calculate_usage_cost(self, input_tokens, output_tokens) -> float:
        return 0.0

    def process_messages(self, messages: Optional[List[Dict[str, Any]]] = None):
        if not self.client or not self.agent_card:
            raise ValidationError(
                f"RemoteAgent '{self.name}' not properly initialized."
            )
        if not messages:
            messages = self.history

        last_user_message = messages[-1]

        a2a_message = convert_swissknife_message_to_a2a(last_user_message)

        a2a_payload: TaskSendParams = TaskSendParams(
            id=str(uuid4()),
            message=a2a_message,
        )
        response_data = asyncio.run(self.client.send_task(a2a_payload.model_dump()))
        while response_data.result and response_data.result.status.state not in [
            TaskState.COMPLETED,
            TaskState.INPUT_REQUIRED,
            TaskState.CANCELED,
            TaskState.FAILED,
        ]:
            time.sleep(1)
            response_data = asyncio.run(self.client.get_task({"id": a2a_payload.id}))
            print(response_data)

        assistant_message = convert_a2a_send_task_response_to_swissknife_message(
            response_data, self.name
        )
        print(assistant_message)
        if assistant_message:
            yield (assistant_message, assistant_message, None)
        else:
            raise AttributeError("Failed to parse response from remote agent.")

    def get_process_result(self) -> Tuple:
        return ([], 0, 0)
