import click
import importlib
from modules.ytdlp import YtDlpService
from modules.scraping import ScrapingService
from modules.web_search import TavilySearchService
from modules.clipboard import ClipboardService
from modules.memory import MemoryService
from modules.code_analysis import CodeAnalysisService
from modules.anthropic import AnthropicService
from modules.chat import InteractiveChat
from modules.llm.service_manager import ServiceManager
from modules.llm.models import ModelRegistry
from modules.coder import SpecPromptValidationService


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


def services_load(provider):
    # Initialize the model registry and service manager
    registry = ModelRegistry.get_instance()
    manager = ServiceManager.get_instance()

    # Set the current model based on provider
    models = registry.get_models_by_provider(provider)
    if models:
        # Find default model for this provider
        default_model = next((m for m in models if m.default), models[0])
        registry.set_current_model(default_model.id)

    # Get the LLM service from the manager
    llm_service = manager.get_service(provider)

    # Initialize services
    memory_service = MemoryService()
    clipboard_service = ClipboardService()
    youtube_service = YtDlpService()
    spec_validator = SpecPromptValidationService("groq")
    # Try to create search service if API key is available
    try:
        search_service = TavilySearchService(llm=llm_service)
    except Exception as e:
        click.echo(f"⚠️ Web search tools not available: {str(e)}")
        search_service = None

    # Initialize code analysis service
    try:
        code_analysis_service = CodeAnalysisService()
    except Exception as e:
        click.echo(f"⚠️ Code analysis tool not available: {str(e)}")
        code_analysis_service = None

    # try:
    #     scraping_service = ScrapingService()
    # except Exception as e:
    #     click.echo(f"⚠️ Scraping service not available: {str(e)}")
    #     scraping_service = None

    # Clean up old memories (older than 1 month)
    try:
        removed_count = memory_service.cleanup_old_memories(months=1)
        if removed_count > 0:
            click.echo(f"🧹 Cleaned up {removed_count} old conversation memories")
    except Exception as e:
        click.echo(f"⚠️ Memory cleanup failed: {str(e)}")

    # Register all tools with their respective services
    services = {
        "llm": llm_service,
        "memory": memory_service,
        "clipboard": clipboard_service,
        "ytdlp": youtube_service,
        "code_analysis": code_analysis_service,
        "web_search": search_service,
        "spec_validator": spec_validator,
        # "scraping": scraping_service,
    }
    return services


def discover_and_register_tools(services=None):
    """
    Discover and register all tools

    Args:
        services: Dictionary mapping service names to service instances
    """
    if services is None:
        services = {}

    # List of tool modules and their corresponding service keys
    tool_modules = [
        ("modules.memory.tool", "memory"),
        ("modules.code_analysis.tool", "code_analysis"),
        ("modules.clipboard.tool", "clipboard"),
        ("modules.web_search.tool", "web_search"),
        (
            "modules.coder.tool",
            "spec_validator",
        ),
    ]

    for module_name, service_key in tool_modules:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "register"):
                service_instance = services.get(service_key)
                module.register(service_instance)
                # print(f"✅ Registered tools from {module_name}")
        except ImportError as e:
            print(f"⚠️ Error importing tool module {module_name}: {e}")

    from modules.mcpclient.tool import register as mcp_register

    mcp_register()


@cli.command()
@click.option("--message", help="Initial message to start the chat")
@click.option("--files", multiple=True, help="Files to include in the initial message")
@click.option(
    "--provider",
    type=click.Choice(["claude", "groq", "openai"]),
    default="claude",
    help="LLM provider to use (claude, groq, or openai)",
)
def chat(message, files, provider):
    """Start an interactive chat session with LLM"""
    try:
        services = services_load(provider)

        discover_and_register_tools(services)

        llm_service = services["llm"]
        # Register all tools with the LLM service
        llm_service.register_all_tools()

        # Create the chat interface with the LLM service injected
        chat_interface = InteractiveChat(llm_service, services["memory"])

        # Start the chat
        chat_interface.start_chat(initial_content=message, files=files)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        # Clean up service manager
        try:
            manager = ServiceManager.get_instance()
            manager.cleanup()
        except Exception as e:
            click.echo(f"⚠️ Error during cleanup: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
