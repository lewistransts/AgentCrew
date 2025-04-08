from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
)
from PySide6.QtCore import (
    Qt,
    Slot,
    QThread,
    Signal,
)


class ConversationSidebar(QWidget):
    """Sidebar widget showing conversation history"""

    conversation_selected = Signal(str)  # Emits conversation_id
    error_occurred = Signal(str)

    def __init__(self, message_handler, parent=None):
        super().__init__(parent)
        self.message_handler = message_handler
        # Store conversations locally to filter
        self._conversations = []
        self.setup_ui()
        # Initial load
        self.update_conversation_list()

    def setup_ui(self):
        self.setFixedWidth(250)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Add some margins
        layout.setSpacing(5)  # Add spacing

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search conversations...")
        self.search_box.textChanged.connect(self.filter_conversations)
        layout.addWidget(self.search_box)

        # Conversation list
        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(self.on_conversation_selected)
        # --- Start of changes ---
        self.conversation_list.setAlternatingRowColors(True) # Keep this for fallback/clarity
        # --- Start of replacement ---
        self.conversation_list.setStyleSheet(
            """
            QListWidget {
                /* Optional: Set a base background for the whole widget */
                /* background-color: white; */
            }
            QListWidget::item {
                /* Define default text and background */
                color: black; /* Or your default text color */
                background-color: transparent; /* Default item background */
                border: none; /* Reset border first */
                border-bottom: 1px solid #555555; /* Darker gray border */
                padding-top: 4px;
                padding-bottom: 4px;
            }
            QListWidget::item:alternate {
                 /* Explicitly define alternating row background */
                 background-color: #f0f0f0; /* Light gray for alternating rows */
            }
            QListWidget::item:last-child {
                /* No bottom border for the very last item in the list */
                border-bottom: none;
            }
            QListWidget::item:selected {
                /* Style for selected items */
                background-color: #a0c4ff; /* Light blue background */
                color: black; /* Black text */
                /* Ensure border is still visible unless it's the last item */
                /* (border-bottom is inherited from QListWidget::item unless overridden) */
            }
            /* Optional: Keep selection visible when widget loses focus */
            QListWidget::item:selected:active {
                 background-color: #a0c4ff;
                 color: black;
            }
            /* Ensure the last selected item also has no bottom border */
            QListWidget::item:selected:last-child {
                 border-bottom: none;
            }
            """
        )
        # --- End of replacement ---
        # --- End of existing changes --- # Note: Adjusted comment slightly to reflect reality
        layout.addWidget(self.conversation_list)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_conversation_list)
        layout.addWidget(self.refresh_btn)

        self.setLayout(layout)

    def update_conversation_list(self):
        """Fetches and displays the list of conversations."""
        try:
            # Assuming message_handler has list_conversations method
            self._conversations = self.message_handler.list_conversations()
            self.filter_conversations()  # Apply current filter
        except Exception as e:
            self.error_occurred.emit(f"Failed to load conversations: {str(e)}")
            self._conversations = []  # Clear local cache on error
            self.conversation_list.clear()  # Clear UI list

    def filter_conversations(self):
        """Filters the displayed list based on search text."""
        search_term = self.search_box.text().lower()
        self.conversation_list.clear()
        if not self._conversations:
            # Handle case where conversations haven't loaded or failed to load
            if not self.search_box.text():  # Avoid showing error if user is just typing
                # Optionally display a message in the list
                # item = QListWidgetItem("No conversations found.")
                # item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # Make it unselectable
                # self.conversation_list.addItem(item)
                pass
            return

        # Sort conversations by timestamp descending (most recent first)
        # Assuming timestamp is sortable (e.g., ISO format string or datetime object)

        for metadata in self._conversations:
            title = metadata.get("preview", "Untitled Conversation")
            timestamp = metadata.get("timestamp", "N/A")
            conv_id = metadata.get("id", "N/A")
            if search_term in title.lower():
                item_text = f"{title}\n{timestamp}"  # Display title and timestamp
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, conv_id)  # Store ID in UserRole
                item.setToolTip(f"ID: {conv_id}\nLast updated: {timestamp}")
                self.conversation_list.addItem(item)

    @Slot(QListWidgetItem)
    def on_conversation_selected(self, item):
        """Emits the ID of the selected conversation."""
        if item and item.data(Qt.ItemDataRole.UserRole):
            self.conversation_selected.emit(item.data(Qt.ItemDataRole.UserRole))


class ConversationLoader(QThread):
    """Thread for async conversation loading"""

    loaded = Signal(list, str)  # Emit messages and conversation_id
    error = Signal(str)

    def __init__(self, message_handler, conv_id):
        super().__init__()
        self.message_handler = message_handler
        self.conv_id = conv_id

    def run(self):
        try:
            # Assuming message_handler has load_conversation method
            messages = self.message_handler.load_conversation(self.conv_id)
            if messages is not None:
                self.loaded.emit(messages, self.conv_id)
            else:
                # Handle case where conversation load returns None (e.g., not found)
                self.error.emit(f"Conversation '{self.conv_id}' not found or empty.")
        except Exception as e:
            # Log the full exception for debugging
            import traceback

            print(
                f"Error loading conversation {self.conv_id}: {traceback.format_exc()}"
            )
            self.error.emit(f"Failed to load conversation '{self.conv_id}': {str(e)}")
