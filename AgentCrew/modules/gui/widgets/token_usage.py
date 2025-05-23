from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)


class TokenUsageWidget(QWidget):
    """Widget to display token usage information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setAutoFillBackground(True) # Remove this line

        # Set background color directly via stylesheet
        self.setStyleSheet("background-color: #11111b;")  # Catppuccin Crust

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove default margins if any

        # Create labels
        self.token_label = QLabel(
            "📊 Token Usage: Input: 0 | Output: 0 | Total: 0 | Cost: $0.0000 | Session: $0.0000"
        )
        self.token_label.setStyleSheet(
            """
            QLabel {
                color: #bac2de; /* Catppuccin Subtext1 */
                font-weight: bold;
                padding: 8px;
                background-color: #11111b; /* Catppuccin Crust */
                border-top: 1px solid #313244; /* Catppuccin Surface0 for a subtle separator */
            }
            """
        )

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
