from typing import Any, Optional
import pyperclip

from PySide6.QtWidgets import (
    QApplication,
    QCompleter,
    QLabel,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QMainWindow,
    QStatusBar,
    QScrollArea,
    QMenu,
    QSplitter,
    QTextEdit,
)
from PySide6.QtCore import (
    Qt,
    Slot,
    QThread,
    Signal,
    QTimer,
)
from AgentCrew.modules.chat.message_handler import MessageHandler, Observer
from AgentCrew.modules.gui.widgets import ConversationSidebar, TokenUsageWidget
from AgentCrew.modules.gui.widgets import MessageBubble


from .worker import LLMWorker
from .qt import (
    StyleProvider,
    MenuBuilder,
    KeyboardHandler,
    MessageEventHandler,
    ToolEventHandler,
    ChatComponents,
    UIStateManager,
    InputComponents,
    ConversationComponents,
)


class ChatWindow(QMainWindow, Observer):
    # Signal for thread-safe event handling
    event_received = Signal(str, object)
    # # Widgets
    status_indicator: QLabel
    chat_scroll: QScrollArea
    chat_layout: QVBoxLayout
    chat_container: QWidget
    version_label: QWidget  # Placeholder for all components
    send_button: QPushButton
    file_button: QPushButton
    message_input: QTextEdit
    file_completer: QCompleter
    # Custom Widgets
    token_usage: TokenUsageWidget

    current_response_bubble: Optional[MessageBubble]
    current_response_container: Optional[QWidget]
    current_user_bubble: Optional[MessageBubble]
    current_thinking_bubble: Optional[MessageBubble]

    def __init__(self, message_handler: MessageHandler):
        super().__init__()
        self.setWindowTitle("AgentCrew - Interactive Chat")
        self.setGeometry(100, 100, 1000, 700)  # Adjust size for sidebar
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled)

        # Initialize MessageHandler - kept in main thread
        self.message_handler = message_handler
        self.message_handler.attach(self)

        # Track if we're waiting for a response
        self.waiting_for_response = False
        self.loading_conversation = False  # Track conversation loading state

        # Initialize component handlers (these create UI widgets during __init__)
        self._setup_components()

        # Set application-wide style
        self.setStyleSheet(self.style_provider.get_main_style())

        # Create menu bar with styling
        self.menu_builder.create_menu_bar()

        # Status Bar (created after components so version_label exists)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.addPermanentWidget(self.version_label)

        # --- Assemble Chat Area Layout ---
        chat_area_widget = QWidget()  # Container for everything right of the sidebar
        chat_area_layout = QVBoxLayout(chat_area_widget)
        chat_area_layout.setContentsMargins(0, 0, 0, 0)
        chat_area_layout.addWidget(self.chat_scroll, 1)  # Give chat area more space
        chat_area_layout.addWidget(self.status_indicator)

        # Create horizontal layout for input and buttons
        input_row = self.input_components.get_input_layout()
        chat_area_layout.addLayout(input_row)
        chat_area_layout.addWidget(self.token_usage)

        # --- Create Sidebar ---
        self.sidebar = ConversationSidebar(self.message_handler, self)
        self.sidebar.conversation_selected.connect(
            self.conversation_components.load_conversation
        )
        self.sidebar.error_occurred.connect(self.display_error)
        self.sidebar.new_conversation_requested.connect(
            self.conversation_components.start_new_conversation
        )

        # --- Create Splitter and Set Central Widget ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(chat_area_widget)
        self.splitter.setStretchFactor(0, 0)  # Sidebar doesn't stretch
        self.splitter.setStretchFactor(1, 1)  # Chat area stretches
        self.splitter.setSizes([250, 750])  # Initial sizes

        # Connect double-click event to toggle sidebar
        self.splitter.handle(1).installEventFilter(self)

        # Update the splitter style to a darker color
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1e1e2e; /* Darker color (Catppuccin Mantle) */
            }
            QSplitter::handle:hover {
                background-color: #313244; /* Catppuccin Surface0 */
            }
            QSplitter::handle:pressed {
                background-color: #45475a; /* Catppuccin Surface1 */
            }
        """)

        self.setCentralWidget(self.splitter)

        # --- Connect signals and slots (rest of the setup) ---
        self.send_button.clicked.connect(self.send_message)
        self.file_button.clicked.connect(self.input_components.browse_file)

        # Setup context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Connect event handling signal
        self.event_received.connect(self.handle_event)

        # Setup keyboard handling after all UI components are ready
        self.keyboard_handler._setup_shortcuts()

        # Override key press event
        self.message_input.keyPressEvent = self.keyboard_handler.handle_key_press

        # Thread and worker for LLM interaction
        self.llm_thread = QThread()
        self.llm_worker = LLMWorker()  # No message_handler passed to worker

        # Connect worker signals to UI slots
        self.llm_worker.response_ready.connect(self.handle_response)
        self.llm_worker.error.connect(self.display_error)
        self.llm_worker.status_message.connect(self.display_status_message)
        self.llm_worker.request_exit.connect(self.handle_exit_request)
        self.llm_worker.request_clear.connect(self.handle_clear_request)

        # Connect message handler to worker in the main thread
        self.llm_worker.connect_handler(self.message_handler)

        # Move worker to thread and start it
        self.llm_worker.moveToThread(self.llm_thread)
        self.llm_thread.start()

        # Initialize history position
        self.history_position = len(self.message_handler.history_manager.history)
        self.message_input.setFocus()

        # Track current response bubble for chunked responses
        self.current_response_bubble = None
        self.current_user_bubble = None
        self.current_response_container = None
        self.current_thinking_bubble = None
        self.current_file_bubble = None
        self.thinking_content = ""
        self.expecting_response = False
        self._is_file_processing = False
        self._delegated_user_input = None

        # Track session cost
        self.session_cost = 0.0

        # Add simple throttling
        self.chunk_buffer = ""
        self.chunk_timer = QTimer(self)
        self.chunk_timer.setSingleShot(True)
        self.chunk_timer.timeout.connect(
            self.message_event_handler._render_buffered_chunks
        )

        # Add thinking message buffering
        self.thinking_buffer = ""
        self.thinking_timer = QTimer(self)
        self.thinking_timer.setSingleShot(True)
        self.thinking_timer.timeout.connect(
            self.message_event_handler._render_buffered_thinking
        )

        # Add welcome message
        self.chat_components.add_system_message(
            "Welcome! Select a past conversation or start a new one."
        )
        self.chat_components.add_system_message(
            "Press Ctrl+Enter to send, Ctrl+Shift+C to copy, Ctrl+L to clear chat."
        )

    def _setup_components(self):
        """Initialize all component handlers."""
        self.style_provider = StyleProvider()
        self.menu_builder = MenuBuilder(self)
        self.keyboard_handler = KeyboardHandler(self)
        self.message_event_handler = MessageEventHandler(self)
        self.tool_event_handler = ToolEventHandler(self)
        self.chat_components = ChatComponents(self)
        self.ui_state_manager = UIStateManager(self)
        self.input_components = InputComponents(self)
        self.conversation_components = ConversationComponents(self)

    def closeEvent(self, event):
        """Handle window close event to clean up threads properly"""
        # Terminate worker thread properly
        self.llm_thread.quit()
        self.llm_thread.wait(1000)  # Wait up to 1 second for thread to finish
        # If the thread didn't quit cleanly, terminate it
        if self.llm_thread.isRunning():
            self.llm_thread.terminate()
            self.llm_thread.wait()
        super().closeEvent(event)

    @Slot()
    def send_message(self):
        user_input = self.message_input.toPlainText().strip()  # Get text from QTextEdit
        if not user_input:  # Skip if empty
            return

        # Disable input controls while waiting for response
        self.ui_state_manager.set_input_controls_enabled(False)

        self.message_input.clear()

        self.ui_state_manager._set_send_button_state(True)

        # Process commands locally that don't need LLM processing
        if user_input.startswith("/"):
            # Clear command
            if user_input.startswith("/clear"):
                self.clear_chat()
                self.ui_state_manager.set_input_controls_enabled(
                    True
                )  # Re-enable controls
                return
            # Copy command
            elif user_input.startswith("/copy"):
                self.copy_last_response()
                self.ui_state_manager.set_input_controls_enabled(
                    True
                )  # Re-enable controls
                return
            # Debug command
            elif user_input.startswith("/debug"):
                self.display_debug_info()
                self.ui_state_manager.set_input_controls_enabled(
                    True
                )  # Re-enable controls
                return
            # Exit command
            elif user_input in ["/exit", "/quit"]:
                QApplication.quit()
                return

        # Add user message to chat
        self.chat_components.append_message(
            user_input, True, self.message_handler.current_user_input_idx
        )  # True = user message

        # Set flag to expect a response (for chunking)
        self.expecting_response = True
        self.current_response_bubble = None
        self.current_response_container = None

        # Send the request to worker thread via signal
        # This is thread-safe and doesn't require QMetaObject.invokeMethod
        if self._is_file_processing:
            self._delegated_user_input = user_input
            return
        # Update status bar
        self.display_status_message("Processing your message...")
        self.llm_worker.process_request.emit(user_input)

    def _update_cost_info(self, input_tokens, output_tokens):
        """Update cost statistic."""
        # Calculate cost
        total_cost = self.message_handler.agent.calculate_usage_cost(
            input_tokens, output_tokens
        )

        # Update token usage
        self.update_token_usage(
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost": total_cost,
            }
        )

    @Slot(str, int, int)
    def handle_response(self, response, input_tokens, output_tokens):
        """Handle the full response from the LLM worker"""
        self._update_cost_info(input_tokens, output_tokens)

        # Reset response expectation
        self.expecting_response = False

        # Re-enable input controls
        self.ui_state_manager.set_input_controls_enabled(True)

    @Slot(str)
    def display_error(self, error):
        """Display an error message."""
        # Handle both string and dictionary error formats
        if isinstance(error, dict):
            # Extract error message from dictionary
            error_message = error.get("message", str(error))
        else:
            error_message = str(error)

        QMessageBox.critical(self, "Error", error_message)
        self.status_bar.showMessage(
            f"Error: {error_message}", 5000
        )  # Display error in status bar
        self.expecting_response = False

    @Slot(str)
    def display_status_message(self, message):
        self.status_bar.showMessage(message, 5000)

    @Slot(dict)
    def update_token_usage(self, usage_data):
        """Update token usage display."""
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        total_cost = usage_data.get("total_cost", 0.0)

        # Update session cost
        self.session_cost += total_cost

        # Update the token usage widget
        self.token_usage.update_token_info(
            input_tokens, output_tokens, total_cost, self.session_cost
        )

    @Slot()
    def copy_last_response(self):
        """Copy the last assistant response to clipboard."""
        text = self.message_handler.latest_assistant_response
        if text:
            pyperclip.copy(text)
            self.status_bar.showMessage("Last response copied to clipboard!", 3000)
        else:
            self.status_bar.showMessage("No response to copy", 3000)

    @Slot()
    def handle_exit_request(self):
        """Handle exit request from worker thread"""
        QApplication.quit()

    @Slot()
    def handle_clear_request(self):
        """Handle clear request from worker thread"""
        self.clear_chat(True)

    @Slot()
    def clear_chat(self, requested=False):
        """Clear the chat history and UI."""
        # Only ask for confirmation if triggered by user (e.g., Ctrl+L), not programmatically
        if not requested:
            reply = QMessageBox.question(
                self,
                "Clear Chat",
                "Are you sure you want to start new conversation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return  # User cancelled

        # Clear the UI immediately
        self.chat_components.clear_chat_ui()

        # Reset session cost display
        self.session_cost = 0.0
        self.token_usage.update_token_info(0, 0, 0.0, 0.0)

        # If the clear was initiated by the user (not loading a conversation),
        # tell the message handler to clear its state.
        if not requested:
            self.llm_worker.process_request.emit("/clear")
            # Add a confirmation message after clearing
            self.chat_components.add_system_message("Chat history cleared.")
            self.display_status_message("Chat history cleared")

        # Ensure input controls are enabled after clearing
        self.ui_state_manager.set_input_controls_enabled(True)
        self.loading_conversation = False  # Ensure loading flag is reset

    def stop_message_stream(self):
        """Stop the current message stream."""
        if self.waiting_for_response:
            self.ui_state_manager.stop_button_stopping_state()
            self.message_handler.stop_streaming = True
            self.display_status_message("Stopping message stream...")

    def show_context_menu(self, position):
        """Show context menu with options."""
        context_menu = QMenu(self)

        # Add Catppuccin styling to context menu
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #181825; /* Catppuccin Mantle */
                color: #cdd6f4; /* Catppuccin Text */
                border: 1px solid #45475a; /* Catppuccin Surface1 */
                padding: 4px;
                border-radius: 6px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #45475a; /* Catppuccin Surface1 */
                color: #b4befe; /* Catppuccin Lavender */
            }
            QMenu::item:pressed {
                background-color: #585b70; /* Catppuccin Surface2 */
            }
            QMenu::separator {
                height: 1px;
                background: #45475a; /* Catppuccin Surface1 */
                margin: 4px 8px;
            }
        """)

        # Add menu actions
        copy_action = context_menu.addAction("Copy Last Response")
        clear_action = context_menu.addAction("Clear Chat")

        # Connect actions to slots
        copy_action.triggered.connect(self.copy_last_response)
        clear_action.triggered.connect(self.clear_chat)

        # Show the menu at the cursor position
        context_menu.exec(self.mapToGlobal(position))

    def rollback_to_message(self, message_bubble):
        """Rollback the conversation to the selected message."""
        if message_bubble.message_index is None:
            self.display_status_message("Cannot rollback: no message index available")
            return

        current_text = message_bubble.message_label.text()

        # Find the turn number for this message
        turn_number = None

        for i, turn in enumerate(self.message_handler.conversation_turns):
            if turn.message_index == message_bubble.message_index:
                turn_number = i + 1  # Turn numbers are 1-indexed
                break

        if turn_number is None:
            self.display_status_message(
                "Cannot rollback: message not found in conversation history"
            )
            return

        # Execute the jump command
        self.llm_worker.process_request.emit(f"/jump {turn_number}")

        # Find and remove all widgets after this message in the UI
        self.chat_components.remove_messages_after(message_bubble)
        self.message_input.setText(current_text)

    def conslidate_messages(self, message_bubble):
        """Consolidate message to the selected message."""
        if message_bubble.message_index is None:
            self.display_status_message(
                "Cannot conslidate messages: no message index available"
            )
            return

        preseved_messages = (
            len(self.message_handler.streamline_messages) - message_bubble.message_index
        )

        # Execute the consolidated command
        self.llm_worker.process_request.emit(f"/consolidated {preseved_messages}")

        self.ui_state_manager.set_input_controls_enabled(
            False
        )  # Disable input while processing
        self.ui_state_manager._set_send_button_state(
            True
        )  # Change button to stop state

    def change_agent(self, agent_name):
        """Change the current agent"""
        # Process the agent change command
        self.llm_worker.process_request.emit(f"/agent {agent_name}")

    def change_model(self, model_id):
        """Change the current model"""
        # Process the model change command
        self.llm_worker.process_request.emit(f"/model {model_id}")

    def open_agents_config(self):
        """Open the agents configuration window."""
        from AgentCrew.modules.gui.widgets.config_window import ConfigWindow

        config_window = ConfigWindow(self)
        config_window.tab_widget.setCurrentIndex(0)  # Show Agents tab
        config_window.exec()

        # Refresh agent list in case changes were made
        self.menu_builder.refresh_agent_menu()

    def open_mcps_config(self):
        """Open the MCP servers configuration window."""
        from AgentCrew.modules.gui.widgets.config_window import ConfigWindow

        config_window = ConfigWindow(self)
        config_window.tab_widget.setCurrentIndex(1)  # Show MCPs tab
        config_window.exec()

    def open_global_settings_config(self):
        """Open the global settings configuration window (API Keys)."""
        from AgentCrew.modules.gui.widgets.config_window import ConfigWindow

        config_window = ConfigWindow(self)
        config_window.tab_widget.setCurrentIndex(3)  # Show Settings tab
        config_window.exec()

    def display_debug_info(self):
        """Display debug information about the current messages."""
        import json

        try:
            # Format the messages for display
            debug_info = json.dumps(self.message_handler.agent.history, indent=2)
        except Exception as _:
            debug_info = str(self.message_handler.agent.history)
        # Add as a system message
        self.chat_components.add_system_message(
            f"DEBUG INFO:\n\n```json\n{debug_info}\n```"
        )

        try:
            # Format the messages for display
            debug_info = json.dumps(self.message_handler.streamline_messages, indent=2)
        except Exception as _:
            debug_info = str(self.message_handler.streamline_messages)
        # Add as a system message
        self.chat_components.add_system_message(
            f"DEBUG INFO:\n\n```json\n{debug_info}\n```"
        )

        # Update status bar
        self.display_status_message("Debug information displayed")

    def listen(self, event: str, data: Any = None):
        """Handle events from the message handler."""
        # Use a signal to ensure thread-safety
        self.event_received.emit(event, data)

    def eventFilter(self, obj, event):
        """Event filter to handle double-click on splitter handle."""
        if (
            obj is self.splitter.handle(1)
            and event.type() == event.Type.MouseButtonDblClick
        ):
            # Get current sizes
            sizes = self.splitter.sizes()
            if sizes[0] > 0:
                # If sidebar is visible, hide it
                self.splitter.setSizes([0, sum(sizes)])
            else:
                # If sidebar is hidden, show it
                self.splitter.setSizes([250, max(sum(sizes) - 250, 0)])
            return True
        return super().eventFilter(obj, event)

    @Slot(str, object)
    def handle_event(self, event: str, data: Any):
        # Delegate to appropriate event handlers
        message_events = [
            "response_chunk",
            "user_message_created",
            "response_completed",
            "assistant_message_added",
            "thinking_started",
            "thinking_chunk",
            "thinking_completed",
            "user_context_request",
        ]

        tool_events = [
            "tool_use",
            "tool_result",
            "tool_error",
            "tool_confirmation_required",
            "tool_denied",
        ]

        if event in message_events:
            self.message_event_handler.handle_event(event, data)
        elif event in tool_events:
            self.tool_event_handler.handle_event(event, data)
        elif event == "error":
            # If an error occurs during LLM processing, ensure loading flag is false
            self.loading_conversation = False
            self.ui_state_manager.set_input_controls_enabled(True)
            if self.current_file_bubble:
                self.chat_components.remove_messages_after(self.current_file_bubble)
                self.current_file_bubble = None
            self._is_file_processing = False
            self.display_error(data)
        elif event == "consolidation_completed":
            self.conversation_components.display_consolidation(data)
            self.ui_state_manager.set_input_controls_enabled(True)
        elif event == "clear_requested":
            self.chat_components.clear_chat_ui()
            self.session_cost = 0.0
            self.token_usage.update_token_info(0, 0, 0.0, 0.0)
            self.chat_components.add_system_message("Chat history cleared by command.")
            self.loading_conversation = False
            self.ui_state_manager.set_input_controls_enabled(True)
            self.sidebar.update_conversation_list()
        elif event == "exit_requested":
            QApplication.quit()
        elif event == "copy_requested":
            if isinstance(data, str):
                pyperclip.copy(data)
                self.display_status_message("Text copied to clipboard!")
        elif event == "debug_requested":
            import json

            try:
                debug_info = json.dumps(data, indent=2)
                self.chat_components.add_system_message(
                    f"DEBUG INFO:\n\n```json\n{debug_info}\n```"
                )
            except Exception:
                self.chat_components.add_system_message(f"DEBUG INFO:\n\n{str(data)}")
        elif event == "file_processing":
            self._is_file_processing = True
            file_path = data["file_path"]
            self.current_file_bubble = self.chat_components.append_file(
                file_path, is_user=True
            )
            if not self.loading_conversation:
                self.ui_state_manager.set_input_controls_enabled(True)
        elif event == "file_processed":
            if self._is_file_processing:
                if self._delegated_user_input:
                    self.llm_worker.process_request.emit(self._delegated_user_input)
                    self._delegated_user_input = None
                self.current_file_bubble = None
                self._is_file_processing = False
        elif event == "image_generated":
            self.chat_components.append_file(data, False, True)
        elif event == "jump_performed":
            self.chat_components.add_system_message(
                f"🕰️ Jumped to turn {data['turn_number']}: {data['preview']}"
            )
        elif event == "agent_changed":
            self.chat_components.add_system_message(f"Switched to {data} agent")
            self.status_indicator.setText(
                f"Agent: {data} | Model: {self.message_handler.agent.get_model()}"
            )
            self.ui_state_manager.set_input_controls_enabled(True)
        elif event == "model_changed":
            self.chat_components.add_system_message(
                f"Switched to {data['name']} ({data['id']})"
            )
            self.status_indicator.setText(
                f"Agent: {self.message_handler.agent.name} | Model: {self.message_handler.agent.get_model()}"
            )
        elif event == "agent_changed_by_transfer":
            self.chat_components.add_system_message(f"Transfered to {data} agent")
            self.status_indicator.setText(
                f"Agent: {data} | Model: {self.message_handler.agent.get_model()}"
            )
            self.current_response_bubble = None
            self.current_response_container = None
        elif event == "think_budget_set":
            self.chat_components.add_system_message(f"Set thinking budget at {data}")
            self.ui_state_manager.set_input_controls_enabled(True)
        elif event == "conversation_saved":
            self.display_status_message(f"Conversation saved: {data.get('id', 'N/A')}")
            self.sidebar.update_conversation_list()
        elif event == "conversations_changed":
            self.display_status_message("Conversation list updated.")
            self.sidebar.update_conversation_list()
        elif event == "conversation_loaded":
            self.display_status_message(f"Conversation loaded: {data.get('id', 'N/A')}")
        elif event == "streaming_stopped":
            self.chat_components.add_system_message(
                "Message streaming stopped by user."
            )
            self.ui_state_manager.set_input_controls_enabled(True)
        elif event == "update_token_usage":
            self._update_cost_info(data["input_tokens"], data["output_tokens"])
