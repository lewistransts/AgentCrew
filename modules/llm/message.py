from typing import Dict, List, Any, Optional, Union
import json


class MessageTransformer:
    """Utility for transforming messages between different provider formats."""

    @staticmethod
    def standardize_messages(
        messages: List[Dict[str, Any]], source_provider: str
    ) -> List[Dict[str, Any]]:
        """
        Convert provider-specific messages to a standard format.

        Args:
            messages: The messages to standardize
            source_provider: The provider the messages are from

        Returns:
            Standardized messages
        """
        if source_provider == "claude":
            return MessageTransformer._standardize_claude_messages(messages)
        elif source_provider == "openai":
            return MessageTransformer._standardize_openai_messages(messages)
        elif source_provider == "groq":
            return MessageTransformer._standardize_groq_messages(messages)
        return messages

    @staticmethod
    def convert_messages(
        messages: List[Dict[str, Any]], target_provider: str
    ) -> List[Dict[str, Any]]:
        """
        Convert standardized messages to provider-specific format.

        Args:
            messages: The standardized messages to convert
            target_provider: The provider to convert to

        Returns:
            Provider-specific messages
        """
        if target_provider == "claude":
            return MessageTransformer._convert_to_claude_format(messages)
        elif target_provider == "openai":
            return MessageTransformer._convert_to_openai_format(messages)
        elif target_provider == "groq":
            return MessageTransformer._convert_to_groq_format(messages)
        return messages

    @staticmethod
    def _standardize_claude_messages(
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Convert Claude-specific messages to standard format."""
        standardized = []
        for msg in messages:
            std_msg = {"role": msg.get("role", "")}

            # Handle content based on type
            content = msg.get("content", [])
            if isinstance(content, str):
                std_msg["content"] = content
            elif isinstance(content, list):
                # For Claude's content array, extract text and other content
                text_parts = []
                tool_calls = []

                for item in content:
                    # Check if item is a dictionary or an object
                    if isinstance(item, dict):
                        # Handle dictionary-style items
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "tool_use":
                            tool_calls.append(
                                {
                                    "id": item.get("id", ""),
                                    "name": item.get("name", ""),
                                    "arguments": item.get("input", {}),
                                    "type": "function",
                                }
                            )
                        elif (
                            item.get("type") == "tool_result"
                            and msg.get("role") == "user"
                        ):
                            std_msg["tool_result"] = {
                                "tool_use_id": item.get("tool_use_id", ""),
                                "content": item.get("content", ""),
                                "is_error": item.get("is_error", False),
                            }
                    else:
                        # Handle object-style items
                        item_type = getattr(item, "type", None)
                        if item_type == "text":
                            text_parts.append(getattr(item, "text", ""))
                        elif item_type == "tool_use":
                            tool_calls.append(
                                {
                                    "id": getattr(item, "id", ""),
                                    "name": getattr(item, "name", ""),
                                    "arguments": getattr(item, "input", {}),
                                    "type": "function",
                                }
                            )
                        elif item_type == "tool_result" and msg.get("role") == "user":
                            std_msg["tool_result"] = {
                                "tool_use_id": getattr(item, "tool_use_id", ""),
                                "content": getattr(item, "content", ""),
                                "is_error": getattr(item, "is_error", False),
                            }

                if text_parts:
                    std_msg["content"] = "\n".join(text_parts)
                else:
                    std_msg["content"] = ""

                # Add tool calls if present
                if tool_calls:
                    std_msg["tool_calls"] = tool_calls

            standardized.append(std_msg)
        return standardized

    @staticmethod
    def _standardize_openai_messages(
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Convert OpenAI-specific messages to standard format."""
        standardized = []
        for msg in messages:
            std_msg = {"role": msg.get("role", "")}

            # Handle content
            if "content" in msg:
                std_msg["content"] = msg["content"]

            # Handle tool calls
            if "tool_calls" in msg:
                std_msg["tool_calls"] = []
                for tool_call in msg["tool_calls"]:
                    std_tool_call = {
                        "id": tool_call.get("id"),
                        "name": tool_call.get("function", {}).get("name"),
                        "arguments": json.loads(
                            tool_call.get("function", {}).get("arguments")
                        ),
                        "type": tool_call.get("type", "function"),
                    }
                    std_msg["tool_calls"].append(std_tool_call)

            # Handle tool results
            if msg.get("role") == "tool":
                std_msg["tool_result"] = {
                    "tool_use_id": msg.get("tool_call_id"),
                    "content": msg.get("content"),
                    "is_error": msg.get("content", "").startswith("ERROR:"),
                }

            standardized.append(std_msg)
        return standardized

    @staticmethod
    def _standardize_groq_messages(
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Convert Groq-specific messages to standard format."""
        # Groq uses OpenAI format, so we can reuse that
        return MessageTransformer._standardize_openai_messages(messages)

    @staticmethod
    def _convert_to_claude_format(
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Convert standard messages to Claude format."""
        claude_messages = []
        for msg in messages:
            claude_msg = {"role": msg.get("role", "")}
            if claude_msg["role"] == "tool":
                claude_msg["role"] = "user"
            # Handle content
            if "content" in msg:
                if msg.get("role") == "assistant" and "tool_calls" in msg:
                    # For assistant messages with tool calls, we need to format differently
                    # Fix issue with empty content
                    if msg["content"] == "":
                        msg["content"] = " "
                    claude_msg["content"] = [{"type": "text", "text": msg["content"]}]

                    # Add tool use blocks
                    for tool_call in msg.get("tool_calls", []):
                        tool_use = {
                            "type": "tool_use",
                            "id": tool_call.get("id", ""),
                            "name": tool_call.get("name", ""),
                            "input": tool_call.get("arguments", {}),
                        }
                        claude_msg["content"].append(tool_use)
                else:
                    # Regular content
                    claude_msg["content"] = [{"type": "text", "text": msg["content"]}]

            # Handle tool results
            if "tool_result" in msg:
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": msg["tool_result"].get("tool_use_id", ""),
                    "content": msg["tool_result"].get("content", ""),
                }

                if msg["tool_result"].get("is_error", False):
                    tool_result["is_error"] = True

                claude_msg["content"] = [tool_result]

            claude_messages.append(claude_msg)
        return claude_messages

    @staticmethod
    def _convert_to_openai_format(
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Convert standard messages to OpenAI format."""
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.get("role", "")}

            # Handle content
            if "content" in msg:
                openai_msg["content"] = msg["content"]

            # Handle tool calls
            if "tool_calls" in msg:
                openai_msg["tool_calls"] = []
                for tool_call in msg.get("tool_calls", []):
                    # Convert arguments to JSON string if it's not already a string
                    arguments = tool_call.get("arguments", {})
                    if not isinstance(arguments, str):
                        arguments = json.dumps(arguments)

                    openai_msg["tool_calls"].append(
                        {
                            "id": tool_call.get("id", ""),
                            "type": tool_call.get("type", "function"),
                            "function": {
                                "name": tool_call.get("name", ""),
                                "arguments": arguments,
                            },
                        }
                    )

            # Handle tool results
            if "tool_result" in msg:
                openai_msg["role"] = "tool"
                openai_msg["tool_call_id"] = msg["tool_result"].get("tool_use_id", "")
                openai_msg["content"] = msg["tool_result"].get("content", "")

                if msg["tool_result"].get("is_error", False):
                    openai_msg["content"] = f"ERROR: {openai_msg['content']}"

            openai_messages.append(openai_msg)
        return openai_messages

    @staticmethod
    def _convert_to_groq_format(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert standard messages to Groq format."""
        # Groq uses OpenAI format, so we can reuse that
        return MessageTransformer._convert_to_openai_format(messages)
