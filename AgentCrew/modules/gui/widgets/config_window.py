from PySide6.QtWidgets import (
    QDialog,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)

from AgentCrew.modules.config.config_management import ConfigManagement
from .configs.custom_llm_provider import CustomLLMProvidersConfigTab
from .configs.global_settings import SettingsTab
from .configs.agent_config import AgentsConfigTab
from .configs.mcp_config import MCPsConfigTab


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
        self.settings_tab = SettingsTab(self.config_manager)
        self.custom_llm_providers_tab = CustomLLMProvidersConfigTab(self.config_manager)

        # Connect change signals
        self.agents_tab.config_changed.connect(self.on_config_changed)
        self.mcps_tab.config_changed.connect(self.on_config_changed)
        self.settings_tab.config_changed.connect(self.on_config_changed)
        self.custom_llm_providers_tab.config_changed.connect(self.on_config_changed)

        # Add tabs to widget
        self.tab_widget.addTab(self.agents_tab, "Agents")
        self.tab_widget.addTab(self.mcps_tab, "MCP Servers")
        self.tab_widget.addTab(self.custom_llm_providers_tab, "Custom LLMs")
        self.tab_widget.addTab(self.settings_tab, "Settings")

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
