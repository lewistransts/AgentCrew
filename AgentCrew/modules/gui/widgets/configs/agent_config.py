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
    QMenu,  # Added
    QStackedWidget,  # Added
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator

from AgentCrew.modules.config.config_management import ConfigManagement
from AgentCrew.modules.agents import AgentManager


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

        self.add_agent_menu_btn = QPushButton("Add Agent")
        self.add_agent_menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                padding-left: 12px; /* Add some padding for text */
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
            QPushButton::menu-indicator {
                /* image: url(myindicator.png); Adjust if using a custom image */
                subcontrol-origin: padding;
                subcontrol-position: right center;
                right: 5px; /* Adjust as needed to position from the right edge */
                width: 16px; /* Ensure there's enough space for the indicator */
            }
        """)
        add_agent_menu = QMenu(self)
        add_agent_menu.setStyleSheet("""
            QMenu {
                background-color: #181825; /* Catppuccin Mantle */
                color: #cdd6f4; /* Catppuccin Text */
                border: 1px solid #313244; /* Catppuccin Surface0 */
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                border-radius: 3px;
            }
            QMenu::separator {
                height: 1px;
                background-color: #313244; /* Catppuccin Surface0 */
                margin-left: 5px;
                margin-right: 5px;
            }
        """)
        add_local_action = add_agent_menu.addAction("Add Local Agent")
        add_remote_action = add_agent_menu.addAction("Add Remote Agent")
        self.add_agent_menu_btn.setMenu(add_agent_menu)

        add_local_action.triggered.connect(self.add_new_local_agent)
        add_remote_action.triggered.connect(self.add_new_remote_agent)

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

        list_buttons_layout.addWidget(
            self.add_agent_menu_btn
        )  # Changed from self.add_agent_btn
        list_buttons_layout.addWidget(self.remove_agent_btn)

        left_layout.addWidget(QLabel("Agents:"))
        left_layout.addWidget(self.agents_list)
        left_layout.addLayout(list_buttons_layout)

        # Right panel - Agent editor
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        # right_panel.setStyleSheet("background-color: #181825;") # Set by QDialog stylesheet

        editor_container_widget = (
            QWidget()
        )  # Container for stacked widget and save button
        editor_container_widget.setStyleSheet("background-color: #181825;")
        self.editor_layout = QVBoxLayout(
            editor_container_widget
        )  # editor_layout now on container

        self.editor_stacked_widget = QStackedWidget()

        # Local Agent Editor Widget
        self.local_agent_editor_widget = QWidget()
        local_agent_layout = QVBoxLayout(self.local_agent_editor_widget)
        local_form_layout = QFormLayout()

        self.name_input = QLineEdit()  # This is for Local Agent Name
        local_form_layout.addRow("Name:", self.name_input)
        self.description_input = QLineEdit()
        local_form_layout.addRow("Description:", self.description_input)
        self.temperature_input = QLineEdit()
        self.temperature_input.setValidator(QDoubleValidator(0.0, 2.0, 1))
        self.temperature_input.setPlaceholderText("0.0 - 2.0")
        local_form_layout.addRow("Temperature:", self.temperature_input)

        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout()
        self.tool_checkboxes = {}
        for tool in self.available_tools:
            checkbox = QCheckBox(tool)
            self.tool_checkboxes[tool] = checkbox
            tools_layout.addWidget(checkbox)
        tools_group.setLayout(tools_layout)

        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setMinimumHeight(200)

        local_agent_layout.addLayout(local_form_layout)
        local_agent_layout.addWidget(tools_group)
        local_agent_layout.addWidget(QLabel("System Prompt:"))
        local_agent_layout.addWidget(self.system_prompt_input)
        local_agent_layout.addStretch()

        # Remote Agent Editor Widget
        self.remote_agent_editor_widget = QWidget()
        remote_agent_layout = QVBoxLayout(self.remote_agent_editor_widget)
        remote_form_layout = QFormLayout()

        self.remote_name_input = QLineEdit()
        remote_form_layout.addRow("Name:", self.remote_name_input)
        self.remote_base_url_input = QLineEdit()
        self.remote_base_url_input.setPlaceholderText("e.g., http://localhost:8000")
        remote_form_layout.addRow("Base URL:", self.remote_base_url_input)

        remote_agent_layout.addLayout(remote_form_layout)
        remote_agent_layout.addStretch()

        self.editor_stacked_widget.addWidget(self.local_agent_editor_widget)
        self.editor_stacked_widget.addWidget(self.remote_agent_editor_widget)

        # Save button (common to both editors)
        self.save_btn = QPushButton("Save")
        # ... (save_btn styling and connect remains the same)
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
        self.save_btn.setEnabled(False)

        # Add stacked widget and save button to editor_layout
        self.editor_layout.addWidget(self.editor_stacked_widget)  # Changed
        self.editor_layout.addWidget(self.save_btn)
        # self.editor_layout.addStretch() # Removed, stretch is within individual editors

        # Connect signals for editor fields to handle changes
        # Local agent fields
        self.name_input.textChanged.connect(self._on_editor_field_changed)
        self.description_input.textChanged.connect(self._on_editor_field_changed)
        self.temperature_input.textChanged.connect(self._on_editor_field_changed)
        self.system_prompt_input.textChanged.connect(self._on_editor_field_changed)
        for checkbox in self.tool_checkboxes.values():
            checkbox.stateChanged.connect(self._on_editor_field_changed)
        # Remote agent fields
        self.remote_name_input.textChanged.connect(self._on_editor_field_changed)
        self.remote_base_url_input.textChanged.connect(self._on_editor_field_changed)

        right_panel.setWidget(editor_container_widget)  # Set the container widget

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

        # Load local agents
        local_agents = self.agents_config.get("agents", [])
        for agent_conf in local_agents:
            item_data = agent_conf.copy()
            item_data["agent_type"] = "local"
            item = QListWidgetItem(item_data.get("name", "Unnamed Local Agent"))
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.agents_list.addItem(item)

        # Load remote agents
        remote_agents = self.agents_config.get("remote_agents", [])
        for agent_conf in remote_agents:
            item_data = agent_conf.copy()
            item_data["agent_type"] = "remote"
            item = QListWidgetItem(item_data.get("name", "Unnamed Remote Agent"))
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.agents_list.addItem(item)

    def on_agent_selected(self, current, previous):
        """Handle agent selection."""
        if current is None:
            self.set_editor_enabled(False)
            self.remove_agent_btn.setEnabled(False)
            # Optionally hide both editors or show a placeholder
            # self.editor_stacked_widget.setCurrentIndex(-1) # or a placeholder widget index
            return

        self.set_editor_enabled(True)
        self.remove_agent_btn.setEnabled(True)

        agent_data = current.data(Qt.ItemDataRole.UserRole)
        agent_type = agent_data.get(
            "agent_type", "local"
        )  # Default to local if type is missing

        # Temporarily block signals
        all_editor_widgets = [
            self.name_input,
            self.description_input,
            self.temperature_input,
            self.system_prompt_input,
            self.remote_name_input,
            self.remote_base_url_input,
        ] + list(self.tool_checkboxes.values())
        for widget in all_editor_widgets:
            widget.blockSignals(True)

        if agent_type == "local":
            self.editor_stacked_widget.setCurrentWidget(self.local_agent_editor_widget)
            self.name_input.setText(agent_data.get("name", ""))
            self.description_input.setText(agent_data.get("description", ""))
            self.temperature_input.setText(str(agent_data.get("temperature", "0.5")))
            tools = agent_data.get("tools", [])
            for tool, checkbox in self.tool_checkboxes.items():
                checkbox.setChecked(tool in tools)
            self.system_prompt_input.setText(agent_data.get("system_prompt", ""))
            # Clear remote fields just in case
            self.remote_name_input.clear()
            self.remote_base_url_input.clear()
        elif agent_type == "remote":
            self.editor_stacked_widget.setCurrentWidget(self.remote_agent_editor_widget)
            self.remote_name_input.setText(agent_data.get("name", ""))
            self.remote_base_url_input.setText(agent_data.get("base_url", ""))
            # Clear local fields
            self.name_input.clear()
            self.description_input.clear()
            self.temperature_input.clear()
            self.system_prompt_input.clear()
            for checkbox in self.tool_checkboxes.values():
                checkbox.setChecked(False)

        for widget in all_editor_widgets:
            widget.blockSignals(False)

        self._is_dirty = False
        self.save_btn.setEnabled(False)

    def _on_editor_field_changed(self):
        """Mark configuration as dirty and enable save if an agent is selected and editor is active."""
        if self.agents_list.currentItem():
            current_editor_widget = self.editor_stacked_widget.currentWidget()
            is_editor_active = False
            if (
                current_editor_widget == self.local_agent_editor_widget
                and self.name_input.isEnabled()
            ):
                is_editor_active = True
            elif (
                current_editor_widget == self.remote_agent_editor_widget
                and self.remote_name_input.isEnabled()
            ):
                is_editor_active = True

            if is_editor_active:
                if not self._is_dirty:
                    self._is_dirty = True
                self.save_btn.setEnabled(True)

    def set_editor_enabled(self, enabled: bool):
        """Enable or disable all editor form fields."""
        # Local agent fields
        self.name_input.setEnabled(enabled)
        self.description_input.setEnabled(enabled)
        self.temperature_input.setEnabled(enabled)
        self.system_prompt_input.setEnabled(enabled)
        for checkbox in self.tool_checkboxes.values():
            checkbox.setEnabled(enabled)

        # Remote agent fields
        self.remote_name_input.setEnabled(enabled)
        self.remote_base_url_input.setEnabled(enabled)

        if not enabled:
            # Clear all fields when disabling
            self.name_input.clear()
            self.description_input.clear()
            self.temperature_input.clear()
            self.system_prompt_input.clear()
            for checkbox in self.tool_checkboxes.values():
                checkbox.setChecked(False)
            self.remote_name_input.clear()
            self.remote_base_url_input.clear()

            self.save_btn.setEnabled(False)
            self._is_dirty = False
            # self.editor_stacked_widget.setCurrentIndex(-1) # Optionally hide content

    def add_new_local_agent(self):
        """Add a new local agent to the configuration."""
        new_agent_data = {
            "name": "NewLocalAgent",
            "description": "Description for the new local agent",
            "temperature": 0.5,
            "tools": ["memory", "clipboard"],
            "system_prompt": "You are a helpful assistant. Today is {current_date}.",
            "agent_type": "local",
        }

        item = QListWidgetItem(new_agent_data["name"])
        item.setData(Qt.ItemDataRole.UserRole, new_agent_data)
        self.agents_list.addItem(item)
        self.agents_list.setCurrentItem(item)  # Triggers on_agent_selected

        # on_agent_selected will switch to local editor and populate.
        # Mark as dirty and enable save.
        self._is_dirty = True
        self.save_btn.setEnabled(True)
        self.name_input.setFocus()
        self.name_input.selectAll()

    def add_new_remote_agent(self):
        """Add a new remote agent to the configuration."""
        new_agent_data = {
            "name": "NewRemoteAgent",
            "base_url": "http://localhost:8000",
            "agent_type": "remote",
        }

        item = QListWidgetItem(new_agent_data["name"])
        item.setData(Qt.ItemDataRole.UserRole, new_agent_data)
        self.agents_list.addItem(item)
        self.agents_list.setCurrentItem(item)  # Triggers on_agent_selected

        # on_agent_selected will switch to remote editor and populate.
        # Mark as dirty and enable save.
        self._is_dirty = True
        self.save_btn.setEnabled(True)
        self.remote_name_input.setFocus()
        self.remote_name_input.selectAll()

    def remove_agent(self):
        """Remove the selected agent."""
        current_item = self.agents_list.currentItem()
        if not current_item:
            return

        agent_data = current_item.data(Qt.ItemDataRole.UserRole)
        agent_name = agent_data.get("name", "this agent")

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the agent '{agent_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            row = self.agents_list.row(current_item)
            self.agents_list.takeItem(row)

            # set_editor_enabled(False) is called by on_agent_selected when currentItem becomes None
            # or when a new item is selected. If list becomes empty, on_agent_selected(None, old_item) is called.
            if self.agents_list.count() == 0:
                self.set_editor_enabled(False)  # Explicitly disable if list is empty
                self.remove_agent_btn.setEnabled(False)

            self.save_all_agents()

    def save_agent(self):
        """Save the current agent configuration."""
        current_item = self.agents_list.currentItem()
        if not current_item:
            return

        agent_data_from_list = current_item.data(Qt.ItemDataRole.UserRole)
        agent_type = agent_data_from_list.get("agent_type", "local")

        updated_agent_data = {}

        if agent_type == "local":
            name = self.name_input.text().strip()
            description = self.description_input.text().strip()
            system_prompt = self.system_prompt_input.toPlainText().strip()
            try:
                temperature = float(self.temperature_input.text().strip() or "0.5")
                temperature = max(0.0, min(2.0, temperature))
            except ValueError:
                temperature = 0.5

            if not name:
                QMessageBox.warning(
                    self, "Validation Error", "Local Agent name cannot be empty."
                )
                return

            tools = [t for t, cb in self.tool_checkboxes.items() if cb.isChecked()]
            updated_agent_data = {
                "name": name,
                "description": description,
                "temperature": temperature,
                "tools": tools,
                "system_prompt": system_prompt,
                "agent_type": "local",
            }
            current_item.setText(name)
        elif agent_type == "remote":
            name = self.remote_name_input.text().strip()
            base_url = self.remote_base_url_input.text().strip()

            if not name:
                QMessageBox.warning(
                    self, "Validation Error", "Remote Agent name cannot be empty."
                )
                return
            if not base_url:  # Basic validation for URL
                QMessageBox.warning(
                    self, "Validation Error", "Remote Agent Base URL cannot be empty."
                )
                return

            updated_agent_data = {
                "name": name,
                "base_url": base_url,
                "agent_type": "remote",
            }
            current_item.setText(name)

        current_item.setData(Qt.ItemDataRole.UserRole, updated_agent_data)
        self.save_all_agents()
        self._is_dirty = False
        self.save_btn.setEnabled(False)

    def save_all_agents(self):
        """Save all agents to the configuration file."""
        local_agents_list = []
        remote_agents_list = []

        for i in range(self.agents_list.count()):
            item = self.agents_list.item(i)
            agent_data = item.data(Qt.ItemDataRole.UserRole)

            # Create a copy for saving, remove UI-specific 'agent_type'
            config_data = agent_data.copy()
            agent_type_for_sorting = config_data.pop(
                "agent_type", "local"
            )  # Default to local if missing

            if agent_type_for_sorting == "local":
                local_agents_list.append(config_data)
            elif agent_type_for_sorting == "remote":
                remote_agents_list.append(config_data)

        self.agents_config["agents"] = local_agents_list
        self.agents_config["remote_agents"] = remote_agents_list

        self.config_manager.write_agents_config(self.agents_config)
        self.config_changed.emit()
