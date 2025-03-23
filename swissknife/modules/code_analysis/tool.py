from os import path as os_path
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
        "Useful for code analysis and understanding project structure. "
        "Example: Enter '.' to analyze all source files in current directory, or 'src' to analyze all files in the src directory."
    )

    if provider == "claude":
        return {
            "name": "analyze_repo",
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
                "name": "analyze_repo",
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
        path = os_path.expanduser(path)
        result = code_analysis_service.analyze_code_structure(path)
        if isinstance(result, dict) and "error" in result:
            raise Exception(f"Failed to analyze code: {result['error']}")

        return result

    return handler


def get_file_content_tool_definition(provider="claude"):
    """
    Return the tool definition for retrieving file content based on provider.

    Args:
        provider: The LLM provider ("claude", "groq", or "openai")

    Returns:
        Dict containing the tool definition
    """
    description = "Read content from local project files. Use this tool to examine any file in the current project workspace. Can retrieve either the entire file content or specific code elements (classes/functions) within the file. For complete files, only provide the file_path parameter."

    properties = {
        "file_path": {
            "type": "string",
            "description": "Relative path from current directory of agent to the local repo file.",
        },
        "element_type": {
            "type": "string",
            "description": "Optional: Type of code element to extract (Always use when only targeting a specific element)",
            "enum": ["class", "function"],
        },
        "element_name": {
            "type": "string",
            "description": "Optional: Name of the class or function to extract (Always use when only targeting a specific element)",
        },
        "scope_path": {
            "type": "string",
            "description": "Optional: Dot-separated path to resolve ambiguity (e.g., 'ClassName.method_name')",
        },
    }

    if provider == "claude":
        return {
            "name": "read_repo_file",
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": ["file_path"],
            },
        }
    else:  # provider == "openai"
        return {
            "type": "function",
            "function": {
                "name": "read_repo_file",
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": ["file_path", "element_type", "element_name"],
                },
            },
        }


def get_file_content_tool_handler(
    code_analysis_service: CodeAnalysisService,
):
    """Returns a function that handles the get_file_content tool."""

    def handler(**params) -> str:
        file_path = params.get("file_path")
        element_type = params.get("element_type")
        element_name = params.get("element_name")
        scope_path = params.get("scope_path")

        if not file_path:
            raise Exception("File path is required")

        # Validate parameters
        if element_type and element_type not in ["class", "function"]:
            raise Exception("Element type must be 'class' or 'function'")

        if (element_type and not element_name) or (element_name and not element_type):
            raise Exception(
                "Both element_type and element_name must be provided together"
            )

        results = code_analysis_service.get_file_content(
            file_path, element_type, element_name, scope_path
        )

        content = ""

        for path, code in results.items():
            content += f"{path}: {code}\n"

        # If we're getting a specific element, format the output accordingly
        if element_type and element_name:
            scope_info = f" in {scope_path}" if scope_path else ""
            return f"CONTENT OF {element_name} {element_type}{scope_info}: {content}"
        else:
            # If we're getting the whole file content
            return content

    return handler


def register(service_instance=None, agent=None):
    """
    Register this tool with the central registry or directly with an agent

    Args:
        service_instance: The code analysis service instance
        agent: Agent instance to register with directly (optional)
    """
    from swissknife.modules.tools.registration import register_tool

    register_tool(
        get_code_analysis_tool_definition,
        get_code_analysis_tool_handler,
        service_instance,
        agent,
    )

    register_tool(
        get_file_content_tool_definition,
        get_file_content_tool_handler,
        service_instance,
        agent,
    )
