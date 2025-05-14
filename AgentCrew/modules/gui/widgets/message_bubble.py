from typing import Optional
import markdown
import os
import mimetypes

from PySide6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QPushButton,
    QHBoxLayout,
    QFileIconProvider,
)
from PySide6.QtCore import Qt, QFileInfo, QByteArray
from PySide6.QtGui import QPixmap

# File display constants
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
MAX_IMAGE_WIDTH = 600  # Maximum width for displayed images

CODE_CSS = """
pre { line-height: 1; background-color: #181825; border-radius: 8px; padding: 12px; color: #cdd6f4; white-space: pre-wrap; word-wrap: break-word; } /* Mantle, Text */
td.linenos .normal { color: #6c7086; background-color: transparent; padding-left: 5px; padding-right: 5px; } /* Overlay0 */
span.linenos { color: #6c7086; background-color: transparent; padding-left: 5px; padding-right: 5px; } /* Overlay0 */
td.linenos .special { color: #cdd6f4; background-color: #313244; padding-left: 5px; padding-right: 5px; } /* Text, Surface0 */
span.linenos.special { color: #cdd6f4; background-color: #313244; padding-left: 5px; padding-right: 5px; } /* Text, Surface0 */
.codehilite .hll { background-color: #313244 } /* Surface0 */
.codehilite { background: #181825; border-radius: 8px; padding: 10px; color: #cdd6f4; } /* Mantle, Text */
.codehilite .c { color: #6c7086; font-style: italic } /* Comment -> Overlay0 */
.codehilite .err { border: 1px solid #f38ba8; color: #f38ba8; } /* Error -> Red */
.codehilite .k { color: #cba6f7; font-weight: bold } /* Keyword -> Mauve */
.codehilite .o { color: #94e2d5 } /* Operator -> Teal */
.codehilite .ch { color: #6c7086; font-style: italic } /* Comment.Hashbang -> Overlay0 */
.codehilite .cm { color: #6c7086; font-style: italic } /* Comment.Multiline -> Overlay0 */
.codehilite .cp { color: #f9e2af } /* Comment.Preproc -> Yellow */
.codehilite .cpf { color: #6c7086; font-style: italic } /* Comment.PreprocFile -> Overlay0 */
.codehilite .c1 { color: #6c7086; font-style: italic } /* Comment.Single -> Overlay0 */
.codehilite .cs { color: #6c7086; font-style: italic } /* Comment.Special -> Overlay0 */
.codehilite .gd { color: #f38ba8 } /* Generic.Deleted -> Red */
.codehilite .ge { font-style: italic } /* Generic.Emph */
.codehilite .ges { font-weight: bold; font-style: italic } /* Generic.EmphStrong */
.codehilite .gr { color: #f38ba8 } /* Generic.Error -> Red */
.codehilite .gh { color: #89b4fa; font-weight: bold } /* Generic.Heading -> Blue */
.codehilite .gi { color: #a6e3a1 } /* Generic.Inserted -> Green */
.codehilite .go { color: #cdd6f4 } /* Generic.Output -> Text */
.codehilite .gp { color: #89b4fa; font-weight: bold } /* Generic.Prompt -> Blue */
.codehilite .gs { font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #89b4fa; font-weight: bold } /* Generic.Subheading -> Blue */
.codehilite .gt { color: #f38ba8 } /* Generic.Traceback -> Red */
.codehilite .kc { color: #cba6f7; font-weight: bold } /* Keyword.Constant -> Mauve */
.codehilite .kd { color: #cba6f7; font-weight: bold } /* Keyword.Declaration -> Mauve */
.codehilite .kn { color: #cba6f7; font-weight: bold } /* Keyword.Namespace -> Mauve */
.codehilite .kp { color: #cba6f7 } /* Keyword.Pseudo -> Mauve */
.codehilite .kr { color: #cba6f7; font-weight: bold } /* Keyword.Reserved -> Mauve */
.codehilite .kt { color: #fab387; font-weight: bold } /* Keyword.Type -> Peach */
.codehilite .m { color: #fab387 } /* Literal.Number -> Peach */
.codehilite .s { color: #a6e3a1 } /* Literal.String -> Green */
.codehilite .na { color: #89dceb } /* Name.Attribute -> Sky */
.codehilite .nb { color: #89b4fa } /* Name.Builtin -> Blue */
.codehilite .nc { color: #f9e2af; font-weight: bold } /* Name.Class -> Yellow */
.codehilite .no { color: #fab387 } /* Name.Constant -> Peach */
.codehilite .nd { color: #cba6f7 } /* Name.Decorator -> Mauve */
.codehilite .ni { color: #cdd6f4; font-weight: bold } /* Name.Entity -> Text */
.codehilite .ne { color: #f38ba8; font-weight: bold } /* Name.Exception -> Red */
.codehilite .nf { color: #89b4fa; font-weight: bold } /* Name.Function -> Blue */
.codehilite .nl { color: #cdd6f4 } /* Name.Label -> Text */
.codehilite .nn { color: #f9e2af; font-weight: bold } /* Name.Namespace -> Yellow */
.codehilite .nt { color: #cba6f7; font-weight: bold } /* Name.Tag -> Mauve */
.codehilite .nv { color: #f5e0dc } /* Name.Variable -> Rosewater */
.codehilite .ow { color: #94e2d5; font-weight: bold } /* Operator.Word -> Teal */
.codehilite .w { color: #45475a } /* Text.Whitespace -> Surface1 */
.codehilite .mb { color: #fab387 } /* Literal.Number.Bin -> Peach */
.codehilite .mf { color: #fab387 } /* Literal.Number.Float -> Peach */
.codehilite .mh { color: #fab387 } /* Literal.Number.Hex -> Peach */
.codehilite .mi { color: #fab387 } /* Literal.Number.Integer -> Peach */
.codehilite .mo { color: #fab387 } /* Literal.Number.Oct -> Peach */
.codehilite .sa { color: #a6e3a1 } /* Literal.String.Affix -> Green */
.codehilite .sb { color: #a6e3a1 } /* Literal.String.Backtick -> Green */
.codehilite .sc { color: #a6e3a1 } /* Literal.String.Char -> Green */
.codehilite .dl { color: #a6e3a1 } /* Literal.String.Delimiter -> Green */
.codehilite .sd { color: #6c7086; font-style: italic } /* Literal.String.Doc -> Overlay0 */
.codehilite .s2 { color: #a6e3a1 } /* Literal.String.Double -> Green */
.codehilite .se { color: #fab387; font-weight: bold } /* Literal.String.Escape -> Peach */
.codehilite .sh { color: #a6e3a1 } /* Literal.String.Heredoc -> Green */
.codehilite .si { color: #a6e3a1; font-weight: bold } /* Literal.String.Interpol -> Green */
.codehilite .sx { color: #a6e3a1 } /* Literal.String.Other -> Green */
.codehilite .sr { color: #a6e3a1 } /* Literal.String.Regex -> Green */
.codehilite .s1 { color: #a6e3a1 } /* Literal.String.Single -> Green */
.codehilite .ss { color: #a6e3a1 } /* Literal.String.Symbol -> Green */
.codehilite .bp { color: #89b4fa } /* Name.Builtin.Pseudo -> Blue */
.codehilite .fm { color: #89b4fa; font-weight: bold } /* Name.Function.Magic -> Blue */
.codehilite .vc { color: #f5e0dc } /* Name.Variable.Class -> Rosewater */
.codehilite .vg { color: #f5e0dc } /* Name.Variable.Global -> Rosewater */
.codehilite .vi { color: #f5e0dc } /* Name.Variable.Instance -> Rosewater */
.codehilite .vm { color: #f5e0dc } /* Name.Variable.Magic -> Rosewater */
.codehilite .il { color: #fab387 } /* Literal.Number.Integer.Long -> Peach */
"""


