from prompt_toolkit.completion import Completer, PathCompleter
from prompt_toolkit.document import Document
import os
import re


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
        path_match = re.search(r"([~\.]?/[^\s]*|~)$", text)

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
