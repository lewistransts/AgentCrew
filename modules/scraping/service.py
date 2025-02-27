import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv


class ScrapingService:
    """Web scraping service for fetching and converting web content to markdown."""

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("FC_API_KEY")
        if not api_key:
            raise ValueError("FC_API_KEY not found in environment variables")
        self.app = FirecrawlApp(api_key=api_key)

    def _is_file_url(self, url: str) -> bool:
        """Check if the URL points to a raw file that should be fetched directly."""
        file_extensions = [".md", ".txt", ".json", ".yaml", ".yml"]
        return any(url.lower().endswith(ext) for ext in file_extensions)

    def scrape_url(self, url: str) -> str:
        """
        Scrape content from a URL and convert it to markdown.

        Args:
            url: The URL to scrape

        Returns:
            The scraped content as markdown text

        Raises:
            Exception: If scraping fails
        """
        try:
            if self._is_file_url(url):
                # For file URLs, request raw format
                scrape_result = self.app.scrape_url(url, params={"formats": ["raw"]})
                return scrape_result.get("raw", "")
            else:
                # For web pages, continue with markdown format
                scrape_result = self.app.scrape_url(
                    url, params={"formats": ["markdown", "html"]}
                )
                return scrape_result.get("markdown", "")
        except Exception as e:
            raise Exception(f"Failed to scrape URL: {str(e)}")


@staticmethod
def get_scraping_tool_handler(scraping_service):
    """
    Returns a handler function for the scraping tool.

    Args:
        scraping_service: An instance of ScrapingService

    Returns:
        function: A handler function that can be registered with the LLM service
    """

    def scraping_handler(url):
        print(f"\n🌐 Scraping content from: {url}")
        content = scraping_service.scrape_url(url)
        print("✅ Content successfully scraped")
        return content

    return scraping_handler
