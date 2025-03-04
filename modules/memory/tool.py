from typing import Dict, Any, Callable
from .service import MemoryService


def get_memory_forget_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Get the tool definition for forgetting memories based on provider.

    Args:
        provider: The LLM provider ("claude" or "groq")

    Returns:
        Dict containing the tool definition
    """
    if provider == "claude":
        return {
            "name": "forget_memory_topic",
            "description": "Remove memories related to a specific topic from the conversation history",
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Keywords describing the topic to forget",
                    },
                },
                "required": ["topic"],
            },
        }
    else:  # provider == "groq"
        return {
            "type": "function",
            "function": {
                "name": "forget_memory_topic",
                "description": "Remove memories related to a specific topic from the conversation history",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Keywords describing the topic to forget",
                        },
                    },
                    "required": ["topic"],
                },
            },
        }


def get_memory_forget_tool_handler(memory_service: MemoryService) -> Callable:
    """
    Get the handler function for the memory forget tool.

    Args:
        memory_service: The memory service instance

    Returns:
        Function that handles memory forgetting requests
    """

    def handle_memory_forget(**params) -> str:
        topic = params.get("topic")

        if not topic:
            return "Error: Topic is required for forgetting memories."

        try:
            result = memory_service.forget_topic(topic)
            if result["success"]:
                return result["message"]
            else:
                return f"Unable to forget memories: {result['message']}"
        except Exception as e:
            return f"Error forgetting memories: {str(e)}"

    return handle_memory_forget


def get_memory_retrieve_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Get the tool definition for retrieving memories based on provider.

    Args:
        provider: The LLM provider ("claude" or "groq")

    Returns:
        Dict containing the tool definition
    """
    if provider == "claude":
        return {
            "name": "retrieve_memory",
            "description": "Retrieve relevant past conversations based on keywords",
            "input_schema": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Keywords to search for in past conversations",
                    },
                },
                "required": ["keywords"],
            },
        }
    else:  # provider == "groq"
        return {
            "type": "function",
            "function": {
                "name": "retrieve_memory",
                "description": "Retrieve relevant past conversations based on keywords",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords to search for in past conversations",
                        },
                    },
                    "required": ["keywords"],
                },
            },
        }


def get_memory_retrieve_tool_handler(memory_service: MemoryService) -> Callable:
    """
    Get the handler function for the memory retrieve tool.

    Args:
        memory_service: The memory service instance

    Returns:
        Function that handles memory retrieval requests
    """

    def handle_memory_retrieve(**params) -> str:
        keywords = params.get("keywords")
        limit = params.get("limit", 20)

        if not keywords:
            return "Error: Keywords are required for memory retrieval."

        try:
            result = memory_service.retrieve_memory(keywords, limit)
            return result
        except Exception as e:
            return f"Error retrieving memories: {str(e)}"

    return handle_memory_retrieve
