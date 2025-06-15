from PySide6.QtCore import QTimer


class UIStateManager:
    """Manages UI state and control enable/disable logic."""

    def __init__(self, chat_window):
        from AgentCrew.modules.gui import ChatWindow

        if isinstance(chat_window, ChatWindow):
            self.chat_window = chat_window
        self.spinner_chars = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.spinner_index = 0
        self._setup_animation_timer()

    def _setup_animation_timer(self):
        """Set up the animation timer for the stop button."""
        self.animation_timer = QTimer(self.chat_window)
        self.animation_timer.timeout.connect(self.update_send_button_text)

    def set_input_controls_enabled(self, enabled: bool):
        """Enable or disable input controls."""
        # Keep controls disabled if loading a conversation, regardless of 'enabled' argument
        actual_enabled = enabled and not self.chat_window.loading_conversation

        self.chat_window.message_input.setEnabled(actual_enabled)
        self.chat_window.send_button.setEnabled(actual_enabled)
        self.chat_window.file_button.setEnabled(actual_enabled)
        self.chat_window.sidebar.setEnabled(actual_enabled)

        # Update cursor and appearance for visual feedback
        if actual_enabled:
            self._set_send_button_state()
            self.chat_window.message_input.setFocus()
            self.chat_window.file_button.setStyleSheet(
                self.chat_window.style_provider.get_button_style("secondary")
            )
        else:
            # Common disabled style for both loading and waiting for response
            disabled_button_style = """
                QPushButton {{
                    background-color: #45475a; /* Catppuccin Surface1 */
                    color: #6c7086; /* Catppuccin Overlay0 */
                    border: none;
                    border-radius: 4px; 
                    padding: 8px;
                    font-weight: bold;
                }}
            """
            self.chat_window.send_button.setStyleSheet(disabled_button_style)
            self.chat_window.file_button.setStyleSheet(disabled_button_style)

        # Update waiting state (only relevant for LLM responses)
        if not self.chat_window.loading_conversation:
            self.chat_window.waiting_for_response = not enabled

    def _set_send_button_state(self, is_stop_stated: bool = False):
        """Set the send button state (normal or stop mode)."""
        # If enabling controls, make sure we reset the send button
        if not is_stop_stated:
            self.animation_timer.stop()
            self.chat_window.send_button.setText("Send")
            self.chat_window.send_button.setStyleSheet(
                self.chat_window.style_provider.get_button_style("primary")
            )
            # Ensure the button is connected to send message
            try:
                self.chat_window.send_button.clicked.disconnect()
            except Exception:
                pass  # In case it wasn't connected
            self.chat_window.send_button.clicked.connect(self.chat_window.send_message)
        else:
            # Change button to stop functionality
            self.chat_window.send_button.setText("Stop \u25a0")
            self.chat_window.send_button.setStyleSheet(
                self.chat_window.style_provider.get_button_style("stop")
            )
            self.animation_timer.setInterval(150)  # Update every 150ms for spinner
            self.animation_timer.start()

            # Change the button to stop functionality
            self.chat_window.send_button.clicked.disconnect()
            self.chat_window.send_button.clicked.connect(
                self.chat_window.stop_message_stream
            )
            self.chat_window.send_button.setEnabled(True)

    def update_send_button_text(self):
        """Cycle through spinner characters for stop button animation."""
        spinner_char = self.spinner_chars[self.spinner_index]
        self.chat_window.send_button.setText(f"Stop {spinner_char}")

        # Move to next character in sequence
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)

    def stop_button_stopping_state(self):
        """Set button to stopping state."""
        if self.chat_window.waiting_for_response:
            self.chat_window.send_button.setDisabled(True)

            # Update button styling to show disabled state more clearly
            self.chat_window.send_button.setStyleSheet("""
                QPushButton {
                    background-color: #6c7086; /* Catppuccin Overlay0 - More grey/disabled look */
                    color: #9399b2; /* Catppuccin Subtext1 - Muted text */
                    border: none;
                    border-radius: 4px; 
                    padding: 8px;
                    font-weight: bold;
                }
            """)
            self.chat_window.send_button.setText("Stopping...")

            # Stop the animation timer since we're now in a disabled state
            self.animation_timer.stop()
