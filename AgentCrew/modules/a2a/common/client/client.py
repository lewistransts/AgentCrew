import json

from collections.abc import AsyncIterable
from typing import Any, Optional
from uuid import uuid4

import httpx

from httpx._types import TimeoutTypes
from httpx_sse import aconnect_sse

from AgentCrew.modules.a2a.common.types import (
    A2AClientHTTPError,
    A2AClientJSONError,
    A2ARequest,
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigResponse,
    GetTaskRequest,
    GetTaskResponse,
    TaskQueryParams,
    SendMessageRequest,
    SendMessageResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SetTaskPushNotificationConfigRequest,
    SetTaskPushNotificationConfigResponse,
    TaskIdParams,
    MessageSendParams,
    Message,
    TextPart,
    Part,
    Role,
)


class A2AClient:
    def __init__(
        self,
        agent_card: AgentCard,
        url: Optional[str] = None,
        timeout: TimeoutTypes = 60.0,
    ):
        if agent_card:
            self.url = agent_card.url
        ##Override URL if provided
        elif url:
            self.url = url
        else:
            raise ValueError("Must provide either agent_card or url")
        self.timeout = timeout

    async def send_message(self, payload: MessageSendParams) -> SendMessageResponse:
        """Send a message using the new A2A v0.2 message/send method"""
        request = SendMessageRequest(id=str(uuid4()), params=payload)
        result = await self._send_request(A2ARequest(root=request))
        return SendMessageResponse.model_validate(result)

    async def send_message_streaming(
        self, payload: MessageSendParams
    ) -> AsyncIterable[SendStreamingMessageResponse]:
        """Send a streaming message using the new A2A v0.2 message/stream method"""
        request = SendStreamingMessageRequest(id=str(uuid4()), params=payload)
        async with httpx.AsyncClient(timeout=None) as client:
            async with aconnect_sse(
                client, "POST", self.url, json=request.model_dump()
            ) as event_source:
                try:
                    async for sse in event_source.aiter_sse():
                        yield SendStreamingMessageResponse.model_validate(
                            json.loads(sse.data)
                        )
                except json.JSONDecodeError as e:
                    raise A2AClientJSONError(str(e)) from e
                except httpx.RequestError as e:
                    raise A2AClientHTTPError(400, str(e)) from e

    async def _send_request(self, request: A2ARequest) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                # Image generation could take time, adding timeout
                response = await client.post(
                    self.url, json=request.root.model_dump(), timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e

    async def get_task(self, payload: TaskQueryParams) -> GetTaskResponse:
        request = GetTaskRequest(id=str(uuid4()), params=payload)
        result = await self._send_request(A2ARequest(root=request))
        return GetTaskResponse.model_validate(result)

    async def cancel_task(self, payload: TaskIdParams) -> CancelTaskResponse:
        request = CancelTaskRequest(id=str(uuid4()), params=payload)
        result = await self._send_request(A2ARequest(root=request))
        return CancelTaskResponse.model_validate(result)

    async def set_task_push_notification_config(
        self, payload: dict[str, Any]
    ) -> SetTaskPushNotificationConfigResponse:
        request = SetTaskPushNotificationConfigRequest(params=payload)
        result = await self._send_request(request)
        return SetTaskPushNotificationConfigResponse.model_validate(result)

    async def get_task_push_notification_config(
        self, payload: dict[str, Any]
    ) -> GetTaskPushNotificationConfigResponse:
        request = GetTaskPushNotificationConfigRequest(params=payload)
        result = await self._send_request(request)
        return GetTaskPushNotificationConfigResponse.model_validate(result)

    # Legacy methods for backward compatibility
    async def send_task(self, payload: dict[str, Any]) -> SendMessageResponse:
        """Legacy method - converts old format to new message format"""
        # Convert old payload to new MessageSendParams format
        message_params = self._convert_task_payload_to_message_params(payload)
        return await self.send_message(message_params)

    async def send_task_streaming(
        self, payload: dict[str, Any]
    ) -> AsyncIterable[SendStreamingMessageResponse]:
        """Legacy method - converts old format to new message format"""
        # Convert old payload to new MessageSendParams format
        message_params = self._convert_task_payload_to_message_params(payload)
        async for response in self.send_message_streaming(message_params):
            yield response

    async def set_task_callback(
        self, payload: dict[str, Any]
    ) -> SetTaskPushNotificationConfigResponse:
        """Legacy method - alias for set_task_push_notification_config"""
        return await self.set_task_push_notification_config(payload)

    async def get_task_callback(
        self, payload: dict[str, Any]
    ) -> GetTaskPushNotificationConfigResponse:
        """Legacy method - alias for get_task_push_notification_config"""
        return await self.get_task_push_notification_config(payload)

    def _convert_task_payload_to_message_params(
        self, payload: dict[str, Any]
    ) -> MessageSendParams:
        """Convert old task payload format to new message format"""
        # This is a basic conversion - you may need to adjust based on your actual payload structure
        message = payload.get("message", {})
        print(payload)
        print("===========")
        print(message.get("messageId"))

        message = Message(
            messageId=message.get("messageId", str(uuid4())),
            role=Role.user,
            parts=message.get("parts", []),
            contextId=payload.get("contextId"),
            taskId=payload.get("taskId"),
        )

        return MessageSendParams(
            message=message,
            configuration=payload.get("configuration"),
            metadata=payload.get("metadata"),
        )
