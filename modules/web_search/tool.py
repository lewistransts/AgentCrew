from typing import Dict, Any
from modules.web_search.service import TavilySearchService


def get_web_search_tool_definition(provider="claude"):
    """Return the tool definition for web search based on provider."""
    if provider == "claude":
        return {
            "name": "web_search",
            "description": "Search the web for current information on a topic or query.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web",
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "description": "The depth of search to perform. 'basic' is faster, 'advanced' is more thorough.",
                        "default": "basic",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (1-10)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
            },
        }
    else:  # provider == "groq"
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for current information on a topic or query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up on the web",
                        },
                        "search_depth": {
                            "type": "string",
                            "enum": ["basic", "advanced"],
                            "description": "The depth of search to perform. 'basic' is faster, 'advanced' is more thorough.",
                            "default": "basic",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-10)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10,
                        },
                    },
                    "required": ["query"],
                },
            },
        }


def get_web_extract_tool_definition(provider="claude"):
    """Return the tool definition for web content extraction based on provider."""
    if provider == "claude":
        return {
            "name": "fetch_webpage",
            "description": "Extract and retrieve the content from external web pages (HTTP/HTTPS URLs only). Use this tool exclusively for accessing online resources, not for reading local project files.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The complete HTTP/HTTPS web address to extract content from (e.g., 'https://example.com/page')",
                    }
                },
                "required": ["url"],
            },
        }
    else:  # provider == "groq"
        return {
            "type": "function",
            "function": {
                "name": "fetch_webpage",
                "description": "Extract and retrieve the content from external web pages (HTTP/HTTPS URLs only). Use this tool exclusively for accessing online resources, not for reading local project files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The complete HTTP/HTTPS web address to extract content from (e.g., 'https://example.com/page')",
                        }
                    },
                    "required": ["url"],
                },
            },
        }


def get_web_search_tool_handler(tavily_service: TavilySearchService):
    """
    Return a handler function for the web search tool.

    Args:
        tavily_service: An instance of TavilySearchService

    Returns:
        Function that handles web search tool calls
    """

    def web_search_handler(**params):
        query = params.get("query")
        search_depth = params.get("search_depth", "basic")
        max_results = params.get("max_results", 5)

        if not query:
            return "Error: No search query provided."

        print(f"🔍 Searching the web for: {query}")
        results = tavily_service.search(
            query=query, search_depth=search_depth, max_results=max_results
        )

        return tavily_service.format_search_results(results)

    return web_search_handler


def get_web_extract_tool_handler(tavily_service: TavilySearchService):
    """
    Return a handler function for the web extract tool.

    Args:
        tavily_service: An instance of TavilySearchService

    Returns:
        Function that handles web extract tool calls
    """

    def web_extract_handler(**params):
        url = params.get("url")

        if not url:
            return "Error: No URL provided."

        print(f"📄 Extracting content from URL: {url}")
        results = tavily_service.extract(url=url)
        return tavily_service.format_extract_results(results)

    return web_extract_handler


def register(service_instance=None, agent=None):
    """
    Register this tool with the central registry or directly with an agent
    
    Args:
        service_instance: The web search service instance
        agent: Agent instance to register with directly (optional)
    """
    from modules.tools.registration import register_tool

    register_tool(
        get_web_search_tool_definition, 
        get_web_search_tool_handler, 
        service_instance,
        agent
    )
    register_tool(
        get_web_extract_tool_definition, 
        get_web_extract_tool_handler, 
        service_instance,
        agent
    )
