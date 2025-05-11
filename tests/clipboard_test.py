import unittest
from AgentCrew.modules.clipboard.service import ClipboardService
from AgentCrew.modules.clipboard.tool import (
    get_clipboard_read_tool_handler,
    get_clipboard_write_tool_handler,
)


class ClipboardServiceTest(unittest.TestCase):
    def setUp(self):
        self.clipboard_service = ClipboardService()
        self.read_handler = get_clipboard_read_tool_handler(self.clipboard_service)
        self.write_handler = get_clipboard_write_tool_handler(self.clipboard_service)

    def test_write_and_read_text(self):
        """Test writing text to clipboard and reading it back."""
        test_text = "This is a test clipboard content"

        # Write to clipboard
        write_result = self.clipboard_service.write(test_text)
        self.assertTrue(write_result["success"])

        # Read from clipboard
        read_result = self.clipboard_service.read()
        self.assertTrue(read_result["success"])
        self.assertEqual(read_result["type"], "text")
        self.assertEqual(read_result["content"], test_text)

    def test_clipboard_write_handler(self):
        """Test the clipboard write tool handler."""
        test_text = "Testing clipboard write handler"

        # Use the handler to write to clipboard
        params = {"content": test_text}
        result = self.write_handler(params)
        self.assertTrue(result["success"])

        # Verify content was written correctly
        read_result = self.clipboard_service.read()
        self.assertTrue(read_result["success"])
        self.assertEqual(read_result["content"], test_text)

    def test_clipboard_read_handler(self):
        """Test the clipboard read tool handler."""
        test_text = "Testing clipboard read handler"

        # Write directly to clipboard
        self.clipboard_service.write(test_text)

        # Use the handler to read from clipboard
        result = self.read_handler({})
        self.assertTrue(result["success"])
        self.assertEqual(result["type"], "text")
        self.assertEqual(result["content"], test_text)

    def test_missing_content_parameter(self):
        """Test write handler with missing content parameter."""
        result = self.write_handler({})
        self.assertFalse(result["success"])
        self.assertIn("Missing required parameter", result["error"])


if __name__ == "__main__":
    unittest.main()
