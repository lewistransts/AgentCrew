import json
import asyncio
from typing import Dict, Any
from AgentCrew.modules.mcpclient import MCPSessionManager
from AgentCrew.modules import logger


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
                    "server_id": {
                        "type": "string",
                        "description": "ID of the server to connect to (must be defined in configuration)",
                    }
                },
                "required": ["server_id"],
            },
        },
    }


def get_mcp_list_servers_tool_definition():
    """Get the tool definition for listing configured MCP servers."""
    return {
        "type": "function",
        "function": {
            "name": "mcp_list_servers",
            "description": "List all configured MCP servers and their connection status",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }


def get_mcp_list_tools_tool_definition():
    """Get the tool definition for listing tools available on MCP servers."""
    return {
        "type": "function",
        "function": {
            "name": "mcp_list_tools",
            "description": "List all tools available on connected MCP servers",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Optional ID of the server to list tools from. If not provided, lists tools from all servers.",
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
            "description": "Call a tool on a connected MCP server",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Full name of the tool to call (format: server_id.tool_name)",
                    },
                    "tool_args": {
                        "type": "object",
                        "description": "Arguments to pass to the tool",
                    },
                },
                "required": ["tool_name", "tool_args"],
            },
        },
    }


def get_mcp_disconnect_tool_definition():
    """Get the tool definition for disconnecting from MCP servers."""
    return {
        "type": "function",
        "function": {
            "name": "mcp_disconnect",
            "description": "Disconnect from all MCP servers or a specific server",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Optional ID of the server to disconnect from. If not provided, disconnects from all servers.",
                    }
                },
                "required": [],
            },
        },
    }


def get_mcp_connect_tool_handler():
    """Get the handler for the MCP connect tool."""

    async def handle_mcp_connect(params: Dict[str, Any]) -> Dict[str, Any]:
        server_id = params.get("server_id")
        manager = MCPSessionManager.get_instance()

        # Ensure the MCPConfigManager has loaded configurations.
        # MCPSessionManager.initialize() handles this and starting the service.
        if not manager.initialized:
            logger.info(
                "MCP Connect Tool: MCPSessionManager not initialized. Initializing now..."
            )
            manager.initialize()  # This is a synchronous call

        # Access configurations after ensuring they are loaded
        server_configs = manager.config_manager.configs
        if not server_configs:  # Might happen if config file is empty or load failed
            manager.config_manager.load_config()  # Attempt to load again
            server_configs = manager.config_manager.configs

        if server_id not in server_configs:
            return {
                "content": f"Server '{server_id}' is not defined in configuration.",
                "status": "error",
            }

        server_config = server_configs[server_id]

        # Check if already connected
        if manager.mcp_service.connected_servers.get(server_id):
            # Optionally, re-register tools if they might have been lost
            # await manager.mcp_service.register_server_tools(server_id, agent_name_if_applicable)
            return {
                "content": f"Already connected to MCP server '{server_id}'.",
                "status": "success",
            }

        logger.info(f"MCP Connect Tool: Attempting to connect to {server_id}...")
        try:
            # Run start_server_connection_management on the MCPService's event loop.
            # This will create/start the management task for the server.
            manager.mcp_service._run_async(
                manager.mcp_service.start_server_connection_management(server_config)
            )

            # Give some time for the connection to establish. This is a simplification.
            # A more robust solution would involve waiting for an event or status change.
            await asyncio.sleep(3)  # Increased sleep slightly

            if manager.mcp_service.connected_servers.get(server_id):
                # Tools should have been registered by _manage_single_connection upon successful connection.
                # We can list them here as confirmation.
                tools_info = await manager.mcp_service.list_tools(
                    server_id
                )  # list_tools is async
                tool_names = [t["name"] for t in tools_info]
                return {
                    "content": f"Successfully initiated connection to MCP server '{server_id}'. Available tools: {json.dumps(tool_names)}",
                    "status": "success",
                }
            else:
                # Check if the task is running, which means it's attempting to connect
                task = manager.mcp_service._server_connection_tasks.get(server_id)
                if task and not task.done():
                    return {
                        "content": f"Connection attempt to MCP server '{server_id}' is in progress. Check status again shortly.",
                        "status": "pending",
                    }
                return {
                    "content": f"Failed to connect to MCP server '{server_id}'. Check server logs and configuration.",
                    "status": "error",
                }
        except Exception as e:
            logger.exception("MCP Connect Tool: Error initiating connection")
            return {
                "content": f"Error initiating connection to MCP server '{server_id}': {str(e)}",
                "status": "error",
            }

    return handle_mcp_connect


