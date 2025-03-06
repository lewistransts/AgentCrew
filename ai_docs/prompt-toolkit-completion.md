from prompt_toolkit import PromptSession
from prompt_toolkit.completion import PathCompleter, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import is_searching
import os
import re

class DirectoryListingCompleter(Completer):
    def __init__(self):
        self.path_completer = PathCompleter(expanduser=True)
        self.path_regex = re.compile(r'(.*?)(~?/[^/]*?)$')

    def get_completions(self, document, complete_event):
        # By default, only process if the user explicitly triggers completion
        if not complete_event.completion_requested:
            return

        text = document.text
        
        # Try to find a path pattern in the text
        match = self.path_regex.search(text)
        if match:
            prefix, path_text = match.groups()
            path_pos = len(prefix)
            
            # Create a new document just for the path part
            path_document = Document(
                path_text, 
                cursor_position=len(path_text)
            )
            
            # Get completions for the path
            for completion in self.path_completer.get_completions(path_document, complete_event):
                # Adjust the start position to account for the prefix
                yield Completion(
                    completion.text,
                    start_position=completion.start_position - len(path_text) + path_pos,
                    display=completion.display,
                    display_meta=completion.display_meta
                )

# Create key bindings
kb = KeyBindings()

@kb.add('/')
def _(event):
    """Pressing the '/' key will insert the slash and trigger completion."""
    buffer = event.app.current_buffer
    buffer.insert_text('/')
    # Only trigger completion if it's a path context
    text = buffer.document.text
    if text.endswith('/') or '~/' in text:
        buffer.start_completion()

# Create a session with our custom completer and key bindings
session = PromptSession(
    completer=DirectoryListingCompleter(),
    key_bindings=kb,
    complete_while_typing=False  # Only complete when explicitly triggered
)

def main():
    while True:
        try:
            text = session.prompt('> ')
            print(f'You entered: {text}')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

if __name__ == '__main__':
    main()
