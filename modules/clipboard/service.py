import pyperclip
import base64
import io
from PIL import ImageGrab, Image
from typing import Dict, Any


class ClipboardService:
    """Service for interacting with the system clipboard."""

    def write_text(self, content: str) -> Dict[str, Any]:
        """
        Write text content to the clipboard.

        Args:
            content: Text content to write to clipboard

        Returns:
            Dict containing success status and any error information
        """
        try:
            pyperclip.copy(content)
            return {
                "success": True,
                "message": "Content successfully copied to clipboard",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write to clipboard: {str(e)}",
            }

    def read(self) -> Dict[str, Any]:
        """
        Read content from the clipboard and automatically determine the content type.

        Returns:
            Dict containing the clipboard content or error information
        """
        try:
            # First check if there's an image in the clipboard
            image = ImageGrab.grabclipboard()

            if image is not None and isinstance(image, Image.Image):
                # Handle image content
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

                return {
                    "success": True,
                    "content": img_str,
                    "type": "image",
                    "format": "base64",
                }
            else:
                # Try to get text content
                content = pyperclip.paste()
                if not content:
                    return {
                        "success": False,
                        "error": "Clipboard is empty or contains unsupported content",
                    }
                return {
                    "success": True,
                    "content": content,
                    "type": "text",
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read from clipboard: {str(e)}",
            }

    def write(self, content: str) -> Dict[str, Any]:
        """
        Write content to the clipboard.

        Args:
            content: Content to write to clipboard

        Returns:
            Dict containing success status and any error information
        """
        return self.write_text(content)
