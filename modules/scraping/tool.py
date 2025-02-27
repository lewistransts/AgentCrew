from .service import ScrapingService


TOOL_DEFINITION = {
    "name": "scrap_url",
    "description": "Scrap the content on given URL and generated markdown output",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "the url that will be scraped",
            },
            "output_file": {
                "type": "string",
                "description": "if defined, the content will be save to this file",
            },
        },
        "required": ["url"],
    },
}


@staticmethod
def get_scraping_tool_handler(scraping_service: ScrapingService):
    """
    Returns a handler function for the scraping tool.

    Args:
        scraping_service: An instance of ScrapingService

    Returns:
        function: A handler function that can be registered with the LLM service
    """

    def scraping_handler(url: str, output_file: str):
        print(f"\n🌐 Scraping content from: {url}")
        content = scraping_service.scrape_url(url)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
        print("✅ Content successfully scraped")
        return content

    return scraping_handler
