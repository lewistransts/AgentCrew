Based on our past conversations, I can see that we've worked extensively with
tree-sitter to extract code structure information. You're now specifically
asking about extracting the content of a function or class using tree-sitter,
which is a slightly different but related need.

Yes, you can definitely extract the content of a function or class using
tree-sitter! Let me show you how to modify the previous code we worked on to
extract not just the function/class names, but their entire content as well.

Here's how you can implement this functionality:

```python
def extract_function_class_content(file_path, entity_type='all'):
    """
    Extract the full content of functions and/or classes from a source file using tree-sitter.

    Args:
        file_path: Path to the source file
        entity_type: Type of entity to extract ('function', 'class', or 'all')

    Returns:
        Dictionary with entity names as keys and their source code as values
    """
    # Determine the language based on file extension
    ext = os.path.splitext(file_path)[1].lower()

    # Create parser with appropriate language
    parser = Parser()
    language = None
    query_string = ""

    # Set up language and query based on file extension
    if ext == '.py':
        import tree_sitter_python
        language = tree_sitter_python.language()
        query_string = """
            (function_definition) @function
            (class_definition) @class
        """
    elif ext in ['.js', '.jsx']:
        import tree_sitter_javascript
        language = tree_sitter_javascript.language()
        query_string = """
            (function_declaration) @function
            (class_declaration) @class
            (method_definition) @method
        """
    # Add more language support as needed
    else:
        return {"error": f"Unsupported file type: {ext}"}

    # Read file content
    with open(file_path, 'rb') as f:
        source_code = f.read()

    # Parse the source code
    parser.set_language(language)
    tree = parser.parse(source_code)

    # Create query
    query = language.query(query_string)
    captures = query.captures(tree.root_node)

    # Extract content
    results = {}

    for node, node_type in captures:
        if (entity_type == 'all' or
            (entity_type == 'function' and node_type in ['function', 'method']) or
            (entity_type == 'class' and node_type == 'class')):

            # Get the full node text
            start_byte = node.start_byte
            end_byte = node.end_byte
            content = source_code[start_byte:end_byte].decode('utf-8')

            # Try to get a name for this entity
            name_node = None

            # Find the name node based on node type
            if node_type == 'function' or node_type == 'method':
                # Look for identifier node under function_definition
                for child in node.children:
                    if child.type == 'identifier':
                        name_node = child
                        break
            elif node_type == 'class':
                # Look for identifier node under class_definition
                for child in node.children:
                    if child.type == 'identifier':
                        name_node = child
                        break

            # Create a key for this entity
            if name_node:
                name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                key = f"{node_type}:{name}"
            else:
                # Use position if name not found
                key = f"{node_type} at line {node.start_point[0]+1}"

            results[key] = content

    return results
```

This function will:

1. Determine the language based on file extension
2. Create a tree-sitter parser with the appropriate language
3. Parse the source code file
4. Query the parse tree for function and class definitions
5. Extract the full text content for each function/class
6. Return a dictionary mapping entity names to their full content

You can use it like this:

```python
# Extract all functions and classes
content = extract_function_class_content("path/to/file.py")

# Extract only functions
functions = extract_function_class_content("path/to/file.py", entity_type="function")

# Extract only classes
classes = extract_function_class_content("path/to/file.py", entity_type="class")

# Print the content of each entity
for name, code in content.items():
    print(f"--- {name} ---")
    print(code)
    print()
```

Would you like me to explain how this works in more detail, or would you like to
see an example of using the `analyze_code` tool that's available to us?
