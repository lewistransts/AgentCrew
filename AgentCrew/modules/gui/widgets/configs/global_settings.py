from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtCore import Signal

from AgentCrew.modules.config import ConfigManagement
from AgentCrew.modules.gui.themes import StyleProvider


class SettingsTab(QWidget):
    """Tab for configuring global settings like API keys."""

    config_changed = Signal()

    API_KEY_DEFINITIONS = [
        {
            "label": "Anthropic API Key:",
            "key_name": "ANTHROPIC_API_KEY",
            "placeholder": "e.g., sk-ant-...",
        },
        {
            "label": "Gemini API Key:",
            "key_name": "GEMINI_API_KEY",
            "placeholder": "e.g., AIzaSy...",
        },
        {
            "label": "OpenAI API Key:",
            "key_name": "OPENAI_API_KEY",
            "placeholder": "e.g., sk-...",
        },
        {
            "label": "Groq API Key:",
            "key_name": "GROQ_API_KEY",
            "placeholder": "e.g., gsk_...",
        },
        {
            "label": "DeepInfra API Key:",
            "key_name": "DEEPINFRA_API_KEY",
            "placeholder": "e.g., ...",
        },
        {
            "label": "Github Copilot API Key:",
            "key_name": "GITHUB_COPILOT_API_KEY",
            "placeholder": "e.g., ...",
        },
        {
            "label": "Tavily API Key:",
            "key_name": "TAVILY_API_KEY",
            "placeholder": "e.g., tvly-...",
        },
        {
            "label": "Voyage API Key:",
            "key_name": "VOYAGE_API_KEY",
            "placeholder": "e.g., pa-...",
        },
    ]

    def __init__(self, config_manager: ConfigManagement):
        super().__init__()
        self.config_manager = config_manager
        self.global_config = self.config_manager.read_global_config_data()

        self.api_key_inputs = {}

        self.init_ui()
        self.load_api_keys()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        style_provider = StyleProvider()
        scroll_area.setStyleSheet(style_provider.get_sidebar_style())

        editor_widget = QWidget()
        editor_widget.setStyleSheet(style_provider.get_sidebar_style())
        form_layout = QFormLayout(editor_widget)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(10)

        api_keys_group = QGroupBox("API Keys")
        api_keys_group.setStyleSheet("background-color: #1e1e2e;")
        api_keys_form_layout = QFormLayout()

        for item in self.API_KEY_DEFINITIONS:
            label = QLabel(item["label"])
            line_edit = QLineEdit()
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            line_edit.setPlaceholderText(item["placeholder"])
            self.api_key_inputs[item["key_name"]] = line_edit
            api_keys_form_layout.addRow(label, line_edit)

        api_keys_group.setLayout(api_keys_form_layout)
        form_layout.addWidget(api_keys_group)

        self.save_btn = QPushButton("Save API Keys")
        self.save_btn.setStyleSheet(style_provider.get_button_style("primary"))
        self.save_btn.clicked.connect(self.save_api_keys)

        form_layout.addWidget(self.save_btn)
        editor_widget.setLayout(form_layout)
        scroll_area.setWidget(editor_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def load_api_keys(self):
        api_keys_data = self.global_config.get("api_keys", {})
        for key_name, line_edit in self.api_key_inputs.items():
            line_edit.setText(api_keys_data.get(key_name, ""))

    def save_api_keys(self):
        if "api_keys" not in self.global_config:
            self.global_config["api_keys"] = {}

        for key_name, line_edit in self.api_key_inputs.items():
            self.global_config["api_keys"][key_name] = line_edit.text()

        try:
            self.config_manager.write_global_config_data(self.global_config)
            QMessageBox.information(
                self,
                "Settings Saved",
                "API Keys saved successfully.\n\nA restart may be required for all changes to take effect.",
            )
            self.config_changed.emit()
        except Exception as e:
            QMessageBox.critical(
                self, "Error Saving Settings", f"Could not save API keys: {str(e)}"
            )
