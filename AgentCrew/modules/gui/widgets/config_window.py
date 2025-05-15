from PySide6.QtWidgets import (
    QDialog,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QScrollArea,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator

from AgentCrew.modules.config.config_management import ConfigManagement
from AgentCrew.modules.agents.manager import AgentManager


class ConfigWindow(QDialog):
    """Configuration window with tabs for Agents and MCP servers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(800, 600)

        # Flag to track if changes were made
        self.changes_made = False

        # Initialize config management
        self.config_manager = ConfigManagement()

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.agents_tab = AgentsConfigTab(self.config_manager)
        self.mcps_tab = MCPsConfigTab(self.config_manager)

        # Connect change signals
        self.agents_tab.config_changed.connect(self.on_config_changed)
        self.mcps_tab.config_changed.connect(self.on_config_changed)

        # Add tabs to widget
        self.tab_widget.addTab(self.agents_tab, "Agents")
        self.tab_widget.addTab(self.mcps_tab, "MCP Servers")

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)

        # Add buttons at the bottom
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.on_close)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e; /* Catppuccin Base */
                color: #cdd6f4; /* Catppuccin Text */
            }
            QTabWidget::pane {
                border: 1px solid #313244; /* Catppuccin Surface0 */
                background-color: #181825; /* Catppuccin Mantle */
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #313244; /* Catppuccin Surface0 */
                color: #cdd6f4; /* Catppuccin Text */
                padding: 8px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #45475a; /* Catppuccin Surface1 */
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #181825; /* Catppuccin Mantle (same as pane) */
                border-bottom-color: #181825; /* Catppuccin Mantle */
                color: #b4befe; /* Catppuccin Lavender for selected tab text */
            }
            QTabBar::tab:hover:!selected {
                background-color: #45475a; /* Catppuccin Surface1 */
            }
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec; /* Catppuccin Sapphire */
            }
            QPushButton:pressed {
                background-color: #b4befe; /* Catppuccin Lavender */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
            QListWidget {
                background-color: #1e1e2e; /* Catppuccin Base */
                border: 1px solid #313244; /* Catppuccin Surface0 */
                border-radius: 4px;
                padding: 4px;
                color: #cdd6f4; /* Catppuccin Text */
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 2px;
                color: #cdd6f4; /* Catppuccin Text */
                background-color: #1e1e2e; /* Catppuccin Base */
            }
            QListWidget::item:selected {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #b4befe; /* Catppuccin Lavender */
            }
            QListWidget::item:hover:!selected {
                background-color: #313244; /* Catppuccin Surface0 */
            }
            QLineEdit, QTextEdit {
                border: 1px solid #45475a; /* Catppuccin Surface1 */
                border-radius: 4px;
                padding: 6px;
                background-color: #313244; /* Catppuccin Surface0 */
                color: #cdd6f4; /* Catppuccin Text */
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #89b4fa; /* Catppuccin Blue */
            }
            QCheckBox {
                spacing: 8px;
                color: #cdd6f4; /* Catppuccin Text */
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 2px;
                background-color: #45475a; /* Catppuccin Surface1 */
                border: 1px solid #585b70; /* Catppuccin Surface2 */
            }
            QCheckBox::indicator:checked {
                background-color: #89b4fa; /* Catppuccin Blue */
                border: 1px solid #89b4fa; /* Catppuccin Blue */
            }
            QCheckBox::indicator:hover {
                border: 1px solid #b4befe; /* Catppuccin Lavender */
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #45475a; /* Catppuccin Surface1 */
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px; /* Ensure space for title */
                background-color: #181825; /* Catppuccin Mantle for groupbox background */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left; /* position at the top left */
                padding: 0 4px 4px 4px; /* padding for title */
                color: #b4befe; /* Catppuccin Lavender for title */
                background-color: #181825; /* Match groupbox background */
                left: 10px; /* Adjust to align with content */
            }
            QScrollArea {
                background-color: #181825; /* Catppuccin Mantle */
                border: none;
            }
            /* Style for the QWidget inside QScrollArea if needed */
            QScrollArea > QWidget > QWidget { /* Target the editor_widget */
                 background-color: #181825; /* Catppuccin Mantle */
            }
            QLabel {
                color: #cdd6f4; /* Catppuccin Text */
                padding: 2px; /* Add some padding to labels */
            }
            QSplitter::handle {
                background-color: #313244; /* Catppuccin Surface0 */
            }
            QSplitter::handle:hover {
                background-color: #45475a; /* Catppuccin Surface1 */
            }
            QSplitter::handle:pressed {
                background-color: #585b70; /* Catppuccin Surface2 */
            }
        """)

    def on_config_changed(self):
        """Track that changes were made to configuration"""
        self.changes_made = True

    def on_close(self):
        """Handle close button click with restart notification if needed"""
        # if self.changes_made:
        #     QMessageBox.information(
        #         self,
        #         "Configuration Changed",
        #         "Configuration changes have been saved.\n\nPlease restart the application for all changes to take effect."
        #     )
        self.accept()


