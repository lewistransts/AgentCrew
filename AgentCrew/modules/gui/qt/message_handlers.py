from typing import Any


class MessageEventHandler:
    """Handles message-related events in the chat UI."""

    def __init__(self, chat_window):
        from ..qt_ui import ChatWindow

        if isinstance(chat_window, ChatWindow):
            self.chat_window = chat_window
        self.thinking_content = ""
        self.thinking_buffer = ""
        self.chunk_buffer = ""

    def handle_event(self, event: str, data: Any):
        """Handle a message-related event."""
        if event == "response_chunk":
            self.handle_response_chunk(data)
        elif event == "user_message_created":
            self.handle_user_message_created(data)
        elif event == "response_completed" or event == "assistant_message_added":
            self.handle_response_completed(data)
        elif event == "thinking_started":
            self.handle_thinking_started(data)
        elif event == "thinking_chunk":
            self.handle_thinking_chunk(data)
        elif event == "thinking_completed":
            self.handle_thinking_completed()
        elif event == "user_context_request":
            self.handle_user_context_request()

    def handle_response_chunk(self, data):
        """Handle a response chunk from the assistant."""
        _, assistant_response = data
        if assistant_response.strip():
            # Don't wait the buffer we need to initialize the response bubble as soon as possible
            if self.chat_window.current_response_bubble is None:
                self.chat_window.current_response_bubble = (
                    self.chat_window.chat_components.append_message("", False)
                )
            # Store latest chunk (replace, don't accumulate)
            self.chunk_buffer = assistant_response
            # Restart timer (50ms delay)
            self.chat_window.chunk_timer.stop()
            self.chat_window.chunk_timer.start(50)

    def handle_user_message_created(self, data):
        """Handle user message creation."""
        if self.chat_window.current_user_bubble:
            self.chat_window.current_user_bubble.message_index = (
                self.chat_window.message_handler.current_user_input_idx
            )
            self.chat_window.current_user_bubble = None

    def handle_response_completed(self, data):
        """Handle response completion."""
        if self.chat_window.current_response_bubble:
            self.chat_window.current_response_bubble.message_index = (
                len(self.chat_window.message_handler.streamline_messages) - 1
            )

    def handle_thinking_started(self, data):
        """Handle thinking process started."""
        agent_name = data
        self.chat_window.chat_components.add_system_message(
            f"💭 {agent_name.upper()}'s thinking process started"
        )

        # Create a new thinking bubble
        self.chat_window.current_thinking_bubble = (
            self.chat_window.chat_components.append_thinking_message(" ", agent_name)
        )
        self.thinking_content = ""  # Initialize thinking content
        self.thinking_buffer = ""  # Initialize thinking buffer

    def handle_thinking_chunk(self, data):
        """Handle a chunk of the thinking process."""
        chunk = data
        # Buffer thinking chunks instead of rendering immediately
        self.thinking_buffer += chunk

        # Restart timer (50ms delay, same as response chunks)
        self.chat_window.thinking_timer.stop()
        self.chat_window.thinking_timer.start(50)

    def handle_thinking_completed(self):
        """Handle thinking process completion."""
        self.chat_window.display_status_message("Thinking completed.")
        self.chat_window.chat_scroll.verticalScrollBar().setValue(
            self.chat_window.chat_scroll.verticalScrollBar().maximum()
        )
        # Reset thinking bubble reference
        self.chat_window.current_thinking_bubble = None

    def handle_user_context_request(self):
        """Handle user context request."""
        self.chat_window.chat_components.add_system_message("Refreshing my memory...")

    def _render_buffered_chunks(self):
        """Render the latest buffered chunk."""
        if self.chunk_buffer:
            self.chat_window.chat_components.display_response_chunk(self.chunk_buffer)
            self.chunk_buffer = ""

    def _render_buffered_thinking(self):
        """Render the latest buffered thinking chunk."""
        if self.thinking_buffer and self.chat_window.current_thinking_bubble:
            # Update the thinking content and display it
            self.chat_window.chat_components.display_thinking_chunk(
                self.thinking_buffer
            )
            # Clear the buffer
            self.thinking_buffer = ""
