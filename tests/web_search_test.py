import unittest
import os
from dotenv import load_dotenv
from swissknife.modules.web_search.service import TavilySearchService
from swissknife.modules.web_search.tool import (
    get_web_search_tool_handler,
    get_web_extract_tool_handler,
)


class WebSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test environment once before all tests."""
        # Ensure API key is loaded
        load_dotenv()
        if not os.getenv("TAVILY_API_KEY"):
            raise unittest.SkipTest("TAVILY_API_KEY not found in environment variables")

        cls.tavily_service = TavilySearchService()
        cls.search_handler = get_web_search_tool_handler(cls.tavily_service)
        cls.extract_handler = get_web_extract_tool_handler(cls.tavily_service)

    def test_web_search_basic(self):
        """Test basic web search functionality."""
        query = "Python programming language"
        result = self.tavily_service.search(query=query, max_results=2)

        self.assertIn("results", result)
        self.assertIsInstance(result["results"], list)
        self.assertGreaterEqual(len(result["results"]), 1)

        # Check result structure
        first_result = result["results"][0]
        self.assertIn("title", first_result)
        self.assertIn("url", first_result)
        self.assertIn("content", first_result)

    def test_web_search_handler(self):
        """Test the web search tool handler."""
        params = {
            "query": "Artificial intelligence news",
            "search_depth": "basic",
            "max_results": 3,
        }

        result = self.search_handler(**params)

        # The handler returns formatted text
        self.assertIsInstance(result, str)
        self.assertIn("Search Results", result)
        self.assertIn("URL:", result)

    def test_web_extract_handler(self):
        """Test the web extract tool handler."""
        # Use a stable URL that's unlikely to change or disappear
        params = {"url": "https://www.python.org/"}

        result = self.extract_handler(**params)

        # The handler returns formatted text
        self.assertIsInstance(result, str)
        self.assertIn("Extracted content", result)
        self.assertNotIn("Extract error", result)

    def test_search_with_advanced_depth(self):
        """Test search with advanced depth parameter."""
        query = "Latest developments in quantum computing"
        result = self.tavily_service.search(
            query=query, search_depth="advanced", max_results=2
        )

        self.assertIn("results", result)
        self.assertIsInstance(result["results"], list)

    def test_invalid_search_params(self):
        """Test search handler with empty query."""
        result = self.search_handler(query="")
        self.assertIn("Error", result)

    def test_invalid_extract_params(self):
        """Test extract handler with empty URL."""
        result = self.extract_handler(url="")
        self.assertIn("Error", result)


if __name__ == "__main__":
    unittest.main()
