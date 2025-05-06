"""
Adapters for converting between SwissKnife and A2A message formats.
"""

import base64
from typing import Dict, Any, List, Optional
from common.types import (
    GetTaskResponse,
    Message,
    TextPart,
    FilePart,
    FileContent,
    Artifact,
    Part,
    SendTaskResponse,
    SendTaskStreamingResponse,
)


# TODO: cover all of cases for images
def convert_a2a_message_to_swissknife(message: Message) -> Dict[str, Any]:
    """
    Convert an A2A message to SwissKnife format.

    Args:
        message: The A2A message to convert

    Returns:
        The message in SwissKnife format
    """
    role = "user" if message.role == "user" else "assistant"
    content = []

    for part in message.parts:
        if part.type == "text":
            content.append({"type": "text", "text": part.text})
        elif part.type == "file":
            # Handle file content
            if part.file.bytes:
                # Base64 encoded file
                content.append(
                    {
                        "type": "file",
                        "file_data": part.file.bytes,
                        "file_name": part.file.name or "file",
                        "mime_type": part.file.mimeType or "application/octet-stream",
                    }
                )
            elif part.file.uri:
                # File URI
                content.append(
                    {
                        "type": "file_uri",
                        "uri": part.file.uri,
                        "file_name": part.file.name or "file",
                        "mime_type": part.file.mimeType or "application/octet-stream",
                    }
                )
        elif part.type == "data":
            # Convert structured data
            content.append({"type": "data", "data": part.data})

    return {"role": role, "content": content}


# TODO: cover all of cases for images
def convert_swissknife_message_to_a2a(message: Dict[str, Any]) -> Message:
    """
    Convert a SwissKnife message to A2A format.

    Args:
        message: The SwissKnife message to convert

    Returns:
        The message in A2A format
    """
    role = "user" if message.get("role") == "user" else "agent"
    parts = []

    content = message.get("content", [])
    if isinstance(content, str):
        # Handle string content (common in some providers)
        parts.append(TextPart(text=content))
    else:
        # Handle list of content parts
        for part in content:
            if isinstance(part, str):
                parts.append(TextPart(text=part))
            elif isinstance(part, dict):
                if part.get("type") == "text":
                    parts.append(TextPart(text=part.get("text", "")))
                elif part.get("type") == "file":
                    # Handle file content
                    parts.append(
                        FilePart(
                            file=FileContent(
                                name=part.get("file_name"),
                                mimeType=part.get("mime_type"),
                                bytes=part.get("file_data"),
                            )
                        )
                    )
                elif part.get("type") == "file_uri":
                    # Handle file URI
                    parts.append(
                        FilePart(
                            file=FileContent(
                                name=part.get("file_name"),
                                mimeType=part.get("mime_type"),
                                uri=part.get("uri"),
                            )
                        )
                    )
                elif part.get("type") == "data":
                    # Handle structured data
                    from common.types import DataPart

                    parts.append(DataPart(data=part.get("data", {})))

    return Message(role=role, parts=parts, metadata=message.get("metadata"))


def convert_swissknife_response_to_a2a(
    response: str, tool_uses: Optional[List[Dict[str, Any]]] = None
) -> Artifact:
    """
    Convert a SwissKnife response to an A2A artifact.

    Args:
        response: The response text from SwissKnife
        tool_uses: Optional list of tool uses

    Returns:
        The response as an A2A artifact
    """
    parts = [TextPart(text=response)]

    # If there were tool uses, we could add them as metadata
    metadata = None
    if tool_uses:
        metadata = {"tool_uses": tool_uses}

    return Artifact(parts=parts, metadata=metadata)


def convert_file_to_a2a_part(
    file_path: str, file_content: bytes, mime_type: Optional[str] = None
) -> Part:
    """
    Convert a file to an A2A part.

    Args:
        file_path: The path to the file
        file_content: The content of the file
        mime_type: Optional MIME type

    Returns:
        The file as an A2A part
    """
    import os
    import mimetypes

    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

    file_name = os.path.basename(file_path)

    # Encode file content as base64
    base64_content = base64.b64encode(file_content).decode("utf-8")

    return FilePart(
        file=FileContent(name=file_name, mimeType=mime_type, bytes=base64_content)
    )


def convert_a2a_send_task_response_to_swissknife_message(
    response: SendTaskResponse | GetTaskResponse, agent_name: str
) -> Optional[str]:
    if not response or not response.result or not response.result.artifacts:
        return None
    assistant_a2a_message = response.result.artifacts[-1]
    content_parts = []
    for part in assistant_a2a_message.parts:
        if part.type == "text":
            content_parts.append(part.text)
    return "\n".join(content_parts)
