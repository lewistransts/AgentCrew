import asyncio
import json
from typing import Dict, Any, Callable
from .service import MCPService

# Dictionary to store MCP service instances
_mcp_services = {}


def get_mcp_connect_tool_definition():
    """Get the tool definition for connecting to an MCP server."""
    return {
        "type": "function",
        "function": {
            "name": "mcp_connect",
            "description": "Connect to a Model Context Protocol (MCP) server",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_path": {
                        "type": "string",
                        "description": "Path to the MCP server script (.py or .js file)",
                    },
                    "service_id": {
                        "type": "string",
                        "description": "Optional identifier for the MCP service. If not provided, a default ID will be used.",
                    },
                },
                "required": ["server_path"],
            },
        },
    }


def get_mcp_list_tools_tool_definition():
    """Get the tool definition for listing tools available on an MCP server."""
    return {
        "type": "function",
        "function": {
            "name": "mcp_list_tools",
            "description": "List all tools available on the connected MCP server",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "Optional identifier for the MCP service. If not provided, the default ID will be used.",
                    }
                },
                "required": [],
            },
        },
    }


def get_mcp_call_tool_definition():
    """Get the tool definition for calling a tool on an MCP server."""
    return {
        "type": "function",
        "function": {
            "name": "mcp_call_tool",
            "description": "Call a tool on the connected MCP server",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to call",
                    },
                    "tool_args": {
                        "type": "object",
                        "description": "Arguments to pass to the tool",
                    },
                    "service_id": {
                        "type": "string",
                        "description": "Optional identifier for the MCP service. If not provided, the default ID will be used.",
                    },
                },
                "required": ["tool_name", "tool_args"],
            },
        },
    }


def get_mcp_disconnect_tool_definition():
    """Get the tool definition for disconnecting from an MCP server."""
    return {
        "type": "function",
        "function": {
            "name": "mcp_disconnect",
            "description": "Disconnect from a connected MCP server",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "Optional identifier for the MCP service. If not provided, the default ID will be used.",
                    }
                },
                "required": [],
            },
        },
    }


def get_mcp_connect_tool_handler():
    """Get the handler for the MCP connect tool."""

    async def handle_mcp_connect(params: Dict[str, Any]) -> Dict[str, Any]:
        server_path = params.get("server_path")
        service_id = params.get("service_id", "default")

        if service_id in _mcp_services:
            # Clean up existing service if it exists
            await _mcp_services[service_id].cleanup()

        service = MCPService()
        success = await service.connect_to_server(server_path)

        if success:
            _mcp_services[service_id] = service
            tools = await service.list_tools()
            return {
                "content": f"Successfully connected to MCP server at {server_path}. Available tools: {json.dumps([t['name'] for t in tools])}",
                "status": "success",
            }
        else:
            return {
                "content": f"Failed to connect to MCP server at {server_path}",
                "status": "error",
            }

    return handle_mcp_connect


def get_mcp_list_tools_tool_handler():
    """Get the handler for the MCP list tools tool."""

    async def handle_mcp_list_tools(params: Dict[str, Any]) -> Dict[str, Any]:
        service_id = params.get("service_id", "default")

        if service_id not in _mcp_services:
            return {
                "content": f"No MCP service connected with ID '{service_id}'",
                "status": "error",
            }

        try:
            tools = await _mcp_services[service_id].list_tools()
            return {"content": json.dumps(tools, indent=2), "status": "success"}
        except Exception as e:
            return {"content": f"Error listing tools: {str(e)}", "status": "error"}

    return handle_mcp_list_tools


def get_mcp_call_tool_tool_handler():
    """Get the handler for the MCP call tool tool."""

    async def handle_mcp_call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        service_id = params.get("service_id", "default")
        tool_name = params.get("tool_name")
        tool_args = params.get("tool_args", {})

        if service_id not in _mcp_services:
            return {
                "content": f"No MCP service connected with ID '{service_id}'",
                "status": "error",
            }

        try:
            result = await _mcp_services[service_id].call_tool(tool_name, tool_args)
            return result
        except Exception as e:
            return {
                "content": f"Error calling tool '{tool_name}': {str(e)}",
                "status": "error",
            }

    return handle_mcp_call_tool


def get_mcp_disconnect_tool_handler():
    """Get the handler for the MCP disconnect tool."""

    async def handle_mcp_disconnect(params: Dict[str, Any]) -> Dict[str, Any]:
        service_id = params.get("service_id", "default")

        if service_id not in _mcp_services:
            return {
                "content": f"No MCP service connected with ID '{service_id}'",
                "status": "error",
            }

        try:
            await _mcp_services[service_id].cleanup()
            del _mcp_services[service_id]
            return {
                "content": f"Successfully disconnected from MCP server with ID '{service_id}'",
                "status": "success",
            }
        except Exception as e:
            return {
                "content": f"Error disconnecting from MCP server: {str(e)}",
                "status": "error",
            }

    return handle_mcp_disconnect


def register():
    """
    Register all MCP tools with the tool registry.

    This function should be called during application initialization.
    """
    from modules.tools.registration import register_tool

    # Import here to avoid circular imports
    from modules.mcp.service import MCPService

    # Register tool definitions and handlers
    register_tool(get_mcp_connect_tool_definition, get_mcp_connect_tool_handler)
    register_tool(get_mcp_list_tools_tool_definition, get_mcp_list_tools_tool_handler)
    register_tool(get_mcp_call_tool_definition, get_mcp_call_tool_handler)
    register_tool(get_mcp_disconnect_tool_definition, get_mcp_disconnect_tool_handler)
