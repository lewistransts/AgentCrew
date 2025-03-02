import click
from modules.ytdlp import (
    YtDlpService,
    get_youtube_subtitles_tool_definition,
    get_youtube_subtitles_tool_handler,
    get_youtube_chapters_tool_definition,
    get_youtube_chapters_tool_handler,
)
from modules.scraping import ScrapingService
from modules.web_search import (
    TavilySearchService,
    get_web_search_tool_definition,
    get_web_search_tool_handler,
    get_web_extract_tool_definition,
    get_web_extract_tool_handler,
)
from modules.clipboard import (
    ClipboardService,
    get_clipboard_read_tool_definition,
    get_clipboard_read_tool_handler,
    get_clipboard_write_tool_definition,
    get_clipboard_write_tool_handler,
)
from modules.anthropic import AnthropicService
from modules.groq import GroqService
from modules.chat import InteractiveChat


@click.group()
def cli():
    """URL to Markdown conversion tool with LLM integration"""
    pass


@cli.command()
@click.argument("url")
@click.argument("output_file")
@click.option("--summarize", is_flag=True, help="Summarize the content using Claude")
@click.option(
    "--explain", is_flag=True, help="Explain the content for non-experts using Claude"
)
def get_url(url: str, output_file: str, summarize: bool, explain: bool):
    """Fetch URL content and save as markdown"""
    if summarize and explain:
        raise click.UsageError(
            "Cannot use both --summarize and --explain options together"
        )

    try:
        click.echo(f"\n🌐 Fetching content from: {url}")
        scraper = ScrapingService()
        content = scraper.scrape_url(url)
        click.echo("✅ Content successfully scraped")

        if summarize or explain:
            # Create the LLM service
            llm_service = AnthropicService()

            if summarize:
                click.echo("\n🤖 Summarizing content using LLM...")
                content = llm_service.summarize_content(content)
                click.echo("✅ Content successfully summarized")
            else:  # explain
                click.echo("\n🤖 Explaining content using LLM...")
                content = llm_service.explain_content(content)
                click.echo("✅ Content successfully explained")

        click.echo(f"\n💾 Saving content to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        operation = "explained" if explain else "summarized" if summarize else ""
        click.echo(
            f"✅ Successfully saved {operation + ' ' if operation else ''}markdown to {output_file}"
        )
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
@click.option("--message", help="Initial message to start the chat")
@click.option("--files", multiple=True, help="Files to include in the initial message")
@click.option(
    "--provider",
    type=click.Choice(["claude", "groq"]),
    default="claude",
    help="LLM provider to use (claude or groq)",
)
def chat(message, files, provider):
    """Start an interactive chat session with LLM"""
    try:
        # Create the LLM service based on provider choice
        if provider == "claude":
            llm_service = AnthropicService()
        else:  # provider == "groq"
            llm_service = GroqService()

        # Create clipboard service
        clipboard_service = ClipboardService()

        # Register clipboard tools
        llm_service.register_tool(
            get_clipboard_read_tool_definition(provider),
            get_clipboard_read_tool_handler(clipboard_service),
        )
        llm_service.register_tool(
            get_clipboard_write_tool_definition(provider),
            get_clipboard_write_tool_handler(clipboard_service),
        )

        # Try to create search service and register web search tools if API key is available
        try:
            search_service = TavilySearchService()
            # If initialization succeeds, register the tools
            llm_service.register_tool(
                get_web_search_tool_definition(provider),
                get_web_search_tool_handler(search_service),
            )
            llm_service.register_tool(
                get_web_extract_tool_definition(provider),
                get_web_extract_tool_handler(search_service),
            )
        except Exception as e:
            click.echo(f"⚠️ Web search tools not available: {str(e)}")

        youtube_service = YtDlpService()

        llm_service.register_tool(
            get_youtube_subtitles_tool_definition(provider),
            get_youtube_subtitles_tool_handler(youtube_service),
        )

        # Register YouTube chapters tool
        llm_service.register_tool(
            get_youtube_chapters_tool_definition(provider),
            get_youtube_chapters_tool_handler(youtube_service),
        )

        # Create the chat interface with the LLM service injected
        chat_interface = InteractiveChat(llm_service)

        # Start the chat
        chat_interface.start_chat(initial_content=message, files=files)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
