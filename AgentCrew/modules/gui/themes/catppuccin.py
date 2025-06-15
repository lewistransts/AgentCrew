"""Catppuccin theme styles for AgentCrew GUI."""

# Main application styles
MAIN_STYLE = """
QMainWindow {
    background-color: #1e1e2e; /* Catppuccin Base */
}
QScrollArea {
    border: none;
    background-color: #181825; /* Catppuccin Mantle */
}
QWidget#chatContainer { /* Specific ID for chat_container */
    background-color: #181825; /* Catppuccin Mantle */
}
QSplitter::handle {
    background-color: #313244; /* Catppuccin Surface0 */
}
QSplitter::handle:hover {
    background-color: #45475a; /* Catppuccin Surface1 */
}
QSplitter::handle:pressed {
    background-color: #585b70; /* Catppuccin Surface2 */
}
QStatusBar {
    background-color: #11111b; /* Catppuccin Crust */
    color: #cdd6f4; /* Catppuccin Text */
}
QToolTip {
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    padding: 4px;
}
QMessageBox {
    background-color: #181825; /* Catppuccin Mantle */
}
QMessageBox QLabel { /* For message text in QMessageBox */
    color: #cdd6f4; /* Catppuccin Text */
    background-color: transparent; /* Ensure no overriding background */
}
/* QCompleter's popup is often a QListView */
QListView { /* General style for QListView, affects completer */
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    padding: 2px;
    outline: 0px; /* Remove focus outline if not desired */
}
QListView::item {
    padding: 4px 8px;
    border-radius: 2px; /* Optional: rounded corners for items */
}
QListView::item:selected {
    background-color: #585b70; /* Catppuccin Surface2 */
    color: #b4befe; /* Catppuccin Lavender */
}
QListView::item:hover {
    background-color: #45475a; /* Catppuccin Surface1 */
}

/* Modern Scrollbar Styles */
QScrollBar:vertical {
    border: none;
    background: #181825; /* Catppuccin Mantle - Track background */
    width: 10px; /* Adjust width for a thinner scrollbar */
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #45475a; /* Catppuccin Surface1 - Handle color */
    min-height: 20px; /* Minimum handle size */
    border-radius: 5px; /* Rounded corners for the handle */
}
QScrollBar::handle:vertical:hover {
    background: #585b70; /* Catppuccin Surface2 - Handle hover color */
}
QScrollBar::handle:vertical:pressed {
    background: #6c7086; /* Catppuccin Overlay0 - Handle pressed color */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none; /* Hide arrow buttons */
    height: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none; /* Track area above/below handle */
}

QScrollBar:horizontal {
    border: none;
    background: #181825; /* Catppuccin Mantle - Track background */
    height: 10px; /* Adjust height for a thinner scrollbar */
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #45475a; /* Catppuccin Surface1 - Handle color */
    min-width: 20px; /* Minimum handle size */
    border-radius: 5px; /* Rounded corners for the handle */
}
QScrollBar::handle:horizontal:hover {
    background: #585b70; /* Catppuccin Surface2 - Handle hover color */
}
QScrollBar::handle:horizontal:pressed {
    background: #6c7086; /* Catppuccin Overlay0 - Handle pressed color */
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none; /* Hide arrow buttons */
    width: 0px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none; /* Track area left/right of handle */
}

/* Context menu styling for QLabel widgets */
QLabel QMenu {
    background-color: #181825; /* Catppuccin Mantle */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    padding: 4px;
    border-radius: 6px;
}
QLabel QMenu::item {
    color: #f8f8f2; /* Brighter text color */
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
    margin: 2px;
}
QLabel QMenu::item:selected {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #ffffff; /* Pure white for selected items */
}
QLabel QMenu::item:pressed {
    background-color: #585b70; /* Catppuccin Surface2 */
}
QLabel QMenu::separator {
    height: 1px;
    background: #45475a; /* Catppuccin Surface1 */
    margin: 4px 8px;
}
"""

# Button styles
PRIMARY_BUTTON = """
QPushButton {
    background-color: #89b4fa; /* Catppuccin Blue */
    color: #1e1e2e; /* Catppuccin Base (for contrast) */
    border: none;
    border-radius: 4px; 
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #74c7ec; /* Catppuccin Sapphire */
}
QPushButton:pressed {
    background-color: #b4befe; /* Catppuccin Lavender */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
"""

SECONDARY_BUTTON = """
QPushButton {
    background-color: #585b70; /* Catppuccin Surface2 */
    color: #cdd6f4; /* Catppuccin Text */
    border: none;
    border-radius: 4px; 
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #6c7086; /* Catppuccin Overlay0 */
}
QPushButton:pressed {
    background-color: #7f849c; /* Catppuccin Overlay1 */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
"""

