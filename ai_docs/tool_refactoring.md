# Revised Tool Registration Architecture

## 1. Centralized Tool Registry

First, let's create a centralized tool registry that builds on your existing
pattern:

```python
# modules/tools/registry.py
from typing import Dict, Any, Callable, List, Optional, Tuple

class ToolRegistry:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ToolRegistry()
        return cls._instance

    def __init__(self):
        self.tools = {}  # {tool_name: (definition_func, handler_func, service_instance)}

    def register_tool(self, definition_func: Callable, handler_factory: Callable, service_instance=None):
        """
        Register a tool with the registry

        Args:
            definition_func: Function that returns tool definition given a provider
            handler_factory: Function that creates a handler given service instance
            service_instance: Instance of the service needed by the handler (optional)
        """
        # Call definition_func with default provider to get tool name
        default_def = definition_func()
        tool_name = self._extract_tool_name(default_def)

        self.tools[tool_name] = (definition_func, handler_factory, service_instance)

    def _extract_tool_name(self, tool_def: Dict) -> str:
        """Extract tool name from definition regardless of format"""
        if "name" in tool_def:
            return tool_def["name"]
        elif "function" in tool_def and "name" in tool_def["function"]:
            return tool_def["function"]["name"]
        else:
            raise ValueError("Could not extract tool name from definition")

    def get_tool_definitions(self, provider: str) -> List[Dict[str, Any]]:
        """Get all tool definitions formatted for the specified provider"""
        definitions = []
        for name, (definition_func, _, _) in self.tools.items():
            try:
                tool_def = definition_func(provider)
                definitions.append(tool_def)
            except Exception as e:
                print(f"Error getting definition for tool {name}: {e}")
        return definitions

    def get_tool_handler(self, tool_name: str) -> Optional[Callable]:
        """Get the handler for a specific tool"""
        if tool_name not in self.tools:
            return None

        _, handler_factory, service_instance = self.tools[tool_name]
        return handler_factory(service_instance) if service_instance else handler_factory()
```

## 2. Tool Registration Function

```python
# modules/tools/registration.py
from .registry import ToolRegistry

def register_tool(definition_func, handler_factory, service_instance=None):
    """
    Register a tool with the central registry

    Args:
        definition_func: Function that returns tool definition given a provider
        handler_factory: Function that creates a handler function
        service_instance: Service instance needed by the handler (optional)
    """
    registry = ToolRegistry.get_instance()
    registry.register_tool(definition_func, handler_factory, service_instance)
```

## 3. Modified LLM Service Base Class

```python
# modules/llm/base.py
from modules.tools.registry import ToolRegistry

class BaseLLMService:
    def __init__(self, provider_name):
        self.provider_name = provider_name
        self.registry = ToolRegistry.get_instance()
        self.registered_tools = {}

    def register_all_tools(self):
        """Register all available tools with this LLM service"""
        tool_definitions = self.registry.get_tool_definitions(self.provider_name)
        for tool_def in tool_definitions:
            self.register_tool_definition(tool_def)

    def register_tool_definition(self, tool_definition):
        """Register a tool definition with the LLM service"""
        # Implementation depends on the provider
        tool_name = self._extract_tool_name(tool_definition)
        self.registered_tools[tool_name] = tool_definition

    def _extract_tool_name(self, tool_def):
        """Extract tool name from definition regardless of format"""
        if "name" in tool_def:
            return tool_def["name"]
        elif "function" in tool_def and "name" in tool_def["function"]:
            return tool_def["function"]["name"]
        else:
            raise ValueError("Could not extract tool name from definition")

    def execute_tool(self, tool_name, params):
        """Execute a tool with the given parameters"""
        handler = self.registry.get_tool_handler(tool_name)
        if not handler:
            raise ValueError(f"No handler found for tool {tool_name}")

        return handler(**params)
```

## 4. Provider-Specific Service Classes

```python
# modules/anthropic/service.py
from modules.llm.base import BaseLLMService

class AnthropicService(BaseLLMService):
    def __init__(self):
        super().__init__("claude")
        # Initialize Anthropic client, etc.

    def register_tool_definition(self, tool_definition):
        """Register a tool definition with the Anthropic service"""
        tool_name = tool_definition["name"]
        self.registered_tools[tool_name] = tool_definition
        # Additional Claude-specific registration logic if needed

# modules/openai/service.py
from modules.llm.base import BaseLLMService

class OpenAIService(BaseLLMService):
    def __init__(self):
        super().__init__("openai")
        # Initialize OpenAI client, etc.

    def register_tool_definition(self, tool_definition):
        """Register a tool definition with the OpenAI service"""
        tool_name = tool_definition["function"]["name"]
        self.registered_tools[tool_name] = tool_definition
        # Additional OpenAI-specific registration logic if needed
```

## 6. Updated Code Analysis Tool Implementation

Your existing code_analysis/tool.py would need minimal changes:

```python
# modules/code_analysis/tool.py
from os import error, path as os_path
from typing import Dict, Any, Callable
from .service import CodeAnalysisService
from modules.tools.registration import register_tool

# Tool definition function
def get_code_analysis_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Return the tool definition for code analysis based on provider.

    Args:
        provider: The LLM provider ("claude", "groq", "openai")

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

    # Parameters section that's common to all formats
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Root directory to analyze",
            }
        },
        "required": ["path"],
    }

    if provider == "claude":
        return {
            "name": "analyze_code",
            "description": description,
            "input_schema": parameters,
        }
    else:  # provider == "openai" or other
        return {
            "type": "function",
            "function": {
                "name": "analyze_code",
                "description": description,
                "parameters": parameters,
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

# Automatically register the tool when this module is imported
# This line would be added to each tool module
def register():
    """Register this tool with the central registry"""
    register_tool(get_code_analysis_tool_definition, get_code_analysis_tool_handler)
```

## 7. Auto-Registration in Main

```python
# main.py
from modules.tools.registry import ToolRegistry
import importlib

def discover_and_register_tools():
    """Discover and register all tools"""
    # List of tool modules
    tool_modules = [
        "modules.web_search.tool",
        "modules.clipboard.tool",
        "modules.code_analysis.tool",
        "modules.ytdlp.tool",
        "modules.memory.tool",
        "modules.scraping.tool",
        # Add other tool modules here
    ]

    for module_name in tool_modules:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "register"):
                module.register()
        except ImportError as e:
            print(f"Error importing tool module {module_name}: {e}")

def main():
    # Discover and register all tools
    discover_and_register_tools()

    # Create LLM service based on provider
    provider = args.provider  # e.g., "claude", "openai"
    llm_service = create_llm_service(provider)

    # Register all tools with the LLM service
    llm_service.register_all_tools()


    # Start chat or other logic
    # ...
```

## Implementation Details and Benefits

1. **Compatible with Your Existing Pattern**: This solution builds on your
   existing pattern of separate definition and handler functions with
   provider-specific formatting.

2. **Centralized Registry**: All tools are registered in a central registry,
   eliminating the need for manual imports and registrations in main.py.

3. **Automatic Tool Registration**: Tools are automatically discovered and
   registered when the application starts.

4. **Provider-Specific Formatting**: Tool definitions are formatted
   appropriately for each provider without duplicating code.

5. **Migration Path**: The changes required to existing tool modules are
   minimal, allowing for incremental adoption.

6. **Service Injection**: The registry supports injecting service instances into
   tool handlers, maintaining your current pattern.