class MessageBubble(QFrame):
    """A custom widget to display messages as bubbles."""

    def __init__(
        self,
        text,
        is_user=True,
        agent_name="ASSISTANT",
        parent=None,
        message_index=None,
        is_thinking=False,  # Add this parameter
    ):
        super().__init__(parent)

        # Store message index for rollback functionality
        self.message_index = message_index
        self.is_user = is_user
        self.is_thinking = is_thinking  # Store thinking state

        # Setup frame appearance
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.rollback_button: Optional[QPushButton] = None

        # Set background color based on sender
        if is_user:
            self.setStyleSheet(
                """
                QFrame { 
                    border-radius: 12px; 
                    background-color: #89b4fa; /* Catppuccin Blue */
                    border: none;
                    padding: 2px;
                }
                """
            )
        elif is_thinking:  # Check is_thinking before general assistant bubble
            self.setStyleSheet(
                """
                QFrame { 
                    border-radius: 12px; 
                    background-color: #45475a; /* Catppuccin Surface1 */
                    border: none;
                    padding: 2px;
                }
                """
            )
        else:  # Assistant bubble
            self.setStyleSheet(
                """
                QFrame { 
                    border-radius: 12px; 
                    background-color: #313244; /* Catppuccin Surface0 */
                    border: none;
                    padding: 2px;
                }
                """
            )

        # This setAutoFillBackground(True) might not be necessary if QFrame style is set
        # self.setAutoFillBackground(True) # You can test if this is needed

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add sender label - Use agent_name for non-user messages
        label_text = "YOU:" if is_user else f"{agent_name}:"
        if is_thinking:
            label_text = (
                f"{agent_name}'s THINKING:"  # Special label for thinking content
            )

        sender_label = QLabel(label_text)
        sender_label_color = (
            "#1e1e2e" if is_user else "#cdd6f4"
        )  # Base for user, Text for others
        if is_thinking:
            sender_label_color = "#bac2de"  # Subtext1 for thinking sender
        sender_label.setStyleSheet(
            f"font-weight: bold; color: {sender_label_color}; padding: 2px;"
        )
        layout.addWidget(sender_label)

        # Create label with HTML support
        self.message_label = QLabel()
        self.message_label.setTextFormat(Qt.TextFormat.RichText)
        self.message_label.setWordWrap(True)
        self.message_label.setOpenExternalLinks(True)  # Allow clicking links
        self.message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        # Increase font size by 10% (original logic was 1.5x, keeping that)
        font = self.message_label.font()
        font_size = font.pointSizeF() * 1.5
        font.setPointSizeF(font_size)
        self.message_label.setFont(font)

        # Set different text color for message content based on bubble type
        message_text_color = (
            "#1e1e2e" if is_user else "#cdd6f4"
        )  # Base for user, Text for assistant
        if is_thinking:
            message_text_color = "#bac2de"  # Subtext1 for thinking text
        self.message_label.setStyleSheet(f"color: {message_text_color};")

        # Set the text content (convert Markdown to HTML)
        self.set_text(text)

        self.message_label.setMinimumWidth(900)
        self.message_label.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )

        if text is not None:
            # Add to layout
            layout.addWidget(self.message_label)

        # Set size policies
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Store the original text (for adding chunks)
        self.text_content = text

        # For user messages, add hover button functionality
        if is_user and message_index is not None:
            # Set up hover events for rollback button
            self.setMouseTracking(True)

            rollback_button = QPushButton("↩ Rollback", self)
            rollback_button.setStyleSheet("""
                QPushButton {
                    background-color: #b4befe; /* Catppuccin Lavender */
                    color: #1e1e2e; /* Catppuccin Base */
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #cba6f7; /* Catppuccin Mauve */
                }
                QPushButton:pressed {
                    background-color: #f5c2e7; /* Catppuccin Pink */
                }
            """)
            rollback_button.hide()

            # Store the button as a property of the message bubble
            self.rollback_button = rollback_button

            # Override enter and leave events
            original_enter_event = self.enterEvent
            original_leave_event = self.leaveEvent

            def enter_event_wrapper(event):
                if self.rollback_button:
                    # Position the button in the top right corner
                    button_width = self.rollback_button.sizeHint().width()
                    button_height = self.rollback_button.sizeHint().height()
                    self.rollback_button.setGeometry(
                        self.width() - button_width - 5,
                        5,
                        button_width,
                        button_height,
                    )
                    self.rollback_button.show()
                if original_enter_event:
                    original_enter_event(event)

            def leave_event_wrapper(event):
                if self.rollback_button:
                    self.rollback_button.hide()
                if original_leave_event:
                    original_leave_event(event)

            self.enterEvent = enter_event_wrapper
            self.leaveEvent = leave_event_wrapper

            # Make sure button is properly positioned when message bubble is resized
            original_resize_event = self.resizeEvent

            def resize_event_wrapper(event):
                if (
                    hasattr(self, "rollback_button")
                    and self.rollback_button
                    and self.rollback_button.isVisible()
                ):
                    button_width = self.rollback_button.sizeHint().width()
                    button_height = self.rollback_button.sizeHint().height()
                    self.rollback_button.setGeometry(
                        self.width() - button_width - 5,
                        5,
                        button_width,
                        button_height,
                    )
                if original_resize_event:
                    original_resize_event(event)

            self.resizeEvent = resize_event_wrapper

    def set_text(self, text):
        """Set or update the text content of the message."""
        try:
            html_content = markdown.markdown(
                text,
                output_format="html",
                extensions=[
                    "tables",
                    "fenced_code",
                    "codehilite",
                    "nl2br",
                    "sane_lists",
                ],
            )
            html_content = (
                f"""<style>
            pre {{ white-space: pre-wrap; margin-bottom: 0;}}
                {CODE_CSS}
            </style>"""
                + html_content
            )
            self.message_label.setText(html_content)
        except Exception as e:
            print(f"Error rendering markdown: {e}")
            self.message_label.setText(text)

    def append_text(self, text):
        """Append text to the existing message."""
        self.text_content = text
        self.set_text(self.text_content)

    def display_file(self, file_path: str):
        """Display a file in the message bubble based on its type."""
        if not os.path.exists(file_path):
            self.append_text(f"File not found: {file_path}")
            return

        # Create a container for the file display
        file_container = QFrame(self)
        file_layout = QVBoxLayout(file_container)
        file_layout.setContentsMargins(1, 1, 1, 1)

        # Get file extension and determine file type
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()
        file_name = os.path.basename(file_path)

        # Handle image files
        if file_extension in IMAGE_EXTENSIONS:
            # Create image label
            image_label = QLabel()
            pixmap = QPixmap(file_path)

            # Scale image if it's too large
            if pixmap.width() > MAX_IMAGE_WIDTH:
                pixmap = pixmap.scaledToWidth(
                    MAX_IMAGE_WIDTH, Qt.TransformationMode.SmoothTransformation
                )

            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Add file name above the image
            name_label = QLabel(file_name)
            name_label_color = "#1e1e2e" if self.is_user else "#cdd6f4"
            name_label.setStyleSheet(f"font-weight: bold; color: {name_label_color};")
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            file_layout.addWidget(name_label)
            file_layout.addWidget(image_label)
        else:
            # For non-image files, show an icon with the file name
            file_info = QFileInfo(file_path)
            icon_provider = QFileIconProvider()
            file_icon = icon_provider.icon(file_info)

            # Create horizontal layout for icon and file name
            icon_layout = QHBoxLayout()

            # Create icon label
            icon_label = QLabel()
            icon_label.setPixmap(file_icon.pixmap(48, 48))

            # Create file name label
            name_label = QLabel(file_name)
            name_label_color = "#1e1e2e" if self.is_user else "#cdd6f4"
            name_label.setStyleSheet(
                f"font-weight: bold; color: {name_label_color}; padding-left: 10px;"
            )

            icon_layout.addWidget(icon_label)
            icon_layout.addWidget(name_label)
            icon_layout.addStretch(1)

            file_layout.addLayout(icon_layout)

            # Add file size and type information
            file_size = os.path.getsize(file_path)
            file_type = mimetypes.guess_type(file_path)[0] or "Unknown type"

            size_label = QLabel(f"Size: {self._format_file_size(file_size)}")
            type_label = QLabel(f"Type: {file_type}")

            file_info_color = "#6c7086"  # Catppuccin Overlay0
            if self.is_user:  # Adjust for better contrast on user bubble
                file_info_color = "#313244"  # Surface0 might be better on Blue

            size_label.setStyleSheet(f"color: {file_info_color};")
            type_label.setStyleSheet(f"color: {file_info_color};")

            file_layout.addWidget(size_label)
            file_layout.addWidget(type_label)

        # Add the file container to the message layout
        self.layout().addWidget(file_container)

        # Force update and scroll
        self.updateGeometry()

    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def display_base64_img(self, data: str):
        """
        Display a base64-encoded image in the message bubble.

        Args:
            data: Base64 image data in format 'data:mime_type;base64,data'
        """
        try:
            # Parse the data URL format
            if not data.startswith("data:"):
                raise ValueError("Invalid data URL format. Must start with 'data:'")

            # Extract mime type and base64 data
            header, encoded_data = data.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]

            if not mime_type.startswith("image/"):
                raise ValueError(
                    f"Unsupported mime type: {mime_type}. Only image types are supported."
                )

            # Create a container for the image display
            img_container = QFrame(self)
            img_layout = QVBoxLayout(img_container)
            img_layout.setContentsMargins(1, 1, 1, 1)

            # Create image label
            image_label = QLabel()
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray.fromBase64(encoded_data.encode()))

            # Scale image if it's too large
            if pixmap.width() > MAX_IMAGE_WIDTH:
                pixmap = pixmap.scaledToWidth(
                    MAX_IMAGE_WIDTH, Qt.TransformationMode.SmoothTransformation
                )

            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Add a label indicating it's a base64 image
            name_label = QLabel("Image")
            name_label_color = "#1e1e2e" if self.is_user else "#cdd6f4"
            name_label.setStyleSheet(f"font-weight: bold; color: {name_label_color};")
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            img_layout.addWidget(name_label)
            img_layout.addWidget(image_label)

            # Add the image container to the message layout
            self.layout().addWidget(img_container)

            # Force update and scroll
            self.updateGeometry()

        except Exception as e:
            error_msg = f"Error displaying base64 image: {str(e)}"
            print(error_msg)
            self.append_text(f"\n\n*{error_msg}*")
