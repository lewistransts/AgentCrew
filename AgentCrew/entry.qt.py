import os
import sys
import traceback
from datetime import datetime
from AgentCrew.modules.gui import ChatWindow
from AgentCrew.modules.chat import MessageHandler
from AgentCrew.modules.web_search import TavilySearchService
from AgentCrew.modules.clipboard import ClipboardService
from AgentCrew.modules.memory import (
    ChromaMemoryService,
    ContextPersistenceService,
)
from AgentCrew.modules.code_analysis import CodeAnalysisService
from AgentCrew.modules.llm.service_manager import ServiceManager
from AgentCrew.modules.llm.model_registry import ModelRegistry
from AgentCrew.modules.coding import SpecPromptValidationService
from AgentCrew.modules.agents import AgentManager, LocalAgent, RemoteAgent
from PySide6.QtWidgets import QApplication, QMessageBox

import nest_asyncio

nest_asyncio.apply()


def setup_env_vars():
    os.environ["MEMORYDB_PATH"] = os.path.expanduser("~/.AgentCrew/memorydb")
    os.environ["MCP_CONFIG_PATH"] = os.path.expanduser("~/.AgentCrew/mcp_server.json")
    os.environ["SW_AGENTS_CONFIG"] = os.path.expanduser("~/.AgentCrew/agents.toml")
    os.environ["PERSISTENCE_DIR"] = os.path.expanduser("~/.AgentCrew/persistents")


def setup_services(provider):
    # Initialize the model registry and service manager
    registry = ModelRegistry.get_instance()
    llm_manager = ServiceManager.get_instance()

    # Set the current model based on provider
    models = registry.get_models_by_provider(provider)
    if models:
        # Find default model for this provider
        default_model = next((m for m in models if m.default), models[0])
        registry.set_current_model(f"{default_model.provider}/{default_model.id}")

    # Get the LLM service from the manager
    llm_service = llm_manager.get_service(provider)

    # Initialize services
    memory_service = ChromaMemoryService()
    context_service = ContextPersistenceService()
    clipboard_service = ClipboardService()
    aider_service = SpecPromptValidationService("groq")
    # Try to create search service if API key is available
    try:
        search_service = TavilySearchService()
    except Exception as e:
        print(f"⚠️ Web search tools not available: {str(e)}")
        search_service = None

    # Initialize code analysis service
    try:
        code_analysis_service = CodeAnalysisService()
    except Exception as e:
        print(f"⚠️ Code analysis tool not available: {str(e)}")
        code_analysis_service = None

    # Clean up old memories (older than 1 month)
    try:
        removed_count = memory_service.cleanup_old_memories(months=1)
        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} old conversation memories")
    except Exception as e:
        print(f"⚠️ Memory cleanup failed: {str(e)}")

    # Register all tools with their respective services
    services = {
        "llm": llm_service,
        "memory": memory_service,
        "clipboard": clipboard_service,
        "code_analysis": code_analysis_service,
        "web_search": search_service,
        "aider": aider_service,
        "context_persistent": context_service,
    }
    return services


