import asyncio
import os
import json
from typing import Optional, Dict, Any, List, Callable
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPService:
    """Service for interacting with Model Context Protocol (MCP) servers."""

    def __init__(self):
        """Initialize the MCP service."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
        self.tools_cache = {}

    async def connect_to_server(self, server_script_path: str) -> bool:
        """
        Connect to an MCP server.

        Args:
            server_script_path: Path to the server script (.py or .js)

        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")

            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command, args=[server_script_path], env=None
            )

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            await self.session.initialize()

            # Cache available tools
            response = await self.session.list_tools()
            self.tools_cache = {tool.name: tool for tool in response.tools}

            return True
        except Exception as e:
            print(f"Error connecting to MCP server: {str(e)}")
            await self.cleanup()
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from the connected MCP server.

        Returns:
            List of tools with their metadata
        """
        if not self.session:
            raise ValueError("Not connected to an MCP server")

        response = await self.session.list_tools()
        self.tools_cache = {tool.name: tool for tool in response.tools}

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

    async def call_tool(
        self, tool_name: str, tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            tool_args: Arguments to pass to the tool

        Returns:
            Dict containing the tool's response
        """
        if not self.session:
            raise ValueError("Not connected to an MCP server")

        if tool_name not in self.tools_cache:
            # Refresh tools cache
            await self.list_tools()
            if tool_name not in self.tools_cache:
                raise ValueError(f"Tool '{tool_name}' is not available")

        result = await self.session.call_tool(tool_name, tool_args)
        return {"content": result.content, "status": "success"}

    async def cleanup(self):
        """Clean up resources."""
        await self.exit_stack.aclose()
        self.session = None
        self.stdio = None
        self.write = None

    def get_available_tool_definitions(self):
        """
        Get the available tool definitions in a format compatible with LLM providers.

        Returns:
            List of tool definitions
        """
        if not self.tools_cache:
            return []

        tools = []
        for name, tool in self.tools_cache.items():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
            )
        return tools
