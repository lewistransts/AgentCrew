import pytest
import json
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from modules.mcpclient.config import MCPConfigManager, MCPServerConfig
from modules.mcpclient.service import MCPService
from modules.mcpclient.manager import MCPSessionManager
from modules.tools.registry import ToolRegistry


@pytest.fixture
def mock_config_file(tmp_path):
    """Create a mock configuration file for testing."""
    config_data = {
        "server1": {
            "name": "Test Server 1",
            "command": "python",
            "args": ["test_server.py"],
            "env": {"TEST_ENV": "value"},
            "enabled": True
        },
        "server2": {
            "name": "Test Server 2",
            "command": "node",
            "args": ["test_server.js"],
            "enabled": False
        }
    }
    
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    return str(config_file)


@pytest.fixture
def config_manager(mock_config_file):
    """Create a config manager with the mock configuration."""
    manager = MCPConfigManager(mock_config_file)
    manager.load_config()
    return manager


@pytest.fixture
def mock_mcp_service():
    """Create a mock MCP service."""
    with patch('modules.mcpclient.service.MCPService', autospec=True) as MockService:
        service = MockService.return_value
        service.connect_to_server = AsyncMock(return_value=True)
        service.list_tools = AsyncMock(return_value=[
            {"name": "server1.tool1", "description": "Test Tool 1", "input_schema": {}}
        ])
        service.call_tool = AsyncMock(return_value={"content": "Tool result", "status": "success"})
        service.cleanup = AsyncMock()
        yield service


@pytest.fixture
def session_manager(mock_mcp_service):
    """Create a session manager with mock dependencies."""
    with patch('modules.mcpclient.manager.MCPService', return_value=mock_mcp_service):
        manager = MCPSessionManager()
        manager.config_manager = MagicMock()
        manager.config_manager.load_config.return_value = {
            "server1": MCPServerConfig(
                name="Test Server 1",
                command="python",
                args=["test_server.py"],
                env={"TEST_ENV": "value"},
                enabled=True
            )
        }
        manager.config_manager.get_enabled_servers.return_value = {
            "server1": MCPServerConfig(
                name="Test Server 1",
                command="python",
                args=["test_server.py"],
                env={"TEST_ENV": "value"},
                enabled=True
            )
        }
        yield manager


class TestMCPConfig:
    """Tests for the MCP configuration functionality."""
    
    def test_load_config(self, config_manager):
        """Test loading configuration from file."""
        configs = config_manager.configs
        
        assert len(configs) == 2
        assert "server1" in configs
        assert "server2" in configs
        assert configs["server1"].name == "Test Server 1"
        assert configs["server1"].command == "python"
        assert configs["server1"].args == ["test_server.py"]
        assert configs["server1"].env == {"TEST_ENV": "value"}
        assert configs["server1"].enabled is True
        
        assert configs["server2"].name == "Test Server 2"
        assert configs["server2"].command == "node"
        assert configs["server2"].args == ["test_server.js"]
        assert configs["server2"].enabled is False
    
    def test_get_enabled_servers(self, config_manager):
        """Test getting only enabled servers."""
        enabled_servers = config_manager.get_enabled_servers()
        
        assert len(enabled_servers) == 1
        assert "server1" in enabled_servers
        assert "server2" not in enabled_servers


