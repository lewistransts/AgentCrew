import re
import os
from typing import Any, Dict
import pyperclip

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QMainWindow,
    QStatusBar,
    QLabel,
    QScrollArea,
    QMenu,
    QMenuBar,
    QFileDialog,
)
from PySide6.QtCore import (
    Qt,
    Slot,
    QThread,
    Signal,
    QStringListModel,
)
from swissknife.modules.llm.models import ModelRegistry
from swissknife.modules.agents.manager import AgentManager
from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
    QFont,
    QAction,
    QTextCursor,
)
from swissknife.modules.chat.message_handler import MessageHandler, Observer
from swissknife.modules.chat.completers import DirectoryListingCompleter
from PySide6.QtWidgets import QCompleter
from swissknife.modules.gui.widgets import (
    TokenUsageWidget,
    SystemMessageWidget,
    MessageBubble,
)

from .worker import LLMWorker


class ChatWindow(QMainWindow, Observer):
    # Signal for thread-safe event handling
    event_received = Signal(str, object)

    def __init__(self, message_handler: MessageHandler):
        super().__init__()
        self.setWindowTitle("Interactive Chat")
        self.setGeometry(100, 100, 800, 600)  # Adjust size as needed

        # Create menu bar
        self.create_menu_bar()

        # Initialize MessageHandler - kept in main thread
        self.message_handler = message_handler
        self.message_handler.attach(self)

        # Create widget for chat messages
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)

        # Create a scroll area for messages
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setWidget(self.chat_container)
        self.chat_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.chat_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Create token usage widget
        self.token_usage = TokenUsageWidget()

        # Create the status indicator (showing current agent and model)
        self.status_indicator = QLabel(
            f"⚙️ {self.message_handler.agent_name} 🧠 {self.message_handler.llm.model}"
        )
        self.status_indicator.setStyleSheet(
            "background-color: #FFFEEE; padding: 5px; border-radius: 5px;"
        )

        # Input area
        self.message_input = QTextEdit()  # Use QTextEdit for multi-line input
        self.message_input.setFont(QFont("Arial", 12))
        self.message_input.setReadOnly(False)
        self.message_input.setMaximumHeight(100)  # Limit input height
        self.message_input.setPlaceholderText(
            "Type your message here... (Ctrl+Enter to send)"
        )

        # Set up file path completion
        self.file_completer = QCompleter(self)
        self.file_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.file_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseSensitive)
        self.file_completer.setWidget(self.message_input)
        self.file_completer.activated.connect(self.insert_completion)
        # Set completer to use Enter and Tab keys
        self.file_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.directory_completer = DirectoryListingCompleter()
        self.path_prefix = ""  # Store the path prefix for completions
        self.message_input.textChanged.connect(self.check_for_path_completion)

        # Create buttons layout
        buttons_layout = QVBoxLayout()  # Change to vertical layout for stacking buttons

        # Create Send button with emoji
        self.send_button = QPushButton("📤 Send")
        self.send_button.setFont(QFont("Arial", 12))
        self.send_button.setStyleSheet(
            "background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;"
        )

        # Create File button with emoji
        self.file_button = QPushButton("📄 File")
        self.file_button.setFont(QFont("Arial", 12))
        self.file_button.setStyleSheet(
            "background-color: #2196F3; color: white; border-radius: 5px; padding: 5px;"
        )

        # Add buttons to layout
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.file_button)
        buttons_layout.addStretch(1)  # Add stretch to keep buttons at the top

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Main Layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.chat_scroll, 1)  # Give chat area more space
        layout.addWidget(self.status_indicator)

        # Create horizontal layout for input and buttons
        input_row = QHBoxLayout()
        input_row.addWidget(self.message_input, 1)  # Give input area stretch priority
        input_row.addLayout(buttons_layout)  # Add buttons layout to the right

        layout.addLayout(input_row)  # Add the horizontal layout to main layout
        layout.addWidget(self.token_usage)
        self.setCentralWidget(central_widget)

        # Connect signals and slots
        self.send_button.clicked.connect(self.send_message)
        self.file_button.clicked.connect(self.browse_file)

        # Setup context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Connect event handling signal
        self.event_received.connect(self.handle_event)

        # Ctrl+Enter shortcut
        self.send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.send_shortcut.activated.connect(self.send_message)

        # Ctrl+C shortcut (copy last response)
        self.copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.copy_shortcut.activated.connect(self.copy_last_response)

        # Ctrl+L shortcut (clear chat)
        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.clear_shortcut.activated.connect(self.clear_chat)

        # Override key press event
        self.message_input.keyPressEvent = self.input_key_press_event

        # Thread and worker for LLM interaction
        self.llm_thread = QThread()
        self.llm_worker = LLMWorker()  # No message_handler passed to worker

        # Connect worker signals to UI slots
        self.llm_worker.response_ready.connect(self.handle_response)
        self.llm_worker.response_chunk.connect(self.display_response_chunk)
        self.llm_worker.error.connect(self.display_error)
        self.llm_worker.status_message.connect(self.display_status_message)
        self.llm_worker.token_usage.connect(self.update_token_usage)
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
        self.current_response_container = None
        self.expecting_response = False

        # Track session cost
        self.session_cost = 0.0

        # Add welcome message
        self.add_system_message(
            "Welcome to the interactive chat! Type a message to begin."
        )
        self.add_system_message(
            "Press Ctrl+Enter to send, Ctrl+C to copy, Ctrl+L to clear chat."
        )

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

    def input_key_press_event(self, event):
        """Custom key press event for the message input."""
        # Handle Tab key for completion
        if event.key() == Qt.Key.Key_Tab and self.file_completer.popup().isVisible():
            # Select the current completion
            current_index = self.file_completer.popup().currentIndex()
            if current_index.isValid():
                completion = self.file_completer.completionModel().data(
                    current_index, Qt.ItemDataRole.DisplayRole
                )
                self.insert_completion(completion)
                self.file_completer.popup().hide()
                event.accept()
                return
        # Handle Enter key for completion
        elif (
            event.key() == Qt.Key.Key_Return and self.file_completer.popup().isVisible()
        ):
            # Select the current completion
            current_index = self.file_completer.popup().currentIndex()
            if current_index.isValid():
                completion = self.file_completer.completionModel().data(
                    current_index, Qt.ItemDataRole.DisplayRole
                )
                self.insert_completion(completion)
                self.file_completer.popup().hide()
                event.accept()
                return
        # Ctrl+Enter to send
        elif (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.send_message()
            event.accept()
            return
        # Up arrow to navigate history
        elif (
            event.key() == Qt.Key.Key_Up
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
            and not self.file_completer.popup().isVisible()
        ):
            self.history_navigate(-1)
            event.accept()
            return
        # Down arrow to navigate history
        elif (
            event.key() == Qt.Key.Key_Down
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
            and not self.file_completer.popup().isVisible()
        ):
            self.history_navigate(1)
            event.accept()
            return
        # Default behavior for other keys
        else:
            QTextEdit.keyPressEvent(self.message_input, event)

    @Slot()
    def send_message(self):
        user_input = self.message_input.toPlainText().strip()  # Get text from QTextEdit
        if not user_input:  # Skip if empty
            return

        self.message_input.clear()

        # Process commands locally that don't need LLM processing
        if user_input.startswith("/"):
            # Clear command
            if user_input.startswith("/clear"):
                self.clear_chat(True)
                return
            # Copy command
            elif user_input.startswith("/copy"):
                self.copy_last_response()
                return
            # Exit command
            elif user_input in ["/exit", "/quit"]:
                QApplication.quit()
                return

        # Add user message to chat
        self.append_message(user_input, True)  # True = user message

        # Set flag to expect a response (for chunking)
        self.expecting_response = True
        self.current_response_bubble = None
        self.current_response_container = None

        # Update status bar
        self.display_status_message("Processing your message...")

        # Send the request to worker thread via signal
        # This is thread-safe and doesn't require QMetaObject.invokeMethod
        self.llm_worker.process_request.emit(user_input)

    def add_system_message(self, text):
        """Add a system message to the chat."""
        system_widget = SystemMessageWidget(text)
        self.chat_layout.addWidget(system_widget)

        # Scroll to show the new message
        QApplication.processEvents()
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )

    def append_message(self, text, is_user=True):
        """Adds a message bubble to the chat container."""
        # Create container for message alignment
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Create the message bubble with agent name for non-user messages
        agent_name = self.message_handler.agent_name if not is_user else "YOU"
        message_bubble = MessageBubble(text, is_user, agent_name)

        # Add bubble to container with appropriate alignment
        if is_user:
            container_layout.addWidget(message_bubble)
            container_layout.addStretch(1)  # Push to left
        else:
            container_layout.addStretch(1)  # Push to right
            container_layout.addWidget(message_bubble)

        # Add the container to the chat layout
        self.chat_layout.addWidget(container)

        # If this is an assistant message, store references for potential future chunks
        if not is_user:
            self.current_response_bubble = message_bubble
            self.current_response_container = container

        # Process events to ensure UI updates immediately
        QApplication.processEvents()

        # Scroll to the bottom to show new message
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )

        return message_bubble

    @Slot(str, int, int)
    def handle_response(self, response, input_tokens, output_tokens):
        """Handle the full response from the LLM worker"""
        # self.display_response_chunk(response)

        # Calculate cost
        total_cost = self.message_handler.llm.calculate_cost(
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

    @Slot(str)
    def display_response_chunk(self, chunk: str):
        """Display a response chunk from the assistant."""

        # If we're expecting a response and don't have a bubble yet, create one
        if self.expecting_response and self.current_response_bubble is None:
            self.current_response_bubble = self.append_message(
                chunk, False
            )  # False = assistant message
        # If we already have a response bubble, append to it
        elif self.expecting_response and self.current_response_bubble is not None:
            self.current_response_bubble.append_text(chunk)
            # Force update and scroll
            QApplication.processEvents()
            self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            )
        # Otherwise, create a new message (should not happen in normal operation)
        else:
            self.current_response_bubble = self.append_message(chunk, False)

    @Slot(str)
    def display_error(self, error):
        """Display an error message.

        Args:
            error: Either a string error message or a dictionary with error details
        """
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

        # Reset response expectation
        self.expecting_response = False

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
        """Clear the chat history."""
        reply = QMessageBox.question(
            self,
            "Clear Chat",
            "Are you sure you want to clear the chat history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Clear the UI
            while self.chat_layout.count():
                item = self.chat_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Let the message handler handle the clear action
            # This will trigger the appropriate events
            if not requested:
                self.llm_worker.process_request.emit("/clear")

            # Reset state variables
            self.current_response_bubble = None
            self.current_response_container = None
            self.expecting_response = False

            # Add welcome message back
            self.add_system_message("Chat history cleared.")

            # Update status bar
            self.display_status_message("Chat history cleared")

    def history_navigate(self, direction):
        if not self.message_handler.history_manager.history:
            return

        new_position = self.history_position + direction

        if 0 <= new_position < len(self.message_handler.history_manager.history):
            self.history_position = new_position
            history_entry = self.message_handler.history_manager.history[
                self.history_position
            ]
            self.message_input.setText(history_entry)  # Set text in input
        elif new_position < 0:
            self.history_position = -1
            self.message_input.clear()
        elif new_position >= len(self.message_handler.history_manager.history):
            self.history_position = len(self.message_handler.history_manager.history)
            self.message_input.clear()

    def display_tool_use(self, tool_use: Dict):
        """Display information about a tool being used."""
        tool_message = f"🔧 Using tool: {tool_use['name']}\n\n```\n{tool_use}\n```"
        self.add_system_message(tool_message)
        self.display_status_message(f"Using tool: {tool_use['name']}")

    def display_tool_result(self, data: Dict):
        """Display the result of a tool execution."""
        tool_use = data["tool_use"]
        tool_result = data["tool_result"]
        result_message = (
            f"✓ Tool result for {tool_use['name']}:\n\n```\n{tool_result}\n```"
        )
        self.add_system_message(result_message)

    def display_tool_error(self, data: Dict):
        """Display an error that occurred during tool execution."""
        tool_use = data["tool_use"]
        error = data["error"]
        error_message = f"❌ Error in tool {tool_use['name']}: {error}"
        self.add_system_message(error_message)
        self.display_status_message(f"Error in tool {tool_use['name']}")

    def browse_file(self):
        """Open file dialog and process selected file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf);;Word Files (*.docx)",
        )

        if file_path:
            # Process the file using the /file command
            file_command = f"/file {file_path}"
            self.display_status_message(f"Processing file: {file_path}")

            # Send the file command to the worker thread
            self.llm_worker.process_request.emit(file_command)

    def show_context_menu(self, position):
        """Show context menu with options."""
        context_menu = QMenu(self)

        # Add menu actions
        copy_action = context_menu.addAction("Copy Last Response")
        clear_action = context_menu.addAction("Clear Chat")

        # Connect actions to slots
        copy_action.triggered.connect(self.copy_last_response)
        clear_action.triggered.connect(self.clear_chat)

        # Show the menu at the cursor position
        context_menu.exec(self.mapToGlobal(position))

    def check_for_path_completion(self):
        """Check if the current text contains a path that should trigger completion."""
        text = self.message_input.toPlainText()
        cursor_position = self.message_input.textCursor().position()

        # Get the text up to the cursor position
        text_to_cursor = text[:cursor_position]

        # Look for path patterns that should trigger completion
        path_match = re.search(r"((~|\.{1,2})?/[^\s]*|~)$", text_to_cursor)

        if path_match:
            path = path_match.group(0)
            completions = self.directory_completer.get_path_completions(path)

            if completions:
                # Create a model for the completer
                model = QStringListModel(completions)
                self.file_completer.setModel(model)

                # Calculate the prefix length to determine what part to complete
                prefix = os.path.basename(path) if "/" in path else path
                self.file_completer.setCompletionPrefix(prefix)

                # Store the path prefix (everything before the basename)
                self.path_prefix = path[: len(path) - len(prefix)]

                # Show the completion popup
                popup = self.file_completer.popup()
                popup.setCurrentIndex(self.file_completer.completionModel().index(0, 0))

                # Calculate position for the popup
                rect = self.message_input.cursorRect()
                rect.setWidth(300)  # Set a reasonable width for the popup

                # Show the popup
                self.file_completer.complete(rect)
            else:
                # Hide the popup if no completions
                self.file_completer.popup().hide()

    def insert_completion(self, completion):
        """Insert the selected completion into the text input."""
        cursor = self.message_input.textCursor()
        text = self.message_input.toPlainText()
        position = cursor.position()

        # Find the start of the path
        text_to_cursor = text[:position]
        path_match = re.search(r"((~|\.{1,2})?/[^\s]*|~)$", text_to_cursor)

        if path_match:
            path_start = path_match.start()
            path = path_match.group(0)

            # Calculate what part of the path to replace
            prefix = os.path.basename(path) if "/" in path else path
            prefix_start = path_start + len(path) - len(prefix)

            # Replace the prefix with the completion
            cursor.setPosition(prefix_start)
            cursor.setPosition(position, QTextCursor.MoveMode.KeepAnchor)

            # If the completion is a directory, add a trailing slash
            # full_path = os.path.join(os.path.expanduser(self.path_prefix), completion)
            cursor.insertText(completion)

    def create_menu_bar(self):
        """Create the application menu bar with Agents and Models menus"""
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        # Create Agents menu
        agents_menu = menu_bar.addMenu("Agents")

        # Get agent manager instance
        agent_manager = AgentManager.get_instance()

        # Get available agents
        available_agents = agent_manager.agents

        # Add agent options to menu
        for agent_name in available_agents:
            agent_action = QAction(agent_name, self)
            agent_action.triggered.connect(
                lambda checked, name=agent_name: self.change_agent(name)
            )
            agents_menu.addAction(agent_action)

        # Create Models menu
        models_menu = menu_bar.addMenu("Models")

        # Get model registry instance
        model_registry = ModelRegistry.get_instance()

        # Add provider submenus
        for provider in ["claude", "openai", "groq", "google", "deepinfra"]:
            provider_menu = models_menu.addMenu(provider.capitalize())

            # Get models for this provider
            models = model_registry.get_models_by_provider(provider)

            # Add model options to submenu
            for model in models:
                model_action = QAction(f"{model.name} ({model.id})", self)
                model_action.triggered.connect(
                    lambda checked, model_id=model.id: self.change_model(model_id)
                )
                provider_menu.addAction(model_action)

    def change_agent(self, agent_name):
        """Change the current agent"""
        # Process the agent change command
        self.llm_worker.process_request.emit(f"/agent {agent_name}")

    def change_model(self, model_id):
        """Change the current model"""
        # Process the model change command
        self.llm_worker.process_request.emit(f"/model {model_id}")

    def listen(self, event: str, data: Any = None):
        """Handle events from the message handler."""
        # Use a signal to ensure thread-safety
        self.event_received.emit(event, data)

    @Slot(str, object)
    def handle_event(self, event: str, data: Any):
        if event == "response_chunk":
            chunk, assistant_response = data
            self.display_response_chunk(chunk)
        elif event == "error":
            self.display_error(data)
        elif event == "thinking_started":
            self.display_status_message(f"Thinking started for {data}...")
        elif event == "thinking_completed":
            self.display_status_message("Thinking completed.")
        elif event == "clear_requested":
            pass
            # self.clear_chat(True)
        elif event == "exit_requested":
            QApplication.quit()
        elif event == "copy_requested":
            if isinstance(data, str):
                pyperclip.copy(data)
                self.display_status_message("Text copied to clipboard!")
        elif event == "file_processed":
            self.add_system_message(f"Processed file: {data['file_path']}")
        elif event == "tool_use":
            self.display_tool_use(data)
        elif event == "tool_result":
            self.display_tool_result(data)
        elif event == "tool_error":
            self.display_tool_error(data)
        elif event == "agent_changed":
            self.add_system_message(f"Switched to {data} agent")
            self.status_indicator.setText(
                f"⚙️ {data} 🧠 {self.message_handler.llm.model}"
            )
        elif event == "model_changed":
            self.add_system_message(f"Switched to {data['name']} ({data['id']})")
            self.status_indicator.setText(
                f"⚙️ {self.message_handler.agent_name} 🧠 {data['id']}"
            )
        elif event == "agent_changed_by_handoff":
            self.add_system_message(f"Handed off to {data} agent")
            self.status_indicator.setText(
                f"⚙️ {data} 🧠 {self.message_handler.llm.model}"
            )
