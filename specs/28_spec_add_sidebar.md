# Implement Conversation History Sidebar

> Implement a conversation history sidebar in Qt UI that shows saved
> conversations from ContextPersistenceService

## Objectives

- Create ConversationSidebar class with signal-slot architecture
- Modify ChatWindow to integrate the sidebar
- Support asynchronous conversation loading
- Maintain clean separation of concerns
- Follow existing code patterns

## Contexts

- swissknife/modules/gui/qt_ui.py (main implementation file)
- MessageHandler provides list_conversations() and load_conversation()
- ContextPersistenceService stores the conversation data

## Low-level Tasks

- UPDATE swissknife/modules/gui/qt_ui.py:
  - Add ConversationSidebar class with:
    - conversation_selected signal
    - update_conversation_list() method
    - Proper UI elements (QListWidget, etc.)
  - Modify ChatWindow to:
    - Add sidebar using QSplitter
    - Connect signals to slots
    - Handle conversation loading
  - Add threading support for async loading
  - Implement error handling

2. Now let me generate the actual implementation. Here are the key changes
   needed:

```python
# In qt_ui.py, after imports add:
class ConversationSidebar(QWidget):
    """Sidebar widget showing conversation history"""
    conversation_selected = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, message_handler, parent=None):
        super().__init__(parent)
        self.message_handler = message_handler
        self.setup_ui()

    def setup_ui(self):
        self.setFixedWidth(250)
        layout = QVBoxLayout()

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search conversations...")
        layout.addWidget(self.search_box)

        # Conversation list
        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(self.on_conversation_selected)
        layout.addWidget(self.conversation_list)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_conversation_list)
        layout.addWidget(self.refresh_btn)

        self.setLayout(layout)
        self.update_conversation_list()

    def update_conversation_list(self):
        try:
            self.conversation_list.clear()
            conversations = self.message_handler.list_conversations()
            for conv_id, metadata in conversations.items():
                item = QListWidgetItem(f"{metadata.get('title', 'Untitled')}")
                item.setData(Qt.UserRole, conv_id)
                item.setToolTip(f"Last updated: {metadata.get('timestamp')}")
                self.conversation_list.addItem(item)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load conversations: {str(e)}")

    def on_conversation_selected(self, item):
        self.conversation_selected.emit(item.data(Qt.UserRole))
```

```python
# In ChatWindow class modifications:
def __init__(self, message_handler: MessageHandler):
    # ... existing code ...
    self.setup_sidebar()
    self.setup_conversation_signals()

def setup_sidebar(self):
    """Setup the conversation history sidebar"""
    splitter = QSplitter(Qt.Horizontal)

    self.sidebar = ConversationSidebar(self.message_handler, self)
    splitter.addWidget(self.sidebar)

    chat_container = QWidget()
    chat_layout = QVBoxLayout()
    chat_layout.addWidget(self.chat_area)
    chat_layout.addWidget(self.input_area)
    chat_container.setLayout(chat_layout)

    splitter.addWidget(chat_container)
    splitter.setStretchFactor(1, 1)
    self.setCentralWidget(splitter)

def setup_conversation_signals(self):
    """Connect conversation-related signals"""
    self.sidebar.conversation_selected.connect(self.load_conversation)
    self.sidebar.error_occurred.connect(self.display_error)

@pyqtSlot(str)
def load_conversation(self, conversation_id):
    """Load conversation from persistence service"""
    self.loader = ConversationLoader(self.message_handler, conversation_id)
    self.loader.loaded.connect(self.display_conversation)
    self.loader.error.connect(self.display_error)
    self.loader.start()
    self.display_thinking_started("Loading conversation...")

@pyqtSlot(list)
def display_conversation(self, messages):
    """Display loaded conversation messages"""
    self.clear_chat()
    for msg in messages:
        self.append_message(
            msg['content'],
            is_user=msg['role'] == 'user',
            agent_name=msg.get('agent', 'ASSISTANT')
        )
    self.display_thinking_chunk("Conversation loaded")
```

```python
# Add at bottom of file:
class ConversationLoader(QThread):
    """Thread for async conversation loading"""
    loaded = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, message_handler, conv_id):
        super().__init__()
        self.message_handler = message_handler
        self.conv_id = conv_id

    def run(self):
        try:
            messages = self.message_handler.load_conversation(self.conv_id)
            self.loaded.emit(messages)
        except Exception as e:
            self.error.emit(f"Failed to load conversation: {str(e)}")
```
