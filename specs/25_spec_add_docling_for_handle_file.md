# Implement Docling Integration for Enhanced File Handling

> Ingest this spec and generate code to fulfill the following requirements.

## 1. Objectives

* Integrate the Docling library (version 2.26.0 or later) to enhance file handling capabilities for the chat application.
* Implement support for specific document formats (PDF, DOC, DOCX) using Docling.
* Directly read the content of text-based files (e.g., TXT, HTML).
* Ensure secure file handling with validation based on MIME type and file size.
* Provide fallback mechanisms for unsupported formats or conversion failures.
* Implement configuration options for enabling/disabling Docling and AI-enhanced parsing.
* Enhance error handling and user feedback for file processing operations.

## 2. Contexts

* `swissknife/modules/chat/interactive.py`: Contains the `InteractiveChat` class and methods for processing user input.
* `swissknife/modules/chat/file_handler.py`: (To be created) A new module to encapsulate Docling functionality.

## 3. Low-Level Tasks

1. **Add Dependencies**:

    * Update `pyproject.toml` to include Docling as a project dependency:

    ```toml
    dependencies = [
    ...
    "docling=^2.26.0",
    # Use the latest version available
    ```

2. **Create File Handling Module**:

    * Create a new module `swissknife/modules/chat/file_handler.py` with the following content:

    ```python
    # swissknife/modules/chat/file_handler.py

    import os
    import mimetypes
    from typing import Optional, Dict, Any
    import logging

    from docling.document_converter import DocumentConverter
    from docling.exceptions import ConversionError

    logger = logging.getLogger(__name__)

    # Docling Configuration
    DOCLING_ENABLED = True  # Toggle to enable/disable Docling integration
    DOCLING_AI_MODE = False  # Toggle for AI-enhanced parsing (more resource-intensive)

    # File Handling Configuration
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
    ALLOWED_MIME_TYPES = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/msword",
        "text/html",
        "text/plain",
        "image/jpeg",
        "image/png"
    ]

    DOCLING_FORMATS = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    class FileHandler:
        """Handler for handling file operations with Docling integration."""

        def __init__(self):
            """Initialize the file handling service."""
            self.converter = None
            if DOCLING_ENABLED:
                try:
                    self.converter = DocumentConverter(enable_ai=DOCLING_AI_MODE)
                    logger.info("Docling converter initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Docling converter: {str(e)}")

        def validate_file(self, file_path: str) -> bool:
            """
            Validate if the file is allowed based on MIME type and size.

            Args:
                file_path: Path to the file

            Returns:
                bool: True if file is valid, False otherwise
            """
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return False

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"File too large: {file_path} ({file_size} bytes)")
                return False

            # Check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type not in ALLOWED_MIME_TYPES:
                logger.warning(f"Unsupported MIME type: {mime_type} for {file_path}")
                return False

            return True

        def process_file(self, file_path: str) -> Optional[Dict[str, Any]]:
            """
            Process a file using Docling or fallback methods.

            Args:
                file_path: Path to the file

            Returns:
                Optional[Dict[str, Any]]: Processed file content or None if processing failed
            """
            # Validate file first
            if not self.validate_file(file_path):
                return None

            # Get file extension and MIME type
            _, file_extension = os.path.splitext(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)

            # Use Docling for specific formats
            if DOCLING_ENABLED and self.converter and mime_type in DOCLING_FORMATS:
                try:
                    logger.info(f"Processing file with Docling: {file_path}")
                    result = self.converter.convert(file_path)
                    markdown_content = result.document.export_to_markdown()

                    return {
                        "type": "text",
                        "text": f"Content of {file_path} (converted to Markdown):\n\n{markdown_content}"
                    }
                except ConversionError as e:
                    logger.warning(f"Docling conversion failed for {file_path}: {str(e)}")
                    # Fall through to fallback methods
                except Exception as e:
                    logger.error(f"Unexpected error in Docling conversion: {str(e)}")
                    # Fall through to fallback methods

            # Directly read text-based files
            if mime_type and mime_type.startswith("text/"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    return {
                        "type": "text",
                        "text": f"Content of {file_path}:\n\n{content}"
                    }
                except Exception as e:
                    logger.error(f"Error reading text file {file_path}: {str(e)}")
                    return None

            # Fallback to other file types
            return self._fallback_processing(file_path, mime_type)

        def _fallback_processing(self, file_path: str, mime_type: str) -> Optional[Dict[str, Any]]:
            """
            Fallback processing for when Docling fails or is disabled.

            Args:
                file_path: Path to the file
                mime_type: MIME type of the file

            Returns:
                Optional[Dict[str, Any]]: Processed file content or None if processing failed
            """
            logger.info(f"Using fallback processing for {file_path}")

            # Handle PDFs and other binary files
            elif mime_type in ["application/pdf", "application/msword",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                return {
                    "type": "text",
                    "text": f"File {file_path} could not be processed with Docling. "
                            f"This is a {mime_type} file that requires special processing."
                }

            # Handle images
            elif mime_type and mime_type.startswith("image/"):
                try:
                    import base64
                    with open(file_path, "rb") as f:
                        content = f.read()
                    encoded = base64.b64encode(content).decode("utf-8")
                    return {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": encoded
                        }
                    }
                except Exception as e:
                    logger.error(f"Error processing image file {file_path}: {str(e)}")
                    return None

            # Default case
            return {
                "type": "text",
                "text": f"File {file_path} could not be processed. Unsupported format: {mime_type}"
            }
    ```

