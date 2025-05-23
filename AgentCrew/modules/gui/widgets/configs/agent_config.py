from PySide6.QtWidgets import (
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
        self._is_dirty = False

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

        # Connect signals for editor fields to handle changes
        self.name_input.textChanged.connect(self._on_editor_field_changed)
        self.description_input.textChanged.connect(self._on_editor_field_changed)
        self.temperature_input.textChanged.connect(self._on_editor_field_changed)
        self.system_prompt_input.textChanged.connect(self._on_editor_field_changed)
        for checkbox in self.tool_checkboxes.values():
            checkbox.stateChanged.connect(self._on_editor_field_changed)

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
            self.set_editor_enabled(False)  # This will disable save_btn and reset dirty flag
            self.remove_agent_btn.setEnabled(False)
            return

        # Enable editor fields and remove button
        self.set_editor_enabled(True)  # Enables fields
        self.remove_agent_btn.setEnabled(True)

        # Get agent data
        agent_data = current.data(Qt.ItemDataRole.UserRole)

        # Temporarily block signals while populating form to avoid triggering _on_editor_field_changed
        editor_widgets = [
            self.name_input,
            self.description_input,
            self.temperature_input,
            self.system_prompt_input,
        ] + list(self.tool_checkboxes.values())

        for widget in editor_widgets:
            widget.blockSignals(True)

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

        for widget in editor_widgets:
            widget.blockSignals(False)

        # After loading data, mark as not dirty and disable save until a change is made
        self._is_dirty = False
        self.save_btn.setEnabled(False)

    def _on_editor_field_changed(self):
        """Mark configuration as dirty and enable save if an agent is selected and editor is active."""
        # Check if an agent is selected and the editor part is enabled
        if self.agents_list.currentItem() and self.name_input.isEnabled():
            if not self._is_dirty:
                self._is_dirty = True
            self.save_btn.setEnabled(True)

    def set_editor_enabled(self, enabled: bool):
        """Enable or disable the editor form."""
        self.name_input.setEnabled(enabled)
        self.description_input.setEnabled(enabled)
        self.temperature_input.setEnabled(enabled)
        self.system_prompt_input.setEnabled(enabled)

        for checkbox in self.tool_checkboxes.values():
            checkbox.setEnabled(enabled)
            
        if not enabled:
            self.save_btn.setEnabled(False)
            self._is_dirty = False  # Reset dirty state when editor is disabled

    def add_new_agent(self):
        """Add a new agent to the configuration."""
        # Create a new agent with default values
        new_agent = {
            "name": "NewAgent",
            "description": "Description for the new agent",
            "temperature": 0.5,
            "tools": ["memory", "clipboard"],
            "system_prompt": "You are a helpful assistant. Today is {current_date}.",
        }

        # Add to list
        item = QListWidgetItem(new_agent["name"])
        item.setData(Qt.ItemDataRole.UserRole, new_agent)
        self.agents_list.addItem(item)
        self.agents_list.setCurrentItem(item)  # This will trigger on_agent_selected

        # on_agent_selected populates fields, sets _is_dirty = False, and save_btn = False.
        # For a new agent, it's inherently "dirty" and should be saveable.
        self._is_dirty = True
        self.save_btn.setEnabled(True)

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

        # After saving, mark as not dirty and disable save button
        self._is_dirty = False
        self.save_btn.setEnabled(False)

        # Show success message with restart notification
        # QMessageBox.information(
        #     self,
        #     "Configuration Saved",
        #     f"Agent '{name}' saved successfully.\n\nPlease restart the application for changes to take effect.",
        # )

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
