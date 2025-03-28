import markdown

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import (
    Qt,
)


class SystemMessageWidget(QWidget):
    """Widget to display system messages."""

    def __init__(self, text, parent=None):
        super().__init__(parent)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Store the full text
        self.full_text = text
        self.is_expanded = False

        # Create collapsible container
        self.container = QWidget()
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Create label with HTML support
        self.message_label = QLabel()
        self.message_label.setTextFormat(Qt.TextFormat.RichText)
        self.message_label.setStyleSheet("color: #6495ED;")  # Olive yellow
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | 
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        font = self.message_label.font()
        font_size = font.pointSizeF() * 1.2  # Increase by 10%
        font.setPointSizeF(font_size)
        self.message_label.setFont(font)

        # Create expand/collapse button
        self.toggle_button = QPushButton("▼ Show More")
        self.toggle_button.setStyleSheet(
            "QPushButton { background-color: transparent; color: #6495ED; border: none; text-align: left; }"
        )
        self.toggle_button.setMaximumHeight(20)
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle_expansion)

        # Add widgets to container
        container_layout.addWidget(self.message_label)
        container_layout.addWidget(self.toggle_button)

        # Add container to main layout
        layout.addWidget(self.container)

        # Set the collapsed text initially
        self.set_collapsed_text()

    def set_collapsed_text(self):
        """Set the text to show only 2 lines when collapsed."""
        # Convert markdown to HTML if the text contains code blocks
        if "```" in self.full_text:
            try:
                html_content = markdown.markdown(
                    self.full_text, extensions=["fenced_code"]
                )

                # Get first two lines (approximate)
                lines = self.full_text.split("\n")
                if len(lines) <= 2:
                    # If there are only 1-2 lines, show everything and hide the button
                    self.message_label.setText(html_content)
                    self.toggle_button.hide()
                    return

                # Show first two lines
                collapsed_text = "\n".join(lines[:2])
                if "```" in collapsed_text and "```" not in collapsed_text + "\n```":
                    # If we cut in the middle of a code block, add closing ```
                    collapsed_text += "\n```"

                collapsed_html = markdown.markdown(
                    collapsed_text, extensions=["fenced_code"]
                )
                self.message_label.setText(collapsed_html + "...")
                self.toggle_button.show()
            except Exception:
                # Fallback to simple text truncation
                lines = self.full_text.split("\n")
                if len(lines) <= 2:
                    self.message_label.setText(self.full_text)
                    self.toggle_button.hide()
                else:
                    self.message_label.setText("\n".join(lines[:2]) + "...")
                    self.toggle_button.show()
        else:
            # Simple text truncation
            lines = self.full_text.split("\n")
            if len(lines) <= 2:
                self.message_label.setText(self.full_text)
                self.toggle_button.hide()
            else:
                self.message_label.setText("\n".join(lines[:2]) + "...")
                self.toggle_button.show()

    def set_expanded_text(self):
        """Set the text to show all content."""
        if "```" in self.full_text:
            try:
                html_content = markdown.markdown(
                    self.full_text, extensions=["fenced_code"]
                )
                self.message_label.setText(html_content)
            except Exception:
                self.message_label.setText(self.full_text)
        else:
            self.message_label.setText(self.full_text)

    def toggle_expansion(self):
        """Toggle between expanded and collapsed states."""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.set_expanded_text()
            self.toggle_button.setText("▲ Show Less")
        else:
            self.set_collapsed_text()
            self.toggle_button.setText("▼ Show More")
