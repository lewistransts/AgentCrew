from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtCore import Qt, Signal
from AgentCrew.modules import logger

from AgentCrew.modules.config.config_management import ConfigManagement


class CustomLLMProvidersConfigTab(QWidget):
    """Tab for configuring custom OpenAI-compatible LLM providers."""

    # Add signal for configuration changes
    config_changed = Signal()

    def __init__(self, config_manager: ConfigManagement, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.providers_data = []  # Initialize to store provider dictionaries

        self.init_ui()
        self.load_providers()

    def load_providers(self):
        """Load providers from configuration and populate the list widget."""
        self.providers_data = self.config_manager.read_custom_llm_providers_config()
        self.providers_list_widget.clear()

        for provider_dict in self.providers_data:
            item = QListWidgetItem(provider_dict.get("name", "Unnamed Provider"))
            item.setData(Qt.ItemDataRole.UserRole, provider_dict)
            self.providers_list_widget.addItem(item)

        self.clear_and_disable_form()

    def clear_and_disable_form(self):
        """Clear and disable the provider detail form fields and buttons."""
        self.name_edit.clear()
        self.api_base_url_edit.clear()
        self.api_key_env_var_edit.clear()
        self.default_model_id_edit.clear()

        self.name_edit.setEnabled(False)
        self.api_base_url_edit.setEnabled(False)
        self.api_key_env_var_edit.setEnabled(False)
        self.default_model_id_edit.setEnabled(False)

        self.save_button.setEnabled(False)
        self.remove_button.setEnabled(False)

        # Also clear and disable the available models section
        self.available_models_list_widget.clear()
        self.available_models_list_widget.setEnabled(False)
        self.add_model_button.setEnabled(False)
        self.remove_model_button.setEnabled(False)

    def on_provider_selected(self, current_item, previous_item):
        """Handle selection changes in the providers list."""
        if current_item is None:
            self.clear_and_disable_form()
            return

        provider_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not provider_data:  # Should not happen if setData was successful
            self.clear_and_disable_form()
            return

        self.name_edit.setText(provider_data.get("name", ""))
        # self.type_display is static "openai_compatible"
        self.api_base_url_edit.setText(provider_data.get("api_base_url", ""))
        self.api_key_env_var_edit.setText(provider_data.get("api_key_env_var", ""))
        self.default_model_id_edit.setText(provider_data.get("default_model_id", ""))

        self.name_edit.setEnabled(True)
        self.api_base_url_edit.setEnabled(True)
        self.api_key_env_var_edit.setEnabled(True)
        self.default_model_id_edit.setEnabled(True)

        self.save_button.setEnabled(True)
        self.remove_button.setEnabled(True)

        # Populate available models
        available_models = provider_data.get("available_models", [])
        self.available_models_list_widget.clear()
        for model_id in available_models:
            self.available_models_list_widget.addItem(str(model_id))

        self.available_models_list_widget.setEnabled(True)
        self.add_model_button.setEnabled(True)
        self.remove_model_button.setEnabled(False)  # Enabled when a model is selected

    def on_available_model_selected(self, current_item, previous_item):
        """Handle selection changes in the available models list."""
        if current_item is not None:
            self.remove_model_button.setEnabled(True)
        else:
            self.remove_model_button.setEnabled(False)

    def init_ui(self):
        """Initialize the UI components."""
        main_layout = QHBoxLayout(self)

        # Left Panel: List of providers and action buttons
        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)

        left_panel_layout.addWidget(QLabel("Custom Providers:"))
        self.providers_list_widget = QListWidget()
        self.providers_list_widget.currentItemChanged.connect(self.on_provider_selected)
        left_panel_layout.addWidget(self.providers_list_widget)

        list_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add New Provider")
        self.add_button.clicked.connect(self.add_new_provider_triggered)
        self.remove_button = QPushButton("Remove Selected Provider")
        self.remove_button.clicked.connect(self.remove_selected_provider)
        self.remove_button.setEnabled(False)  # Initially disabled

        list_buttons_layout.addWidget(self.add_button)
        list_buttons_layout.addWidget(self.remove_button)
        left_panel_layout.addLayout(list_buttons_layout)

        # Right Panel: Editor for provider details
        editor_panel_widget = QWidget()
        editor_layout = QVBoxLayout(editor_panel_widget)

        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.type_display = QLabel("openai_compatible")  # Read-only type display
        self.api_base_url_edit = QLineEdit()
        self.api_key_env_var_edit = QLineEdit()
        self.default_model_id_edit = QLineEdit()

        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Type:", self.type_display)
        form_layout.addRow("API Base URL:", self.api_base_url_edit)
        form_layout.addRow("API Key Env Var:", self.api_key_env_var_edit)
        form_layout.addRow("Default Model ID:", self.default_model_id_edit)

        editor_layout.addLayout(form_layout)

        # Available Models Section
        editor_layout.addWidget(QLabel("Available Models:"))
        self.available_models_list_widget = QListWidget()
        self.available_models_list_widget.setMinimumHeight(100)
        self.available_models_list_widget.setEnabled(False)
        self.available_models_list_widget.currentItemChanged.connect(
            self.on_available_model_selected
        )
        editor_layout.addWidget(self.available_models_list_widget)

        model_buttons_layout = QHBoxLayout()
        self.add_model_button = QPushButton("Add Model")
        self.add_model_button.setEnabled(False)
        self.add_model_button.clicked.connect(self.add_model_button_clicked)
        self.remove_model_button = QPushButton("Remove Selected Model")
        self.remove_model_button.setEnabled(False)
        self.remove_model_button.clicked.connect(self.remove_model_button_clicked)
        model_buttons_layout.addWidget(self.add_model_button)
        model_buttons_layout.addWidget(self.remove_model_button)
        editor_layout.addLayout(model_buttons_layout)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_provider_details)
        editor_layout.addWidget(self.save_button)
        editor_layout.addStretch()  # Push form and button to the top

        # Add panels to main layout with stretch factors
        main_layout.addWidget(left_panel_widget, 1)  # Stretch factor 1 for left
        main_layout.addWidget(editor_panel_widget, 3)  # Stretch factor 3 for right

        # Set initial enabled state for editor fields and save button
        self.name_edit.setEnabled(False)
        self.api_base_url_edit.setEnabled(False)
        self.api_key_env_var_edit.setEnabled(False)
        self.default_model_id_edit.setEnabled(False)
        self.save_button.setEnabled(False)

        self.setLayout(main_layout)

    def add_model_button_clicked(self):
        """Handle the 'Add Model' button click."""
        current_provider_item = self.providers_list_widget.currentItem()
        if not current_provider_item:
            QMessageBox.warning(
                self,
                "No Provider Selected",
                "Please select a provider before adding a model.",
            )
            return

        model_id, ok = QInputDialog.getText(self, "Add Model ID", "Enter Model ID:")
        if ok and model_id:
            model_id = model_id.strip()
            if not model_id:
                QMessageBox.warning(self, "Invalid Input", "Model ID cannot be empty.")
                return

            existing_models = [
                self.available_models_list_widget.item(i).text()
                for i in range(self.available_models_list_widget.count())
            ]
            if model_id in existing_models:
                QMessageBox.warning(
                    self,
                    "Duplicate Model ID",
                    "This Model ID already exists in the list.",
                )
                return

            self.available_models_list_widget.addItem(model_id)
            # Note: Actual saving of this change to the config will happen
            # when the main "Save Changes" button for the provider is clicked.
        elif ok and not model_id:  # User pressed OK but input was empty or whitespace
            QMessageBox.warning(self, "Invalid Input", "Model ID cannot be empty.")

    def remove_model_button_clicked(self):
        """Handle the 'Remove Selected Model' button click."""
        current_item = self.available_models_list_widget.currentItem()
        if current_item:
            row = self.available_models_list_widget.row(current_item)
            self.available_models_list_widget.takeItem(row)
            # The on_available_model_selected will be triggered by selection change,
            # which will disable the button if the list becomes empty or no item is selected.

    def add_new_provider_triggered(self):
        """Clear the form and prepare for adding a new provider."""
        # This will trigger on_provider_selected(None, ...) which calls clear_and_disable_form()
        self.providers_list_widget.setCurrentItem(None)

        # Explicitly clear and enable fields for a new entry
        self.name_edit.clear()
        self.api_base_url_edit.clear()
        self.api_key_env_var_edit.clear()
        self.default_model_id_edit.clear()

        self.name_edit.setEnabled(True)
        self.api_base_url_edit.setEnabled(True)
        self.api_key_env_var_edit.setEnabled(True)
        self.default_model_id_edit.setEnabled(True)

        # self.type_display is static "openai_compatible", already set

        self.save_button.setEnabled(True)
        self.remove_button.setEnabled(
            False
        )  # Cannot remove a provider that doesn't exist yet

        # Enable the available models section for the new provider
        self.available_models_list_widget.setEnabled(True)
        self.add_model_button.setEnabled(True)
        # remove_model_button should remain disabled until a model is selected in its list
        self.remove_model_button.setEnabled(False)

        self.name_edit.setFocus()

    def save_provider_details(self):
        """Save the current provider's details or add a new provider."""
        name = self.name_edit.text().strip()
        api_base_url = self.api_base_url_edit.text().strip()
        api_key_env_var = self.api_key_env_var_edit.text().strip()
        default_model_id = self.default_model_id_edit.text().strip()

        if not name or not api_base_url:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Provider Name and API Base URL cannot be empty.",
            )
            return

        available_models_data = [
            self.available_models_list_widget.item(i).text()
            for i in range(self.available_models_list_widget.count())
        ]

        provider_detail = {
            "name": name,
            "type": "openai_compatible",  # As per spec
            "api_base_url": api_base_url,
            "api_key_env_var": api_key_env_var,
            "default_model_id": default_model_id,
            "available_models": available_models_data,
        }

        # Validate default_model_id against available_models
        current_default_model = provider_detail.get("default_model_id", "").strip()
        current_available_models = provider_detail.get("available_models", [])

        if (
            current_default_model
            and current_available_models
            and current_default_model not in current_available_models
        ):
            QMessageBox.warning(
                self,
                "Validation Error",
                f"The Default Model ID '{current_default_model}' is not in the list of available models. "
                "Please correct it or add it to the list.",
            )
            return

        current_item = self.providers_list_widget.currentItem()
        is_new_provider = (
            current_item is None or current_item.data(Qt.ItemDataRole.UserRole) is None
        )

        if not is_new_provider:
            # Editing existing provider
            list_widget_index = self.providers_list_widget.row(current_item)

            if list_widget_index < 0 or list_widget_index >= len(self.providers_data):
                # This case should ideally not happen if UI and data are in sync
                logger.error(
                    f"ERROR: list_widget_index {list_widget_index} is out of bounds for self.providers_data (len {len(self.providers_data)})"
                )
                QMessageBox.critical(
                    self, "Internal Error", "Provider list mismatch. Cannot save."
                )
                return

            # Before replacing, if the name is being changed, check for conflicts with *other* providers.
            original_provider_data_at_index = self.providers_data[list_widget_index]
            original_name = original_provider_data_at_index.get("name")
            new_name_from_form = provider_detail.get("name")

            if new_name_from_form != original_name:
                for i, p_dict in enumerate(self.providers_data):
                    if i == list_widget_index:  # Skip comparing with itself
                        continue
                    if p_dict.get("name") == new_name_from_form:
                        QMessageBox.warning(
                            self,
                            "Duplicate Name",
                            f"Another provider with the name '{new_name_from_form}' already exists. Please use a unique name.",
                        )
                        return  # Abort save

            # Replace the dictionary at the specific index
            self.providers_data[list_widget_index] = provider_detail
            logger.debug(
                f"DEBUG: Replaced self.providers_data[{list_widget_index}] with provider_detail: {self.providers_data[list_widget_index]}"
            )
        else:
            # Adding new provider
            # Check if a provider with the same name already exists
            for p_data in self.providers_data:
                if p_data.get("name") == name:
                    QMessageBox.warning(
                        self,
                        "Duplicate Name",
                        f"A provider with the name '{name}' already exists. Please use a unique name.",
                    )
                    return
            self.providers_data.append(provider_detail)

        try:
            # Modify your existing print to be more identifiable
            self.config_manager.write_custom_llm_providers_config(self.providers_data)
            self.config_changed.emit()
            QMessageBox.information(
                self, "Success", "Provider configuration saved successfully."
            )

            # Reload providers and attempt to re-select the saved item
            self.load_providers()
            for i in range(self.providers_list_widget.count()):
                item = self.providers_list_widget.item(i)
                if item.text() == name:
                    self.providers_list_widget.setCurrentItem(item)
                    break

        except Exception as e:
            QMessageBox.critical(
                self, "Error Saving", f"Could not save provider configuration: {str(e)}"
            )

    def remove_selected_provider(self):
        """Remove the selected provider from the configuration."""
        current_item = self.providers_list_widget.currentItem()

        if not current_item:
            QMessageBox.warning(
                self, "No Selection", "Please select a provider to remove."
            )
            return

        item_index = self.providers_list_widget.row(current_item)

        if item_index < 0 or item_index >= len(self.providers_data):
            # This case should ideally not happen if UI and data are in sync
            QMessageBox.critical(
                self,
                "Error",
                "Selected provider not found in internal list. Cannot remove.",
            )
            # Attempt to reload to resync, though this indicates a deeper issue if reached.
            self.load_providers()
            return

        provider_name = self.providers_data[item_index].get("name", "Unnamed Provider")

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the provider '{provider_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove the provider from the list by index
            del self.providers_data[item_index]

            try:
                self.config_manager.write_custom_llm_providers_config(
                    self.providers_data
                )
                self.config_changed.emit()
                QMessageBox.information(
                    self, "Success", f"Provider '{provider_name}' removed successfully."
                )
                self.load_providers()  # Refresh list and clear/disable form
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Removing",
                    f"Could not remove provider configuration: {str(e)}",
                )
                # Optionally, reload providers to revert to consistent state if save failed
                self.load_providers()