STOP_BUTTON = """
QPushButton {
    background-color: #f38ba8; /* Catppuccin Red */
    color: #1e1e2e; /* Catppuccin Base (for contrast) */
    border: none;
    border-radius: 4px; 
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #eba0ac; /* Catppuccin Maroon */
}
QPushButton:pressed {
    background-color: #f5c2e7; /* Catppuccin Pink */
}
"""

RED_BUTTON = """
QPushButton {
    background-color: #f38ba8; /* Catppuccin Red */
    color: #1e1e2e; /* Catppuccin Base (for contrast) */
    border: none;
    border-radius: 4px;
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #eba0ac; /* Catppuccin Maroon (lighter red for hover) */
}
QPushButton:pressed {
    background-color: #e67e8a; /* A slightly darker/more intense red for pressed */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
"""

GREEN_BUTTON = """
QPushButton {
    background-color: #a6e3a1; /* Catppuccin Green */
    color: #1e1e2e; /* Catppuccin Base */
    border: none;
    border-radius: 4px;
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #94e2d5; /* Catppuccin Teal - lighter green for hover */
}
QPushButton:pressed {
    background-color: #8bd5ca; /* Slightly darker for pressed state */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
"""

MENU_BUTTON = """
QPushButton {
    background-color: #89b4fa; /* Catppuccin Blue */
    color: #1e1e2e; /* Catppuccin Base */
    border: none;
    border-radius: 4px;
    padding: 8px;
    font-weight: bold;
    padding-left: 12px; /* Add some padding for text */
}
QPushButton:hover {
    background-color: #74c7ec; /* Catppuccin Sapphire */
}
QPushButton:pressed {
    background-color: #b4befe; /* Catppuccin Lavender */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
QPushButton::menu-indicator {
    /* image: url(myindicator.png); Adjust if using a custom image */
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 5px; /* Adjust as needed to position from the right edge */
    width: 16px; /* Ensure there's enough space for the indicator */
}
"""

DISABLED_BUTTON = """
QPushButton {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
    border: none;
    border-radius: 4px; 
    padding: 8px;
    font-weight: bold;
}
"""

STOP_BUTTON_STOPPING = """
QPushButton {
    background-color: #6c7086; /* Catppuccin Overlay0 - More grey/disabled look */
    color: #9399b2; /* Catppuccin Subtext1 - Muted text */
    border: none;
    border-radius: 4px; 
    padding: 8px;
    font-weight: bold;
}
"""

# Input styles
TEXT_INPUT = """
QTextEdit {
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    border-radius: 4px;
    padding: 8px;
}
QTextEdit:focus {
    border: 1px solid #89b4fa; /* Catppuccin Blue */
}
"""

LINE_EDIT = """
QLineEdit {
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    border-radius: 4px;
    padding: 8px;
}
QLineEdit:focus {
    border: 1px solid #89b4fa; /* Catppuccin Blue */
}
"""

# Menu styles
MENU_BAR = """
QMenuBar {
    background-color: #1e1e2e; /* Catppuccin Base */
    color: #cdd6f4; /* Catppuccin Text */
    padding: 2px;
}
QMenuBar::item {
    background-color: transparent;
    color: #cdd6f4; /* Catppuccin Text */
    padding: 4px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected { /* When menu is open or item is hovered */
    background-color: #313244; /* Catppuccin Surface0 */
}
QMenuBar::item:pressed { /* When menu item is pressed to open the menu */
    background-color: #45475a; /* Catppuccin Surface1 */
}
QMenu {
    background-color: #181825; /* Catppuccin Mantle */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px; /* Add border-radius to menu items */
}
QMenu::item:selected {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #b4befe; /* Catppuccin Lavender */
}
QMenu::separator {
    height: 1px;
    background: #45475a; /* Catppuccin Surface1 */
    margin-left: 10px;
    margin-right: 5px;
}
"""

CONTEXT_MENU = """
QMenu {
    background-color: #181825; /* Catppuccin Mantle */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    padding: 4px;
    border-radius: 6px;
}
QMenu::item {
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
    margin: 2px;
}
QMenu::item:selected {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #b4befe; /* Catppuccin Lavender */
}
QMenu::item:pressed {
    background-color: #585b70; /* Catppuccin Surface2 */
}
QMenu::separator {
    height: 1px;
    background: #45475a; /* Catppuccin Surface1 */
    margin: 4px 8px;
}
"""

