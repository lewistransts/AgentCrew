from .catppuccin import CatppuccinTheme
from .atom_light import AtomLightTheme


class StyleProvider:
    """Provides styling for the chat window and components."""

    def __init__(self, theme="atom_light"):
        """Initialize the style provider with a specific theme.

        Args:
            theme: Theme name ("catppuccin" or "atom_light")
        """
        self.theme = theme
        if theme == "atom_light":
            self.theme_class = AtomLightTheme
        else:
            self.theme_class = CatppuccinTheme  # Default to Catppuccin

    def get_main_style(self):
        """Get the main style for the chat window."""
        return self.theme_class.MAIN_STYLE

    def get_config_window_style(self):
        return self.theme_class.CONFIG_DIALOG

    def get_button_style(self, button_type="primary"):
        """Get style for buttons based on type."""
        if button_type == "primary":
            return self.theme_class.PRIMARY_BUTTON
        elif button_type == "secondary":
            return self.theme_class.SECONDARY_BUTTON
        elif button_type == "stop":
            return self.theme_class.STOP_BUTTON
        elif button_type == "disabled":
            return self.theme_class.DISABLED_BUTTON
        elif button_type == "stop_stopping":
            return self.theme_class.STOP_BUTTON_STOPPING
        elif button_type == "red":
            return self.theme_class.RED_BUTTON
        elif button_type == "green":
            return self.theme_class.GREEN_BUTTON
        elif button_type == "agent_menu":
            return self.theme_class.AGENT_MENU_BUTTON
        else:
            return ""

    def get_input_style(self):
        """Get style for text input."""
        return self.theme_class.TEXT_INPUT

    def get_menu_style(self):
        """Get style for menus."""
        return self.theme_class.MENU_BAR

    def get_status_indicator_style(self):
        """Get style for status indicator."""
        return self.theme_class.STATUS_INDICATOR

    def get_version_label_style(self):
        """Get style for version label."""
        return self.theme_class.VERSION_LABEL

    def get_tool_dialog_text_edit_style(self):
        """Get style for tool dialog text edit."""
        return self.theme_class.TOOL_DIALOG_TEXT_EDIT

    def get_tool_dialog_yes_button_style(self):
        """Get style for tool dialog yes button."""
        return self.theme_class.TOOL_DIALOG_YES_BUTTON

    def get_tool_dialog_all_button_style(self):
        """Get style for tool dialog all button."""
        return self.theme_class.TOOL_DIALOG_ALL_BUTTON

    def get_tool_dialog_no_button_style(self):
        """Get style for tool dialog no button."""
        return self.theme_class.TOOL_DIALOG_NO_BUTTON

    def get_system_message_label_style(self):
        """Get style for system message labels."""
        return self.theme_class.SYSTEM_MESSAGE_LABEL

    def get_system_message_toggle_style(self):
        """Get style for system message toggle buttons."""
        return self.theme_class.SYSTEM_MESSAGE_TOGGLE

    def get_sidebar_style(self):
        """Get style for sidebar widgets."""
        return self.theme_class.SIDEBAR

    def get_conversation_list_style(self):
        """Get style for conversation list."""
        return self.theme_class.CONVERSATION_LIST

    def get_search_box_style(self):
        """Get style for search boxes."""
        return self.theme_class.SEARCH_BOX

    def get_token_usage_style(self):
        """Get style for token usage widgets."""
        return self.theme_class.TOKEN_USAGE

    def get_token_usage_widget_style(self):
        """Get style for token usage widget background."""
        return self.theme_class.TOKEN_USAGE_WIDGET

    def get_context_menu_style(self):
        """Get style for context menus."""
        return self.theme_class.CONTEXT_MENU

    def get_agent_menu_style(self):
        """Get style for agent menus."""
        return self.theme_class.AGENT_MENU

    def get_user_bubble_style(self):
        """Get style for user message bubbles."""
        return self.theme_class.USER_BUBBLE

    def get_assistant_bubble_style(self):
        """Get style for assistant message bubbles."""
        return self.theme_class.ASSISTANT_BUBBLE

    def get_thinking_bubble_style(self):
        """Get style for thinking message bubbles."""
        return self.theme_class.THINKING_BUBBLE

    def get_consolidated_bubble_style(self):
        """Get style for consolidated message bubbles."""
        return self.theme_class.CONSOLIDATED_BUBBLE

    def get_splitter_style(self):
        return self.theme_class.SPLITTER_COLOR

    def get_code_color_style(self):
        return self.theme_class.CODE_CSS

    def get_rollback_button_style(self):
        """Get style for rollback buttons."""
        return self.theme_class.ROLLBACK_BUTTON

    def get_consolidated_button_style(self):
        """Get style for consolidated buttons."""
        return self.theme_class.CONSOLIDATED_BUTTON

    def get_user_message_label_style(self):
        """Get style for user message labels."""
        return self.theme_class.USER_MESSAGE_LABEL

    def get_assistant_message_label_style(self):
        """Get style for assistant message labels."""
        return self.theme_class.ASSISTANT_MESSAGE_LABEL

    def get_thinking_message_label_style(self):
        """Get style for thinking message labels."""
        return self.theme_class.THINKING_MESSAGE_LABEL

    def get_user_sender_label_style(self):
        """Get style for user sender labels."""
        return self.theme_class.USER_SENDER_LABEL

    def get_assistant_sender_label_style(self):
        """Get style for assistant sender labels."""
        return self.theme_class.ASSISTANT_SENDER_LABEL

    def get_thinking_sender_label_style(self):
        """Get style for thinking sender labels."""
        return self.theme_class.THINKING_SENDER_LABEL

    def get_metadata_header_label_style(self):
        """Get style for metadata header labels."""
        return self.theme_class.METADATA_HEADER_LABEL

    def get_user_file_name_label_style(self):
        """Get style for user file name labels."""
        return self.theme_class.USER_FILE_NAME_LABEL

    def get_assistant_file_name_label_style(self):
        """Get style for assistant file name labels."""
        return self.theme_class.ASSISTANT_FILE_NAME_LABEL

    def get_user_file_info_label_style(self):
        """Get style for user file info labels."""
        return self.theme_class.USER_FILE_INFO_LABEL

    def get_assistant_file_info_label_style(self):
        """Get style for assistant file info labels."""
        return self.theme_class.ASSISTANT_FILE_INFO_LABEL

    def get_api_keys_group_style(self):
        """Get style for API keys group boxes."""
        return self.theme_class.API_KEYS_GROUP

    def get_editor_container_widget_style(self):
        """Get style for editor container widgets."""
        return self.theme_class.EDITOR_CONTAINER_WIDGET
