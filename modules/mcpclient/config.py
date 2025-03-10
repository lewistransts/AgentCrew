import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    enabled: bool = True


class MCPConfigManager:
    """Manager for MCP server configurations."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, uses the default path.
        """
        self.config_path = config_path or os.environ.get(
            "MCP_CONFIG_PATH",
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mcp_servers.json",
            ),
        )
        self.configs: Dict[str, MCPServerConfig] = {}

    def load_config(self) -> Dict[str, MCPServerConfig]:
        """
        Load server configurations from the config file.

        Returns:
            Dictionary of server configurations keyed by server ID.
        """
        try:
            if not os.path.exists(self.config_path):
                # Create default config directory if it doesn't exist
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                # Create empty config file
                with open(self.config_path, "w") as f:
                    json.dump({}, f)
                return {}

            with open(self.config_path, "r") as f:
                config_data = json.load(f)

            self.configs = {}
            for server_id, config in config_data.items():
                self.configs[server_id] = MCPServerConfig(
                    name=config.get("name", server_id),
                    command=config["command"],
                    args=config.get("args", []),
                    env=config.get("env"),
                    enabled=config.get("enabled", True),
                )

            return self.configs
        except Exception as e:
            print(f"Error loading MCP configuration: {e}")
            return {}

    def get_enabled_servers(self) -> Dict[str, MCPServerConfig]:
        """
        Get all enabled server configurations.

        Returns:
            Dictionary of enabled server configurations.
        """
        return {
            server_id: config
            for server_id, config in self.configs.items()
            if config.enabled
        }