AGENT_MENU = """
QMenu {
    background-color: #181825; /* Catppuccin Mantle */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #313244; /* Catppuccin Surface0 */
    border-radius: 4px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 20px;
    background-color: transparent;
}
QMenu::item:selected {
    background-color: #89b4fa; /* Catppuccin Blue */
    color: #1e1e2e; /* Catppuccin Base */
    border-radius: 3px;
}
QMenu::separator {
    height: 1px;
    background-color: #313244; /* Catppuccin Surface0 */
    margin-left: 5px;
    margin-right: 5px;
}
"""

# Label styles
STATUS_INDICATOR = """
QLabel {
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
    padding: 8px; 
    font-weight: bold;
}
"""

VERSION_LABEL = """
QLabel {
    color: #a6adc8; /* Catppuccin Subtext0 */
    padding: 2px 8px;
    font-size: 11px;
}
"""

SYSTEM_MESSAGE_TOGGLE_BUTTON = """
QPushButton {
    background-color: transparent;
    color: #94e2d5; /* Catppuccin Teal */
    border: none;
    text-align: left;
    padding: 2px;
}
QPushButton:hover {
    color: #89dceb; /* Catppuccin Sky */
}
"""

# Widget-specific styles
SIDEBAR = """
background-color: #181825; /* Catppuccin Mantle */
"""

CONVERSATION_LIST = """
QListWidget {
    background-color: #1e1e2e; /* Catppuccin Base */
    border: 1px solid #313244; /* Catppuccin Surface0 */
    border-radius: 4px;
}
QListWidget::item {
    color: #cdd6f4; /* Catppuccin Text */
    background-color: #1e1e2e; /* Catppuccin Base */
    border: none; /* Remove individual item borders if not desired */
    border-bottom: 1px solid #313244; /* Surface0 for separator */
    margin: 0px; /* Remove margin if using border for separation */
    padding: 8px;
}
/* QListWidget::item:alternate { */ /* Remove if not using alternating */
/*     background-color: #1a1a2e; */ /* Slightly different base if needed */
/* } */
QListWidget::item:selected {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #b4befe; /* Catppuccin Lavender */
}
QListWidget::item:hover:!selected {
    background-color: #313244; /* Catppuccin Surface0 */
}
"""

SEARCH_BOX = """
QLineEdit {
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    border-radius: 4px;
    padding: 8px;
}
QLineEdit:focus {
    border: 1px solid #89b4fa; /* Catppuccin Blue */
}
"""

TOKEN_USAGE = """
QLabel {
    color: #bac2de; /* Catppuccin Subtext1 */
    font-weight: bold;
    padding: 8px;
    background-color: #11111b; /* Catppuccin Crust */
    border-top: 1px solid #313244; /* Catppuccin Surface0 for a subtle separator */
}
"""

TOKEN_USAGE_WIDGET = """
background-color: #11111b; /* Catppuccin Crust */
"""

# Message bubble styles
USER_BUBBLE = """
QFrame { 
    border-radius: 12px; 
    background-color: #89b4fa; /* Catppuccin Blue */
    border: none;
    padding: 2px;
}
"""

ASSISTANT_BUBBLE = """
QFrame { 
    border-radius: 12px; 
    background-color: #313244; /* Catppuccin Surface0 */
    border: none;
    padding: 2px;
}
"""

THINKING_BUBBLE = """
QFrame { 
    border-radius: 12px; 
    background-color: #45475a; /* Catppuccin Surface1 */
    border: none;
    padding: 2px;
}
"""

CONSOLIDATED_BUBBLE = """
QFrame { 
    border-radius: 12px; 
    background-color: #313244; /* Catppuccin Surface0 */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    padding: 2px;
}
"""

ROLLBACK_BUTTON = """
QPushButton {
    background-color: #b4befe; /* Catppuccin Lavender */
    color: #1e1e2e; /* Catppuccin Base */
    border: none;
    border-radius: 15px;
    padding: 8px;
    font-size: 24px;
    font-weight: bold;
    width: 30px;
    height: 30px;
}
QPushButton:hover {
    background-color: #cba6f7; /* Catppuccin Mauve */
}
QPushButton:pressed {
    background-color: #f5c2e7; /* Catppuccin Pink */
}
"""

CONSOLIDATED_BUTTON = """
QPushButton {
    background-color: #b4befe; /* Catppuccin Lavender */
    color: #1e1e2e; /* Catppuccin Base */
    border: none;
    border-radius: 15px;
    padding: 8px;
    font-size: 24px;
    font-weight: bold;
    width: 30px;
    height: 30px;
}
QPushButton:hover {
    background-color: #cba6f7; /* Catppuccin Mauve */
}
QPushButton:pressed {
    background-color: #f5c2e7; /* Catppuccin Pink */
}
"""

