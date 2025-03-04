from typing import Dict, Any, Callable
from .service import MemoryService


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
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to retrieve (default: 5)",
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
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of memories to retrieve (default: 5)",
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
        limit = params.get("limit", 5)

        if not keywords:
            return "Error: Keywords are required for memory retrieval."

        try:
            result = memory_service.retrieve_memory(keywords, limit)
            print(result)
            return result
        except Exception as e:
            return f"Error retrieving memories: {str(e)}"

    return handle_memory_retrieve
