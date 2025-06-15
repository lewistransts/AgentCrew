from AgentCrew.modules.gui.themes import catppuccin


class StyleProvider:
    """Provides styling for the chat window and components."""

    def get_main_style(self):
        """Get the main style for the chat window."""
        return catppuccin.MAIN_STYLE

    def get_config_window_style(self):
        return catppuccin.CONFIG_DIALOG

    def get_button_style(self, button_type="primary"):
        """Get style for buttons based on type."""
        if button_type == "primary":
            return catppuccin.PRIMARY_BUTTON
        elif button_type == "secondary":
            return catppuccin.SECONDARY_BUTTON
        elif button_type == "stop":
            return catppuccin.STOP_BUTTON
        elif button_type == "disabled":
            return catppuccin.DISABLED_BUTTON
        elif button_type == "stop_stopping":
            return catppuccin.STOP_BUTTON_STOPPING
        elif button_type == "red":
            return catppuccin.RED_BUTTON
        elif button_type == "green":
            return catppuccin.GREEN_BUTTON
        elif button_type == "agent_menu":
            return catppuccin.AGENT_MENU_BUTTON
        else:
            return ""

    def get_input_style(self):
        """Get style for text input."""
        return catppuccin.TEXT_INPUT

    def get_menu_style(self):
        """Get style for menus."""
        return catppuccin.MENU_BAR

    def get_status_indicator_style(self):
        """Get style for status indicator."""
        return catppuccin.STATUS_INDICATOR

    def get_version_label_style(self):
        """Get style for version label."""
        return catppuccin.VERSION_LABEL

    def get_tool_dialog_text_edit_style(self):
        """Get style for tool dialog text edit."""
        return catppuccin.TOOL_DIALOG_TEXT_EDIT

    def get_tool_dialog_yes_button_style(self):
        """Get style for tool dialog yes button."""
        return catppuccin.TOOL_DIALOG_YES_BUTTON

    def get_tool_dialog_all_button_style(self):
        """Get style for tool dialog all button."""
        return catppuccin.TOOL_DIALOG_ALL_BUTTON

    def get_tool_dialog_no_button_style(self):
        """Get style for tool dialog no button."""
        return catppuccin.TOOL_DIALOG_NO_BUTTON

    def get_system_message_label_style(self):
        """Get style for system message labels."""
        return catppuccin.SYSTEM_MESSAGE_LABEL

    def get_system_message_toggle_style(self):
        """Get style for system message toggle buttons."""
        return catppuccin.SYSTEM_MESSAGE_TOGGLE

    def get_sidebar_style(self):
        """Get style for sidebar widgets."""
        return catppuccin.SIDEBAR

    def get_conversation_list_style(self):
        """Get style for conversation list."""
        return catppuccin.CONVERSATION_LIST

    def get_search_box_style(self):
        """Get style for search boxes."""
        return catppuccin.SEARCH_BOX

    def get_token_usage_style(self):
        """Get style for token usage widgets."""
        return catppuccin.TOKEN_USAGE

    def get_token_usage_widget_style(self):
        """Get style for token usage widget background."""
        return catppuccin.TOKEN_USAGE_WIDGET

    def get_context_menu_style(self):
        """Get style for context menus."""
        return catppuccin.CONTEXT_MENU

    def get_agent_menu_style(self):
        """Get style for agent menus."""
        return catppuccin.AGENT_MENU

    def get_user_bubble_style(self):
        """Get style for user message bubbles."""
        return catppuccin.USER_BUBBLE

    def get_assistant_bubble_style(self):
        """Get style for assistant message bubbles."""
        return catppuccin.ASSISTANT_BUBBLE

    def get_thinking_bubble_style(self):
        """Get style for thinking message bubbles."""
        return catppuccin.THINKING_BUBBLE

    def get_consolidated_bubble_style(self):
        """Get style for consolidated message bubbles."""
        return catppuccin.CONSOLIDATED_BUBBLE

    def get_rollback_button_style(self):
        """Get style for rollback buttons."""
        return catppuccin.ROLLBACK_BUTTON

    def get_consolidated_button_style(self):
        """Get style for consolidated buttons."""
        return catppuccin.CONSOLIDATED_BUTTON

    def get_user_message_label_style(self):
        """Get style for user message labels."""
        return catppuccin.USER_MESSAGE_LABEL

    def get_assistant_message_label_style(self):
        """Get style for assistant message labels."""
        return catppuccin.ASSISTANT_MESSAGE_LABEL

    def get_thinking_message_label_style(self):
        """Get style for thinking message labels."""
        return catppuccin.THINKING_MESSAGE_LABEL

    def get_user_sender_label_style(self):
        """Get style for user sender labels."""
        return catppuccin.USER_SENDER_LABEL

    def get_assistant_sender_label_style(self):
        """Get style for assistant sender labels."""
        return catppuccin.ASSISTANT_SENDER_LABEL

    def get_thinking_sender_label_style(self):
        """Get style for thinking sender labels."""
        return catppuccin.THINKING_SENDER_LABEL

    def get_metadata_header_label_style(self):
        """Get style for metadata header labels."""
        return catppuccin.METADATA_HEADER_LABEL