class AgentsConfigTab(QWidget):
    """Tab for configuring agents."""

    # Add signal for configuration changes
    config_changed = Signal()

    def __init__(self, config_manager: ConfigManagement):
        super().__init__()
        self.config_manager = config_manager
        self.agent_manager = AgentManager.get_instance()
        self.available_tools = [
            "memory",
            "clipboard",
            "code_analysis",
            "web_search",
            "aider",
        ]

        # Load agents configuration
        self.agents_config = self.config_manager.read_agents_config()

        self.init_ui()
        self.load_agents()

    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QHBoxLayout()

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Agent list
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #181825;")  # Catppuccin Mantle
        left_layout = QVBoxLayout(left_panel)

        self.agents_list = QListWidget()
        self.agents_list.currentItemChanged.connect(self.on_agent_selected)

        # Buttons for agent list management
        list_buttons_layout = QHBoxLayout()
        self.add_agent_btn = QPushButton("Add")
        self.add_agent_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec; /* Catppuccin Sapphire */
            }
            QPushButton:pressed {
                background-color: #b4befe; /* Catppuccin Lavender */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)
        self.add_agent_btn.clicked.connect(self.add_new_agent)
        self.remove_agent_btn = QPushButton("Remove")
        self.remove_agent_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8; /* Catppuccin Red */
                color: #1e1e2e; /* Catppuccin Base (for contrast) */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eba0ac; /* Catppuccin Maroon (lighter red for hover) */
            }
            QPushButton:pressed {
                background-color: #e67e8a; /* A slightly darker/more intense red for pressed */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)
        self.remove_agent_btn.clicked.connect(self.remove_agent)
        self.remove_agent_btn.setEnabled(False)  # Disable until selection

        list_buttons_layout.addWidget(self.add_agent_btn)
        list_buttons_layout.addWidget(self.remove_agent_btn)

        left_layout.addWidget(QLabel("Agents:"))
        left_layout.addWidget(self.agents_list)
        left_layout.addLayout(list_buttons_layout)

        # Right panel - Agent editor
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        # right_panel.setStyleSheet("background-color: #181825;") # Set by QDialog stylesheet

        self.editor_widget = QWidget()
        self.editor_widget.setStyleSheet(
            "background-color: #181825;"
        )  # Catppuccin Mantle
        self.editor_layout = QVBoxLayout(self.editor_widget)

        # Form layout for agent properties
        form_layout = QFormLayout()

        # Name field
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)

        # Description field
        self.description_input = QLineEdit()
        form_layout.addRow("Description:", self.description_input)

        # Temperature field
        self.temperature_input = QLineEdit()
        self.temperature_input.setValidator(
            QDoubleValidator(0.0, 2.0, 1)
        )  # Range 0-2, 1 decimal
        self.temperature_input.setPlaceholderText("0.0 - 2.0")
        form_layout.addRow("Temperature:", self.temperature_input)

        # Tools selection
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout()

        self.tool_checkboxes = {}
        for tool in self.available_tools:
            checkbox = QCheckBox(tool)
            self.tool_checkboxes[tool] = checkbox
            tools_layout.addWidget(checkbox)

        tools_group.setLayout(tools_layout)

        # System prompt
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setMinimumHeight(200)

        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec; /* Catppuccin Sapphire */
            }
            QPushButton:pressed {
                background-color: #b4befe; /* Catppuccin Lavender */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)
        self.save_btn.clicked.connect(self.save_agent)
        self.save_btn.setEnabled(False)  # Disable until selection

        # Add all components to editor layout
        self.editor_layout.addLayout(form_layout)
        self.editor_layout.addWidget(tools_group)
        self.editor_layout.addWidget(QLabel("System Prompt:"))
        self.editor_layout.addWidget(self.system_prompt_input)
        self.editor_layout.addWidget(self.save_btn)
        self.editor_layout.addStretch()

        right_panel.setWidget(self.editor_widget)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 600])  # Initial sizes

        # Add splitter to main layout
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Disable editor initially
        self.set_editor_enabled(False)

    def load_agents(self):
        """Load agents from configuration."""
        self.agents_list.clear()

        agents = self.agents_config.get("agents", [])
        for agent in agents:
            item = QListWidgetItem(agent.get("name", "Unnamed Agent"))
            item.setData(Qt.ItemDataRole.UserRole, agent)
            self.agents_list.addItem(item)

    def on_agent_selected(self, current, previous):
        """Handle agent selection."""
        if current is None:
            self.set_editor_enabled(False)
            self.remove_agent_btn.setEnabled(False)
            return

        # Enable editor and remove button
        self.set_editor_enabled(True)
        self.remove_agent_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        # Get agent data
        agent_data = current.data(Qt.ItemDataRole.UserRole)

        # Populate form
        self.name_input.setText(agent_data.get("name", ""))
        self.description_input.setText(agent_data.get("description", ""))
        self.temperature_input.setText(str(agent_data.get("temperature", "0.5")))

        # Set tool checkboxes
        tools = agent_data.get("tools", [])
        for tool, checkbox in self.tool_checkboxes.items():
            checkbox.setChecked(tool in tools)

        # Set system prompt
        self.system_prompt_input.setText(agent_data.get("system_prompt", ""))

    def set_editor_enabled(self, enabled: bool):
        """Enable or disable the editor form."""
        self.name_input.setEnabled(enabled)
        self.description_input.setEnabled(enabled)
        self.temperature_input.setEnabled(enabled)
        self.system_prompt_input.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)

        for checkbox in self.tool_checkboxes.values():
            checkbox.setEnabled(enabled)

    def add_new_agent(self):
        """Add a new agent to the configuration."""
        # Create a new agent with default values
        new_agent = {
            "name": "New Agent",
            "description": "Description for the new agent",
            "temperature": 0.5,
            "tools": ["memory", "clipboard"],
            "system_prompt": "You are a helpful assistant. Today is {current_date}.",
        }

        # Add to list
        item = QListWidgetItem(new_agent["name"])
        item.setData(Qt.ItemDataRole.UserRole, new_agent)
        self.agents_list.addItem(item)
        self.agents_list.setCurrentItem(item)

        # Focus on name field for immediate editing
        self.name_input.setFocus()
        self.name_input.selectAll()

    def remove_agent(self):
        """Remove the selected agent."""
        current_item = self.agents_list.currentItem()
        if not current_item:
            return

        agent_name = current_item.text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the agent '{agent_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from list
            row = self.agents_list.row(current_item)
            self.agents_list.takeItem(row)

            # Clear editor
            self.set_editor_enabled(False)
            self.name_input.clear()
            self.description_input.clear()
            self.system_prompt_input.clear()
            for checkbox in self.tool_checkboxes.values():
                checkbox.setChecked(False)
            self.save_all_agents()

    def save_agent(self):
        """Save the current agent configuration."""
        current_item = self.agents_list.currentItem()
        if not current_item:
            return

        # Get values from form
        name = self.name_input.text().strip()
        description = self.description_input.text().strip()
        system_prompt = self.system_prompt_input.toPlainText().strip()

        # Get and validate temperature
        try:
            temperature = float(self.temperature_input.text().strip() or "0.5")
            temperature = max(0.0, min(2.0, temperature))  # Clamp between 0 and 2
        except ValueError:
            temperature = 0.5  # Default value if invalid

        # Validate
        if not name:
            QMessageBox.warning(self, "Validation Error", "Agent name cannot be empty.")
            return

        # Get selected tools
        tools = [
            tool
            for tool, checkbox in self.tool_checkboxes.items()
            if checkbox.isChecked()
        ]

        # Update agent data
        agent_data = {
            "name": name,
            "description": description,
            "temperature": temperature,
            "tools": tools,
            "system_prompt": system_prompt,
        }

        # Update item in list
        current_item.setText(name)
        current_item.setData(Qt.ItemDataRole.UserRole, agent_data)

        # Save all agents to config
        self.save_all_agents()

        # Show success message with restart notification
        QMessageBox.information(
            self,
            "Configuration Saved",
            f"Agent '{name}' saved successfully.\n\nPlease restart the application for changes to take effect.",
        )

    def save_all_agents(self):
        """Save all agents to the configuration file."""
        agents = []

        for i in range(self.agents_list.count()):
            item = self.agents_list.item(i)
            agent_data = item.data(Qt.ItemDataRole.UserRole)
            agents.append(agent_data)

        # Update config
        self.agents_config["agents"] = agents

        # Save to file
        self.config_manager.write_agents_config(self.agents_config)

        # Emit signal that configuration changed
        self.config_changed.emit()