# Tool dialog styles
TOOL_DIALOG_TEXT_EDIT = """
QTextEdit {
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    border-radius: 4px;
    padding: 8px;
    font-family: monospace;
}
QTextEdit:focus {
    border: 1px solid #89b4fa; /* Catppuccin Blue */
}
"""

TOOL_DIALOG_YES_BUTTON = """
QPushButton {
    background-color: #a6e3a1; /* Catppuccin Green */
    color: #1e1e2e; /* Catppuccin Base */
    font-weight: bold;
    padding: 6px 14px;
    border: none;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #94e2d5; /* Catppuccin Teal */
}
"""

TOOL_DIALOG_ALL_BUTTON = """
QPushButton {
    background-color: #89b4fa; /* Catppuccin Blue */
    color: #1e1e2e; /* Catppuccin Base */
    font-weight: bold;
    padding: 6px 14px;
    border: none;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #74c7ec; /* Catppuccin Sapphire */
}
"""

TOOL_DIALOG_NO_BUTTON = """
QPushButton {
    background-color: #f38ba8; /* Catppuccin Red */
    color: #1e1e2e; /* Catppuccin Base */
    font-weight: bold;
    padding: 6px 14px;
    border: none;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #eba0ac; /* Catppuccin Maroon */
}
"""

# Additional button styles
RED_BUTTON = """
QPushButton {
    background-color: #f38ba8; /* Catppuccin Red */
    color: #1e1e2e; /* Catppuccin Base (for contrast) */
    border: none;
    border-radius: 4px;
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #eba0ac; /* Catppuccin Maroon (lighter red for hover) */
}
QPushButton:pressed {
    background-color: #e67e8a; /* A slightly darker/more intense red for pressed */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
"""

GREEN_BUTTON = """
QPushButton {
    background-color: #a6e3a1; /* Catppuccin Green */
    color: #1e1e2e; /* Catppuccin Base */
    border: none;
    border-radius: 4px;
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #94e2d5; /* Catppuccin Teal - lighter green for hover */
}
QPushButton:pressed {
    background-color: #8bd5ca; /* Slightly darker for pressed state */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
"""

AGENT_MENU_BUTTON = """
QPushButton {
    background-color: #89b4fa; /* Catppuccin Blue */
    color: #1e1e2e; /* Catppuccin Base */
    border: none;
    border-radius: 4px;
    padding: 8px;
    font-weight: bold;
    padding-left: 12px; /* Add some padding for text */
}
QPushButton:hover {
    background-color: #74c7ec; /* Catppuccin Sapphire */
}
QPushButton:pressed {
    background-color: #b4befe; /* Catppuccin Lavender */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
QPushButton::menu-indicator {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 5px;
    width: 16px;
}
"""

# Widget-specific styles
SYSTEM_MESSAGE_LABEL = """
color: #a6adc8; /* Catppuccin Subtext0 */
padding: 2px;
"""

SYSTEM_MESSAGE_TOGGLE = """
QPushButton {
    background-color: transparent;
    color: #94e2d5; /* Catppuccin Teal */
    border: none;
    text-align: left;
    padding: 2px;
}
QPushButton:hover {
    color: #89dceb; /* Catppuccin Sky */
}
"""

