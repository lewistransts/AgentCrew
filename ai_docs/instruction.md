## Directory Listing Completion in prompt-toolkit

The solution involves creating a custom completer that shows directory listings when a user types a path with a "/".

### Step 1: Install prompt-toolkit

```bash
pip install prompt-toolkit
```

### Step 2: Create a custom completer

Here's a complete example that shows how to implement a directory listing completions when a user types a path:

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.document import Document
import os
import re

class DirectoryListingCompleter(Completer):
    def __init__(self):
        # Use PathCompleter for the heavy lifting
        self.path_completer = PathCompleter(expanduser=True)
        
    def get_completions(self, document, complete_event):
        text = document.text
        
        # Look for patterns that might indicate a path
        # This regex searches for a potential directory path
        path_match = re.search(r'(~?/[^\s]*|~)$', text)
        
        if path_match:
            path = path_match.group(0)
            
            # Create a new document with just the path part
            # This is needed because we want completions only for the path part
            path_document = Document(path, cursor_position=len(path))
            
            # Get completions from PathCompleter
            for completion in self.path_completer.get_completions(path_document, complete_event):
                # Yield the completions
                yield completion
                
    def get_path_completions(self, path):
        """Helper method to get completions for a specific path"""
        # Expand user directory if path starts with ~
        if path.startswith('~'):
            path = os.path.expanduser(path)
            
        # Get the directory part
        directory = os.path.dirname(path) if '/' in path else path
        
        # If directory is empty, use current directory
        if not directory:
            directory = '.'
            
        # If directory ends with '/', it's already a complete directory path
        if path.endswith('/'):
            directory = path
            
        # Get files and directories in the given directory
        try:
            entries = os.listdir(directory)
            return entries
        except (FileNotFoundError, NotADirectoryError):
            return []

def main():
    # Create a session with our custom completer
    session = PromptSession(
        completer=DirectoryListingCompleter(),
    )
    
    # Start the REPL
    while True:
        try:
            user_input = session.prompt("Enter command (type 'exit' to quit): ")
            
            if user_input.strip() == 'exit':
                break
                
            # Process user input
            if user_input.startswith("show me file in "):
                path = user_input[len("show me file in "):]
                if path.startswith('~'):
                    path = os.path.expanduser(path)
                    
                try:
                    files = os.listdir(path)
                    print(f"Files in {path}:")
                    for file in files:
                        print(f"  - {file}")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print(f"You entered: {user_input}")
                
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
            
    print("Goodbye!")

if __name__ == "__main__":
    main()
```

### Example Usage

1. When you run this program, you can type a command like:
   ```
   show me file in ~/
   ```

2. As you type the `~/` part, the completer will activate and show completions for the home directory.

3. You can navigate through directories by typing `/` after selecting a directory:
   ```
   show me file in ~/Documents/
   ```

4. The completions will update to show the contents of the `~/Documents/` directory.

### How it Works

1. **DirectoryListingCompleter**:
   - This custom completer checks if the text ends with a path pattern
   - It uses a regular expression to find potential directory paths in the input
   - When found, it uses `PathCompleter` to generate completions for that path

2. **Path Detection**:
   - The regex `r'(~?/[^\s]*|~)$'` looks for:
     - A tilde followed by a slash and any non-space characters, or
     - Just a tilde at the end of the text

3. **Completion Generation**:
   - When a path is detected, a new document containing just the path is created
   - This is passed to `PathCompleter` which handles the heavy lifting of finding files/directories
   - The completions from `PathCompleter` are yielded to prompt-toolkit

4. **User Experience**:
   - When the user types a path ending with "/", the completer shows files and directories 
   - Directories will be shown with a trailing "/", making it easy to navigate deeper

### Customizations

You can customize the `PathCompleter` with these options:

```python
PathCompleter(
    only_directories=False,  # Set to True to show only directories
    expanduser=True,         # Expand ~ to the user's home directory
    file_filter=None,        # Optional function to filter files (return True to include)
)
```

If you want the command to work specifically with slashes, you can modify the regex pattern to be more specific to your use case.
