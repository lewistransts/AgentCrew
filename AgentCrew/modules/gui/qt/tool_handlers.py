from typing import Any, Dict
from PySide6.QtWidgets import QMessageBox, QTextEdit, QGridLayout
from PySide6.QtCore import Qt


class ToolEventHandler:
    """Handles tool-related events in the chat UI."""

    def __init__(self, chat_window):
        from ..qt_ui import ChatWindow

        if isinstance(chat_window, ChatWindow):
            self.chat_window = chat_window

    def handle_event(self, event: str, data: Any):
        """Handle a tool-related event."""
        if event == "tool_use":
            self.handle_tool_use(data)
        elif event == "tool_result":
            self.handle_tool_result(data)
        elif event == "tool_error":
            self.handle_tool_error(data)
        elif event == "tool_confirmation_required":
            self.handle_tool_confirmation_required(data)
        elif event == "tool_denied":
            self.handle_tool_denied(data)

    def handle_tool_use(self, tool_use: Dict):
        """Display information about a tool being used."""
        tool_message = f"TOOL: Using {tool_use['name']}\n\n```\n{tool_use}\n```"
        self.chat_window.chat_components.add_system_message(tool_message)
        self.chat_window.display_status_message(f"Using tool: {tool_use['name']}")

    def handle_tool_result(self, data: Dict):
        """Display the result of a tool execution."""
        tool_use = data["tool_use"]
        tool_result = data["tool_result"]
        result_message = f"RESULT: Tool {tool_use['name']}:\n\n```\n{tool_result}\n```"
        self.chat_window.chat_components.add_system_message(result_message)

        # Reset the current response bubble so the next agent message starts in a new bubble
        self.chat_window.current_response_bubble = None
        self.chat_window.current_response_container = None

    def handle_tool_error(self, data: Dict):
        """Display an error that occurred during tool execution."""
        tool_use = data["tool_use"]
        error = data["error"]
        error_message = f"ERROR: Tool {tool_use['name']}: {error}"
        self.chat_window.chat_components.add_system_message(error_message)
        self.chat_window.display_status_message(f"Error in tool {tool_use['name']}")

        # Reset the current response bubble so the next agent message starts in a new bubble
        self.chat_window.current_response_bubble = None
        self.chat_window.current_response_container = None

    def handle_tool_confirmation_required(self, tool_info):
        """Display a dialog for tool confirmation request."""
        tool_use = tool_info.copy()
        confirmation_id = tool_use.pop("confirmation_id")

        # Create dialog
        dialog = QMessageBox(self.chat_window)
        dialog.setWindowTitle("Tool Execution Confirmation")
        dialog.setIcon(QMessageBox.Icon.Question)

        # Format tool information for display
        tool_description = f"The assistant wants to use the '{tool_use['name']}' tool."
        params_text = ""

        if isinstance(tool_use["input"], dict):
            params_text = "Parameters:"
            for key, value in tool_use["input"].items():
                params_text += f"\n• {key}: {value}"
        else:
            params_text = f"\n\nInput: {tool_use['input']}"

        dialog.setInformativeText("Do you want to allow this tool to run?")
        dialog.setText(tool_description)

        lt = dialog.layout()
        text_edit = QTextEdit()
        text_edit.setMinimumWidth(500)
        text_edit.setMinimumHeight(300)
        text_edit.setReadOnly(True)
        text_edit.setText(params_text)

        # Style the text edit to match the main theme
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #313244; /* Catppuccin Surface0 */
                color: #cdd6f4; /* Catppuccin Text */
                border: 1px solid #45475a; /* Catppuccin Surface1 */
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
            }
            QTextEdit:focus {
                border: 1px solid #89b4fa; /* Catppuccin Blue */
            }
        """)

        if isinstance(lt, QGridLayout):
            lt.addWidget(
                text_edit,
                lt.rowCount() - 2,
                2,
                1,
                lt.columnCount() - 2,
                Qt.AlignmentFlag.AlignLeft,
            )

        # Add buttons
        yes_button = dialog.addButton("Yes (Once)", QMessageBox.ButtonRole.YesRole)
        no_button = dialog.addButton("No", QMessageBox.ButtonRole.NoRole)
        all_button = dialog.addButton("Yes to All", QMessageBox.ButtonRole.AcceptRole)

        # Style the buttons with Catppuccin colors
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1; /* Catppuccin Green */
                color: #1e1e2e; /* Catppuccin Base */
                font-weight: bold;
                padding: 6px 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #94e2d5; /* Catppuccin Teal */
            }
        """)

        all_button.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; /* Catppuccin Blue */
                color: #1e1e2e; /* Catppuccin Base */
                font-weight: bold;
                padding: 6px 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #74c7ec; /* Catppuccin Sapphire */
            }
        """)

        no_button.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8; /* Catppuccin Red */
                color: #1e1e2e; /* Catppuccin Base */
                font-weight: bold;
                padding: 6px 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #eba0ac; /* Catppuccin Maroon */
            }
        """)

        # Execute dialog and get result
        dialog.exec()
        clicked_button = dialog.clickedButton()

        # Process result
        if clicked_button == yes_button:
            self.chat_window.message_handler.resolve_tool_confirmation(
                confirmation_id, {"action": "approve"}
            )
            self.chat_window.display_status_message(
                f"Approved tool: {tool_use['name']}"
            )
        elif clicked_button == all_button:
            self.chat_window.message_handler.resolve_tool_confirmation(
                confirmation_id, {"action": "approve_all"}
            )
            self.chat_window.display_status_message(
                f"Approved all future calls to tool: {tool_use['name']}"
            )
        else:  # No or dialog closed
            self.chat_window.message_handler.resolve_tool_confirmation(
                confirmation_id, {"action": "deny"}
            )
            self.chat_window.display_status_message(f"Denied tool: {tool_use['name']}")

    def handle_tool_denied(self, data):
        """Display a message about a denied tool execution."""
        tool_use = data["tool_use"]
        self.chat_window.chat_components.add_system_message(
            f"❌ Tool execution denied: {tool_use['name']}"
        )
        self.chat_window.display_status_message(
            f"Tool execution denied: {tool_use['name']}"
        )