class MCPsConfigTab(QWidget):
    """Tab for configuring MCP servers."""

    # Add signal for configuration changes
    config_changed = Signal()

    def __init__(self, config_manager: ConfigManagement):
        super().__init__()
        self.config_manager = config_manager
        self.agent_manager = AgentManager.get_instance()

        # Load MCP configuration
        self.mcps_config = self.config_manager.read_mcp_config()

        self.init_ui()
        self.load_mcps()

    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QHBoxLayout()

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - MCP server list
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #181825;")  # Catppuccin Mantle
        left_layout = QVBoxLayout(left_panel)

        self.mcps_list = QListWidget()
        self.mcps_list.currentItemChanged.connect(self.on_mcp_selected)

        # Buttons for MCP list management
        list_buttons_layout = QHBoxLayout()
        self.add_mcp_btn = QPushButton("Add")
        self.add_mcp_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec; /* Catppuccin Sapphire */
            }
            QPushButton:pressed {
                background-color: #b4befe; /* Catppuccin Lavender */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)
        self.add_mcp_btn.clicked.connect(self.add_new_mcp)
        self.remove_mcp_btn = QPushButton("Remove")
        self.remove_mcp_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8; /* Catppuccin Red */
                color: #1e1e2e; /* Catppuccin Base (for contrast) */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eba0ac; /* Catppuccin Maroon (lighter red for hover) */
            }
            QPushButton:pressed {
                background-color: #e67e8a; /* A slightly darker/more intense red for pressed */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)
        self.remove_mcp_btn.clicked.connect(self.remove_mcp)
        self.remove_mcp_btn.setEnabled(False)  # Disable until selection

        list_buttons_layout.addWidget(self.add_mcp_btn)
        list_buttons_layout.addWidget(self.remove_mcp_btn)

        left_layout.addWidget(QLabel("MCP Servers:"))
        left_layout.addWidget(self.mcps_list)
        left_layout.addLayout(list_buttons_layout)

        # Right panel - MCP editor
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        # right_panel.setStyleSheet("background-color: #181825;") # Set by QDialog stylesheet

        self.editor_widget = QWidget()
        self.editor_widget.setStyleSheet(
            "background-color: #181825;"
        )  # Catppuccin Mantle
        self.editor_layout = QVBoxLayout(self.editor_widget)

        # Form layout for MCP properties
        form_layout = QFormLayout()

        # Name field
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)

        # Command field
        self.command_input = QLineEdit()
        form_layout.addRow("Command:", self.command_input)

        # Arguments section
        args_group = QGroupBox("Arguments")
        self.args_layout = QVBoxLayout()
        self.arg_inputs = []

        # Add button for arguments
        args_btn_layout = QHBoxLayout()
        self.add_arg_btn = QPushButton("Add Argument")
        self.add_arg_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec; /* Catppuccin Sapphire */
            }
            QPushButton:pressed {
                background-color: #b4befe; /* Catppuccin Lavender */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)
        self.add_arg_btn.clicked.connect(lambda: self.add_argument_field(""))
        args_btn_layout.addWidget(self.add_arg_btn)
        args_btn_layout.addStretch()

        self.args_layout.addLayout(args_btn_layout)
        args_group.setLayout(self.args_layout)

        # Environment variables section
        env_group = QGroupBox("Environment Variables")
        self.env_layout = QVBoxLayout()
        self.env_inputs = []

        # Add button for env vars
        env_btn_layout = QHBoxLayout()
        self.add_env_btn = QPushButton("Add Environment Variable")
        self.add_env_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec; /* Catppuccin Sapphire */
            }
            QPushButton:pressed {
                background-color: #b4befe; /* Catppuccin Lavender */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)
        self.add_env_btn.clicked.connect(lambda: self.add_env_field("", ""))
        env_btn_layout.addWidget(self.add_env_btn)
        env_btn_layout.addStretch()

        self.env_layout.addLayout(env_btn_layout)
        env_group.setLayout(self.env_layout)

        # Enabled for agents section
        enabled_group = QGroupBox("Enabled For Agents")
        enabled_layout = QVBoxLayout()

        # Get available agents
        self.available_agents = list(self.agent_manager.agents.keys())

        self.agent_checkboxes = {}
        for agent in self.available_agents:
            checkbox = QCheckBox(agent)
            self.agent_checkboxes[agent] = checkbox
            enabled_layout.addWidget(checkbox)

        enabled_group.setLayout(enabled_layout)

        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec; /* Catppuccin Sapphire */
            }
            QPushButton:pressed {
                background-color: #b4befe; /* Catppuccin Lavender */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)
        self.save_btn.clicked.connect(self.save_mcp)
        self.save_btn.setEnabled(False)  # Disable until selection

        # Add all components to editor layout
        self.editor_layout.addLayout(form_layout)
        self.editor_layout.addWidget(args_group)
        self.editor_layout.addWidget(env_group)
        self.editor_layout.addWidget(enabled_group)
        self.editor_layout.addWidget(self.save_btn)
        self.editor_layout.addStretch()

        right_panel.setWidget(self.editor_widget)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 600])  # Initial sizes

        # Add splitter to main layout
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Disable editor initially
        self.set_editor_enabled(False)

    def load_mcps(self):
        """Load MCP servers from configuration."""
        self.mcps_list.clear()

        for server_id, server_config in self.mcps_config.items():
            item = QListWidgetItem(server_config.get("name", server_id))
            item.setData(Qt.ItemDataRole.UserRole, (server_id, server_config))
            self.mcps_list.addItem(item)

    def on_mcp_selected(self, current, previous):
        """Handle MCP server selection."""
        if current is None:
            self.set_editor_enabled(False)
            self.remove_mcp_btn.setEnabled(False)
            return

        # Enable editor and remove button
        self.set_editor_enabled(True)
        self.remove_mcp_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        # Get MCP data
        server_id, server_config = current.data(Qt.ItemDataRole.UserRole)

        # Populate form
        self.name_input.setText(server_config.get("name", ""))
        self.command_input.setText(server_config.get("command", ""))

        # Clear existing argument fields
        self.clear_argument_fields()

        # Add argument fields
        args = server_config.get("args", [])
        for arg in args:
            self.add_argument_field(arg)

        # Clear existing env fields
        self.clear_env_fields()

        # Add env fields
        env = server_config.get("env", {})
        for key, value in env.items():
            self.add_env_field(key, value)

        # Set agent checkboxes
        enabled_agents = server_config.get("enabledForAgents", [])
        for agent, checkbox in self.agent_checkboxes.items():
            checkbox.setChecked(agent in enabled_agents)

    def set_editor_enabled(self, enabled: bool):
        """Enable or disable the editor form."""
        self.name_input.setEnabled(enabled)
        self.command_input.setEnabled(enabled)
        self.add_arg_btn.setEnabled(enabled)
        self.add_env_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)

        for checkbox in self.agent_checkboxes.values():
            checkbox.setEnabled(enabled)

        for arg_input in self.arg_inputs:
            arg_input["input"].setEnabled(enabled)
            arg_input["remove_btn"].setEnabled(enabled)

        for env_input in self.env_inputs:
            env_input["key_input"].setEnabled(enabled)
            env_input["value_input"].setEnabled(enabled)
            env_input["remove_btn"].setEnabled(enabled)

    def add_argument_field(self, value=""):
        """Add a field for an argument."""
        arg_layout = QHBoxLayout()

        arg_input = QLineEdit()
        arg_input.setText(str(value))

        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumWidth(80)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8; /* Catppuccin Red */
                color: #1e1e2e; /* Catppuccin Base (for contrast) */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eba0ac; /* Catppuccin Maroon (lighter red for hover) */
            }
            QPushButton:pressed {
                background-color: #e67e8a; /* A slightly darker/more intense red for pressed */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)

        arg_layout.addWidget(arg_input)
        arg_layout.addWidget(remove_btn)

        # Insert before the add button
        self.args_layout.insertLayout(len(self.arg_inputs), arg_layout)

        # Store references
        arg_data = {"layout": arg_layout, "input": arg_input, "remove_btn": remove_btn}
        self.arg_inputs.append(arg_data)

        # Connect remove button
        remove_btn.clicked.connect(lambda: self.remove_argument_field(arg_data))

        return arg_data

    def remove_argument_field(self, arg_data):
        """Remove an argument field."""
        # Remove from layout
        self.args_layout.removeItem(arg_data["layout"])

        # Delete widgets
        arg_data["input"].deleteLater()
        arg_data["remove_btn"].deleteLater()

        # Remove from list
        self.arg_inputs.remove(arg_data)

    def clear_argument_fields(self):
        """Clear all argument fields."""
        while self.arg_inputs:
            self.remove_argument_field(self.arg_inputs[0])

    def add_env_field(self, key="", value=""):
        """Add a field for an environment variable."""
        env_layout = QHBoxLayout()

        key_input = QLineEdit()
        key_input.setText(str(key))
        key_input.setPlaceholderText("Key")

        value_input = QLineEdit()
        value_input.setText(str(value))
        value_input.setPlaceholderText("Value")

        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumWidth(80)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8; /* Catppuccin Red */
                color: #1e1e2e; /* Catppuccin Base (for contrast) */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eba0ac; /* Catppuccin Maroon (lighter red for hover) */
            }
            QPushButton:pressed {
                background-color: #e67e8a; /* A slightly darker/more intense red for pressed */
            }
            QPushButton:disabled {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #6c7086; /* Catppuccin Overlay0 */
            }
        """)

        env_layout.addWidget(key_input)
        env_layout.addWidget(value_input)
        env_layout.addWidget(remove_btn)

        # Insert before the add button
        self.env_layout.insertLayout(len(self.env_inputs), env_layout)

        # Store references
        env_data = {
            "layout": env_layout,
            "key_input": key_input,
            "value_input": value_input,
            "remove_btn": remove_btn,
        }
        self.env_inputs.append(env_data)

        # Connect remove button
        remove_btn.clicked.connect(lambda: self.remove_env_field(env_data))

        return env_data

    def remove_env_field(self, env_data):
        """Remove an environment variable field."""
        # Remove from layout
        self.env_layout.removeItem(env_data["layout"])

        # Delete widgets
        env_data["key_input"].deleteLater()
        env_data["value_input"].deleteLater()
        env_data["remove_btn"].deleteLater()

        # Remove from list
        self.env_inputs.remove(env_data)

    def clear_env_fields(self):
        """Clear all environment variable fields."""
        while self.env_inputs:
            self.remove_env_field(self.env_inputs[0])

    def add_new_mcp(self):
        """Add a new MCP server to the configuration."""
        # Create a new server with default values
        server_id = f"new_server_{len(self.mcps_config) + 1}"
        new_server = {
            "name": "New Server",
            "command": "docker",
            "args": ["run", "-i", "--rm"],
            "env": {},
            "enabledForAgents": [],
        }

        # Add to list
        item = QListWidgetItem(new_server["name"])
        item.setData(Qt.ItemDataRole.UserRole, (server_id, new_server))
        self.mcps_list.addItem(item)
        self.mcps_list.setCurrentItem(item)

        # Focus on name field for immediate editing
        self.name_input.setFocus()
        self.name_input.selectAll()

    def remove_mcp(self):
        """Remove the selected MCP server."""
        current_item = self.mcps_list.currentItem()
        if not current_item:
            return

        server_id, server_config = current_item.data(Qt.ItemDataRole.UserRole)
        server_name = server_config.get("name", server_id)

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the MCP server '{server_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from list
            row = self.mcps_list.row(current_item)
            self.mcps_list.takeItem(row)

            # Clear editor
            self.set_editor_enabled(False)
            self.name_input.clear()
            self.command_input.clear()
            self.clear_argument_fields()
            self.clear_env_fields()
            for checkbox in self.agent_checkboxes.values():
                checkbox.setChecked(False)

    def save_mcp(self):
        """Save the current MCP server configuration."""
        current_item = self.mcps_list.currentItem()
        if not current_item:
            return

        server_id, old_config = current_item.data(Qt.ItemDataRole.UserRole)

        # Get values from form
        name = self.name_input.text().strip()
        command = self.command_input.text().strip()

        # Validate
        if not name:
            QMessageBox.warning(
                self, "Validation Error", "Server name cannot be empty."
            )
            return

        if not command:
            QMessageBox.warning(self, "Validation Error", "Command cannot be empty.")
            return

        # Get arguments
        args = []
        for arg_data in self.arg_inputs:
            arg_value = arg_data["input"].text().strip()
            if arg_value:
                args.append(arg_value)

        # Get environment variables
        env = {}
        for env_data in self.env_inputs:
            key = env_data["key_input"].text().strip()
            value = env_data["value_input"].text().strip()
            if key:
                env[key] = value

        # Get enabled agents
        enabled_agents = [
            agent
            for agent, checkbox in self.agent_checkboxes.items()
            if checkbox.isChecked()
        ]

        # Update server data
        server_config = {
            "name": name,
            "command": command,
            "args": args,
            "env": env,
            "enabledForAgents": enabled_agents,
        }

        # Update item in list
        current_item.setText(name)
        current_item.setData(Qt.ItemDataRole.UserRole, (server_id, server_config))

        # Save all servers to config
        self.save_all_mcps()

        # Show success message with restart notification
        QMessageBox.information(
            self,
            "Configuration Saved",
            f"MCP server '{name}' saved successfully.\n\nPlease restart the application for changes to take effect.",
        )

    def save_all_mcps(self):
        """Save all MCP servers to the configuration file."""
        mcps_config = {}

        for i in range(self.mcps_list.count()):
            item = self.mcps_list.item(i)
            server_id, server_config = item.data(Qt.ItemDataRole.UserRole)
            mcps_config[server_id] = server_config

        # Save to file
        self.config_manager.write_mcp_config(mcps_config)

        # Update local copy
        self.mcps_config = mcps_config

        # Emit signal that configuration changed
        self.config_changed.emit()