# Config window styles
CONFIG_DIALOG = """
QDialog {
    background-color: #1e1e2e; /* Catppuccin Base */
    color: #cdd6f4; /* Catppuccin Text */
}
QTabWidget::pane {
    border: 1px solid #313244; /* Catppuccin Surface0 */
    background-color: #181825; /* Catppuccin Mantle */
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
    padding: 8px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    border-bottom: none;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #181825; /* Catppuccin Mantle (same as pane) */
    border-bottom-color: #181825; /* Catppuccin Mantle */
    color: #b4befe; /* Catppuccin Lavender for selected tab text */
}
QTabBar::tab:hover:!selected {
    background-color: #45475a; /* Catppuccin Surface1 */
}
QPushButton {
    background-color: #89b4fa; /* Catppuccin Blue */
    color: #1e1e2e; /* Catppuccin Base */
    border: none;
    border-radius: 4px;
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #74c7ec; /* Catppuccin Sapphire */
}
QPushButton:pressed {
    background-color: #b4befe; /* Catppuccin Lavender */
}
QPushButton:disabled {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #6c7086; /* Catppuccin Overlay0 */
}
QListWidget {
    background-color: #1e1e2e; /* Catppuccin Base */
    border: 1px solid #313244; /* Catppuccin Surface0 */
    border-radius: 4px;
    padding: 4px;
    color: #cdd6f4; /* Catppuccin Text */
}
QListWidget::item {
    padding: 6px;
    border-radius: 2px;
    color: #cdd6f4; /* Catppuccin Text */
    background-color: #1e1e2e; /* Catppuccin Base */
}
QListWidget::item:selected {
    background-color: #45475a; /* Catppuccin Surface1 */
    color: #b4befe; /* Catppuccin Lavender */
}
QListWidget::item:hover:!selected {
    background-color: #313244; /* Catppuccin Surface0 */
}
QLineEdit, QTextEdit {
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    border-radius: 4px;
    padding: 6px;
    background-color: #313244; /* Catppuccin Surface0 */
    color: #cdd6f4; /* Catppuccin Text */
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #89b4fa; /* Catppuccin Blue */
}
QCheckBox {
    spacing: 8px;
    color: #cdd6f4; /* Catppuccin Text */
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 2px;
    background-color: #45475a; /* Catppuccin Surface1 */
    border: 1px solid #585b70; /* Catppuccin Surface2 */
}
QCheckBox::indicator:checked {
    background-color: #89b4fa; /* Catppuccin Blue */
    border: 1px solid #89b4fa; /* Catppuccin Blue */
}
QCheckBox::indicator:hover {
    border: 1px solid #b4befe; /* Catppuccin Lavender */
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #45475a; /* Catppuccin Surface1 */
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px; /* Ensure space for title */
    background-color: #181825; /* Catppuccin Mantle for groupbox background */
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; /* position at the top left */
    padding: 0 4px 4px 4px; /* padding for title */
    color: #b4befe; /* Catppuccin Lavender for title */
    background-color: #181825; /* Match groupbox background */
    left: 10px; /* Adjust to align with content */
}
QScrollArea {
    background-color: #181825; /* Catppuccin Mantle */
    border: none;
}
/* Style for the QWidget inside QScrollArea if needed */
QScrollArea > QWidget > QWidget { /* Target the editor_widget */
     background-color: #181825; /* Catppuccin Mantle */
}
QLabel {
    color: #cdd6f4; /* Catppuccin Text */
    padding: 2px; /* Add some padding to labels */
}
QSplitter::handle {
    background-color: #313244; /* Catppuccin Surface0 */
}
QSplitter::handle:hover {
    background-color: #45475a; /* Catppuccin Surface1 */
}
QSplitter::handle:pressed {
    background-color: #585b70; /* Catppuccin Surface2 */
}
"""

PANEL = """
background-color: #181825; /* Catppuccin Mantle */
"""

SCROLL_AREA = """
background-color: #181825; /* Catppuccin Mantle */
border: none;
"""

EDITOR_WIDGET = """
background-color: #181825; /* Catppuccin Mantle */
"""

GROUP_BOX = """
background-color: #1e1e2e; /* Catppuccin Base */
"""

SPLITTER_DARK = """
QSplitter::handle {
    background-color: #1e1e2e; /* Darker color (Catppuccin Mantle) */
}
QSplitter::handle:hover {
    background-color: #313244; /* Catppuccin Surface0 */
}
QSplitter::handle:pressed {
    background-color: #45475a; /* Catppuccin Surface1 */
}
"""

METADATA_HEADER_LABEL = """
QLabel {
    color: #a6adc8; /* Catppuccin Subtext0 */
    font-style: italic;
    padding-bottom: 5px;
}
"""

# Message label styles
USER_MESSAGE_LABEL = """
QLabel {
    color: #1e1e2e; /* Catppuccin Base */
}
"""

ASSISTANT_MESSAGE_LABEL = """
QLabel {
    color: #cdd6f4; /* Catppuccin Text */
}
"""

THINKING_MESSAGE_LABEL = """
QLabel {
    color: #bac2de; /* Catppuccin Subtext1 */
}
"""

# Sender label styles
USER_SENDER_LABEL = """
QLabel {
    font-weight: bold;
    color: #1e1e2e; /* Catppuccin Base */
    padding: 2px;
}
"""

ASSISTANT_SENDER_LABEL = """
QLabel {
    font-weight: bold;
    color: #cdd6f4; /* Catppuccin Text */
    padding: 2px;
}
"""

THINKING_SENDER_LABEL = """
QLabel {
    font-weight: bold;
    color: #bac2de; /* Catppuccin Subtext1 */
    padding: 2px;
}
"""
