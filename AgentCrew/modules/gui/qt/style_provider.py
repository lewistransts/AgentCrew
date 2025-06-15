class StyleProvider:
    """Provides styling for the chat window and components."""

    def get_main_style(self):
        """Get the main style for the chat window."""
        return """
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

    def get_button_style(self, button_type="primary"):
        """Get style for buttons based on type."""
        if button_type == "primary":
            return """
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
        elif button_type == "secondary":
            return """
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
        elif button_type == "stop":
            return """
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
        else:
            return ""

    def get_input_style(self):
        """Get style for text input."""
        return """
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

    def get_menu_style(self):
        """Get style for menus."""
        return """
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

    def get_status_indicator_style(self):
        """Get style for status indicator."""
        return """
            QLabel {
                background-color: #313244; /* Catppuccin Surface0 */
                color: #cdd6f4; /* Catppuccin Text */
                padding: 8px; 
                font-weight: bold;
            }
        """

    def get_version_label_style(self):
        """Get style for version label."""
        return """
            QLabel {
                color: #a6adc8; /* Catppuccin Subtext0 */
                padding: 2px 8px;
                font-size: 11px;
            }
        """
