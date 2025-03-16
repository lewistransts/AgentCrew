from .service import ScrapingService


def get_scraping_tool_definition(provider="claude"):
    """Return the tool definition for web scraping based on provider."""
    if provider == "claude":
        return {
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
                        "description": "if defined, the content will be save to this file, only save to file if explicit demand to",
                        "default": "None",
                    },
                },
                "required": ["url"],
            },
        }
    else:  # provider == "groq"
        return {
            "type": "function",
            "function": {
                "name": "scrap_url",
                "description": "Scrap the content on given URL and generated markdown output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "the url that will be scraped",
                        },
                        "output_file": {
                            "type": "string",
                            "description": "if defined, the content will be save to this file, only save to file if explicit demand to",
                            "default": "None",
                        },
                    },
                    "required": ["url"],
                },
            },
        }


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
        if output_file and output_file != "None":
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
        print("✅ Content successfully scraped")
        return content

    return scraping_handler


def register(service_instance=None, agent=None):
    """
    Register this tool with the central registry or directly with an agent
    
    Args:
        service_instance: The scraping service instance
        agent: Agent instance to register with directly (optional)
    """
    from modules.tools.registration import register_tool
    register_tool(
        get_scraping_tool_definition,
        get_scraping_tool_handler,
        service_instance,
        agent
    )
