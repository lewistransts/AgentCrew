from typing import Dict, Any, Callable
from .service import YtDlpService


def get_youtube_chapters_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Get the tool definition for extracting YouTube chapters based on provider.

    Args:
        provider: The LLM provider ("claude" or "groq")

    Returns:
        Dict containing the tool definition
    """
    if provider == "claude":
        return {
            "name": "youtube_chapters",
            "description": "Extract chapters from a YouTube video",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "YouTube video URL",
                    },
                },
                "required": ["url"],
            },
        }
    else:  # provider == "groq"
        return {
            "type": "function",
            "function": {
                "name": "youtube_chapters",
                "description": "Extract chapters from a YouTube video",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "YouTube video URL",
                        },
                    },
                    "required": ["url"],
                },
            },
        }


def get_youtube_chapters_tool_handler(yt_dlp_service: YtDlpService) -> Callable:
    """
    Get the handler function for the YouTube chapters extraction tool.

    Args:
        yt_dlp_service: The YtDlpService instance

    Returns:
        Function that handles YouTube chapters extraction requests
    """

    def handle_youtube_chapters(**params) -> str:
        url = params.get("url")
        if not url:
            raise Exception("URL is required")
        
        result = yt_dlp_service.extract_chapters(url)
        
        if result["success"]:
            return result["content"]
        else:
            error_message = result.get("error", "Unknown error")
            raise Exception(f"Failed to extract chapters: {error_message}")

    return handle_youtube_chapters


def get_youtube_subtitles_tool_definition(provider="claude") -> Dict[str, Any]:
    """
    Get the tool definition for extracting YouTube subtitles based on provider.

    Args:
        provider: The LLM provider ("claude" or "groq")

    Returns:
        Dict containing the tool definition
    """
    if provider == "claude":
        return {
            "name": "youtube_subtitles",
            "description": "Extract subtitles from a YouTube video for specific chapters",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "YouTube video URL",
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code for subtitles (e.g., 'en' for English, 'es' for Spanish)",
                        "default": "en"
                    },
                    "chapters": {
                        "type": "array",
                        "description": "List of chapters to extract subtitles for, with start_time in seconds and title",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start_time": {"type": "number"},
                                "title": {"type": "string"}
                            }
                        }
                    },
                },
                "required": ["url", "chapters"],
            },
        }
    else:  # provider == "groq"
        return {
            "type": "function",
            "function": {
                "name": "youtube_subtitles",
                "description": "Extract subtitles from a YouTube video for specific chapters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "YouTube video URL",
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code for subtitles (e.g., 'en' for English, 'es' for Spanish)",
                            "default": "en"
                        },
                        "chapters": {
                            "type": "array",
                            "description": "List of chapters to extract subtitles for, with start_time in seconds and title",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "start_time": {"type": "number"},
                                    "title": {"type": "string"}
                                }
                            }
                        },
                    },
                    "required": ["url", "chapters"],
                },
            },
        }


def get_youtube_subtitles_tool_handler(yt_dlp_service: YtDlpService) -> Callable:
    """
    Get the handler function for the YouTube subtitles extraction tool.

    Args:
        yt_dlp_service: The YtDlpService instance

    Returns:
        Function that handles YouTube subtitle extraction requests
    """

    def handle_youtube_subtitles(**params) -> str:
        url = params.get("url")
        if not url:
            raise Exception("URL is required")

        chapters = params.get("chapters")
        if not chapters:
            raise Exception("Chapters are required")

        language = params.get("language", "en")
        
        result = yt_dlp_service.extract_subtitles(url, language, chapters)
        
        if result["success"]:
            return result["content"]
        else:
            error_message = result.get("error", "Unknown error")
            raise Exception(f"Failed to extract subtitles: {error_message}")

    return handle_youtube_subtitles
