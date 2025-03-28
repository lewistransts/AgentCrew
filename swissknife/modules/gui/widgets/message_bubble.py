import markdown

from PySide6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
)


class MessageBubble(QFrame):
    """A custom widget to display messages as bubbles."""

    def __init__(self, text, is_user=True, agent_name="ASSISTANT", parent=None):
        super().__init__(parent)

        # Setup frame appearance
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)

        # Set background color based on sender
        if is_user:
            self.setStyleSheet(
                "QFrame { border-radius: 10px; background-color: #DCF8C6; }"
            )
        else:
            self.setStyleSheet(
                "QFrame { border-radius: 10px; background-color: #ADD8E6; }"
            )
        self.setAutoFillBackground(True)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add sender label - Use agent_name for non-user messages
        sender_label = QLabel(is_user and "YOU:" or f"{agent_name}:")
        sender_label.setStyleSheet("font-weight: bold; color: #333333;")
        layout.addWidget(sender_label)

        # Create label with HTML support
        self.message_label = QLabel()
        self.message_label.setTextFormat(Qt.TextFormat.RichText)
        self.message_label.setWordWrap(True)
        self.message_label.setOpenExternalLinks(True)  # Allow clicking links

        # Increase font size by 10%
        font = self.message_label.font()
        font_size = font.pointSizeF() * 1.5  # Increase by 10%
        font.setPointSizeF(font_size)
        self.message_label.setFont(font)

        # Set the text content (convert Markdown to HTML)
        self.set_text(text)

        # Set minimum and maximum width - increase max width by 3 times
        self.message_label.setMinimumWidth(500)
        self.message_label.setMaximumWidth(1200)  # Increased from 500 to 1500

        # Add to layout
        layout.addWidget(self.message_label)

        # Set size policies
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Store the original text (for adding chunks)
        self.text_content = text

    def set_text(self, text):
        """Set or update the text content of the message."""
        try:
            html_content = markdown.markdown(text, extensions=["fenced_code"])
            self.message_label.setText(html_content)
        except Exception as e:
            print(f"Error rendering markdown: {e}")
            self.message_label.setText(text)

    def append_text(self, text):
        """Append text to the existing message."""
        self.text_content += text
        self.set_text(self.text_content)
