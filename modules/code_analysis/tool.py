from os import error
from typing import Dict, Any, Callable
from .service import CodeAnalysisService


# Tool definition function
def get_code_analysis_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Return the tool definition for code analysis based on provider.

    Args:
        provider: The LLM provider ("claude", "groq", or "openai")

    Returns:
        Dict containing the tool definition
    """
    description = (
        "Build a tree-sitter based structural map of source code files. "
        "This tool analyzes code structure to identify classes, functions, and methods. "
        "Only analyzes files within the allowed directory. "
        "Useful for code analysis and understanding project structure. "
        "Example: Enter '.' to analyze all source files in current directory, or 'src' to analyze all files in the src directory."
    )

    if provider == "claude":
        return {
            "name": "analyze_code",
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Root directory to analyze",
                    }
                },
                "required": ["path"],
            },
        }
    else:  # provider == "openai"
        return {
            "type": "function",
            "function": {
                "name": "analyze_code",
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Root directory to analyze",
                        }
                    },
                    "required": ["path"],
                },
            },
        }


# Tool handler function
def get_code_analysis_tool_handler(
    code_analysis_service: CodeAnalysisService,
) -> Callable:
    """Return the handler function for the code analysis tool."""

    def handler(**params) -> str:
        path = params.get("path", ".")
        result = code_analysis_service.analyze_code_structure(path)

        if isinstance(result, dict) and "error" in result:
            raise Exception(f"Failed to analyze code: {result['error']}")

        return result

    return handler
