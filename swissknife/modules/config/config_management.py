import os
import json
import toml
from typing import Dict, Any, Optional, List


class ConfigManagement:
    """
    A class to manage configuration files in different formats (JSON, TOML).
    Supports reading, writing, and updating configuration files.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigManagement class.

        Args:
            config_path: Optional path to the configuration file.
                         If not provided, it will be set later.
        """
        self.config_path = config_path
        self.config_data = {}
        self.file_format = None

        if config_path:
            self.load_config()

    def set_config_path(self, config_path: str) -> None:
        """
        Set the configuration file path.

        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from the file.

        Returns:
            The loaded configuration data.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the file format is not supported.
        """
        if not self.config_path:
            raise ValueError("Configuration path not set")

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        file_extension = os.path.splitext(self.config_path)[1].lower()

        try:
            if file_extension == ".json":
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
                self.file_format = "json"
            elif file_extension == ".toml":
                self.config_data = toml.load(self.config_path)
                self.file_format = "toml"
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

            return self.config_data
        except Exception as e:
            raise ValueError(f"Error loading configuration: {str(e)}")

    def save_config(self) -> None:
        """
        Save the configuration to the file.

        Raises:
            ValueError: If the file format is not supported or the configuration path is not set.
        """
        if not self.config_path:
            raise ValueError("Configuration path not set")

        if not self.file_format:
            # Determine format from file extension
            file_extension = os.path.splitext(self.config_path)[1].lower()
            if file_extension == ".json":
                self.file_format = "json"
            elif file_extension == ".toml":
                self.file_format = "toml"
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

        try:
            if self.file_format == "json":
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.config_data, f, indent=2)
            elif self.file_format == "toml":
                with open(self.config_path, "w", encoding="utf-8") as f:
                    toml.dump(self.config_data, f)
            else:
                raise ValueError(f"Unsupported file format: {self.file_format}")
        except Exception as e:
            raise ValueError(f"Error saving configuration: {str(e)}")

    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration data.

        Returns:
            The current configuration data.
        """
        return self.config_data

    def update_config(
        self, new_data: Dict[str, Any], merge: bool = True
    ) -> Dict[str, Any]:
        """
        Update the configuration with new data.

        Args:
            new_data: The new data to update the configuration with.
            merge: If True, merge the new data with the existing data.
                   If False, replace the existing data with the new data.

        Returns:
            The updated configuration data.
        """
        if merge:
            self._deep_update(self.config_data, new_data)
        else:
            self.config_data = new_data

        return self.config_data

    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep update a nested dictionary.

        Args:
            target: The target dictionary to update.
            source: The source dictionary with new values.
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a value from the configuration using a dot-separated key path.

        Args:
            key_path: A dot-separated path to the value (e.g., "section.subsection.key").
            default: The default value to return if the key doesn't exist.

        Returns:
            The value at the specified key path, or the default value if not found.
        """
        keys = key_path.split(".")
        current = self.config_data

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    def set_value(self, key_path: str, value: Any) -> None:
        """
        Set a value in the configuration using a dot-separated key path.

        Args:
            key_path: A dot-separated path to the value (e.g., "section.subsection.key").
            value: The value to set.
        """
        keys = key_path.split(".")
        current = self.config_data

        # Navigate to the nested dictionary
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Set the value
        current[keys[-1]] = value

    def delete_value(self, key_path: str) -> bool:
        """
        Delete a value from the configuration using a dot-separated key path.

        Args:
            key_path: A dot-separated path to the value (e.g., "section.subsection.key").

        Returns:
            True if the value was deleted, False otherwise.
        """
        keys = key_path.split(".")
        current = self.config_data

        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                return False
            current = current[key]

        # Delete the value
        if keys[-1] in current:
            del current[keys[-1]]
            return True
        return False

    def get_sections(self) -> List[str]:
        """
        Get the top-level sections of the configuration.

        Returns:
            A list of top-level section names.
        """
        return list(self.config_data.keys())

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a specific section of the configuration.

        Args:
            section: The name of the section to get.

        Returns:
            The section data, or an empty dictionary if the section doesn't exist.
        """
        return self.config_data.get(section, {})

    def read_agents_config(self) -> Dict[str, Any]:
        """
        Read the agents configuration file.

        Returns:
            The agents configuration data.
        """
        agents_config_path = os.getenv(
            "SW_AGENTS_CONFIG", os.path.expanduser("./agents.toml")
        )
        try:
            config = ConfigManagement(agents_config_path)
            return config.get_config()
        except Exception:
            # If file doesn't exist or has errors, return empty config
            return {"agents": []}

    def write_agents_config(self, config_data: Dict[str, Any]) -> None:
        """
        Write the agents configuration to file.

        Args:
            config_data: The configuration data to write.
        """
        agents_config_path = os.getenv(
            "SW_AGENTS_CONFIG", os.path.expanduser("./agents.toml")
        )
        try:
            config = ConfigManagement(agents_config_path)
            config.update_config(config_data, merge=False)
            config.save_config()
        except FileNotFoundError:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(agents_config_path), exist_ok=True)

            # Create new config file
            with open(agents_config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)

    def read_mcp_config(self) -> Dict[str, Any]:
        """
        Read the MCP servers configuration file.

        Returns:
            The MCP servers configuration data.
        """
        mcp_config_path = os.getenv(
            "MCP_CONFIG_PATH", os.path.expanduser("./mcp_server.json")
        )
        try:
            with open(mcp_config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # If file doesn't exist or has errors, return empty config
            return {}

    def write_mcp_config(self, config_data: Dict[str, Any]) -> None:
        """
        Write the MCP servers configuration to file.

        Args:
            config_data: The configuration data to write.
        """
        mcp_config_path = os.getenv(
            "MCP_CONFIG_PATH", os.path.expanduser("./mcp_server.json")
        )
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(mcp_config_path), exist_ok=True)

            # Write to file
            with open(mcp_config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Error writing MCP configuration: {str(e)}")
