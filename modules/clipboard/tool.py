from typing import Dict, Any, Callable
from .service import ClipboardService


def get_clipboard_read_tool_definition() -> Dict[str, Any]:
    """
    Get the tool definition for reading from clipboard.

    Returns:
        Dict containing the tool definition
    """
    return {
        "name": "clipboard_read",
        "description": "Read content from the system clipboard (automatically detects text or image)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    }


def get_clipboard_write_tool_definition() -> Dict[str, Any]:
    """
    Get the tool definition for writing to clipboard.

    Returns:
        Dict containing the tool definition
    """
    return {
        "name": "clipboard_write",
        "description": "Write content to the system clipboard",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to write to the clipboard",
                },
            },
            "required": ["content"],
        },
    }


def get_clipboard_read_tool_handler(clipboard_service: ClipboardService) -> Callable:
    """
    Get the handler function for the clipboard read tool.

    Args:
        clipboard_service: The clipboard service instance

    Returns:
        Function that handles clipboard read requests
    """

    def handle_clipboard_read() -> str | list[Dict[str, Any]]:
        result = clipboard_service.read()
        if result["type"] == "image":
            return [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result["content"],
                    },
                }
            ]
        else:
            return result["content"]

    return handle_clipboard_read


def get_clipboard_write_tool_handler(clipboard_service: ClipboardService) -> Callable:
    """
    Get the handler function for the clipboard write tool.

    Args:
        clipboard_service: The clipboard service instance

    Returns:
        Function that handles clipboard write requests
    """

    def handle_clipboard_write(params: Dict[str, Any]) -> Dict[str, Any]:
        if "content" not in params:
            return {
                "success": False,
                "error": "Missing required parameter: content",
            }

        content = params["content"]
        return clipboard_service.write(content)

    return handle_clipboard_write
