from .registry import ToolRegistry

def register_tool(definition_func, handler_factory, service_instance=None):
    """
    Register a tool with the central registry

    Args:
        definition_func: Function that returns tool definition given a provider
        handler_factory: Function that creates a handler function
        service_instance: Service instance needed by the handler (optional)
    """
    registry = ToolRegistry.get_instance()
    registry.register_tool(definition_func, handler_factory, service_instance)