@pytest.mark.asyncio
class TestMCPService:
    """Tests for the MCP service functionality."""
    
    async def test_connect_to_server(self):
        """Test connecting to an MCP server."""
        with patch('modules.mcpclient.service.stdio_client', new_callable=AsyncMock) as mock_stdio_client, \
             patch('modules.mcpclient.service.ClientSession', new_callable=AsyncMock) as mock_client_session:
            
            # Set up mocks
            mock_stdio = AsyncMock()
            mock_write = AsyncMock()
            mock_stdio_client.return_value.__aenter__.return_value = (mock_stdio, mock_write)
            
            mock_session = AsyncMock()
            mock_client_session.return_value.__aenter__.return_value = mock_session
            mock_session.initialize = AsyncMock()
            mock_session.list_tools = AsyncMock()
            mock_session.list_tools.return_value.tools = []
            
            # Create service and connect
            service = MCPService()
            config = MCPServerConfig(
                name="test_server",
                command="python",
                args=["test_server.py"],
                env=None,
                enabled=True
            )
            
            result = await service.connect_to_server(config)
            
            # Verify
            assert result is True
            assert "test_server" in service.sessions
            assert service.connected_servers["test_server"] is True
            mock_stdio_client.assert_called_once()
            mock_session.initialize.assert_called_once()
            mock_session.list_tools.assert_called_once()
    
    async def test_register_server_tools(self):
        """Test registering tools from a server."""
        with patch('modules.mcpclient.service.ToolRegistry') as mock_registry_class, \
             patch('modules.mcpclient.service.ClientSession', new_callable=AsyncMock) as mock_client_session:
            
            # Set up mocks
            mock_registry = MagicMock()
            mock_registry_class.get_instance.return_value = mock_registry
            
            mock_session = AsyncMock()
            mock_client_session.return_value.__aenter__.return_value = mock_session
            
            # Create mock tool
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_tool.description = "Test tool description"
            mock_tool.inputSchema = {"type": "object", "properties": {}}
            
            mock_session.list_tools = AsyncMock()
            mock_session.list_tools.return_value.tools = [mock_tool]
            
            # Create service with mock session
            service = MCPService()
            service.sessions = {"test_server": mock_session}
            service.connected_servers = {"test_server": True}
            
            # Register tools
            await service.register_server_tools("test_server")
            
            # Verify
            assert "test_server" in service.tools_cache
            assert "test_tool" in service.tools_cache["test_server"]
            mock_registry.register_tool.assert_called()
    
    async def test_call_tool(self):
        """Test calling a tool on a server."""
        # Set up mocks
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = "Tool result"
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Create service with mock session
        service = MCPService()
        service.sessions = {"test_server": mock_session}
        service.connected_servers = {"test_server": True}
        service.tools_cache = {"test_server": {"test_tool": {}}}
        
        # Call tool
        result = await service.call_tool("test_server", "test_tool", {"arg": "value"})
        
        # Verify
        assert result["content"] == "Tool result"
        assert result["status"] == "success"
        mock_session.call_tool.assert_called_once_with("test_tool", {"arg": "value"})


@pytest.mark.asyncio
class TestMCPSessionManager:
    """Tests for the MCP session manager functionality."""
    
    async def test_initialize_servers(self, session_manager):
        """Test initializing connections to servers."""
        # Initialize servers
        results = await session_manager.initialize_servers()
        
        # Verify
        assert results == {"server1": True}
        session_manager.mcp_service.connect_to_server.assert_called_once()
        assert session_manager.initialized is True
    
    async def test_cleanup(self, session_manager):
        """Test cleaning up resources."""
        # Clean up
        await session_manager.cleanup()
        
        # Verify
        session_manager.mcp_service.cleanup.assert_called_once()
        assert session_manager.initialized is False


@pytest.mark.asyncio
class TestMCPTools:
    """Tests for the MCP tool handlers."""
    
    async def test_mcp_connect_tool(self, session_manager):
        """Test the MCP connect tool handler."""
        from modules.mcpclient.tool import get_mcp_connect_tool_handler
        
        with patch('modules.mcpclient.tool.MCPSessionManager.get_instance', return_value=session_manager):
            # Get handler
            handler = get_mcp_connect_tool_handler()
            
            # Call handler
            result = await handler({"server_id": "server1"})
            
            # Verify
            assert result["status"] == "success"
            assert "Successfully connected" in result["content"]
    
    async def test_mcp_list_tools_tool(self, session_manager):
        """Test the MCP list tools tool handler."""
        from modules.mcpclient.tool import get_mcp_list_tools_tool_handler
        
        with patch('modules.mcpclient.tool.MCPSessionManager.get_instance', return_value=session_manager):
            # Get handler
            handler = get_mcp_list_tools_tool_handler()
            
            # Call handler
            result = await handler({"server_id": "server1"})
            
            # Verify
            assert result["status"] == "success"
            assert "server1.tool1" in result["content"]
    
    async def test_mcp_call_tool_tool(self, session_manager):
        """Test the MCP call tool tool handler."""
        from modules.mcpclient.tool import get_mcp_call_tool_tool_handler
        
        with patch('modules.mcpclient.tool.MCPSessionManager.get_instance', return_value=session_manager):
            # Get handler
            handler = get_mcp_call_tool_tool_handler()
            
            # Call handler
            result = await handler({
                "tool_name": "server1.tool1",
                "tool_args": {"arg": "value"}
            })
            
            # Verify
            assert result["status"] == "success"
            assert result["content"] == "Tool result"
            session_manager.mcp_service.call_tool.assert_called_once_with(
                "server1", "tool1", {"arg": "value"}
            )