def get_mcp_list_servers_tool_handler():
    """Get the handler for the MCP list servers tool."""

    async def handle_mcp_list_servers(params: Dict[str, Any]) -> Dict[str, Any]:
        manager = MCPSessionManager.get_instance()

        if not manager.initialized:
            manager.initialize()  # Ensures config is loaded and service is running

        # Get server configurations and connection status
        # Ensure configs are loaded if they weren't by initialize() for some reason (e.g. empty file initially)
        if not manager.config_manager.configs:
            manager.config_manager.load_config()

        server_configs = manager.config_manager.configs
        connected_servers = manager.mcp_service.connected_servers

        servers_info = []
        for (
            server_id,
            config,
        ) in server_configs.items():  # Iterate over all defined servers
            is_connected = connected_servers.get(server_id, False)
            # enabledForAgents might be a list or a single string, ensure consistent check

            servers_info.append(
                {
                    "id": server_id,
                    "name": config.name,
                    "enabled_for_agents": config.enabledForAgents,  # Show which agents it's for
                    "currently_managed": server_id
                    in manager.mcp_service._server_connection_tasks
                    and not manager.mcp_service._server_connection_tasks[
                        server_id
                    ].done(),
                    "connected": is_connected,
                }
            )

        if not servers_info:
            return {
                "content": "No MCP servers defined in the configuration.",
                "status": "info",
            }

        return {"content": json.dumps(servers_info, indent=2), "status": "success"}

    return handle_mcp_list_servers


def get_mcp_list_tools_tool_handler():
    """Get the handler for the MCP list tools tool."""

    async def handle_mcp_list_tools(params: Dict[str, Any]) -> Dict[str, Any]:
        server_id = params.get("server_id")

        # Get session manager
        manager = MCPSessionManager.get_instance()

        # Make sure configuration is loaded and service is running
        if not manager.initialized:
            logger.info(
                "MCP List Tools Tool: MCPSessionManager not initialized. Initializing now..."
            )
            manager.initialize()

        try:
            tools = await manager.mcp_service.list_tools(server_id)
            if not tools:
                if server_id:
                    # Check if server is supposed to be connected
                    if manager.mcp_service.connected_servers.get(server_id):
                        return {
                            "content": f"No tools reported by connected server '{server_id}'.",
                            "status": "info",
                        }
                    else:
                        return {
                            "content": f"Server '{server_id}' is not connected or does not exist. Cannot list tools.",
                            "status": "error",
                        }
                else:  # No server_id provided, listing for all
                    return {
                        "content": "No tools available from any connected MCP servers.",
                        "status": "info",
                    }

            return {"content": json.dumps(tools, indent=2), "status": "success"}
        except Exception as e:
            return {"content": f"Error listing tools: {str(e)}", "status": "error"}

    return handle_mcp_list_tools


