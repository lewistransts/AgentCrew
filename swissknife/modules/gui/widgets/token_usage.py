from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)
from PySide6.QtGui import (
    QColor,
    QPalette,
)


class TokenUsageWidget(QWidget):
    """Widget to display token usage information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        # Set background color
        palette = self.palette()
        palette.setColor(
            QPalette.ColorRole.Window, QColor("#EEEEFF")
        )  # Light blue background
        self.setPalette(palette)

        # Create layout
        layout = QVBoxLayout(self)

        # Create labels
        self.token_label = QLabel(
            "📊 Token Usage: Input: 0 | Output: 0 | Total: 0 | Cost: $0.0000 | Session: $0.0000"
        )
        self.token_label.setStyleSheet("color: #555555; font-weight: bold;")

        # Add to layout
        layout.addWidget(self.token_label)

    def update_token_info(
        self,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        session_cost: float,
    ):
        """Update the token usage information."""
        self.token_label.setText(
            f"📊 Token Usage: Input: {input_tokens:,} | Output: {output_tokens:,} | "
            f"Total: {input_tokens + output_tokens:,} | Cost: ${total_cost:.4f} | Session: ${session_cost:.4f}"
        )
