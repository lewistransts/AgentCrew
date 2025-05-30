from prompt_toolkit.completion import Completer, PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion
from AgentCrew.modules.llm.model_registry import ModelRegistry
import os
import re


class JumpCompleter(Completer):
    """Completer that shows available conversation turns when typing /jump command."""

    def __init__(self, conversation_turns=None):
        self.conversation_turns = conversation_turns or []

    def get_completions(self, document, complete_event):
        text = document.text

        # Only provide completions for the /jump command
        if text.startswith("/jump "):
            word_before_cursor = document.get_word_before_cursor()

            # Get all available turn numbers
            for i, turn in enumerate(self.conversation_turns, 1):
                turn_str = str(i)
                if turn_str.startswith(word_before_cursor):
                    # Use the stored preview
                    preview = turn.get_preview(40)
                    display = f"{turn_str}: {preview}"
                    yield Completion(
                        turn_str,
                        start_position=-len(word_before_cursor),
                        display=display,
                    )


class ModelCompleter(Completer):
    """Completer that shows available models when typing /model command."""

    def __init__(self):
        self.registry = ModelRegistry.get_instance()

    def get_completions(self, document, complete_event):
        text = document.text

        # Only provide completions for the /model command
        if text.startswith("/model "):
            word_before_cursor = document.get_word_before_cursor()

            # Get all available models from the registry
            all_models = []
            for provider in self.registry.get_providers():
                for model in self.registry.get_models_by_provider(provider):
                    all_models.append((model.id, model.name, provider))

            # Filter models based on what the user has typed so far
            for model_id, model_name, provider in all_models:
                if model_id.startswith(word_before_cursor):
                    display = f"{model_id} - {model_name} ({provider})"
                    yield Completion(
                        f"{provider}/{model_id}",
                        start_position=-len(word_before_cursor),
                        display=display,
                    )


class ChatCompleter(Completer):
    """Combined completer for chat commands."""

    def __init__(self, conversation_turns=None):
        self.file_completer = DirectoryListingCompleter()
        self.model_completer = ModelCompleter()
        self.jump_completer = JumpCompleter(conversation_turns)

    def get_completions(self, document, complete_event):
        text = document.text

        if text.startswith("/model "):
            # Use model completer for /model command
            yield from self.model_completer.get_completions(document, complete_event)
        elif text.startswith("/jump "):
            # Use jump completer for /jump command
            yield from self.jump_completer.get_completions(document, complete_event)
        else:
            yield from self.file_completer.get_completions(document, complete_event)


class DirectoryListingCompleter(Completer):
    def __init__(self):
        # Use PathCompleter for the heavy lifting
        self.path_completer = PathCompleter(expanduser=True)

    def get_completions(self, document, complete_event):
        text = document.text
        if text == "/":
            return
        # Look for patterns that might indicate a path
        # This regex searches for a potential directory path
        path_match = re.search(r"((~|\.{1,2})?/[^\s]*|~)$", text)

        if path_match:
            path = path_match.group(0)

            # Create a new document with just the path part
            # This is needed because we want completions only for the path part
            path_document = Document(path, cursor_position=len(path))

            # Get completions from PathCompleter
            for completion in self.path_completer.get_completions(
                path_document, complete_event
            ):
                # Yield the completions
                yield completion

    def get_path_completions(self, path):
        """Helper method to get completions for a specific path"""
        # Expand user directory if path starts with ~
        if path.startswith("~"):
            path = os.path.expanduser(path)

        # Get the directory part
        directory = os.path.dirname(path) if "/" in path else path

        # If directory is empty, use current directory
        if not directory:
            directory = "."

        # If directory ends with '/', it's already a complete directory path
        if path.endswith("/"):
            directory = path

        # Get files and directories in the given directory
        try:
            entries = os.listdir(directory)
            return entries
        except (FileNotFoundError, NotADirectoryError):
            return []