def get_mcp_call_tool_tool_handler():
    """Get the handler for the MCP call tool tool."""

    async def handle_mcp_call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        tool_name: str = str(params.get("tool_name"))
        tool_args = params.get("tool_args", {})

        # Parse server_id and tool_name from the full tool name
        if "." not in tool_name:
            return {
                "content": f"Invalid tool name format: '{tool_name}'. Expected format: 'server_id.tool_name'",
                "status": "error",
            }

        server_id, actual_tool_name = tool_name.split(".", 1)

        # Get session manager
        manager = MCPSessionManager.get_instance()

        # Make sure configuration is loaded and service is running
        if not manager.initialized:
            logger.info(
                "MCP Call Tool: MCPSessionManager not initialized. Initializing now..."
            )
            manager.initialize()

        # Check if server is connected before attempting to call tool
        if not manager.mcp_service.connected_servers.get(server_id):
            return {
                "content": f"Server '{server_id}' is not connected. Cannot call tool '{actual_tool_name}'.",
                "status": "error",
            }

        try:
            result = await manager.mcp_service.call_tool(
                server_id, actual_tool_name, tool_args
            )
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
        server_id = params.get("server_id")

        # Get session manager
        manager = MCPSessionManager.get_instance()

        if not manager.initialized and not (
            hasattr(manager.mcp_service, "loop_thread")
            and manager.mcp_service.loop_thread.is_alive()
        ):
            return {
                "content": "MCP system not initialized or service not running. Nothing to disconnect.",
                "status": "info",
            }

        if server_id:
            # Check if the server is even known or managed before attempting disconnect
            is_managed = (
                server_id in manager.mcp_service._server_connection_tasks
                or server_id in manager.mcp_service._server_shutdown_events
                or manager.mcp_service.connected_servers.get(server_id)
            )

            if not is_managed:  # Check if server_id is valid or was ever managed
                return {
                    "content": f"Server '{server_id}' is not currently managed, connected, or known. Cannot disconnect.",
                    "status": "info",
                }

            logger.info(
                f"MCP Disconnect Tool: Attempting to disconnect from {server_id}..."
            )
            try:
                # Run shutdown_single_server_connection on the MCPService's event loop.
                manager.mcp_service._run_async(
                    manager.mcp_service.shutdown_single_server_connection(server_id)
                )
                # Tool unregistration from agents is a more complex topic.
                # For now, agents would need to handle failing tool calls if a server is disconnected.
                return {
                    "content": f"Disconnection process for MCP server '{server_id}' initiated.",
                    "status": "success",
                }
            except Exception as e:
                logger.exception(
                    f"MCP Disconnect Tool: Error disconnecting from MCP server '{server_id}'"
                )
                return {
                    "content": f"Error disconnecting from MCP server '{server_id}': {str(e)}",
                    "status": "error",
                }
        else:
            # Disconnect from all servers and stop the service
            logger.info(
                "MCP Disconnect Tool: Attempting to disconnect from all servers and cleanup MCP manager..."
            )
            try:
                manager.cleanup()  # This handles everything including stopping the service thread.
                return {
                    "content": "Disconnection process for all MCP servers and service cleanup initiated.",
                    "status": "success",
                }
            except Exception as e:
                logger.exception("MCP Disconnect Tool: Error during full MCP cleanup")
                return {
                    "content": f"Error during full MCP cleanup: {str(e)}",
                    "status": "error",
                }

    return handle_mcp_disconnect


# from AgentCrew.modules.tools.registration import register_tool # Add this import


def register(
    service_instance=None, agent=None
):  # agent parameter is kept for compatibility but not used for global MCP tools
    """
    Register all MCP tools with the global tool registry.

    Args:
        service_instance: Not used for MCP tools, but included for consistency
        agent: Agent instance to register with directly (optional)

    This function should beCalled during application initialization.
    """
    # Register tool definitions and handlers globally
    # For these MCP management tools, service_instance is None as they use the MCPSessionManager singleton.
    # agent is also None for global registration.
    # register_tool(
    #     get_mcp_connect_tool_definition,
    #     get_mcp_connect_tool_handler,
    #     service_instance=None,
    #     agent=agent,
    # )
    # register_tool(
    #     get_mcp_list_servers_tool_definition,
    #     get_mcp_list_servers_tool_handler,
    #     service_instance=None,
    #     agent=agent,
    # )
    # register_tool(
    #     get_mcp_list_tools_tool_definition,
    #     get_mcp_list_tools_tool_handler,
    #     service_instance=None,
    #     agent=agent,
    # )
    # register_tool(
    #     get_mcp_call_tool_definition,
    #     get_mcp_call_tool_tool_handler,
    #     service_instance=None,
    #     agent=agent,
    # )
    # register_tool(
    #     get_mcp_disconnect_tool_definition,
    #     get_mcp_disconnect_tool_handler,
    #     service_instance=None,
    #     agent=agent,
    # )

    # Initialize the MCPSessionManager if it hasn't been already.
    # This starts the MCPService event loop and connects to initially configured servers.
    # The call in main.py's setup_agents also does this, so this is a safeguard.
    mcp_manager = MCPSessionManager.get_instance()
    if not mcp_manager.initialized:
        logger.info(
            "MCP Tools: MCPSessionManager not initialized by main flow, initializing now."
        )
        mcp_manager.initialize()

    logger.info("MCP Tools registered.")
