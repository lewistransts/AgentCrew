# MCP Client Module Revision Specification
>
> Enhance the MCP client module to support dynamic tool registration from multiple servers

## Objectives

- Implement JSON-based configuration for multiple MCP servers
- Enable concurrent server connections and management
- Support dynamic tool registration from each server
- Maintain backward compatibility with existing tool registry
- Provide robust error handling and resource management

## Context Files

- modules/mcpclient/service.py: Current MCP service implementation
- modules/mcpclient/tool.py: Tool registration and handlers
- modules/tools/registry.py: Core tool registry functionality
- tests/mcpclient_test.py: pytest file

## Requirements

### Configuration Management

- JSON schema for server definitions
- Support for multiple server configurations
- Environment variable configuration
- Server enable/disable functionality

### Server Connection

- Asynchronous connection handling
- Concurrent server initialization
- Connection state management
- Resource cleanup on shutdown

### Tool Registration

- Dynamic tool discovery from servers
- Namespace isolation between servers
- Tool conflict resolution
- Provider-agnostic tool definitions

## Low-level Tasks

1. CREATE modules/mcpclient/config.py:

    ```python
    # Required classes:
    - MCPServerConfig: Dataclass for server configuration
        - Properties: name, command, args, env, enabled
    - MCPConfigManager: Configuration file handler
        - Methods: load_config(), get_enabled_servers()
    ```

2. UPDATE modules/mcpclient/service.py:

    ```python
    # Required classes:
    - MCPService:
        - Properties:
            - sessions: Dict[str, ClientSession]
            - connected_servers: Dict[str, bool]
        - Methods:
            - connect_to_server(server_config: MCPServerConfig) -> bool
            - register_server_tools(server_name: str)
            - _format_tool_definition(tool: dict, server_name: str) -> dict
            - _create_tool_handler(server_name: str, tool_name: str)
            - cleanup()
    ```

3. CREATE modules/mcpclient/manager.py:

    ```python
    # Required classes:
    - MCPSessionManager:
        - Properties:
            - config_manager: MCPConfigManager
            - mcp_service: MCPService
        - Methods:
            - get_instance() -> MCPSessionManager
            - initialize_servers()
            - cleanup()
    ```

4. UPDATE modules/mcpclient/tool.py:

    ```python
    # Required functions:
    - get_mcp_connect_tool_definition() -> dict
    - handle_mcp_connect() -> dict
    - register()
    ```

## Implementation Details

### 1. Configuration Schema (config/mcp_servers.json)

```json
{
    "server_id": {
        "name": "string",
        "command": "string",
        "args": ["string"],
        "env": {
            "key": "value"
        },
        "enabled": boolean
    }
}
```

### 2. Tool Registration Format

```python
{
    "name": "server_name.tool_name",
    "description": "Tool description",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}
```

### 3. Error Handling Requirements

- Connection failures should not crash the system
- Failed servers should be marked as disconnected
- Tools from disconnected servers should be unregistered
- Retry logic for failed connections
- Proper resource cleanup on errors

### 4. Testing Requirements

```python
# Required test cases:
- Configuration loading and validation
- Server connection success/failure
- Tool registration and namespacing
- Concurrent server initialization
- Error handling and recovery
- Resource cleanup
```
