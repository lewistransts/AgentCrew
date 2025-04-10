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

CODE_CSS = """
pre { line-height: 1; }
td.linenos .normal { color: inherit; background-color: transparent; padding-left: 5px; padding-right: 5px; }
span.linenos { color: inherit; background-color: transparent; padding-left: 5px; padding-right: 5px; }
td.linenos .special { color: #000000; background-color: #ffffc0; padding-left: 5px; padding-right: 5px; }
span.linenos.special { color: #000000; background-color: #ffffc0; padding-left: 5px; padding-right: 5px; }
.codehilite .hll { background-color: #ffffcc }
.codehilite { background: #f8f8f8; }
.codehilite .c { color: #3D7B7B; font-style: italic } /* Comment */
.codehilite .err { border: 1px solid #F00 } /* Error */
.codehilite .k { color: #008000; font-weight: bold } /* Keyword */
.codehilite .o { color: #666 } /* Operator */
.codehilite .ch { color: #3D7B7B; font-style: italic } /* Comment.Hashbang */
.codehilite .cm { color: #3D7B7B; font-style: italic } /* Comment.Multiline */
.codehilite .cp { color: #9C6500 } /* Comment.Preproc */
.codehilite .cpf { color: #3D7B7B; font-style: italic } /* Comment.PreprocFile */
.codehilite .c1 { color: #3D7B7B; font-style: italic } /* Comment.Single */
.codehilite .cs { color: #3D7B7B; font-style: italic } /* Comment.Special */
.codehilite .gd { color: #A00000 } /* Generic.Deleted */
.codehilite .ge { font-style: italic } /* Generic.Emph */
.codehilite .ges { font-weight: bold; font-style: italic } /* Generic.EmphStrong */
.codehilite .gr { color: #E40000 } /* Generic.Error */
.codehilite .gh { color: #000080; font-weight: bold } /* Generic.Heading */
.codehilite .gi { color: #008400 } /* Generic.Inserted */
.codehilite .go { color: #717171 } /* Generic.Output */
.codehilite .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
.codehilite .gs { font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
.codehilite .gt { color: #04D } /* Generic.Traceback */
.codehilite .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
.codehilite .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
.codehilite .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
.codehilite .kp { color: #008000 } /* Keyword.Pseudo */
.codehilite .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
.codehilite .kt { color: #B00040 } /* Keyword.Type */
.codehilite .m { color: #666 } /* Literal.Number */
.codehilite .s { color: #BA2121 } /* Literal.String */
.codehilite .na { color: #687822 } /* Name.Attribute */
.codehilite .nb { color: #008000 } /* Name.Builtin */
.codehilite .nc { color: #00F; font-weight: bold } /* Name.Class */
.codehilite .no { color: #800 } /* Name.Constant */
.codehilite .nd { color: #A2F } /* Name.Decorator */
.codehilite .ni { color: #717171; font-weight: bold } /* Name.Entity */
.codehilite .ne { color: #CB3F38; font-weight: bold } /* Name.Exception */
.codehilite .nf { color: #00F } /* Name.Function */
.codehilite .nl { color: #767600 } /* Name.Label */
.codehilite .nn { color: #00F; font-weight: bold } /* Name.Namespace */
.codehilite .nt { color: #008000; font-weight: bold } /* Name.Tag */
.codehilite .nv { color: #19177C } /* Name.Variable */
.codehilite .ow { color: #A2F; font-weight: bold } /* Operator.Word */
.codehilite .w { color: #BBB } /* Text.Whitespace */
.codehilite .mb { color: #666 } /* Literal.Number.Bin */
.codehilite .mf { color: #666 } /* Literal.Number.Float */
.codehilite .mh { color: #666 } /* Literal.Number.Hex */
.codehilite .mi { color: #666 } /* Literal.Number.Integer */
.codehilite .mo { color: #666 } /* Literal.Number.Oct */
.codehilite .sa { color: #BA2121 } /* Literal.String.Affix */
.codehilite .sb { color: #BA2121 } /* Literal.String.Backtick */
.codehilite .sc { color: #BA2121 } /* Literal.String.Char */
.codehilite .dl { color: #BA2121 } /* Literal.String.Delimiter */
.codehilite .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
.codehilite .s2 { color: #BA2121 } /* Literal.String.Double */
.codehilite .se { color: #AA5D1F; font-weight: bold } /* Literal.String.Escape */
.codehilite .sh { color: #BA2121 } /* Literal.String.Heredoc */
.codehilite .si { color: #A45A77; font-weight: bold } /* Literal.String.Interpol */
.codehilite .sx { color: #008000 } /* Literal.String.Other */
.codehilite .sr { color: #A45A77 } /* Literal.String.Regex */
.codehilite .s1 { color: #BA2121 } /* Literal.String.Single */
.codehilite .ss { color: #19177C } /* Literal.String.Symbol */
.codehilite .bp { color: #008000 } /* Name.Builtin.Pseudo */
.codehilite .fm { color: #00F } /* Name.Function.Magic */
.codehilite .vc { color: #19177C } /* Name.Variable.Class */
.codehilite .vg { color: #19177C } /* Name.Variable.Global */
.codehilite .vi { color: #19177C } /* Name.Variable.Instance */
.codehilite .vm { color: #19177C } /* Name.Variable.Magic */
.codehilite .il { color: #666 } /* Literal.Number.Integer.Long */
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
        label_text = "YOU:" if is_user else f"{agent_name}:"
        if is_thinking:
            label_text = (
                f"{agent_name}'s THINKING:"  # Special label for thinking content
            )

        sender_label = QLabel(label_text)
        sender_label.setStyleSheet("font-weight: bold; color: #333333;")
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
                "color: #666666;"
            )  # Gray color for thinking text

        # Set the text content (convert Markdown to HTML)
        self.set_text(text)

        self.message_label.setMinimumWidth(900)
        self.message_label.setMaximumWidth(1600)

        # Add to layout
        layout.addWidget(self.message_label)

        # Set size policies
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Store the original text (for adding chunks)
        self.text_content = text

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
