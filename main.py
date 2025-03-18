import click
import importlib

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
from modules.agents.manager import AgentManager
from modules.agents.specialized import (
    ArchitectAgent,
    TechLeadAgent,
    DocumentationAgent,
)


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


def setup_services(provider):
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
        "code_analysis": code_analysis_service,
        "web_search": search_service,
        "spec_validator": spec_validator,
        # "scraping": scraping_service,
    }
    return services


def register_agent_tools(agent, services):
    """
    Register appropriate tools for each agent type.

    Args:
        agent: The agent to register tools for
        services: Dictionary of available services
    """
    # Register the handoff tool with all agents
    if services.get("agent_manager"):
        from modules.agents.tools.handoff import register as register_handoff

        register_handoff(services["agent_manager"], agent)

    # Common tools for all agents
    if services.get("clipboard"):
        from modules.clipboard.tool import register as register_clipboard

        register_clipboard(services["clipboard"], agent)

    if services.get("memory"):
        from modules.memory.tool import register as register_memory

        register_memory(services["memory"], agent)

    if agent.name == "Architect":
        if services.get("web_search"):
            from modules.web_search.tool import register as register_web_search

            register_web_search(services["web_search"], agent)

    # Agent-specific tools
    if agent.name == "Architect" or agent.name == "TechLead":
        # Code analysis tools for technical agents
        if services.get("code_analysis"):
            from modules.code_analysis.tool import register as register_code_analysis

            register_code_analysis(services["code_analysis"], agent)

    if agent.name == "TechLead":
        # Spec validation for Code Assistant
        if services.get("spec_validator"):
            from modules.coder.tool import register as register_spec_validator

            register_spec_validator(services["spec_validator"], agent)


def setup_agents(services):
    """
    Set up the agent system with specialized agents.

    Args:
        services: Dictionary of services
    """
    # Get the singleton instance of agent manager
    agent_manager = AgentManager.get_instance()

    # Add agent_manager to services for tool registration
    services["agent_manager"] = agent_manager

    # Get the LLM service
    llm_service = services["llm"]

    # Create specialized agents
    architect = ArchitectAgent(llm_service)
    code_assistant = TechLeadAgent(llm_service)
    documentation = DocumentationAgent(llm_service)

    # Register appropriate tools for each agent
    register_agent_tools(architect, services)
    register_agent_tools(code_assistant, services)
    register_agent_tools(documentation, services)

    # Register agents with the manager - this will keep them deactivated until selected
    agent_manager.register_agent(architect)
    agent_manager.register_agent(code_assistant)
    agent_manager.register_agent(documentation)

    return agent_manager

def discover_and_register_tools(services=None):
    """
    Discover and register all tools

    DEPRECATED: This function is deprecated and will be removed in a future version.
    Use setup_agents() and register_agent_tools() instead.

    Args:
        services: Dictionary mapping service names to service instances
    """
    import warnings

    warnings.warn(
        "discover_and_register_tools is deprecated. Use setup_agents() and register_agent_tools() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if services is None:
        services = {}

    # List of tool modules and their corresponding service keys
    tool_modules = [
        ("modules.memory.tool", "memory"),
        ("modules.code_analysis.tool", "code_analysis"),
        ("modules.clipboard.tool", "clipboard"),
        ("modules.web_search.tool", "web_search"),
        ("modules.coder.tool", "spec_validator"),
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
@click.option(
    "--agent",
    type=str,
    default="Architect",
    help="Initial agent to use (Architect, TechLead, Documentation, Evaluation)",
)
def chat(message, files, provider, agent):
    """Start an interactive chat session with LLM"""
    try:
        services = setup_services(provider)

        # Set up the agent system
        agent_manager = setup_agents(services)

        # Select the initial agent if specified
        if agent:
            if not agent_manager.select_agent(agent):
                available_agents = ", ".join(agent_manager.agents.keys())
                click.echo(
                    f"⚠️ Unknown agent: {agent}. Using default agent. Available agents: {available_agents}"
                )

        # Create the chat interface with the agent manager injected
        chat_interface = InteractiveChat(services["memory"])

        # Start the chat
        chat_interface.start_chat(initial_content=message, files=files)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