def setup_agents(services, config_path, standalone_provider=None):
    """
    Set up the agent system with specialized agents.

    Args:
        services: Dictionary of services
    """
    # Get the singleton instance of agent manager
    agent_manager = AgentManager.get_instance()
    llm_manager = ServiceManager.get_instance()

    # Add agent_manager to services for tool registration
    services["agent_manager"] = agent_manager

    # Get the LLM service
    llm_service = services["llm"]

    # Create specialized agents
    if config_path:
        os.environ["SW_AGENTS_CONFIG"] = config_path
    else:
        config_path = os.getenv("SW_AGENTS_CONFIG")
        if not config_path:
            config_path = "./agents.toml"
        if not os.path.exists(config_path):
            print(
                f"Agent configuration not found at {config_path}. Creating default configuration."
            )
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            default_config = """# Default SwissKnife Agent Configuration
[[agents]]
name = "default"
description = "Default assistant agent"
system_prompt = \"\"\"You are a helpful AI assistant. Always provide accurate, helpful, and ethical responses.
Current date: {current_date}
\"\"\"
tools = ["memory", "clipboard", "web_search", "code_analysis"]
"""

            with open(config_path, "w+") as f:
                f.write(default_config)

            print(f"Created default agent configuration at {config_path}")

    # Load agents from configuration
    agent_definitions = AgentManager.load_agents_from_config(config_path)
    first_agent_name = None
    for agent_def in agent_definitions:
        if agent_def.get("base_url", ""):
            agent = RemoteAgent(agent_def["name"], agent_def.get("base_url"))
        else:
            if not first_agent_name:
                first_agent_name = agent_def["name"]
            if standalone_provider:
                llm_service = llm_manager.initialize_standalone_service(
                    standalone_provider
                )
            agent = LocalAgent(
                name=agent_def["name"],
                description=agent_def["description"],
                llm_service=llm_service,
                services=services,
                tools=agent_def["tools"],
                temperature=agent_def.get("temperature", None),
            )
            agent.set_system_prompt(
                agent_def["system_prompt"].replace(
                    "{current_date}", datetime.today().strftime("%Y-%m-%d")
                )
            )
        agent_manager.register_agent(agent)

    from AgentCrew.modules.mcpclient.tool import register as mcp_register

    mcp_register()

    # Select the initial agent if specified
    if first_agent_name:
        if not agent_manager.select_agent(first_agent_name):
            available_agents = ", ".join(agent_manager.agents.keys())
            print(
                f"⚠️ Unknown agent: {first_agent_name}. Using default agent. Available agents: {available_agents}"
            )


def start_chat_gui():
    """Start an interactive chat session with LLM using Qt GUI."""
    try:
        provider = None
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "claude"
        elif os.getenv("GEMINI_API_KEY"):
            provider = "google"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("GROQ_API_KEY"):
            provider = "groq"
        elif os.getenv("DEEPINFRA_API_KEY"):
            provider = "deepinfra"
        else:
            error_message = "No LLM API key found. Please set ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, or DEEPINFRA_API_KEY."
            print(f"❌ Error: {error_message}", file=sys.stderr)
            try:
                app_exists = QApplication.instance()
                if not app_exists:
                    app_temp = QApplication(sys.argv)
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setText("Configuration Error")
                msg_box.setInformativeText(error_message)
                msg_box.setWindowTitle("Application Error")
                msg_box.exec()
                if not app_exists:
                    app_temp.quit()
            except Exception as e_gui:
                print(f"Error showing GUI message: {e_gui}", file=sys.stderr)
            sys.exit(1)

        services = setup_services(provider)

        # Agent config path is taken from environment variable set by setup_env_vars()
        # or defaults within setup_agents()
        agent_config_path = os.getenv("SW_AGENTS_CONFIG")
        setup_agents(services, agent_config_path)

        message_handler = MessageHandler(
            services["memory"], services["context_persistent"]
        )

        app = QApplication(sys.argv)
        chat_window = ChatWindow(message_handler)
        chat_window.show()
        sys.exit(app.exec())

    except SystemExit:
        # This allows graceful exit and cleanup if sys.exit() is called
        from AgentCrew.modules.mcpclient import MCPSessionManager

        MCPSessionManager.get_instance().cleanup()
    except Exception as e:
        print(traceback.format_exc(), file=sys.stderr)
        error_message = f"An unexpected error occurred: {str(e)}"
        print(f"❌ Error: {error_message}", file=sys.stderr)
        try:
            app_exists = QApplication.instance()
            if not app_exists:
                app_temp = QApplication(sys.argv)
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText("Application Error")
            msg_box.setInformativeText(error_message)
            msg_box.setWindowTitle("Fatal Error")
            msg_box.exec()
            if not app_exists:
                app_temp.quit()
        except Exception as e_gui:
            print(f"Error showing GUI message: {e_gui}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    setup_env_vars()
    start_chat_gui()
