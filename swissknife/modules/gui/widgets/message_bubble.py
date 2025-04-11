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
pre { line-height: 1; background-color: #F3F4E9; border-radius: 8px; padding: 12px; }
td.linenos .normal { color: #44483D; background-color: transparent; padding-left: 5px; padding-right: 5px; }
span.linenos { color: #44483D; background-color: transparent; padding-left: 5px; padding-right: 5px; }
td.linenos .special { color: #1A1C16; background-color: #DCE7C8; padding-left: 5px; padding-right: 5px; }
span.linenos.special { color: #1A1C16; background-color: #DCE7C8; padding-left: 5px; padding-right: 5px; }
.codehilite .hll { background-color: #CDEDA3 }
.codehilite { background: #F3F4E9; border-radius: 8px; padding: 10px; }
.codehilite .c { color: #5C6550; font-style: italic } /* Comment */
.codehilite .err { border: 1px solid #B00020 } /* Error */
.codehilite .k { color: #4C662B; font-weight: bold } /* Keyword */
.codehilite .o { color: #44483D } /* Operator */
.codehilite .ch { color: #5C6550; font-style: italic } /* Comment.Hashbang */
.codehilite .cm { color: #5C6550; font-style: italic } /* Comment.Multiline */
.codehilite .cp { color: #7D5700 } /* Comment.Preproc */
.codehilite .cpf { color: #5C6550; font-style: italic } /* Comment.PreprocFile */
.codehilite .c1 { color: #5C6550; font-style: italic } /* Comment.Single */
.codehilite .cs { color: #5C6550; font-style: italic } /* Comment.Special */
.codehilite .gd { color: #B00020 } /* Generic.Deleted */
.codehilite .ge { font-style: italic } /* Generic.Emph */
.codehilite .ges { font-weight: bold; font-style: italic } /* Generic.EmphStrong */
.codehilite .gr { color: #B00020 } /* Generic.Error */
.codehilite .gh { color: #354E16; font-weight: bold } /* Generic.Heading */
.codehilite .gi { color: #4C662B } /* Generic.Inserted */
.codehilite .go { color: #44483D } /* Generic.Output */
.codehilite .gp { color: #354E16; font-weight: bold } /* Generic.Prompt */
.codehilite .gs { font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #586249; font-weight: bold } /* Generic.Subheading */
.codehilite .gt { color: #1B4D90 } /* Generic.Traceback */
.codehilite .kc { color: #4C662B; font-weight: bold } /* Keyword.Constant */
.codehilite .kd { color: #4C662B; font-weight: bold } /* Keyword.Declaration */
.codehilite .kn { color: #4C662B; font-weight: bold } /* Keyword.Namespace */
.codehilite .kp { color: #4C662B } /* Keyword.Pseudo */
.codehilite .kr { color: #4C662B; font-weight: bold } /* Keyword.Reserved */
.codehilite .kt { color: #7D3C00 } /* Keyword.Type */
.codehilite .m { color: #44483D } /* Literal.Number */
.codehilite .s { color: #7D3C00 } /* Literal.String */
.codehilite .na { color: #4C662B } /* Name.Attribute */
.codehilite .nb { color: #4C662B } /* Name.Builtin */
.codehilite .nc { color: #1B4D90; font-weight: bold } /* Name.Class */
.codehilite .no { color: #7D3C00 } /* Name.Constant */
.codehilite .nd { color: #586249 } /* Name.Decorator */
.codehilite .ni { color: #44483D; font-weight: bold } /* Name.Entity */
.codehilite .ne { color: #B00020; font-weight: bold } /* Name.Exception */
.codehilite .nf { color: #1B4D90 } /* Name.Function */
.codehilite .nl { color: #4C662B } /* Name.Label */
.codehilite .nn { color: #1B4D90; font-weight: bold } /* Name.Namespace */
.codehilite .nt { color: #4C662B; font-weight: bold } /* Name.Tag */
.codehilite .nv { color: #354E16 } /* Name.Variable */
.codehilite .ow { color: #586249; font-weight: bold } /* Operator.Word */
.codehilite .w { color: #C5C8BA } /* Text.Whitespace */
.codehilite .mb { color: #44483D } /* Literal.Number.Bin */
.codehilite .mf { color: #44483D } /* Literal.Number.Float */
.codehilite .mh { color: #44483D } /* Literal.Number.Hex */
.codehilite .mi { color: #44483D } /* Literal.Number.Integer */
.codehilite .mo { color: #44483D } /* Literal.Number.Oct */
.codehilite .sa { color: #7D3C00 } /* Literal.String.Affix */
.codehilite .sb { color: #7D3C00 } /* Literal.String.Backtick */
.codehilite .sc { color: #7D3C00 } /* Literal.String.Char */
.codehilite .dl { color: #7D3C00 } /* Literal.String.Delimiter */
.codehilite .sd { color: #7D3C00; font-style: italic } /* Literal.String.Doc */
.codehilite .s2 { color: #7D3C00 } /* Literal.String.Double */
.codehilite .se { color: #7D5700; font-weight: bold } /* Literal.String.Escape */
.codehilite .sh { color: #7D3C00 } /* Literal.String.Heredoc */
.codehilite .si { color: #7D3C00; font-weight: bold } /* Literal.String.Interpol */
.codehilite .sx { color: #4C662B } /* Literal.String.Other */
.codehilite .sr { color: #7D3C00 } /* Literal.String.Regex */
.codehilite .s1 { color: #7D3C00 } /* Literal.String.Single */
.codehilite .ss { color: #354E16 } /* Literal.String.Symbol */
.codehilite .bp { color: #4C662B } /* Name.Builtin.Pseudo */
.codehilite .fm { color: #1B4D90 } /* Name.Function.Magic */
.codehilite .vc { color: #354E16 } /* Name.Variable.Class */
.codehilite .vg { color: #354E16 } /* Name.Variable.Global */
.codehilite .vi { color: #354E16 } /* Name.Variable.Instance */
.codehilite .vm { color: #354E16 } /* Name.Variable.Magic */
.codehilite .il { color: #44483D } /* Literal.Number.Integer.Long */
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
                    background-color: #CDEDA3; 
                    border: none;
                    padding: 2px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QFrame { 
                    border-radius: 12px; 
                    background-color: #F9FAEF; 
                    border: none;
                    padding: 2px;
                }
                """
            )

        # For thinking bubbles, add this condition
        if is_thinking:
            self.setStyleSheet(
                """
                QFrame { 
                    border-radius: 12px; 
                    background-color: #DCE7C8; 
                    border: none;
                    padding: 2px;
                }
                """
            )
        self.setAutoFillBackground(True)

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
        sender_label.setStyleSheet("font-weight: bold; color: #1A1C16; padding: 2px;")
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

        # Increase font size by 10%
        font = self.message_label.font()
        font_size = font.pointSizeF() * 1.5  # Increase by 10%
        font.setPointSizeF(font_size)
        self.message_label.setFont(font)

        # Set different text color for thinking content
        if is_thinking:
            self.message_label.setStyleSheet(
                "color: #44483D;"
            )  # Updated color for thinking text

        # Set the text content (convert Markdown to HTML)
        self.set_text(text)

        self.message_label.setMinimumWidth(900)
        self.message_label.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )

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
                    background-color: #4C662B;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #354E16;
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
                extensions=["tables", "fenced_code", "codehilite", "nl2br"],
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
            name_label.setStyleSheet("font-weight: bold; color: #1A1C16;")
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
            name_label.setStyleSheet(
                "font-weight: bold; color: #1A1C16; padding-left: 10px;"
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

            size_label.setStyleSheet("color: #44483D;")
            type_label.setStyleSheet("color: #44483D;")

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
            name_label.setStyleSheet("font-weight: bold; color: #1A1C16;")
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