3. **Integrate with Interactive Chat**:

    * Modify the `InteractiveChat` class in `swissknife/modules/chat/interactive.py` to use the new file handling module:

    ```python
    # swissknife/modules/chat/interactive.py

    from swissknife.modules.chat.file_handler import FileHandler

    class InteractiveChat:
        # ... existing code ...

        def __init__(self, memory_service=None):
            # ... existing initialization ...
            self.file_handler = FileHandler()

        def _process_user_input(self, user_input, messages, message_content, files):
            # ... existing code ...

            # Handle file command
            if user_input.startswith("/file "):
                file_path = user_input[6:].strip()
                file_path = os.path.expanduser(file_path)

                # Process file with the file handling service
                file_content = self.file_handler.process_file(file_path)

                if file_content:
                    messages.append({"role": "user", "content": [file_content]})
                    return messages, False, True
                else:
                    print(f"{RED}Error: Failed to process file {file_path}{RESET}")
                    return messages, False, True

            # ... rest of the existing code ...

        def start_chat(self, initial_content=None, files=None):
            # ... existing code ...

            # Process files if provided
            if files:
                message_content = []
                for file_path in files:
                    # Use the file handling service instead of direct LLM processing
                    file_content = self.file_handler.process_file(file_path)
                    if file_content:
                        message_content.append(file_content)

            # ... rest of the existing code ...
    ```

4. **Enhance Error Handling and User Feedback**:

    * Add the following helper function to `swissknife/modules/chat/interactive.py`:

    ```python
    # Add to interactive.py

    def _handle_file_error(self, file_path, error_message):
        """Handle file processing errors with appropriate user feedback."""
        error_type = "Unknown error"

        if "size limit" in error_message.lower():
            error_type = "File size limit exceeded"
        elif "mime type" in error_message.lower():
            error_type = "Unsupported file type"
        elif "not found" in error_message.lower():
            error_type = "File not found"
        elif "permission" in error_message.lower():
            error_type = "Permission denied"

        print(f"{RED}Error processing file {file_path}: {error_type}{RESET}")
        print(f"{YELLOW}Details: {error_message}{RESET}")

        # Provide helpful suggestions
        if error_type == "Unsupported file type":
            print(f"{YELLOW}Tip: Try converting the file to a supported format like PDF or text.{RESET}")
        elif error_type == "File size limit exceeded":
            print(f"{YELLOW}Tip: Try splitting the file into smaller parts or extracting relevant sections.{RESET}")
    ```
